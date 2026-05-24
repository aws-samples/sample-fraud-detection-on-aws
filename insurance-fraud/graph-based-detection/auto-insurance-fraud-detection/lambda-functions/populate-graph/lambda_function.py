import json
import os
import random
import time
import uuid
import aiohttp  # Required by gremlinpython
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.traversal import T
from gremlin_python.process.graph_traversal import __
from aws_lambda_powertools import Logger

logger = Logger()

# --- Geolocation Data ---
# Metro area center (e.g., Miami FL area)
METRO_CENTER = (25.76, -80.19)

# Fraud hotspot zones — small clusters where fraud concentrates
FRAUD_ZONES = [
    {'center': (25.82, -80.22), 'radius': 0.015, 'zip': '33142'},  # NW cluster
    {'center': (25.69, -80.25), 'radius': 0.012, 'zip': '33155'},  # SW cluster
    {'center': (25.78, -80.13), 'radius': 0.010, 'zip': '33137'},  # NE cluster
]

# Legitimate spread — wider metro area zip codes
LEGIT_ZIPS = ['33101', '33109', '33125', '33130', '33133', '33139',
              '33145', '33150', '33160', '33165', '33170', '33175',
              '33180', '33185', '33190', '33196']


def _random_point_near(center, radius):
    """Generate a random lat/lng within radius degrees of center."""
    lat = center[0] + random.uniform(-radius, radius)
    lng = center[1] + random.uniform(-radius, radius)
    return round(lat, 6), round(lng, 6)


def _legit_location():
    """Generate a random location spread across the wider metro."""
    lat = METRO_CENTER[0] + random.uniform(-0.15, 0.15)
    lng = METRO_CENTER[1] + random.uniform(-0.15, 0.15)
    return round(lat, 6), round(lng, 6), random.choice(LEGIT_ZIPS)


def _fraud_location():
    """Generate a location within one of the fraud hotspot zones."""
    zone = random.choice(FRAUD_ZONES)
    lat, lng = _random_point_near(zone['center'], zone['radius'])
    return lat, lng, zone['zip']


# --- Temporal Burst Helpers ---
def _fraud_burst_timestamp(burst_base):
    """Generate a timestamp within a 7-day burst window."""
    return burst_base + random.randint(0, 7 * 86400)


def _legit_timestamp():
    """Generate a timestamp spread evenly across the past year."""
    return int(time.time()) - random.randint(0, 365 * 86400)


# --- Shared Contact Data ---
FRAUD_PHONES = [f'305-555-{i:04d}' for i in range(10)]
FRAUD_EMAILS = [f'user{i}@quickmail.net' for i in range(10)]
FRAUD_ADDRESSES = [
    '1420 NW 7th St, Apt 3', '890 SW 8th St, Unit 12', '2250 NW 36th St, Apt 7',
    '445 NW 27th Ave, Unit 5', '1100 SW 1st St, Apt 9',
]


RANDOM_SEED = 42  # Deterministic seed for reproducible graph data


def _add_entity_with_fraud(g, label, entity_id, properties, fraud_score):
    """Create an entity vertex and a linked ::fraudEntity vertex with the fraud score."""
    t = g.addV(label).property(T.id, entity_id)
    for k, v in properties.items():
        t = t.property(k, v)
    t.next()

    fraud_id = f"{entity_id}::fraud"
    g.addV('fraudEntity').property(T.id, fraud_id).property('fraudScore', fraud_score).next()
    g.V(entity_id).addE('has_fraud_score').to(__.V(fraud_id)).next()


def _batch_add_vertices(g, vertices):
    """Add vertices one at a time.

    NOTE: Neptune does NOT support chaining multiple addV() calls in a single
    traversal (e.g. g.addV(...).addV(...).iterate()). Doing so throws:
    'Could not locate method: NeptuneGraphTraversal.discard()'
    Each vertex must be its own traversal with .next().
    """
    for label, vid, props in vertices:
        t = g.addV(label).property(T.id, vid)
        for k, v in props.items():
            t = t.property(k, v)
        t.next()


