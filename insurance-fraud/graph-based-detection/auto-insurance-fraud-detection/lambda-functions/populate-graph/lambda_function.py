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


def _add_entity_with_fraud(g, label, entity_id, properties, fraud_score):
    """Create an entity vertex and a linked ::fraudEntity vertex with the fraud score.

    The entity vertex gets the clean label (e.g. 'repairShop') with business properties.
    The fraudEntity vertex gets 'label::fraudEntity' with only the fraudScore property.
    They are linked by a 'has_fraud_score' edge from entity -> fraudEntity.
    """
    # Entity vertex
    t = g.addV(label).property(T.id, entity_id)
    for k, v in properties.items():
        t = t.property(k, v)
    t.next()

    # FraudEntity vertex
    fraud_id = f"{entity_id}::fraud"
    g.addV('fraudEntity').property(T.id, fraud_id).property('fraudScore', fraud_score).next()
    g.V(entity_id).addE('has_fraud_score').to(__.V(fraud_id)).next()


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

    # --- Claimants (no fraud score - they are assessed via their claims) ---
    claimants = []
    for i in range(1000):
        claimant_id = str(uuid.uuid4())
        g.addV('claimant').property(T.id, claimant_id).property('name', f'Claimant {i}').property('licenseNumber', f'DL{i:06d}').next()
        claimants.append(claimant_id)
    logger.info(f"Created {len(claimants)} claimants")

    # --- Vehicles (no fraud score - assessed via claims) ---
    vehicles = []
    makes = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes', 'Nissan', 'Hyundai']
    for i in range(1500):
        vehicle_id = str(uuid.uuid4())
        owner_id = random.choice(claimants)
        plate = f'{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.randint(1000,9999)}'
        g.addV('vehicle').property(T.id, vehicle_id).property('vin', f'VIN{i:010d}').property('make', random.choice(makes)).property('year', random.randint(2010, 2024)).property('plate', plate).property('ownerId', owner_id).next()
        g.V(owner_id).addE('owns').to(__.V(vehicle_id)).next()
        vehicles.append(vehicle_id)
    logger.info(f"Created {len(vehicles)} vehicles")

    # --- Repair Shops (10% suspicious) ---
    repair_shops = []
    for i in range(200):
        shop_id = str(uuid.uuid4())
        is_suspicious = i < 20
        rating = 2.5 if is_suspicious else random.uniform(4.0, 5.0)
        fraud_score = random.uniform(0.7, 0.95) if is_suspicious else random.uniform(0.1, 0.4)
        _add_entity_with_fraud(g, 'repairShop', shop_id,
            {'name': f'Repair Shop {i}', 'rating': rating, 'suspicious': is_suspicious},
            fraud_score)
        repair_shops.append(shop_id)
    logger.info(f"Created {len(repair_shops)} repair shops")

    # --- Medical Providers ---
    medical_providers = []
    specialties = ['Orthopedic', 'Chiropractor', 'Physical Therapy']
    for i in range(150):
        provider_id = str(uuid.uuid4())
        is_suspicious = i < 20
        fraud_score = random.uniform(0.7, 0.9) if is_suspicious else random.uniform(0.1, 0.4)
        _add_entity_with_fraud(g, 'medicalProvider', provider_id,
            {'name': f'Dr. Provider {i}', 'specialty': random.choice(specialties)},
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

    # --- Tow Companies (20% corrupt) ---
    tow_companies = []
    for i in range(200):
        tow_id = str(uuid.uuid4())
        is_corrupt = i < 40
        fraud_score = random.uniform(0.7, 0.9) if is_corrupt else random.uniform(0.1, 0.35)
        _add_entity_with_fraud(g, 'towCompany', tow_id,
            {'name': f'Tow Company {i}'},
            fraud_score)
        tow_companies.append(tow_id)
    logger.info(f"Created {len(tow_companies)} tow companies")

    # --- Claims & Accidents ---
    claims_created = 0
    fraud_rings = [claimants[:50], claimants[100:150]]

    for i in range(2000):
        is_fraud = i < 40

        # Accident vertex (no fraud score)
        accident_id = str(uuid.uuid4())
        locations = ['Main St & 5th Ave', 'Highway 101', 'Park Blvd', 'Downtown', 'Suburb Area']
        if is_fraud:
            accident_type = random.choice(['rear-end', 'rear-end', 'side-impact'])
            maneuver_type = random.choice(['swoop-squat', 'sudden-stop', 'normal'])
            police_verified = random.random() < 0.3
        else:
            accident_type = random.choice(['rear-end', 'side-impact', 'head-on'])
            maneuver_type = 'normal'
            police_verified = random.random() < 0.9

        g.addV('accident').property(T.id, accident_id).property('date', f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}').property('location', random.choice(locations)).property('accidentType', accident_type).property('maneuverType', maneuver_type).property('policeVerified', police_verified).next()

        # Claim (entity + fraudEntity)
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

        claim_ts = int(time.time()) - random.randint(0, 365 * 86400)
        _add_entity_with_fraud(g, 'claim', claim_id,
            {'amount': amount, 'isFraud': is_fraud, 'status': 'approved', 'claimDate': claim_ts},
            fraud_score)

        # Edges
        g.V(claimant_id).addE('filed_claim').to(__.V(claim_id)).next()
        g.V(claim_id).addE('for_accident').to(__.V(accident_id)).next()

        vehicle_id = random.choice(vehicles)
        g.V(accident_id).addE('involved_vehicle').to(__.V(vehicle_id)).next()
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
                passenger_id = str(uuid.uuid4())
                passenger_fraud_score = random.uniform(0.7, 0.95)
                _add_entity_with_fraud(g, 'passenger', passenger_id,
                    {'name': f'Passenger {passenger_id[:8]}'},
                    passenger_fraud_score)
                g.V(passenger_id).addE('passenger_in').to(__.V(accident_id)).next()
                g.V(passenger_id).addE('claimed_injury').to(__.V(claim_id)).next()
                provider_id = medical_providers[random.randint(0, 19)] if random.random() < 0.7 else random.choice(medical_providers)
                g.V(passenger_id).addE('treated_by').to(__.V(provider_id)).next()

        claims_created += 1

    logger.info(f"Created {claims_created} claims and accidents")

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
            'claims': claims_created
        })
    }