def _batch_add_edges(g, edges):
    """Add edges one at a time (same Neptune limitation as vertices)."""
    for from_id, edge_label, to_id in edges:
        g.V(from_id).addE(edge_label).to(__.V(to_id)).next()


@logger.inject_lambda_context
def lambda_handler(event, context):
    """Populate Neptune with synthetic auto insurance data"""

    endpoint = os.environ['NEPTUNE_ENDPOINT']
    conn_string = f"wss://{endpoint}:8182/gremlin"
    region = os.environ['AWS_REGION']

    credentials = Session().get_credentials()
    if credentials is None:
        raise Exception("No AWS credentials found")
    creds = credentials.get_frozen_credentials()

    request = AWSRequest(method='GET', url=conn_string, data=None)
    SigV4Auth(creds, 'neptune-db', region).add_auth(request)

    remoteConn = DriverRemoteConnection(conn_string, 'g', headers=dict(request.headers.items()))
    g = traversal().withRemote(remoteConn)

    logger.info("Clearing existing graph data")
    try:
        while True:
            count = g.V().count().next()
            if count == 0:
                break
            logger.info(f"Dropping batch ({count} vertices remaining)")
            g.V().limit(500).drop().toList()
        logger.info("Graph cleared successfully")
    except Exception as e:
        logger.warning(f"Graph clear failed or already empty: {str(e)}")

    logger.info("Starting to populate auto insurance graph")

    random.seed(RANDOM_SEED)

    # --- Claimants ---
    # Improvement 4 & 5: Address and phone/email sharing for fraud claimants
    claimants = []
    claimant_vertices = []
    for i in range(1000):
        claimant_id = str(uuid.uuid4())
        props = {'name': f'Claimant {i}', 'licenseNumber': f'DL{i:06d}'}

        # First 50 claimants are fraud ring members — share addresses/phones
        if i < 50:
            props['address'] = FRAUD_ADDRESSES[i % len(FRAUD_ADDRESSES)]
            props['phone'] = FRAUD_PHONES[i % len(FRAUD_PHONES)]
            props['email'] = FRAUD_EMAILS[i % len(FRAUD_EMAILS)]
        else:
            props['address'] = f'{random.randint(100,9999)} {random.choice(["Oak","Pine","Elm","Maple","Cedar"])} {random.choice(["St","Ave","Blvd","Dr"])}'
            props['phone'] = f'305-{random.randint(200,999)}-{random.randint(1000,9999)}'
            props['email'] = f'claimant{i}@{random.choice(["gmail.com","yahoo.com","outlook.com"])}'

        claimant_vertices.append(('claimant', claimant_id, props))
        claimants.append(claimant_id)
    _batch_add_vertices(g, claimant_vertices)
    logger.info(f"Created {len(claimants)} claimants")

    # --- Vehicles ---
    vehicles = []
    makes = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes', 'Nissan', 'Hyundai']
    vehicle_vertices = []
    vehicle_edges = []
    for i in range(1500):
        vehicle_id = str(uuid.uuid4())
        owner_id = random.choice(claimants)
        plate = f'{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.randint(1000,9999)}'
        vehicle_vertices.append(('vehicle', vehicle_id, {'vin': f'VIN{i:010d}', 'make': random.choice(makes), 'year': random.randint(2010, 2024), 'plate': plate, 'ownerId': owner_id}))
        vehicle_edges.append((owner_id, 'owns', vehicle_id))
        vehicles.append(vehicle_id)
    _batch_add_vertices(g, vehicle_vertices)
    _batch_add_edges(g, vehicle_edges)
    logger.info(f"Created {len(vehicles)} vehicles")

    # --- Repair Shops (10% suspicious) — with geolocation ---
    repair_shops = []
    for i in range(200):
        shop_id = str(uuid.uuid4())
        is_suspicious = i < 20
        rating = 2.5 if is_suspicious else random.uniform(4.0, 5.0)
        fraud_score = random.uniform(0.7, 0.95) if is_suspicious else random.uniform(0.1, 0.4)

        if is_suspicious:
            lat, lng, zip_code = _fraud_location()
        else:
            lat, lng, zip_code = _legit_location()

        _add_entity_with_fraud(g, 'repairShop', shop_id,
            {'name': f'Repair Shop {i}', 'rating': rating, 'suspicious': is_suspicious,
             'latitude': lat, 'longitude': lng, 'zipCode': zip_code},
            fraud_score)
        repair_shops.append(shop_id)
    logger.info(f"Created {len(repair_shops)} repair shops")

    # --- Medical Providers — with geolocation ---
    medical_providers = []
    specialties = ['Orthopedic', 'Chiropractor', 'Physical Therapy']
    for i in range(150):
        provider_id = str(uuid.uuid4())
        is_suspicious = i < 20
        fraud_score = random.uniform(0.7, 0.9) if is_suspicious else random.uniform(0.1, 0.4)

        if is_suspicious:
            lat, lng, zip_code = _fraud_location()
        else:
            lat, lng, zip_code = _legit_location()

        _add_entity_with_fraud(g, 'medicalProvider', provider_id,
            {'name': f'Dr. Provider {i}', 'specialty': random.choice(specialties),
             'latitude': lat, 'longitude': lng, 'zipCode': zip_code},
            fraud_score)
        medical_providers.append(provider_id)
    logger.info(f"Created {len(medical_providers)} medical providers")

    # --- Witnesses (20% professional) ---
    witnesses = []
    for i in range(300):
        witness_id = str(uuid.uuid4())
        is_professional = i < 60
        fraud_score = random.uniform(0.75, 0.95) if is_professional else random.uniform(0.1, 0.3)
        _add_entity_with_fraud(g, 'witness', witness_id,
            {'name': f'Witness {i}', 'professional': is_professional},
            fraud_score)
        witnesses.append(witness_id)
    logger.info(f"Created {len(witnesses)} witnesses")

    # --- Attorneys (20% corrupt) ---
    attorneys = []
    for i in range(250):
        attorney_id = str(uuid.uuid4())
        is_corrupt = i < 50
        fraud_score = random.uniform(0.7, 0.9) if is_corrupt else random.uniform(0.1, 0.35)
        _add_entity_with_fraud(g, 'attorney', attorney_id,
            {'name': f'Attorney {i}', 'firmName': f'Law Firm {i}'},
            fraud_score)
        attorneys.append(attorney_id)
    logger.info(f"Created {len(attorneys)} attorneys")

    # --- Tow Companies (20% corrupt) — with geolocation ---
    tow_companies = []
    for i in range(200):
        tow_id = str(uuid.uuid4())
        is_corrupt = i < 40
        fraud_score = random.uniform(0.7, 0.9) if is_corrupt else random.uniform(0.1, 0.35)

        if is_corrupt:
            lat, lng, zip_code = _fraud_location()
        else:
            lat, lng, zip_code = _legit_location()

        _add_entity_with_fraud(g, 'towCompany', tow_id,
            {'name': f'Tow Company {i}',
             'latitude': lat, 'longitude': lng, 'zipCode': zip_code},
            fraud_score)
        tow_companies.append(tow_id)
    logger.info(f"Created {len(tow_companies)} tow companies")

    # --- Serial "jump-in" passengers (Stuffed Passengers pattern) ---
    serial_jumpins = []
    for i in range(20):
        sp_id = str(uuid.uuid4())
        accomplice_provider = medical_providers[i % 5]
        _add_entity_with_fraud(g, 'passenger', sp_id,
            {'name': f'Serial Jump-in {sp_id[:8]}'},
            random.uniform(0.88, 0.98))
        g.V(sp_id).addE('treated_by').to(__.V(accomplice_provider)).next()
        serial_jumpins.append((sp_id, accomplice_provider))
    logger.info(f"Created {len(serial_jumpins)} serial jump-in passengers")

    # --- Cross-Ring Passengers (Improvement 2) ---
    # These passengers appear in accidents filed by UNRELATED claimants,
    # creating the strongest fraud signal: same person in 3+ unrelated accidents.
    cross_ring_passengers = []
    for i in range(15):
        cp_id = str(uuid.uuid4())
        _add_entity_with_fraud(g, 'passenger', cp_id,
            {'name': f'Cross-Ring Passenger {cp_id[:8]}',
             'phone': FRAUD_PHONES[i % len(FRAUD_PHONES)]},
            random.uniform(0.90, 0.99))
        cross_ring_passengers.append(cp_id)
    logger.info(f"Created {len(cross_ring_passengers)} cross-ring passengers")

    # --- Policy-Hopping Vehicles (Improvement 1) ---
    # Vehicles that appear in claims under DIFFERENT owners — classic "paper car" fraud.
    # Pick 10 vehicles and reassign ownership across unrelated claimants.
    policy_hop_vehicles = vehicles[:10]
    for v_id in policy_hop_vehicles:
        # Add 2-3 extra owners (different from original) via 'owns' edges
        extra_owners = random.sample(claimants[50:100], random.randint(2, 3))
        for owner_id in extra_owners:
            g.V(owner_id).addE('owns').to(__.V(v_id)).next()
    logger.info(f"Created {len(policy_hop_vehicles)} policy-hopping vehicles")

    # --- High-Velocity Claimants (Improvement 2) ---
    # Claimants who file 4-5 claims in a 60-day window — abnormal claim frequency.
    high_velocity_claimants = claimants[50:60]  # 10 claimants, outside fraud rings

    # --- Injury Escalation Claimants (Improvement 3) ---
    # Claimants whose claim amounts escalate: $2K -> $5K -> $12K pattern.
    escalation_claimants = claimants[60:70]  # 10 claimants
    ESCALATION_AMOUNTS = [2000, 3500, 5500, 9000, 14000]

    # --- Claims & Accidents ---
    claims_created = 0
    fraud_rings = [claimants[:50], claimants[100:150]]

    # Temporal burst bases — fraud rings operate in tight time windows
    burst_bases = [
        int(time.time()) - random.randint(30, 90) * 86400  # burst 1: 1-3 months ago
        for _ in range(4)
    ]

    for i in range(2000):
        is_fraud = i < 40

        # Accident vertex with geolocation
        accident_id = str(uuid.uuid4())
        if is_fraud:
            lat, lng, zip_code = _fraud_location()
            accident_type = random.choice(['rear-end', 'rear-end', 'side-impact'])
            maneuver_type = random.choice(['swoop-squat', 'sudden-stop', 'normal'])
            police_verified = random.random() < 0.3
            # Temporal burst: fraud claims cluster in time
            claim_ts = _fraud_burst_timestamp(random.choice(burst_bases))
        else:
            lat, lng, zip_code = _legit_location()
            accident_type = random.choice(['rear-end', 'side-impact', 'head-on'])
            maneuver_type = 'normal'
            police_verified = random.random() < 0.9
            claim_ts = _legit_timestamp()

        accident_date = time.strftime('%Y-%m-%d', time.gmtime(claim_ts))
        g.addV('accident').property(T.id, accident_id) \
            .property('date', accident_date) \
            .property('location', f'{zip_code}') \
            .property('latitude', lat).property('longitude', lng) \
            .property('zipCode', zip_code) \
            .property('accidentType', accident_type) \
            .property('maneuverType', maneuver_type) \
            .property('policeVerified', police_verified).next()

        # Claim
        claim_id = str(uuid.uuid4())
        if is_fraud:
            fraud_score = random.uniform(0.7, 0.95)
            amount = random.uniform(8000, 15000)
            claimant_id = random.choice(random.choice(fraud_rings))
            repair_shop_id = repair_shops[0] if random.random() > 0.5 else repair_shops[1]
            witness_id = witnesses[random.randint(0, 5)]
        else:
            fraud_score = random.uniform(0.1, 0.5)
            amount = random.uniform(1000, 6000)
            claimant_id = random.choice(claimants)
            repair_shop_id = random.choice(repair_shops[2:])
            witness_id = random.choice(witnesses[6:])

        _add_entity_with_fraud(g, 'claim', claim_id,
            {'amount': amount, 'isFraud': is_fraud, 'status': 'approved', 'claimDate': claim_ts},
            fraud_score)

        # Edges
        g.V(claimant_id).addE('filed_claim').to(__.V(claim_id)).next()
        g.V(claim_id).addE('for_accident').to(__.V(accident_id)).next()

        vehicle_id = random.choice(vehicles)
        role = random.choice(['at-fault', 'victim'])
        g.V(accident_id).addE('involved_vehicle').to(__.V(vehicle_id)).property('role', role).next()
        g.V(claim_id).addE('repaired_at').to(__.V(repair_shop_id)).next()
        g.V(accident_id).addE('witnessed_by').to(__.V(witness_id)).next()

        # Medical provider (50% of claims)
        if random.random() > 0.5:
            provider_id = random.choice(medical_providers)
            g.V(claimant_id).addE('treated_by').to(__.V(provider_id)).next()

        # Attorney (60% fraud, 20% legitimate)
        if (is_fraud and random.random() < 0.6) or (not is_fraud and random.random() < 0.2):
            attorney_id = attorneys[random.randint(0, 2)] if is_fraud else random.choice(attorneys[3:])
            g.V(claimant_id).addE('represented_by').to(__.V(attorney_id)).next()

        # Tow company (50% of claims)
        if random.random() < 0.5:
            tow_id = tow_companies[random.randint(0, 1)] if is_fraud else random.choice(tow_companies[2:])
            g.V(vehicle_id).addE('towed_by').to(__.V(tow_id)).next()

        # Stuffed passengers (40% of fraud claims)
        if is_fraud and random.random() < 0.4:
            for _ in range(random.randint(1, 3)):
                if random.random() < 0.3:
                    sp_id, accomplice_provider = random.choice(serial_jumpins)
                    g.V(sp_id).addE('passenger_in').to(__.V(accident_id)).next()
                    g.V(sp_id).addE('claimed_injury').to(__.V(claim_id)).next()
                else:
                    passenger_id = str(uuid.uuid4())
                    _add_entity_with_fraud(g, 'passenger', passenger_id,
                        {'name': f'Passenger {passenger_id[:8]}'},
                        random.uniform(0.7, 0.95))
                    g.V(passenger_id).addE('passenger_in').to(__.V(accident_id)).next()
                    g.V(passenger_id).addE('claimed_injury').to(__.V(claim_id)).next()
                    provider_id = medical_providers[random.randint(0, 19)] if random.random() < 0.7 else random.choice(medical_providers)
                    g.V(passenger_id).addE('treated_by').to(__.V(provider_id)).next()

        # Cross-ring passengers: inject into BOTH fraud and some legit claims
        # to create the pattern of same passenger in unrelated accidents
        if is_fraud and random.random() < 0.5:
            cp = random.choice(cross_ring_passengers)
            g.V(cp).addE('passenger_in').to(__.V(accident_id)).next()
            g.V(cp).addE('claimed_injury').to(__.V(claim_id)).next()
        elif not is_fraud and random.random() < 0.03:
            # Rare appearance in legit claims — makes the pattern more realistic
            cp = random.choice(cross_ring_passengers)
            g.V(cp).addE('passenger_in').to(__.V(accident_id)).next()
            g.V(cp).addE('claimed_injury').to(__.V(claim_id)).next()

        claims_created += 1

    logger.info(f"Created {claims_created} claims and accidents")

    # --- High-Velocity Claims (4-5 claims per claimant in 60 days) ---
    velocity_burst_base = int(time.time()) - random.randint(20, 60) * 86400
    for claimant_id in high_velocity_claimants:
        for k in range(random.randint(4, 5)):
            acc_id = str(uuid.uuid4())
            lat, lng, zip_code = _fraud_location()
            ts = velocity_burst_base + random.randint(0, 60 * 86400)
            g.addV('accident').property(T.id, acc_id) \
                .property('date', time.strftime('%Y-%m-%d', time.gmtime(ts))) \
                .property('latitude', lat).property('longitude', lng) \
                .property('zipCode', zip_code).property('location', zip_code) \
                .property('accidentType', 'rear-end').property('maneuverType', 'sudden-stop') \
                .property('policeVerified', False).next()
            cl_id = str(uuid.uuid4())
            amount = random.uniform(6000, 12000)
            _add_entity_with_fraud(g, 'claim', cl_id,
                {'amount': amount, 'isFraud': True, 'status': 'approved', 'claimDate': ts},
                random.uniform(0.75, 0.92))
            g.V(claimant_id).addE('filed_claim').to(__.V(cl_id)).next()
            g.V(cl_id).addE('for_accident').to(__.V(acc_id)).next()
            # Use a policy-hopping vehicle
            v_id = random.choice(policy_hop_vehicles)
            g.V(acc_id).addE('involved_vehicle').to(__.V(v_id)).property('role', 'victim').next()
            g.V(cl_id).addE('repaired_at').to(__.V(random.choice(repair_shops[:5]))).next()
            claims_created += 1
    logger.info(f"Created high-velocity claims for {len(high_velocity_claimants)} claimants")

    # --- Injury Escalation Claims (increasing amounts over time) ---
    for claimant_id in escalation_claimants:
        base_ts = int(time.time()) - 300 * 86400  # start ~10 months ago
        for step, amount in enumerate(ESCALATION_AMOUNTS):
            acc_id = str(uuid.uuid4())
            ts = base_ts + step * 60 * 86400  # ~60 days apart
            lat, lng, zip_code = _legit_location() if step < 2 else _fraud_location()
            g.addV('accident').property(T.id, acc_id) \
                .property('date', time.strftime('%Y-%m-%d', time.gmtime(ts))) \
                .property('latitude', lat).property('longitude', lng) \
                .property('zipCode', zip_code).property('location', zip_code) \
                .property('accidentType', 'rear-end').property('maneuverType', 'normal') \
                .property('policeVerified', step < 2).next()
            cl_id = str(uuid.uuid4())
            # Early claims look legit, later ones are fraud
            is_fraud = step >= 2
            fraud_score = 0.2 + step * 0.15  # escalates: 0.2, 0.35, 0.5, 0.65, 0.8
            _add_entity_with_fraud(g, 'claim', cl_id,
                {'amount': amount + random.uniform(-500, 500), 'isFraud': is_fraud,
                 'status': 'approved', 'claimDate': ts},
                min(fraud_score, 0.95))
            g.V(claimant_id).addE('filed_claim').to(__.V(cl_id)).next()
            g.V(cl_id).addE('for_accident').to(__.V(acc_id)).next()
            g.V(acc_id).addE('involved_vehicle').to(__.V(random.choice(vehicles))).property('role', 'victim').next()
            g.V(cl_id).addE('repaired_at').to(__.V(random.choice(repair_shops[:10]))).next()
            claims_created += 1
    logger.info(f"Created escalation claims for {len(escalation_claimants)} claimants")

    # --- Explicit Staged-Accident Rings (with temporal bursts + geolocation) ---
    def _plant_ring(ring_index, ring_claimants, ring_vehicles, ring_witnesses,
                    ring_shop, ring_attorney, maneuver):
        """Plant one ring with temporal burst and geographic clustering."""
        claims_added = 0
        burst_base = int(time.time()) - random.randint(14, 45) * 86400
        zone = FRAUD_ZONES[ring_index % len(FRAUD_ZONES)]

        for j, ring_claimant in enumerate(ring_claimants):
            for k in range(2):
                ring_accident_id = str(uuid.uuid4())
                ring_vehicle = ring_vehicles[(j + k) % len(ring_vehicles)]
                ring_witness = ring_witnesses[(j + k) % len(ring_witnesses)]
                ring_ts = _fraud_burst_timestamp(burst_base)
                ring_date = time.strftime('%Y-%m-%d', time.gmtime(ring_ts))
                lat, lng = _random_point_near(zone['center'], zone['radius'])

                g.addV('accident').property(T.id, ring_accident_id) \
                    .property('date', ring_date) \
                    .property('location', zone['zip']) \
                    .property('latitude', lat).property('longitude', lng) \
                    .property('zipCode', zone['zip']) \
                    .property('accidentType', 'rear-end') \
                    .property('maneuverType', maneuver) \
                    .property('policeVerified', False).next()

                ring_claim_id = str(uuid.uuid4())
                ring_amount = random.uniform(10000, 18000)
                _add_entity_with_fraud(g, 'claim', ring_claim_id,
                    {'amount': ring_amount, 'isFraud': True, 'status': 'approved', 'claimDate': ring_ts},
                    random.uniform(0.85, 0.98))
                g.V(ring_claimant).addE('filed_claim').to(__.V(ring_claim_id)).next()
                g.V(ring_claim_id).addE('for_accident').to(__.V(ring_accident_id)).next()
                g.V(ring_accident_id).addE('involved_vehicle').to(__.V(ring_vehicle)).property('role', 'at-fault').next()
                g.V(ring_accident_id).addE('witnessed_by').to(__.V(ring_witness)).next()
                g.V(ring_claim_id).addE('repaired_at').to(__.V(ring_shop)).next()

                # Cross-ring passenger in planted rings too
                if random.random() < 0.4:
                    cp = random.choice(cross_ring_passengers)
                    g.V(cp).addE('passenger_in').to(__.V(ring_accident_id)).next()
                    g.V(cp).addE('claimed_injury').to(__.V(ring_claim_id)).next()

                claims_added += 1
            g.V(ring_claimant).addE('represented_by').to(__.V(ring_attorney)).next()

        logger.info(f"Planted ring {ring_index}: {len(ring_claimants)} claimants × 2 staged claims = {claims_added}, "
                    f"burst={ring_date}, zone={zone['zip']}")
        return claims_added

    _plant_ring(1, claimants[200:205], [vehicles[0], vehicles[1]], [witnesses[0]],
                repair_shops[0], attorneys[0], 'swoop-squat')
    _plant_ring(2, claimants[210:215], [vehicles[2]], [witnesses[1], witnesses[2]],
                repair_shops[1], attorneys[1], 'sudden-stop')
    _plant_ring(3, claimants[220:225], [vehicles[3], vehicles[4]], [witnesses[3]],
                repair_shops[2], attorneys[2], 'swoop-squat')
    _plant_ring(4, claimants[230:235], [vehicles[5]], [witnesses[4], witnesses[5]],
                repair_shops[3], attorneys[3], 'sudden-stop')

    # --- Vehicle-Pivot Staged Rings ---
    # These rings share a SINGLE at-fault vehicle across all members' accidents,
    # creating the "prop car" pattern visible in the Staged Accidents page.
    # Ring 5: 4 claimants all "hit by" the same vehicle (vehicles[6])
    burst_base_5 = int(time.time()) - random.randint(14, 30) * 86400
    zone_5 = FRAUD_ZONES[0]
    for j, cid in enumerate(claimants[240:244]):
        for k in range(2):
            acc_id = str(uuid.uuid4())
            ts = _fraud_burst_timestamp(burst_base_5)
            lat, lng = _random_point_near(zone_5['center'], zone_5['radius'])
            g.addV('accident').property(T.id, acc_id) \
                .property('date', time.strftime('%Y-%m-%d', time.gmtime(ts))) \
                .property('latitude', lat).property('longitude', lng) \
                .property('zipCode', zone_5['zip']).property('location', zone_5['zip']) \
                .property('accidentType', 'rear-end').property('maneuverType', 'swoop-squat') \
                .property('policeVerified', False).next()
            cl_id = str(uuid.uuid4())
            _add_entity_with_fraud(g, 'claim', cl_id,
                {'amount': random.uniform(9000, 16000), 'isFraud': True, 'status': 'approved', 'claimDate': ts},
                random.uniform(0.85, 0.97))
            g.V(cid).addE('filed_claim').to(__.V(cl_id)).next()
            g.V(cl_id).addE('for_accident').to(__.V(acc_id)).next()
            # Same at-fault vehicle in every accident
            g.V(acc_id).addE('involved_vehicle').to(__.V(vehicles[6])).property('role', 'at-fault').next()
            g.V(cl_id).addE('repaired_at').to(__.V(repair_shops[4])).next()
            claims_created += 1
        g.V(cid).addE('represented_by').to(__.V(attorneys[4])).next()
    logger.info("Planted ring 5: 4 claimants × 2 claims, shared at-fault vehicle")

    # Ring 6: 4 claimants all claim their vehicle (vehicles[7]) was the victim
    burst_base_6 = int(time.time()) - random.randint(14, 30) * 86400
    zone_6 = FRAUD_ZONES[2]
    for j, cid in enumerate(claimants[244:248]):
        for k in range(2):
            acc_id = str(uuid.uuid4())
            ts = _fraud_burst_timestamp(burst_base_6)
            lat, lng = _random_point_near(zone_6['center'], zone_6['radius'])
            g.addV('accident').property(T.id, acc_id) \
                .property('date', time.strftime('%Y-%m-%d', time.gmtime(ts))) \
                .property('latitude', lat).property('longitude', lng) \
                .property('zipCode', zone_6['zip']).property('location', zone_6['zip']) \
                .property('accidentType', 'rear-end').property('maneuverType', 'sudden-stop') \
                .property('policeVerified', False).next()
            cl_id = str(uuid.uuid4())
            _add_entity_with_fraud(g, 'claim', cl_id,
                {'amount': random.uniform(9000, 16000), 'isFraud': True, 'status': 'approved', 'claimDate': ts},
                random.uniform(0.85, 0.97))
            g.V(cid).addE('filed_claim').to(__.V(cl_id)).next()
            g.V(cl_id).addE('for_accident').to(__.V(acc_id)).next()
            # Same victim vehicle in every accident
            g.V(acc_id).addE('involved_vehicle').to(__.V(vehicles[7])).property('role', 'victim').next()
            g.V(cl_id).addE('repaired_at').to(__.V(repair_shops[5])).next()
            claims_created += 1
        g.V(cid).addE('represented_by').to(__.V(attorneys[5])).next()
    logger.info("Planted ring 6: 4 claimants × 2 claims, shared victim vehicle")

    claims_created += 40
    logger.info(f"Total claims after rings: {claims_created}")

    remoteConn.close()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Auto insurance graph populated successfully',
            'claimants': len(claimants),
            'vehicles': len(vehicles),
            'repairShops': len(repair_shops),
            'medicalProviders': len(medical_providers),
            'witnesses': len(witnesses),
            'attorneys': len(attorneys),
            'towCompanies': len(tow_companies),
            'claims': claims_created,
            'crossRingPassengers': len(cross_ring_passengers),
            'policyHoppingVehicles': len(policy_hop_vehicles),
            'highVelocityClaimants': len(high_velocity_claimants),
            'escalationClaimants': len(escalation_claimants),
            'fraudZones': len(FRAUD_ZONES),
        })
    }
