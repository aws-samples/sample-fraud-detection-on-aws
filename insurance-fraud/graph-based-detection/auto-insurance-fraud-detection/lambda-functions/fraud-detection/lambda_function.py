import json
import os
import uuid
import time
import hmac
import hashlib
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from gremlin_python.process.traversal import T, P, Order
from gremlin_python.process.graph_traversal import __
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Connection cache for reuse within Lambda container
_connection_cache = {'conn': None, 'g': None, 'expires': 0}


def verify_request_signature(raw_body, signature, timestamp):
    """Verify HMAC-SHA256 signature of request body"""
    # Check timestamp (prevent replay attacks - 5 min window)
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        return False, "Request expired"
    
    signing_key = os.environ.get('REQUEST_SIGNING_KEY', 'default-key-change-in-production')
    
    message = f"{timestamp}:{raw_body}"
    expected_sig = hmac.new(
        signing_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_sig):
        return False, "Invalid signature"
    
    return True, None

import math
def _trunc(value, decimals=2):
    """Truncate (not round) a float to the given decimal places."""
    factor = 10 ** decimals
    return math.trunc(float(value) * factor) / factor

def get_node_label(node_type):
    if isinstance(node_type, list):
        node_type = next((l for l in node_type if l != 'fraudEntity'), node_type[0])
    
    labels = {
        'claimant': 'Claimant',
        'claim': 'Claim',
        'vehicle': 'Vehicle',
        'repairShop': 'Repair Shop',
        'witness': 'Witness',
        'accident': 'Accident',
        'medicalProvider': 'Medical Provider',
        'attorney': 'Attorney',
        'towCompany': 'Tow Company',
        'passenger': 'Passenger'
    }
    return labels.get(node_type, str(node_type).capitalize())

def _prop(vertex_map, key, default=None):
    """Safely extract a property from Neptune valueMap result (always returns lists)."""
    val = vertex_map.get(key)
    if val is None:
        return default
    return val[0] if isinstance(val, list) else val

def get_neptune_connection():
    """Get Neptune connection with IAM SigV4 authentication, reusing cached connections."""
    global _connection_cache
    now = time.time()

    # Reuse if connection exists and SigV4 token hasn't expired (4 min buffer)
    if _connection_cache['conn'] and now < _connection_cache['expires']:
        try:
            # Quick check if connection is still alive
            _connection_cache['g'].V().limit(0).toList()
            return _connection_cache['g'], _connection_cache['conn']
        except Exception:
            logger.info("Cached connection stale, reconnecting")

    # Close stale connection
    if _connection_cache['conn']:
        try:
            _connection_cache['conn'].close()
        except Exception:
            logger.warning("Failed to close stale connection", exc_info=True)

    endpoint = os.environ['NEPTUNE_ENDPOINT']
    conn_string = f"wss://{endpoint}:8182/gremlin"
    region = os.environ['AWS_REGION']

    credentials = Session().get_credentials()
    if credentials is None:
        raise Exception("No AWS credentials found")
    creds = credentials.get_frozen_credentials()

    request = AWSRequest(method='GET', url=conn_string, data=None)
    SigV4Auth(creds, 'neptune-db', region).add_auth(request)

    signed_headers = dict(request.headers.items())

    remoteConn = DriverRemoteConnection(
        conn_string,
        'g',
        headers=signed_headers,
        transport_factory=lambda: AiohttpTransport()
    )
    g = traversal().withRemote(remoteConn)

    _connection_cache = {'conn': remoteConn, 'g': g, 'expires': now + 240}
    return g, remoteConn


_ml_available = None  # Cache ML availability per Lambda invocation

def _get_fraud_score(g, entity_id, default=0.0):
    """Get fraud score via Neptune ML inference, falling back to stored score,
    then to average of connected claims' scores."""
    global _ml_available
    # Try Neptune ML inference (skip if previously failed this invocation)
    if _ml_available is not False:
        try:
            score = g.V(entity_id).properties('fraudScore').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
            _ml_available = True
            return _trunc(score)
        except Exception as e:
            logger.debug(f"ML inference failed for {entity_id}: {e}")
            _ml_available = False
    # Try stored score on linked fraudEntity vertex
    try:
        score = g.V(entity_id).out('has_fraud_score').values('fraudScore').next()
        return _trunc(score)
    except Exception as e:
        logger.debug(f"Stored score failed for {entity_id}: {e}")
    # Derive from connected claims (for claimants)
    try:
        scores = g.V(entity_id).out('filed_claim').out('has_fraud_score').values('fraudScore').fold().next()
        if scores:
            return _trunc(sum(float(s) for s in scores) / len(scores))
        logger.debug(f"No derived scores for {entity_id}")
    except Exception as e:
        logger.debug(f"Derived score failed for {entity_id}: {e}")
    # Derive from connected claims (for vehicles: vehicle ← involved_vehicle ← accident ← for_accident ← claim)
    try:
        scores = g.V(entity_id).in_('involved_vehicle').in_('for_accident').out('has_fraud_score').values('fraudScore').fold().next()
        if scores:
            return _trunc(sum(float(s) for s in scores) / len(scores))
    except Exception as e:
        logger.debug(f"Vehicle derived score failed for {entity_id}: {e}")
    return default


def _build_neighborhood_graph(g, center_id, center_type):
    """Build a 1-hop neighborhood graph for any entity. Reused by multiple endpoints."""
    nodes = []
    edges = []

    vertex = g.V(center_id).valueMap(True).next()
    nodes.append({
        'id': str(vertex.get(T.id)), 'name': _prop(vertex, 'name'),
        'label': get_node_label(center_type),
        'type': center_type,
        'fraudScore': _get_fraud_score(g, center_id)
    })

    neighbors = g.V(center_id).both().not_(__.hasLabel('fraudEntity')).hasNot('fraudScore').dedup().valueMap(True).toList()
    for neighbor in neighbors:
        neighbor_id = str(neighbor.get(T.id))
        neighbor_label = neighbor.get(T.label)
        if isinstance(neighbor_label, list):
            neighbor_label = next((l for l in neighbor_label if l != 'fraudEntity'), neighbor_label[0])
        neighbor_type = neighbor_label

        nodes.append({
            'id': neighbor_id, 'name': _prop(neighbor, 'name'),
            'label': get_node_label(neighbor_label),
            'type': neighbor_type,
            'fraudScore': _get_fraud_score(g, neighbor_id)
        })
        edges.append({'source': str(center_id), 'target': neighbor_id})

    return {'nodes': nodes, 'edges': edges}


def _build_claimant_graph(g, claimant_id):
    """Build a full graph around a claimant: claims → accidents → vehicles, shops, witnesses, passengers, tow companies.
    Reused by get_claimant_claims, analyze_claimant_fraud, and detect_collision_rings."""
    nodes = []
    edges = []
    seen = set()

    def add_node(nid, label, ntype, size, fraud_score=None, name=None):
        if nid not in seen:
            seen.add(nid)
            node = {'id': nid, 'label': label, 'type': ntype, 'size': size}
            if fraud_score is not None:
                node['fraudScore'] = fraud_score
            if name:
                node['name'] = name
            nodes.append(node)

    def add_edge(source, target, etype):
        edges.append({'source': source, 'target': target, 'type': etype})

    claimant_vertex = g.V(claimant_id).valueMap(True).next()
    claimant_fraud_score = _get_fraud_score(g, claimant_id)
    add_node(claimant_id, get_node_label('claimant'), 'claimant', 12, claimant_fraud_score, name=_prop(claimant_vertex, 'name'))

    claims = g.V(claimant_id).out('filed_claim').valueMap(True).toList()
    for claim in claims:
        claim_id = str(claim[T.id])
        amount = _prop(claim, 'amount', 0)
        add_node(claim_id, f"${amount}", 'claim', 8, _get_fraud_score(g, claim_id))
        add_edge(claimant_id, claim_id, 'filed_claim')

        # Repair shops
        for shop in g.V(claim_id).out('repaired_at').valueMap(True).toList():
            sid = str(shop[T.id])
            add_node(sid, get_node_label('repairShop'), 'repairShop', 10, _get_fraud_score(g, sid), name=_prop(shop, 'name'))
            add_edge(claim_id, sid, 'repaired_at')

        # Accidents and their sub-entities
        for accident in g.V(claim_id).out('for_accident').valueMap(True).toList():
            aid = str(accident[T.id])
            add_node(aid, get_node_label('accident'), 'accident', 6, _get_fraud_score(g, aid))
            add_edge(claim_id, aid, 'for_accident')

            # Witnesses
            for w in g.V(aid).out('witnessed_by').valueMap(True).toList():
                wid = str(w[T.id])
                add_node(wid, get_node_label('witness'), 'witness', 8, _get_fraud_score(g, wid), name=_prop(w, 'name'))
                add_edge(aid, wid, 'witnessed_by')

            # Passengers
            for p in g.V(aid).in_('passenger_in').valueMap(True).toList():
                pid = str(p[T.id])
                add_node(pid, get_node_label('passenger'), 'passenger', 7, _get_fraud_score(g, pid), name=_prop(p, 'name'))
                add_edge(pid, aid, 'passenger_in')
                add_edge(pid, claim_id, 'claimed_injury')

            # Vehicles + tow companies
            for v in g.V(aid).in_('involved_vehicle').valueMap(True).toList():
                vid = str(v[T.id])
                make = _prop(v, 'make', 'Unknown')
                add_node(vid, make, 'vehicle', 6, _get_fraud_score(g, vid), name=_prop(v, 'make'))
                add_edge(aid, vid, 'involved_vehicle')

                for tc in g.V(vid).out('towed_by').valueMap(True).toList():
                    tcid = str(tc[T.id])
                    add_node(tcid, get_node_label('towCompany'), 'towCompany', 8, _get_fraud_score(g, tcid), name=_prop(tc, 'name'))
                    add_edge(vid, tcid, 'towed_by')

    return {'nodes': nodes, 'edges': edges}


def _list_entities(g, label, name_key='name'):
    """Generic list + deduplicate-by-name for dropdown endpoints.
    Filters out ::fraudEntity vertices which share the base label in Neptune."""
    entities = g.V().hasLabel(label).has('name').dedup().by(T.id).valueMap(True).toList()

    seen_names = {}
    for e in entities:
        eid = str(e.get(T.id))
        name = _prop(e, name_key, eid)
        if name not in seen_names:
            seen_names[name] = eid

    result = [{'id': eid, 'name': name} for name, eid in seen_names.items()]
    result.sort(key=lambda x: x['name'])
    return result

@app.post("/claims")
@tracer.capture_method
def submit_claim():
    """
    Submit a new insurance claim and get real-time fraud prediction
    
    FRAUD CASE: Real-time Fraud Detection
    WHAT IT DOES: Uses Neptune ML to predict fraud probability when a claim is submitted
    WHY IT'S FRAUD: Claims with patterns similar to known fraudulent claims (high amounts,
    suspicious repair shops, collision ring members) get high fraud scores. The ML model
    learns from historical fraud patterns to identify new fraudulent claims instantly.
    
    BUSINESS VALUE: Prevents fraudulent claims from being paid by catching them at submission time.
    """
    body = app.current_event.json_body
    raw_body = app.current_event.body  # raw string, before parsing

    signature = app.current_event.get_header_value("X-Request-Signature")
    timestamp = app.current_event.get_header_value("X-Request-Timestamp")

    if not signature or not timestamp:
        return {'error': 'Request signature required'}, 400

    valid, error = verify_request_signature(raw_body, signature, timestamp)
    if not valid:
        return {'error': f'Invalid request signature: {error}'}, 403

    claim_id = body.get('claimId', f"claim-{uuid.uuid4()}")
    claimant_id = body.get('claimantId')
    vehicle_id = body.get('vehicleId')
    repair_shop_id = body.get('repairShopId')
    
    # Validate ID format (alphanumeric, hyphens, underscores only)
    import re
    id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    for id_name, id_value in [('claimId', claim_id), ('claimantId', claimant_id), 
                               ('vehicleId', vehicle_id), ('repairShopId', repair_shop_id)]:
        if not id_value or not id_pattern.match(str(id_value)):
            return {'error': f'Invalid {id_name} format'}, 400
    
    # Validate claim amount
    try:
        claim_amount = float(body.get('claimAmount'))
        if claim_amount <= 0 or claim_amount > 1000000:
            return {'error': 'Claim amount must be between 0 and 1,000,000'}, 400
    except (ValueError, TypeError):
        return {'error': 'Invalid claim amount'}, 400
    
    # Log original request for audit trail
    logger.info("Claim submission received", extra={
        "audit": True,
        "request_body": body,
        "source_ip": app.current_event.request_context.identity.source_ip,
        "user_agent": app.current_event.request_context.identity.user_agent,
        "request_id": app.current_event.request_context.request_id
    })
    
    g, remoteConn = get_neptune_connection()
    
    # Verify vertices exist
    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 400
    if not g.V(vehicle_id).hasNext():
        return {'error': f'Vehicle {vehicle_id} not found'}, 400
    if not g.V(repair_shop_id).hasNext():
        return {'error': f'Repair shop {repair_shop_id} not found'}, 400

    # Create claim vertex
    g.addV('claim').property(T.id, claim_id).property('amount', claim_amount).property('status', 'pending').property('claimDate', int(time.time())).next()

    # Create edges
    g.V(claimant_id).addE('filed_claim').to(__.V(claim_id)).next()
    g.V(claim_id).addE('for_vehicle').to(__.V(vehicle_id)).next()
    g.V(claim_id).addE('repaired_at').to(__.V(repair_shop_id)).next()

    # Get ML prediction with fallback
    logger.info(f"Getting fraud prediction for claim {claim_id}")
    fraud_score = 0.0  # Default score

    try:
        # Try Neptune ML inference
        result = g.V(claim_id).properties('fraudScore').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
        fraud_score = float(result) if result else 0.0
        logger.info(f"Neptune ML fraud score: {fraud_score}")
    except Exception as e:
        logger.warning(f"Neptune ML inference failed, using fallback calculation: {str(e)}")

        # Fallback: Calculate fraud score based on patterns
        try:
            # Check repair shop fraud rate
            shop_claims = g.V(repair_shop_id).inE('repaired_at').outV().count().next()
            if shop_claims > 10:  # Shop has enough history
                shop_fraud_rate = g.V(repair_shop_id).inE('repaired_at').outV().where(__.out('has_fraud_score').has('fraudScore', P.gt(0.7))).count().next() / shop_claims
                fraud_score += shop_fraud_rate * 0.3

            # Check claimant history
            claimant_claims = g.V(claimant_id).out('filed_claim').count().next()
            if claimant_claims > 1:  # Claimant has history
                claimant_fraud_rate = g.V(claimant_id).out('filed_claim').where(__.out('has_fraud_score').has('fraudScore', P.gt(0.7))).count().next() / claimant_claims
                fraud_score += claimant_fraud_rate * 0.3

            # Check claim amount anomaly
            avg_amount = g.V().hasLabel('claim').has('amount').values('amount').mean().next()
            if claim_amount > avg_amount * 2:  # Unusually high amount
                fraud_score += 0.2

            # Ensure score is between 0 and 1
            fraud_score = min(max(fraud_score, 0.0), 1.0)
            logger.info(f"Fallback fraud score calculated: {fraud_score}")

        except Exception as fallback_error:
            logger.error(f"Fallback calculation also failed: {str(fallback_error)}")
            fraud_score = 0.0  # Safe default

    if fraud_score > 0.7:
        g.V(claim_id).property('status', 'rejected').property('fraudScore', fraud_score).next()
        status = 'rejected'
        message = 'Claim rejected - potential fraud detected'
    else:
        g.V(claim_id).property('status', 'approved').property('fraudScore', fraud_score).next()
        status = 'approved'
        message = 'Claim approved'

    # Log final decision for audit trail
    logger.info("Claim decision made", extra={
        "audit": True,
        "claim_id": claim_id,
        "status": status,
        "fraud_score": fraud_score,
        "claim_amount": claim_amount,
        "claimant_id": claimant_id,
        "repair_shop_id": repair_shop_id,
        "timestamp": int(time.time())
    })

    return {
        'claimId': claim_id,
        'status': status,
        'fraudScore': fraud_score,
        'message': message
    }

@app.get("/claims/<claim_id>")
@tracer.capture_method
def get_claim(claim_id: str):
    """
    Get claim details and fraud score
    
    Retrieves complete information about a specific claim including its Neptune ML
    fraud score, claimant details, and all related entities.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(claim_id).hasNext():
        return {'error': f'Claim {claim_id} not found'}, 404

    claim = g.V(claim_id).valueMap(True).next()

    return {
        'claimId': claim_id,
        'amount': _prop(claim, 'amount', 0),
        'status': _prop(claim, 'status', 'unknown'),
        'fraudScore': _get_fraud_score(g, claim_id),
        'timestamp': _prop(claim, 'claimDate')
    }

@app.get("/claims/<claim_id>/graph")
@tracer.capture_method
def get_claim_graph(claim_id: str):
    """Get a claim's neighborhood as a graph visualization"""
    g, remoteConn = get_neptune_connection()

    if not g.V(claim_id).hasNext():
        return {'error': f'Claim {claim_id} not found'}, 404

    nodes = []
    edges = []
    seen = set()

    def add_node(nid, label, ntype, size, fraud_score=None, name=None):
        if nid not in seen:
            seen.add(nid)
            node = {'id': nid, 'label': label, 'type': ntype, 'size': size}
            if fraud_score is not None:
                node['fraudScore'] = fraud_score
            if name:
                node['name'] = name
            nodes.append(node)

    claim = g.V(claim_id).valueMap(True).next()
    amount = _prop(claim, 'amount', 0)
    add_node(claim_id, f"${amount}", 'claim', 10, _get_fraud_score(g, claim_id))

    # Claimant
    for c in g.V(claim_id).in_('filed_claim').valueMap(True).toList():
        cid = str(c[T.id])
        add_node(cid, get_node_label('claimant'), 'claimant', 12, _get_fraud_score(g, cid), name=_prop(c, 'name'))
        edges.append({'source': cid, 'target': claim_id, 'type': 'filed_claim'})

    # Repair shop
    for s in g.V(claim_id).out('repaired_at').valueMap(True).toList():
        sid = str(s[T.id])
        add_node(sid, get_node_label('repairShop'), 'repairShop', 10, _get_fraud_score(g, sid), name=_prop(s, 'name'))
        edges.append({'source': claim_id, 'target': sid, 'type': 'repaired_at'})

    # Accident and sub-entities
    for a in g.V(claim_id).out('for_accident').valueMap(True).toList():
        aid = str(a[T.id])
        add_node(aid, get_node_label('accident'), 'accident', 8, _get_fraud_score(g, aid))
        edges.append({'source': claim_id, 'target': aid, 'type': 'for_accident'})

        for w in g.V(aid).out('witnessed_by').valueMap(True).toList():
            wid = str(w[T.id])
            add_node(wid, get_node_label('witness'), 'witness', 8, _get_fraud_score(g, wid), name=_prop(w, 'name'))
            edges.append({'source': aid, 'target': wid, 'type': 'witnessed_by'})

        for v in g.V(aid).in_('involved_vehicle').valueMap(True).toList():
            vid = str(v[T.id])
            add_node(vid, _prop(v, 'make', 'Vehicle'), 'vehicle', 6, _get_fraud_score(g, vid))
            edges.append({'source': aid, 'target': vid, 'type': 'involved_vehicle'})

    return {'nodes': nodes, 'edges': edges}

@app.get("/claimants/<claimant_id>/claims")
@tracer.capture_method
def get_claimant_claims(claimant_id: str):
    """
    Get all claims for a claimant as a graph visualization
    Shows claimant, their claims, vehicles, and repair shops
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 404

    return _build_claimant_graph(g, claimant_id)

@app.get("/claimants/<claimant_id>/risk-score")
@tracer.capture_method
def get_claimant_risk_score(claimant_id: str):
    """
    Calculate comprehensive risk score for a claimant
    
    FRAUD CASE: Repeat Offender Detection
    WHAT IT DOES: Analyzes claimant's entire claim history to calculate overall fraud risk
    WHY IT'S FRAUD: Claimants with multiple rejected claims, high average fraud scores,
    or large total claim amounts are likely repeat fraudsters. Pattern of fraudulent behavior
    across multiple claims indicates systematic fraud rather than isolated incidents.
    
    BUSINESS VALUE: Helps underwriters decide whether to accept new policies or flag
    existing policyholders for investigation.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 404

    # Get all claims
    claims = g.V(claimant_id).out('filed_claim').valueMap(True).toList()

    if not claims:
        return {
            'claimantId': claimant_id,
            'riskScore': 0.0,
            'totalClaims': 0,
            'message': 'No claims history'
        }

    # Calculate risk metrics
    claim_ids = [str(c.get(T.id)) for c in claims]

    rejected_claims = sum(1 for c in claims if _prop(c, 'status', '') == 'rejected')
    rejection_rate = rejected_claims / len(claims)

    total_amount = sum(_prop(c, 'amount', 0) for c in claims)

    # Risk score: same as the claimant's derived fraud score
    risk_score = _get_fraud_score(g, claimant_id)

    return {
        'claimantId': claimant_id,
        'riskScore': risk_score,
        'totalClaims': len(claims),
        'rejectedClaims': rejected_claims,
        'rejectionRate': _trunc(rejection_rate),
        'totalClaimAmount': _trunc(total_amount)
    }

@app.get("/repair-shops/<shop_id>/statistics")
@tracer.capture_method
def get_repair_shop_statistics(shop_id: str):
    """
    Get repair shop fraud statistics
    
    Provides comprehensive statistics about a repair shop's claim history, including
    total claims processed, fraud rate, and risk indicators for identifying complicit shops.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(shop_id).hasNext():
        return {'error': f'Repair shop {shop_id} not found'}, 404

    # Get shop details
    shop = g.V(shop_id).valueMap(True).next()

    # Get all claims at this shop
    claims = g.V(shop_id).inE('repaired_at').outV().valueMap(True).toList()

    if not claims:
        return {
            'repairShopId': shop_id,
            'name': _prop(shop, 'name', 'Unknown'),
            'totalClaims': 0,
            'message': 'No claims history'
        }

    claim_ids = [str(c.get(T.id)) for c in claims]
    fraud_scores = [_get_fraud_score(g, cid) for cid in claim_ids]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores)

    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)

    return {
        'repairShopId': shop_id,
        'name': _prop(shop, 'name', 'Unknown'),
        'rating': _prop(shop, 'rating', 0),
        'suspicious': _prop(shop, 'suspicious', False),
        'totalClaims': len(claims),
        'averageFraudScore': _trunc(avg_fraud_score),
        'highFraudClaims': high_fraud_claims,
        'highFraudRate': _trunc(high_fraud_claims / len(claims))
    }

@app.get("/repair-shops/<shop_id>")
@tracer.capture_method
def get_repair_shop_network(shop_id: str):
    """Get repair shop's one-level neighborhood network graph"""
    g, remoteConn = get_neptune_connection()
    
    return _build_neighborhood_graph(g, shop_id, 'repairShop')

@app.get("/fraud-patterns/collision-rings")
@tracer.capture_method
def detect_collision_rings():
    """
    Detect comprehensive collision ring fraud patterns - returns actual network graph
    """
    g, remoteConn = get_neptune_connection()
    
    nodes = []
    edges = []
    node_ids = set()

    # Get claimants with multiple claims (potential fraud ring members)
    claimants = g.V().hasLabel('claimant').where(
        __.out('filed_claim').count().is_(P.gte(2))
    ).limit(10).valueMap(True).toList()

    for c in claimants:
        c_id = str(c.get(T.id))
        if c_id not in node_ids:
            node_ids.add(c_id)
            nodes.append({
                'id': c_id,
                'label': get_node_label('claimant'),
                'name': _prop(c, 'name'),
                'type': 'claimant',
                'fraudScore': _get_fraud_score(g, c_id),
                'size': 12
            })

        # Get their claims (limit to 2 per claimant)
        claims = g.V(c_id).out('filed_claim').limit(2).valueMap(True).toList()
        for claim in claims:
            claim_id = str(claim.get(T.id))
            if claim_id not in node_ids:
                node_ids.add(claim_id)
                amount = claim.get('amount', [0])[0] if isinstance(claim.get('amount'), list) else claim.get('amount', 0)
                nodes.append({
                    'id': claim_id,
                    'label': f"${amount:.0f}",
                    'type': 'claim',
                    'fraudScore': _get_fraud_score(g, claim_id),
                    'size': 8
                })
            edges.append({'source': c_id, 'target': claim_id, 'type': 'filed_claim'})

            # Get repair shop for this claim
            shops = g.V(claim_id).out('repaired_at').limit(1).valueMap(True).toList()
            for s in shops:
                s_id = str(s.get(T.id))
                if s_id not in node_ids:
                    node_ids.add(s_id)
                    nodes.append({
                        'id': s_id,
                        'label': get_node_label('repairShop'),
            'name': _prop(s, 'name'),
                        'name': _prop(s, 'name'),
                        'type': 'repairShop',
                        'fraudScore': _get_fraud_score(g, s_id),
                        'size': 10
                    })
                edges.append({'source': claim_id, 'target': s_id, 'type': 'repaired_at'})

            # Get accident for this claim
            accidents = g.V(claim_id).out('for_accident').limit(1).valueMap(True).toList()
            for accident in accidents:
                accident_id = str(accident.get(T.id))
                if accident_id not in node_ids:
                    node_ids.add(accident_id)
                    nodes.append({
                        'id': accident_id,
                        'label': get_node_label('accident'),
                        'type': 'accident',
                        'fraudScore': _get_fraud_score(g, accident_id),
                        'size': 6
                    })
                edges.append({'source': claim_id, 'target': accident_id, 'type': 'for_accident'})

                # Get witness for this accident
                witnesses = g.V(accident_id).out('witnessed_by').limit(1).valueMap(True).toList()
                for w in witnesses:
                    w_id = str(w.get(T.id))
                    if w_id not in node_ids:
                        node_ids.add(w_id)
                        nodes.append({
                            'id': w_id,
                            'label': get_node_label('witness'),
            'name': _prop(w, 'name'),
                            'name': _prop(w, 'name'),
                            'type': 'witness',
                            'fraudScore': _get_fraud_score(g, w_id),
                            'size': 8
                        })
                    edges.append({'source': accident_id, 'target': w_id, 'type': 'witnessed_by'})

                # Get passengers for this accident (stuffed passengers fraud)
                passengers = g.V(accident_id).in_('passenger_in').valueMap(True).toList()
                for p in passengers:
                    p_id = str(p.get(T.id))
                    if p_id not in node_ids:
                        node_ids.add(p_id)
                        nodes.append({
                            'id': p_id,
                            'label': get_node_label('passenger'),
                            'name': _prop(p, 'name'),
                            'type': 'passenger',
                            'fraudScore': _get_fraud_score(g, p_id),
                            'size': 7
                        })
                    edges.append({'source': p_id, 'target': accident_id, 'type': 'passenger_in'})
                    edges.append({'source': p_id, 'target': claim_id, 'type': 'claimed_injury'})

                # Get vehicles involved in accident
                vehicles = g.V(accident_id).in_('involved_vehicle').limit(1).valueMap(True).toList()
                for v in vehicles:
                    v_id = str(v.get(T.id))
                    if v_id not in node_ids:
                        node_ids.add(v_id)
                        nodes.append({
                            'id': v_id,
                            'label': get_node_label('vehicle'),
                            'name': _prop(v, 'make'),
                            'type': 'vehicle',
                            'fraudScore': _get_fraud_score(g, v_id),
                            'size': 6
                        })
                    edges.append({'source': accident_id, 'target': v_id, 'type': 'involved_vehicle'})

                    # Get tow company for this vehicle
                    tow_companies = g.V(v_id).out('towed_by').limit(1).valueMap(True).toList()
                    for tc in tow_companies:
                        tc_id = str(tc.get(T.id))
                        if tc_id not in node_ids:
                            node_ids.add(tc_id)
                            nodes.append({
                                'id': tc_id,
                                'label': get_node_label('towCompany'),
                                'name': _prop(tc, 'name'),
                                'type': 'towCompany',
                                'fraudScore': tc.get('fraudScore', [0.0])[0] if 'fraudScore' in tc else 0.0,
                                'size': 8
                            })
                        edges.append({'source': v_id, 'target': tc_id, 'type': 'towed_by'})

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.get("/fraud-patterns/professional-witnesses")
@tracer.capture_method
def detect_professional_witnesses():
    """
    Detect professional witnesses - returns network graph showing witnesses and their claims
    """
    g, remoteConn = get_neptune_connection()
    
    nodes = []
    edges = []
    node_ids = set()

    # Get witnesses who appear in multiple accidents (limit to 10 for clearer visualization)
    witnesses = g.V().hasLabel('witness').has('name').where(
        __.inE('witnessed_by').count().is_(P.gte(3))
    ).limit(10).valueMap(True).toList()

    for w in witnesses:
        w_id = str(w.get(T.id))
        node_ids.add(w_id)
        nodes.append({
            'id': w_id,
            'label': get_node_label('witness'),
            'name': _prop(w, 'name'),
            'type': 'witness',
            'fraudScore': _get_fraud_score(g, w_id),
            'size': 15
        })

        # Get accidents they witnessed
        accidents = g.V(w_id).inE('witnessed_by').outV().valueMap(True).toList()
        for a in accidents:
            a_id = str(a.get(T.id))
            if a_id not in node_ids:
                node_ids.add(a_id)
                nodes.append({
                    'id': a_id,
                    'label': get_node_label('accident'),
                    'type': 'accident',
                    'fraudScore': _get_fraud_score(g, a_id),
                    'size': 10
                })
            edges.append({'source': w_id, 'target': a_id})

            # Get claimants from those accidents (limit to 1 per accident)
            claimants = g.V(a_id).inE('for_accident').outV().inE('filed_claim').outV().dedup().limit(1).valueMap(True).toList()
            for c in claimants:
                c_id = str(c.get(T.id))
                if c_id not in node_ids:
                    node_ids.add(c_id)
                    nodes.append({
                        'id': c_id,
                        'label': get_node_label('claimant'),
                'name': _prop(c, 'name'),
                        'type': 'claimant',
                        'fraudScore': _get_fraud_score(g, c_id),
                        'size': 12
                    })
                edges.append({'source': a_id, 'target': c_id})

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.get("/analytics/fraud-trends")
@tracer.capture_method
def get_fraud_trends():
    """
    Get fraud summary statistics across all claims
    """
    g, remoteConn = get_neptune_connection()

    claims = g.V().hasLabel('claim').has('amount').valueMap('amount', 'status').toList()
    total = len(claims)
    if total == 0:
        return {'totalClaims': 0}

    amounts = [_prop(c, 'amount', 0) for c in claims]
    statuses = [_prop(c, 'status', '') for c in claims]

    rejected = sum(1 for s in statuses if s == 'rejected')
    approved = sum(1 for s in statuses if s == 'approved')
    pending = total - rejected - approved
    total_amount = sum(amounts)

    # Use statistical anomaly detection (z-score > 2) as high-fraud proxy
    mean_amount = total_amount / total
    variance = sum((x - mean_amount) ** 2 for x in amounts) / total
    std_dev = variance ** 0.5
    high_fraud_amounts = [a for a in amounts if std_dev > 0 and abs((a - mean_amount) / std_dev) > 2]
    high_fraud = len(high_fraud_amounts)
    estimated_fraud_exposure = sum(high_fraud_amounts)

    suspicious_shops = g.V().hasLabel('repairShop').has('suspicious', True).count().next()
    total_claimants = g.V().hasLabel('claimant').count().next()

    return {
        'totalClaims': total,
        'approvedClaims': approved,
        'rejectedClaims': rejected,
        'pendingClaims': pending,
        'highFraudClaims': high_fraud,
        'fraudRate': _trunc(high_fraud / total) if total > 0 else 0,
        'estimatedFraudExposure': _trunc(estimated_fraud_exposure),
        'fraudExposureRate': _trunc(estimated_fraud_exposure / total_amount) if total_amount > 0 else 0,
        'totalClaimAmount': _trunc(total_amount),
        'avgClaimAmount': _trunc(mean_amount),
        'suspiciousRepairShops': suspicious_shops,
        'totalClaimants': total_claimants
    }

@app.get("/fraud-networks/influential-claimants")
@tracer.capture_method
def get_influential_claimants():
    """
    Identify most connected claimants who may be organizing fraud rings
    
    FRAUD CASE: Fraud Ring Organizers
    WHAT IT DOES: Uses PageRank-style analysis to find claimants with the most connections
    to other entities (vehicles, repair shops, witnesses, other claimants)
    WHY IT'S FRAUD: Highly connected claimants are often the organizers of fraud rings,
    recruiting others, coordinating staged accidents, and connecting fraudsters with
    complicit repair shops and witnesses. They're the "hub" of the fraud network.
    
    BUSINESS VALUE: Identifying and investigating ring leaders can dismantle entire
    fraud operations, preventing future fraudulent claims.
    """
    g, remoteConn = get_neptune_connection()
    
    # Use Neptune Analytics PageRank via openCypher
    # Get claimants with their connections and calculate influence
    claimants = g.V().hasLabel('claimant').project('id', 'name', 'claimCount', 'connectionScore').by(T.id).by('name').by(
        __.out('filed_claim').count()
    ).by(
        # Connection score: number of unique entities connected to
        __.union(
            __.out('owns'),  # vehicles
            __.out('filed_claim').out('repaired_at'),  # repair shops
            __.out('filed_claim').out('witnessed_by')  # witnesses
        ).dedup().count()
    ).order().by('connectionScore', Order.desc).toList()

    return {
        'algorithm': 'PageRank (approximated via connection scoring)',
        'topInfluentialClaimants': [
            {
                'claimantId': str(c['id']),
                'name': c['name'],
                'claimCount': c['claimCount'],
                'connectionScore': c['connectionScore'],
                'influenceLevel': 'high' if c['connectionScore'] > 10 else 'medium' if c['connectionScore'] > 5 else 'low'
            }
            for c in claimants
        ]
    }

@app.get("/fraud-networks/organized-rings")
@tracer.capture_method
def detect_organized_fraud_rings():
    """
    Detect organized fraud rings - groups of claimants working together
    
    FRAUD CASE: Organized Fraud Syndicates
    WHAT IT DOES: Uses community detection to find densely connected groups of claimants
    who share vehicles, repair shops, and witnesses
    WHY IT'S FRAUD: Organized fraud rings involve multiple people working together to
    stage accidents, file false claims, and split the payouts. Members share resources
    and coordinate their activities, creating a dense network of connections that
    legitimate claimants wouldn't have.
    
    BUSINESS VALUE: Exposes entire fraud syndicates, allowing insurers to investigate
    all members simultaneously and prevent coordinated fraud schemes.
    """
    g, remoteConn = get_neptune_connection()
    
    # Find densely connected subgraphs - OPTIMIZED for performance
    communities = []

    # Get only top claimants with multiple claims (limit to 50 for performance)
    seed_claimants = g.V().hasLabel('claimant').where(
        __.out('filed_claim').count().is_(P.gt(2))
    ).limit(50).toList()

    seen_seeds = set()

    for seed in seed_claimants:
        seed_id = str(seed.id)

        if seed_id in seen_seeds:
            continue

        # Find 1-hop neighborhood only (faster than 2-hop)
        community_members = g.V(seed_id).union(
            # Claimants sharing vehicles
            __.out('owns').inE('owns').outV(),
            # Claimants using same repair shops
            __.out('filed_claim').out('repaired_at').inE('repaired_at').outV().inE('filed_claim').outV()
        ).dedup().where(__.is_(P.neq(seed))).limit(10).toList()

        if len(community_members) >= 2:
            member_ids = [seed_id] + [str(m.id) for m in community_members]
            seen_seeds.update(member_ids)

            # Calculate community fraud score
            fraud_scores = g.V(*member_ids).out('filed_claim').out('has_fraud_score').values('fraudScore').limit(20).toList()
            avg_fraud = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

            communities.append({
                'seedClaimant': seed_id,
                'communitySize': len(community_members) + 1,
                'members': member_ids,
                'averageFraudScore': _trunc(avg_fraud),
                'riskLevel': 'high' if avg_fraud > 0.7 else 'medium' if avg_fraud > 0.5 else 'low'
            })

            # Stop after finding 10 good rings
            if len([c for c in communities if c['riskLevel'] in ['high', 'medium']]) >= 10:
                break

    # Sort by size and fraud score
    communities.sort(key=lambda x: (x['communitySize'], x['averageFraudScore']), reverse=True)

    # Get top 9 rings and build graph data for each
    rings = []
    for community in communities[:9]:
        member_ids = community['members']

        # Get the full subgraph including connecting entities
        claimant_vertices = g.V(*member_ids).valueMap(True).toList()
        connected_entities = g.V(*member_ids).both().not_(__.hasLabel('fraudEntity')).hasNot('fraudScore').dedup().valueMap(True).toList()

        all_vertices = claimant_vertices + connected_entities
        all_vertex_ids = [str(v[T.id]) for v in all_vertices]

        # Get edges - exclude has_fraud_score
        edges_data = []
        for vid in all_vertex_ids:
            paths = g.V(vid).outE().not_(__.hasLabel('has_fraud_score')).inV().hasId(*all_vertex_ids).path().limit(20).toList()
            for path in paths:
                objs = path.objects
                if len(objs) >= 3:
                    edges_data.append({
                        'source': str(objs[0].id),
                        'target': str(objs[2].id),
                        'label': str(objs[1].label)
                    })

        # Format nodes
        nodes = []
        for v in all_vertices:
            label_value = v[T.label]
            if isinstance(label_value, list):
                label_value = next((l for l in label_value if l != 'fraudEntity'), label_value[0])
            if '::' in str(label_value):
                label_value = str(label_value).split('::')[-1]
            node = {'id': str(v[T.id]), 'label': get_node_label(label_value), 'type': label_value}
            for key, value in v.items():
                if key not in [T.id, T.label]:
                    node[str(key)] = value[0] if isinstance(value, list) and len(value) == 1 else value
            node['fraudScore'] = _get_fraud_score(g, str(v[T.id]))
            nodes.append(node)

        # Split into connected components so each sub-graph is its own ring
        node_map = {n['id']: n for n in nodes}
        adj = {n['id']: set() for n in nodes}
        for e in edges_data:
            adj.setdefault(e['source'], set()).add(e['target'])
            adj.setdefault(e['target'], set()).add(e['source'])

        visited = set()
        for start in node_map:
            if start in visited:
                continue
            # BFS to find connected component
            component = set()
            queue = [start]
            while queue:
                nid = queue.pop()
                if nid in component:
                    continue
                component.add(nid)
                queue.extend(adj.get(nid, set()) - component)
            visited.update(component)

            comp_nodes = [node_map[nid] for nid in component if nid in node_map]
            comp_edges = [e for e in edges_data if e['source'] in component and e['target'] in component]
            if len(comp_nodes) >= 3:
                scores = [n.get('fraudScore', 0) for n in comp_nodes if n.get('fraudScore', 0) > 0]
                avg = _trunc(sum(scores) / len(scores)) if scores else community['averageFraudScore']
                rings.append({
                    'members': [n['id'] for n in comp_nodes if n.get('label') == 'Claimant'],
                    'averageFraudScore': avg,
                    'riskLevel': 'high' if avg > 0.7 else 'medium' if avg > 0.5 else 'low',
                    'graph': {'nodes': comp_nodes, 'edges': comp_edges}
                })

    return {
        'algorithm': 'Community Detection (1-hop neighborhood analysis)',
        'totalCommunities': len(communities),
        'rings': rings
    }

@app.get("/repair-shops/fraud-hubs")
@tracer.capture_method
def identify_fraud_hub_shops():
    # Legacy redirect — kept for API compatibility
    return _get_fraud_hubs_data()

@app.get("/fraud-networks/hubs")
@tracer.capture_method
def get_fraud_hubs():
    return _get_fraud_hubs_data()

def _get_fraud_hubs_data():
    """
    Identify fraud hubs across repair shops, medical providers, and attorneys.
    Ranks by unique claimant count (breadth of network), then scores by shared-entity
    collusion: how many of those claimants also share another entity (witness, attorney,
    repair shop, medical provider) — a strong indicator of coordinated fraud.
    """
    g, remoteConn = get_neptune_connection()

    # All edges go claimant -outE-> hub, EXCEPT repaired_at which goes claim -outE-> repairShop
    # repaired_at: shop.inE().outV() = claims, claims.inE('filed_claim').outV() = claimants
    # treated_by / represented_by: hub.inE().outV() = claimants directly
    hub_configs = [
        ('repairShop',      'repaired_at',    True),   # True = via claim
        ('medicalProvider', 'treated_by',     False),
        ('attorney',        'represented_by', False),
    ]

    result = {}

    for hub_label, claim_edge, via_claim in hub_configs:
        if via_claim:
            count_step = __.inE(claim_edge).outV().inE('filed_claim').outV().dedup().count()
        else:
            count_step = __.inE(claim_edge).outV().hasLabel('claimant').dedup().count()

        top_hubs = (
            g.V().hasLabel(hub_label).has('name')
            .project('id', 'claimantCount')
            .by(T.id)
            .by(count_step)
            .order().by('claimantCount', Order.desc)
            .limit(5).toList()
        )

        result[hub_label] = {'hubs': []}

        for hub_data in top_hubs:
            hub_id = str(hub_data['id'])
            hub_v = g.V(hub_id).valueMap(True).next()

            if via_claim:
                claimant_ids = g.V(hub_id).inE(claim_edge).outV().inE('filed_claim').outV().dedup().id_().toList()
            else:
                claimant_ids = g.V(hub_id).inE(claim_edge).outV().hasLabel('claimant').dedup().id_().toList()
            claimant_ids = [str(c) for c in claimant_ids]
            unique_count = len(claimant_ids)

            colluding = set()
            if unique_count > 1:
                shared = (
                    g.V(*claimant_ids)
                    .both('filed_claim')
                    .bothE('witnessed_by', 'represented_by', 'repaired_at', 'treated_by').otherV()
                    .bothE('witnessed_by', 'represented_by', 'repaired_at', 'treated_by').otherV()
                    .both('filed_claim')
                    .hasLabel('claimant')
                    .hasId(*claimant_ids)
                    .dedup().id_().toList()
                )
                colluding = {str(c) for c in shared}

            collusion_score = round(len(colluding) / unique_count, 2) if unique_count else 0

            hub_nodes = [{
                'id': hub_id,
                'label': get_node_label(hub_label),
                'name': _prop(hub_v, 'name'),
                'type': hub_label,
                'size': 15,
                'uniqueClaimants': unique_count,
                'collusionScore': collusion_score,
            }]
            hub_edges = []

            for cid in claimant_ids[:12]:
                try:
                    cv = g.V(cid).valueMap(True).next()
                    hub_nodes.append({
                        'id': cid,
                        'label': get_node_label('claimant'),
                        'name': _prop(cv, 'name'),
                        'type': 'claimant',
                        'size': 10 if cid in colluding else 7,
                        'colluding': cid in colluding,
                        'fraudScore': _get_fraud_score(g, cid),
                    })
                    hub_edges.append({'source': cid, 'target': hub_id, 'type': 'connected_to'})
                except Exception:
                    continue

            result[hub_label]['hubs'].append({
                'name': _prop(hub_v, 'name'),
                'uniqueClaimants': unique_count,
                'collusionScore': collusion_score,
                'graph': {'nodes': hub_nodes, 'edges': hub_edges},
            })

    return result

@app.get("/fraud-networks/connections")
@tracer.capture_method
def find_fraudster_connections():
    """
    Find shortest connection path between two entities in fraud network
    
    FRAUD CASE: Hidden Relationships Between Suspects
    WHAT IT DOES: Finds the shortest path of relationships connecting two people, vehicles,
    or organizations in the fraud network
    WHY IT'S FRAUD: When investigating suspected fraud, finding how two entities are connected
    reveals the structure of the fraud operation. A short path between seemingly unrelated
    claimants suggests coordination. Paths through specific repair shops or witnesses expose
    the fraud infrastructure.
    
    BUSINESS VALUE: Helps investigators understand fraud network structure, identify key
    players, and build cases showing how fraud participants are connected.
    """
    g, remoteConn = get_neptune_connection()
    
    params = app.current_event.query_string_parameters or {}
    source_id = params.get('source')
    target_id = params.get('target')

    if source_id and target_id:
        # Find shortest path between the two specified claimants
        nodes = []
        edges = []
        node_ids = set()

        try:
            path = g.V(source_id).repeat(
                __.bothE().not_(__.hasLabel('has_fraud_score')).otherV().not_(__.hasLabel('fraudEntity')).simplePath()
            ).until(
                __.or_(__.hasId(target_id), __.loops().is_(6))
            ).hasId(target_id).limit(1).path().toList()

            if path:
                objs = path[0].objects
                # Separate vertices (even indices) and edges (odd indices)
                for i, obj in enumerate(objs):
                    if i % 2 == 0:
                        # Vertex
                        v_id = str(obj.id)
                        if v_id not in node_ids:
                            node_ids.add(v_id)
                            v = g.V(v_id).valueMap(True).next()
                            v_label = v.get(T.label)
                            if isinstance(v_label, list):
                                v_label = next((l for l in v_label if l != 'fraudEntity'), v_label[0])
                            nodes.append({
                                'id': v_id,
                                'label': _prop(v, 'name', get_node_label(v_label)),
                                'type': v_label,
                                'fraudScore': _get_fraud_score(g, v_id),
                                'size': 10
                            })
                    else:
                        # Edge - build connection
                        src = str(objs[i - 1].id)
                        tgt = str(objs[i + 1].id)
                        edges.append({
                            'source': src,
                            'target': tgt,
                            'type': str(obj.label) if hasattr(obj, 'label') else 'connected'
                        })

                return {
                    'algorithm': 'Shortest Path',
                    'source': source_id,
                    'target': target_id,
                    'pathLength': len(nodes),
                    'nodes': nodes,
                    'edges': edges
                }
            else:
                return {
                    'algorithm': 'Shortest Path',
                    'source': source_id,
                    'target': target_id,
                    'pathLength': 0,
                    'message': 'No path found between the selected claimants',
                    'nodes': [],
                    'edges': []
                }
        except Exception as e:
            logger.error(f"Path finding failed: {e}")
            return {
                'algorithm': 'Shortest Path',
                'source': source_id,
                'target': target_id,
                'pathLength': 0,
                'message': f'Path analysis failed: {str(e)}',
                'nodes': [],
                'edges': []
            }

    # Default: auto-detect connected claimant pairs via shared entities (shops, witnesses, etc.)
    # Find claimants that share a repair shop (2 hops: claimant->claim->shop<-claim<-claimant)
    pairs = g.V().hasLabel('claimant').as_('a') \
        .out('filed_claim').out('repaired_at').in_('repaired_at').in_('filed_claim') \
        .hasLabel('claimant').where(P.neq('a')).as_('b') \
        .select('a', 'b').by(T.id).dedup().limit(10).toList()

    # Deduplicate unordered pairs
    seen = set()
    unique_pairs = []
    for p in pairs:
        key = tuple(sorted([str(p['a']), str(p['b'])]))
        if key not in seen:
            seen.add(key)
            unique_pairs.append(key)
        if len(unique_pairs) >= 3:
            break

    if len(unique_pairs) < 1:
        return {
            'algorithm': 'Shortest Path',
            'message': 'No connected claimant pairs found',
            'fraudNetworkConnections': []
        }

    paths = []
    for source_id, target_id in unique_pairs:
        path = g.V(source_id).repeat(
            __.bothE().not_(__.hasLabel('has_fraud_score')).otherV().not_(__.hasLabel('fraudEntity')).simplePath()
        ).until(
            __.hasId(target_id)
        ).limit(1).path().toList()

        if path:
            path_len = (len(path[0].objects) + 1) // 2
            s_name = _prop(g.V(source_id).valueMap(True).next(), 'name', source_id)
            t_name = _prop(g.V(target_id).valueMap(True).next(), 'name', target_id)
            paths.append({
                'source': source_id,
                'target': target_id,
                'sourceName': s_name,
                'targetName': t_name,
                'pathLength': path_len,
                'connectionType': 'direct' if path_len <= 3 else 'indirect'
            })

    return {
        'algorithm': 'Shortest Path',
        'fraudNetworkConnections': paths,
        'insight': 'Short paths between claimants indicate potential organized fraud rings'
    }

@app.get("/fraud-patterns/collusion-indicators")
@tracer.capture_method
def detect_collusion_indicators():
    """
    Detect collusion indicators - returns network graph showing shared resources
    """
    g, remoteConn = get_neptune_connection()
    
    nodes = []
    edges = []
    node_ids = set()

    # Get repair shops with multiple claimants (potential collusion hubs)
    shops = g.V().hasLabel('repairShop').has('name').where(
        __.inE('repaired_at').count().is_(P.gte(5))
    ).limit(5).valueMap(True).toList()

    for s in shops:
        s_id = str(s.get(T.id))
        node_ids.add(s_id)
        nodes.append({
            'id': s_id,
            'label': get_node_label('repairShop'),
            'name': _prop(s, 'name'),
            'type': 'repairShop',
            'fraudScore': _get_fraud_score(g, s_id),
            'size': 20
        })

        # Get claimants who use this shop
        claimants = g.V(s_id).inE('repaired_at').outV().inE('filed_claim').outV().dedup().limit(5).valueMap(True).toList()
        for c in claimants:
            c_id = str(c.get(T.id))
            if c_id not in node_ids:
                node_ids.add(c_id)
                nodes.append({
                    'id': c_id,
                    'label': get_node_label('claimant'),
                'name': _prop(c, 'name'),
                    'fraudScore': _get_fraud_score(g, c_id),
                    'size': 12
                })
            edges.append({'source': c_id, 'target': s_id})

    return {
        'nodes': nodes,
        'edges': edges
    }

@app.get("/fraud-networks/isolated-rings")
@tracer.capture_method
def find_isolated_fraud_rings():
    """
    Find isolated fraud rings - independent groups operating separately
    
    If id and type query parameters are provided, returns the specific isolated ring for that entity.
    Otherwise, returns a list of all isolated rings.
    """
    # Check for query parameters
    query_params = app.current_event.get('queryStringParameters', {}) if app.current_event.get('queryStringParameters') else {}
    entity_id = query_params.get('id')
    entity_type = query_params.get('type')
    
    # If entity_id is provided, return the specific ring
    if entity_id:
        return get_entity_isolated_ring(entity_id, entity_type)
    
    # Otherwise, return list of all isolated rings
    g, remoteConn = get_neptune_connection()
    
    # Find weakly connected components by grouping claimants
    # who share any resources (vehicles, repair shops, witnesses)
    components = []
    visited = set()

    claimants = g.V().hasLabel('claimant').toList()

    for claimant in claimants:
        c_id = str(claimant.id)
        if c_id in visited:
            continue

        # BFS to find all connected claimants
        component = g.V(c_id).repeat(
            __.union(
                __.out('owns').inE('owns').outV(),
                __.out('filed_claim').out('repaired_at').inE('repaired_at').outV().inE('filed_claim').outV(),
                __.out('filed_claim').out('witnessed_by').inE('witnessed_by').outV().inE('filed_claim').outV()
            ).dedup()
        ).times(3).dedup().toList()

        component_ids = [str(v.id) for v in component]
        visited.update(component_ids)

        if len(component) > 3:
            # Calculate component fraud metrics
            fraud_scores = g.V(*component_ids).out('filed_claim').out('has_fraud_score').values('fraudScore').toList()
            avg_fraud = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

            components.append({
                'componentId': len(components) + 1,
                'size': len(component),
                'members': component_ids[:5],
                'averageFraudScore': _trunc(avg_fraud),
                'isolationLevel': 'isolated' if len(component) < 10 else 'connected',
                'riskLevel': 'high' if avg_fraud > 0.7 and len(component) > 5 else 'medium' if avg_fraud > 0.5 else 'low'
            })

    components.sort(key=lambda x: (x['size'], x['averageFraudScore']), reverse=True)

    return {
        'algorithm': 'Connected Components',
        'totalComponents': len(components),
        'largestComponent': components[0] if components else None,
        'suspiciousComponents': [c for c in components if c['riskLevel'] in ['high', 'medium']][:10],
        'insight': 'Isolated components may represent independent fraud rings'
    }

@app.get("/vehicles/<vehicle_id>/fraud-history")
@tracer.capture_method
def get_vehicle_fraud_history(vehicle_id: str):
    """
    Analyze vehicle's claim history and fraud risk using Neptune ML
    
    FRAUD CASE: Vehicle-Centric Fraud Schemes
    WHAT IT DOES: Uses Neptune ML to predict fraud risk for a specific vehicle based on its
    claim history, ownership patterns, and repair shop relationships
    WHY IT'S FRAUD: Vehicles involved in multiple suspicious claims, frequently changing owners,
    or always repaired at the same shop may be used in staged accidents. Fraudsters often use
    the same vehicle repeatedly to file false claims, or pass vehicles between ring members to
    create new "accidents."
    
    BUSINESS VALUE: Flags high-risk vehicles before approving claims, preventing repeat fraud
    and identifying vehicles that should trigger enhanced investigation.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(vehicle_id).hasNext():
        return {'error': f'Vehicle {vehicle_id} not found'}, 404

    vehicle = g.V(vehicle_id).valueMap(True).next()

    # Get all claims for this vehicle
    claims = g.V(vehicle_id).inE('for_vehicle').outV().valueMap(True).toList()

    if not claims:
        return {
            'vehicleId': vehicle_id,
            'make': vehicle.get('make', ['Unknown'])[0],
            'year': vehicle.get('year', [0])[0],
            'totalClaims': 0,
            'riskLevel': 'unknown'
        }

    # Calculate fraud metrics
    fraud_scores = [_get_fraud_score(g, str(c.get(T.id))) for c in claims]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.0
    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)

    # Get different owners
    owners = g.V(vehicle_id).inE('owns').outV().dedup().count().next()

    # Get different repair shops
    repair_shops = g.V(vehicle_id).inE('for_vehicle').outV().out('repaired_at').dedup().count().next()

    # Use Neptune ML to predict if vehicle itself is high-risk
    # This uses inductive inference on the vehicle node
    try:
        vehicle_risk = g.V(vehicle_id).properties('riskScore').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
        ml_risk_score = float(vehicle_risk) if vehicle_risk else avg_fraud_score
    except Exception:
        ml_risk_score = avg_fraud_score

    return {
        'vehicleId': vehicle_id,
        'make': vehicle.get('make', ['Unknown'])[0],
        'year': vehicle.get('year', [0])[0],
        'vin': vehicle.get('vin', ['Unknown'])[0],
        'totalClaims': len(claims),
        'highFraudClaims': high_fraud_claims,
        'averageFraudScore': _trunc(avg_fraud_score),
        'mlRiskScore': _trunc(ml_risk_score),
        'differentOwners': owners,
        'differentRepairShops': repair_shops,
        'riskLevel': 'high' if ml_risk_score > 0.7 else 'medium' if ml_risk_score > 0.5 else 'low',
        'redFlags': {
            'multipleOwners': owners > 2,
            'frequentClaims': len(claims) > 3,
            'highFraudRate': high_fraud_claims / len(claims) > 0.5 if claims else False
        }
    }

@app.get("/vehicles/<vehicle_id>")
@tracer.capture_method
def get_vehicle_network(vehicle_id: str):
    """Get vehicle's one-level neighborhood network graph"""
    g, remoteConn = get_neptune_connection()
    return _build_neighborhood_graph(g, vehicle_id, 'vehicle')

@app.get("/medical-providers/<provider_id>/fraud-analysis")
@tracer.capture_method
def analyze_medical_provider_fraud(provider_id: str):
    """
    Analyze medical provider fraud patterns using Neptune ML
    
    FRAUD CASE: Medical Provider Fraud and Billing Schemes
    WHAT IT DOES: Uses Neptune ML to assess fraud risk for medical providers based on their
    billing patterns, patient relationships, and claim characteristics
    WHY IT'S FRAUD: Fraudulent medical providers inflate treatment costs, bill for services
    never rendered, or collude with claimants to exaggerate injuries. Providers consistently
    associated with high-fraud claims, treating the same claimants repeatedly, or billing
    unusually high amounts are likely participating in fraud schemes.
    
    BUSINESS VALUE: Identifies corrupt medical providers, prevents inflated medical billing,
    and protects against organized fraud rings involving healthcare professionals.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(provider_id).hasNext():
        return {'error': f'Medical provider {provider_id} not found'}, 404

    provider = g.V(provider_id).valueMap(True).next()

    # Get all claims involving this provider
    claims = g.V(provider_id).inE('treated_by').outV().valueMap(True).toList()

    if not claims:
        return {
            'providerId': provider_id,
            'name': provider.get('name', ['Unknown'])[0],
            'totalClaims': 0,
            'riskLevel': 'unknown'
        }

    # Calculate fraud metrics
    fraud_scores = [_get_fraud_score(g, str(c.get(T.id))) for c in claims]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.0
    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)

    # Get unique claimants
    unique_claimants = g.V(provider_id).inE('treated_by').outV().inE('filed_claim').outV().dedup().count().next()

    # Use Neptune ML to predict provider fraud risk
    try:
        provider_risk = g.V(provider_id).properties('fraudRisk').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
        ml_risk_score = float(provider_risk) if provider_risk else avg_fraud_score
    except Exception:
        ml_risk_score = avg_fraud_score

    # Find if provider is part of a fraud network (degree centrality)
    network_connections = g.V(provider_id).inE('treated_by').outV().inE('filed_claim').outV().out('filed_claim').out('repaired_at').dedup().count().next()

    return {
        'providerId': provider_id,
        'name': provider.get('name', ['Unknown'])[0],
        'totalClaims': len(claims),
        'uniqueClaimants': unique_claimants,
        'highFraudClaims': high_fraud_claims,
        'averageFraudScore': _trunc(avg_fraud_score),
        'mlRiskScore': _trunc(ml_risk_score),
        'networkConnections': network_connections,
        'riskLevel': 'high' if ml_risk_score > 0.7 else 'medium' if ml_risk_score > 0.5 else 'low',
        'suspicionIndicators': {
            'highFraudRate': high_fraud_claims / len(claims) > 0.5 if claims else False,
            'limitedClaimants': unique_claimants < 5 and len(claims) > 10,
            'networkHub': network_connections > 20
        }
    }

@app.get("/medical-providers/<provider_id>")
@tracer.capture_method
def get_medical_provider_network(provider_id: str):
    """Get medical provider's one-level neighborhood network graph"""
    g, remoteConn = get_neptune_connection()
    
    return _build_neighborhood_graph(g, provider_id, 'medicalProvider')

@app.get("/claimants/<claimant_id>/claim-velocity")
@tracer.capture_method
def analyze_claim_velocity(claimant_id: str):
    """
    Analyze claim filing frequency using time-series pattern detection
    
    FRAUD CASE: Serial Claim Filers and Velocity Fraud
    WHAT IT DOES: Analyzes how frequently a claimant files claims over time, detecting
    suspicious patterns like claim bursts or unusually high filing rates
    WHY IT'S FRAUD: Legitimate claimants rarely file multiple claims in short periods.
    Fraudsters file many claims quickly to maximize payouts before detection. High claim
    velocity indicates professional fraud operations where individuals systematically file
    false claims, often timing them to avoid detection thresholds.
    
    BUSINESS VALUE: Identifies serial fraudsters early, prevents claim farming schemes,
    and flags accounts for immediate review when velocity exceeds normal patterns.
    """
    g, remoteConn = get_neptune_connection()
    
    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 404

    # Get all claims with timestamps
    claims = g.V(claimant_id).out('filed_claim').valueMap('claimDate', 'amount', 'fraudScore').toList()

    if len(claims) < 2:
        return {
            'claimantId': claimant_id,
            'totalClaims': len(claims),
            'velocityRisk': 'low',
            'message': 'Insufficient claim history'
        }

    # Sort by timestamp
    claims_sorted = sorted(claims, key=lambda x: x.get('claimDate', [0])[0])
    timestamps = [c.get('claimDate', [0])[0] for c in claims_sorted]

    # Calculate time intervals between claims (in days)
    intervals = []
    for i in range(1, len(timestamps)):
        interval_days = (timestamps[i] - timestamps[i-1]) / 86400  # seconds to days
        intervals.append(interval_days)

    avg_interval = sum(intervals) / len(intervals) if intervals else 0
    min_interval = min(intervals) if intervals else 0

    # Velocity score: claims per year
    if timestamps:
        time_span_years = (timestamps[-1] - timestamps[0]) / (86400 * 365)
        claims_per_year = len(claims) / time_span_years if time_span_years > 0 else len(claims)
    else:
        claims_per_year = 0

    # Use Neptune ML to predict velocity-based fraud risk
    try:
        velocity_risk = g.V(claimant_id).properties('velocityRisk').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
        ml_velocity_score = float(velocity_risk) if velocity_risk else min(claims_per_year / 10, 1.0)
    except Exception:
        ml_velocity_score = min(claims_per_year / 10, 1.0)

    return {
        'claimantId': claimant_id,
        'totalClaims': len(claims),
        'claimsPerYear': _trunc(claims_per_year),
        'averageIntervalDays': _trunc(avg_interval),
        'shortestIntervalDays': _trunc(min_interval),
        'mlVelocityScore': _trunc(ml_velocity_score),
        'velocityRisk': 'high' if claims_per_year > 5 or min_interval < 30 else 'medium' if claims_per_year > 3 else 'low',
        'redFlags': {
            'rapidFiling': min_interval < 30,
            'highFrequency': claims_per_year > 5,
            'suspiciousPattern': min_interval < 30 and claims_per_year > 3
        }
    }

@app.get("/analytics/geographic-hotspots")
@tracer.capture_method
def detect_geographic_fraud_hotspots():
    """
    Detect fraud hotspots across entity types: repair shops, medical providers, attorneys, tow companies
    """
    g, remoteConn = get_neptune_connection()

    def build_entity_hotspots(label, in_edge, limit=5):
        """Find top entities by claim volume with their claimant networks — single traversal"""
        rows = (
            g.V().hasLabel(label).has('name')
            .order().by(__.inE(in_edge).count(), Order.desc)
            .limit(limit)
            .project('id', 'name', 'count', 'claimIds', 'claimantData')
            .by(T.id)
            .by('name')
            .by(__.inE(in_edge).count())
            .by(__.inE(in_edge).outV().limit(8).id_().fold())
            .by(__.inE(in_edge).outV().limit(8).in_('filed_claim').dedup()
                .project('id', 'name').by(T.id).by(__.values('name').fold()).fold())
            .toList()
        )

        nodes = []
        edges = []
        node_ids = set()

        for row in rows:
            eid = str(row['id'])
            node_ids.add(eid)
            nodes.append({
                'id': eid,
                'label': get_node_label(label),
                'name': row['name'],
                'type': label,
                'size': min(int(row['count']) * 2 + 10, 40)
            })

            claim_ids = [str(c) for c in row['claimIds']]
            for cid in claim_ids:
                if cid not in node_ids:
                    node_ids.add(cid)
                    nodes.append({'id': cid, 'label': get_node_label('claim'), 'type': 'claim', 'size': 7})
                edges.append({'source': cid, 'target': eid, 'type': in_edge})

            for cl in row['claimantData']:
                clid = str(cl['id'])
                name = cl['name'][0] if cl['name'] else None
                if clid not in node_ids:
                    node_ids.add(clid)
                    nodes.append({'id': clid, 'label': get_node_label('claimant'), 'name': name, 'type': 'claimant', 'size': 10})
                # Edge from claimant to one of the claims (approximate — link to first shared claim)
                for cid in claim_ids:
                    edges.append({'source': clid, 'target': cid, 'type': 'filed_claim'})
                    break  # one edge per claimant is enough for visualization

        return {'nodes': nodes, 'edges': edges}

    return {
        'repairShops': build_entity_hotspots('repairShop', 'repaired_at'),
        'medicalProviders': build_entity_hotspots('medicalProvider', 'treated_by'),
        'attorneys': build_entity_hotspots('attorney', 'represented_by'),
        'towCompanies': build_entity_hotspots('towCompany', 'towed_by'),
    }

@app.get("/analytics/claim-amount-anomalies")
@tracer.capture_method
def detect_claim_amount_anomalies():
    """
    Detect anomalous claim amounts using statistical analysis and Neptune ML
    
    FRAUD CASE: Inflated Claim Amounts and Billing Fraud
    WHAT IT DOES: Uses statistical analysis to identify claims with unusually high amounts
    compared to similar claims, flagging potential inflation or billing fraud
    WHY IT'S FRAUD: Fraudsters inflate claim amounts by exaggerating damages, billing for
    unnecessary repairs, or adding fictitious expenses. Claims that are statistical outliers
    (significantly higher than average for similar incidents) indicate deliberate inflation
    to maximize fraudulent payouts.
    
    BUSINESS VALUE: Prevents overpayment on inflated claims, identifies systematic billing
    fraud patterns, and saves money by flagging claims for detailed cost review.
    """
    g, remoteConn = get_neptune_connection()
    
    # Get all claims with amounts
    claims = g.V().hasLabel('claim').has('amount').elementMap('amount', 'fraudScore').toList()

    if len(claims) < 10:
        return {'error': 'Insufficient data for anomaly detection'}, 400

    amounts = [c.get('amount', 0) for c in claims]

    # Calculate statistics
    mean_amount = sum(amounts) / len(amounts)
    variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
    std_dev = variance ** 0.5

    # Find anomalies (> 2 standard deviations)
    anomalies = []
    for claim in claims:
        amount = claim.get('amount', 0)
        if isinstance(amount, list):
            amount = amount[0] if amount else 0

        fraud_score = claim.get('fraudScore', 0.0)
        if isinstance(fraud_score, list):
            fraud_score = fraud_score[0] if fraud_score else 0.0

        claim_id = str(claim[T.id])

        z_score = (amount - mean_amount) / std_dev if std_dev > 0 else 0

        if abs(z_score) > 2:
            # Use Neptune ML to validate if high amount is fraudulent
            try:
                ml_anomaly_score = g.V(claim_id).properties('anomalyScore').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
                ml_score = float(ml_anomaly_score) if ml_anomaly_score else fraud_score
            except Exception:
                ml_score = fraud_score

            anomalies.append({
                'claimId': claim_id,
                'amount': _trunc(amount),
                'zScore': _trunc(z_score),
                'fraudScore': _trunc(fraud_score),
                'mlAnomalyScore': _trunc(ml_score),
                'anomalyType': 'unusually_high' if z_score > 0 else 'unusually_low',
                'riskLevel': 'high' if ml_score > 0.7 and abs(z_score) > 3 else 'medium'
            })

    anomalies.sort(key=lambda x: abs(x['zScore']), reverse=True)

    return {
        'algorithm': 'Statistical Anomaly Detection + Neptune ML',
        'statistics': {
            'meanAmount': _trunc(mean_amount),
            'standardDeviation': _trunc(std_dev),
            'totalClaims': len(claims)
        },
        'anomaliesDetected': len(anomalies),
        'highRiskAnomalies': [a for a in anomalies if a['riskLevel'] == 'high'][:10],
        'allAnomalies': anomalies
    }

@app.get("/analytics/temporal-patterns")
@tracer.capture_method
def detect_temporal_fraud_patterns():
    """
    Detect time-based fraud patterns using temporal analysis
    
    FRAUD CASE: Timing-Based Fraud Schemes
    WHAT IT DOES: Analyzes temporal patterns in claim filing, identifying suspicious timing
    through timing analysis, and prevents "buy policy, file claim, cancel policy" schemes.
    """
    g, remoteConn = get_neptune_connection()
    
    # Find claims filed shortly after policy inception (suspicious timing)
    # Using claim timestamps as proxy
    claims = g.V().hasLabel('claim').has('amount').valueMap('claimDate', 'fraudScore', 'amount').toList()

    if len(claims) < 10:
        return {'error': 'Insufficient data for temporal analysis'}, 400

    # Group by time of day (hour)
    hourly_fraud = {}
    for claim in claims:
        timestamp = claim.get('claimDate', [0])[0]
        fraud_score = claim.get('fraudScore', [0.0])[0]

        # Extract hour (0-23)
        hour = (timestamp // 3600) % 24

        if hour not in hourly_fraud:
            hourly_fraud[hour] = {'count': 0, 'total_fraud': 0}

        hourly_fraud[hour]['count'] += 1
        hourly_fraud[hour]['total_fraud'] += fraud_score

    # Calculate average fraud by hour
    hourly_patterns = [
        {
            'hour': hour,
            'claimCount': data['count'],
            'averageFraudScore': _trunc(data['total_fraud'] / data['count']),
            'suspicionLevel': 'high' if data['total_fraud'] / data['count'] > 0.7 else 'medium' if data['total_fraud'] / data['count'] > 0.5 else 'low'
        }
        for hour, data in hourly_fraud.items()
    ]

    hourly_patterns.sort(key=lambda x: x['averageFraudScore'], reverse=True)

    # Find rapid-fire claims (multiple claims in short time)
    rapid_filers = g.V().hasLabel('claimant').where(
        __.out('filed_claim').count().is_(P.gt(2))
    ).project('claimantId', 'name', 'claimCount').by(T.id).by(
        __.values('name')
    ).by(
        __.out('filed_claim').count()
    ).order().by('claimCount', Order.desc).toList()

    result = []
    for r in rapid_filers:
        cid = str(r['claimantId'])
        claims = g.V(cid).out('filed_claim').valueMap(True).toList()
        amounts = [_prop(c, 'amount', 0) for c in claims]
        statuses = [_prop(c, 'status', '') for c in claims]
        dates = sorted([_prop(c, 'claimDate', 0) for c in claims if _prop(c, 'claimDate', 0)])
        fraud_scores = [_get_fraud_score(g, str(c[T.id])) for c in claims]

        total_amount = sum(amounts)
        rejected = sum(1 for s in statuses if s == 'rejected')
        rejection_rate = rejected / len(claims) if claims else 0
        avg_fraud = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

        if len(dates) >= 2:
            intervals = [(dates[i+1] - dates[i]) for i in range(len(dates)-1)]
            avg_days = sum(intervals) / len(intervals) / 86400  # seconds to days
        else:
            avg_days = None

        result.append({
            'claimantId': cid,
            'name': r['name'],
            'claimCount': r['claimCount'],
            'totalAmount': _trunc(total_amount),
            'rejectionRate': _trunc(rejection_rate),
            'avgFraudScore': _trunc(avg_fraud),
            'avgDaysBetweenClaims': _trunc(avg_days) if avg_days is not None else None,
            'suspicionLevel': 'high' if r['claimCount'] > 5 else 'medium'
        })

    return {
        'algorithm': 'Temporal Pattern Analysis',
        'hourlyPatterns': hourly_patterns[:10],
        'suspiciousHours': [p for p in hourly_patterns if p['suspicionLevel'] in ['high', 'medium']][:5],
        'rapidFilers': result
    }

@app.get("/fraud-patterns/cross-claim-patterns")
@tracer.capture_method
def detect_cross_claim_patterns():
    """
    Detect claimants who always use same entities (repair shops, witnesses, providers)
    
    FRAUD CASE: Habitual Pattern Fraud
    WHAT IT DOES: Identifies claimants who consistently use the same repair shops, witnesses,
    or medical providers across multiple claims, indicating pre-arranged fraud relationships
    WHY IT'S FRAUD: Legitimate claimants use different service providers based on accident
    location, convenience, and recommendations. Fraudsters repeatedly use the same complicit
    repair shops, witnesses, and medical providers because these entities are part of their
    fraud operation. Consistent patterns across claims reveal pre-arranged fraud relationships.
    
    BUSINESS VALUE: Exposes fraud networks by identifying habitual relationships, helps
    investigators focus on claimants with suspicious loyalty patterns, and reveals the
    infrastructure supporting fraud operations.
    """
    g, remoteConn = get_neptune_connection()
    
    # Find claimants with consistent patterns across claims
    patterns = []

    claimants = g.V().hasLabel('claimant').where(
        __.out('filed_claim').count().is_(P.gt(2))
    ).toList()

    for claimant in claimants:
        c_id = str(claimant.id)

        # Get claim count
        claim_count = g.V(c_id).out('filed_claim').count().next()

        # Get unique repair shops used
        repair_shops = g.V(c_id).out('filed_claim').out('repaired_at').dedup().toList()

        # Get unique witnesses
        witnesses = g.V(c_id).out('filed_claim').out('witnessed_by').dedup().toList()

        # Get unique medical providers
        providers = g.V(c_id).out('filed_claim').out('treated_by').dedup().toList()

        # Calculate pattern consistency (low diversity = suspicious)
        shop_diversity = len(repair_shops) / claim_count if claim_count > 0 else 0
        witness_diversity = len(witnesses) / claim_count if claim_count > 0 else 0
        provider_diversity = len(providers) / claim_count if claim_count > 0 else 0

        # Low diversity across multiple claims is suspicious
        if claim_count >= 3 and (shop_diversity < 0.5 or witness_diversity < 0.5):
            # Use Neptune ML to assess pattern-based fraud risk
            try:
                pattern_risk = g.V(c_id).properties('patternRisk').with_("Neptune#ml.regression").with_("Neptune#ml.inductiveInference").value().next()
                ml_pattern_score = float(pattern_risk) if pattern_risk else (1 - shop_diversity)
            except Exception:
                ml_pattern_score = 1 - shop_diversity

            patterns.append({
                'claimantId': c_id,
                'totalClaims': claim_count,
                'uniqueRepairShops': len(repair_shops),
                'uniqueWitnesses': len(witnesses),
                'uniqueProviders': len(providers),
                'shopDiversity': _trunc(shop_diversity),
                'witnessDiversity': _trunc(witness_diversity),
                'mlPatternScore': _trunc(ml_pattern_score),
                'suspicionLevel': 'high' if ml_pattern_score > 0.7 else 'medium' if ml_pattern_score > 0.5 else 'low',
                'redFlags': {
                    'sameShopAlways': len(repair_shops) == 1 and claim_count > 2,
                    'sameWitnessAlways': len(witnesses) == 1 and claim_count > 2,
                    'lowDiversity': shop_diversity < 0.3 and claim_count > 3
                }
            })

    patterns.sort(key=lambda x: x['mlPatternScore'], reverse=True)

    return {
        'algorithm': 'Cross-Claim Pattern Analysis + Neptune ML',
        'totalSuspiciousPatterns': len(patterns),
        'highRiskPatterns': [p for p in patterns if p['suspicionLevel'] == 'high'][:10],
        'allPatterns': patterns[:20]
    }

@app.get("/claimants/<claimant_id>/fraud-analysis")
@tracer.capture_method
def analyze_claimant_fraud(claimant_id: str):
    """Deep dive analysis of claimant showing all fraud connections as a graph"""
    g, remoteConn = get_neptune_connection()
    
    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 404

    return _build_claimant_graph(g, claimant_id)

@app.get("/claimants/<claimant_id>")
@tracer.capture_method
def get_claimant_network(claimant_id: str):
    """Get claimant's one-level neighborhood network graph"""
    g, remoteConn = get_neptune_connection()
    
    return _build_neighborhood_graph(g, claimant_id, 'claimant')

@app.get("/fraud-patterns/cross-claim-patterns/<claimant_id>")
@tracer.capture_method
def get_claimant_neighborhood(claimant_id: str):
    """Get cross-claim pattern metrics and neighborhood graph for a claimant"""
    g, remoteConn = get_neptune_connection()

    if not g.V(claimant_id).hasNext():
        return {'error': f'Claimant {claimant_id} not found'}, 404

    # Calculate cross-claim metrics
    claim_count = g.V(claimant_id).out('filed_claim').count().next()
    repair_shops = g.V(claimant_id).out('filed_claim').out('repaired_at').dedup().toList()
    witnesses = g.V(claimant_id).out('filed_claim').out('witnessed_by').dedup().toList()
    providers = g.V(claimant_id).out('filed_claim').out('treated_by').dedup().toList()

    shop_diversity = len(repair_shops) / claim_count if claim_count > 0 else 0
    witness_diversity = len(witnesses) / claim_count if claim_count > 0 else 0

    graph = _build_neighborhood_graph(g, claimant_id, 'claimant')

    return {
        'metrics': {
            'totalClaims': claim_count,
            'uniqueRepairShops': len(repair_shops),
            'uniqueWitnesses': len(witnesses),
            'uniqueProviders': len(providers),
            'shopDiversity': _trunc(shop_diversity),
            'witnessDiversity': _trunc(witness_diversity),
            'redFlags': {
                'sameShopAlways': len(repair_shops) == 1 and claim_count > 2,
                'sameWitnessAlways': len(witnesses) == 1 and claim_count > 2,
                'lowDiversity': shop_diversity < 0.3 and claim_count > 3
            }
        },
        'nodes': graph.get('nodes', []),
        'edges': graph.get('edges', [])
    }

# List endpoints for dropdowns
@app.get("/claimants")
@tracer.capture_method
def list_claimants():
    """List all claimants"""
    g, remoteConn = get_neptune_connection()
    return {'claimants': _list_entities(g, 'claimant')}

@app.get("/claims")
@tracer.capture_method
def list_claims():
    """List all claims"""
    g, remoteConn = get_neptune_connection()
    claims = g.V().hasLabel('claim').has('amount').valueMap(True).toList()
    return {
        'claims': [
            {
                'id': str(c.get(T.id)),
                'amount': _prop(c, 'amount', 0),
                'date': _prop(c, 'claimDate', None)
            }
            for c in claims
        ]
    }

@app.get("/repair-shops")
@tracer.capture_method
def list_repair_shops():
    """List all repair shops"""
    g, remoteConn = get_neptune_connection()
    return {'repairShops': _list_entities(g, 'repairShop')}

@app.get("/vehicles")
@tracer.capture_method
def list_vehicles():
    """List all vehicles"""
    g, remoteConn = get_neptune_connection()
    vehicles = g.V().hasLabel('vehicle').valueMap(True).toList()
    return {
        'vehicles': [
            {
                'id': str(v.get(T.id)),
                'make': _prop(v, 'make', 'Unknown'),
                'year': _prop(v, 'year', 0),
                'plate': _prop(v, 'plate', '')
            }
            for v in vehicles
        ]
    }

@app.get("/medical-providers")
@tracer.capture_method
def list_medical_providers():
    """List all medical providers"""
    g, remoteConn = get_neptune_connection()
    return {'medicalProviders': _list_entities(g, 'medicalProvider')}

@app.get("/attorneys")
@tracer.capture_method
def list_attorneys():
    """List all attorneys"""
    g, remoteConn = get_neptune_connection()
    return {'attorneys': _list_entities(g, 'attorney')}

@app.get("/witnesses")
@tracer.capture_method
def list_witnesses():
    """List all witnesses"""
    g, remoteConn = get_neptune_connection()
    return {'witnesses': _list_entities(g, 'witness')}

@app.get("/passengers")
@tracer.capture_method
def list_passengers():
    """List all passengers"""
    g, remoteConn = get_neptune_connection()
    return {'passengers': _list_entities(g, 'passenger')}

@app.get("/tow-companies")
@tracer.capture_method
def list_tow_companies():
    """List all tow companies"""
    g, remoteConn = get_neptune_connection()
    return {'towCompanies': _list_entities(g, 'towCompany')}

@app.get("/isolated-rings/<entity_id>")
@tracer.capture_method
def get_entity_isolated_ring(entity_id: str, entity_type: str = None):
    """Get the isolated ring (2-hop neighborhood) for an entity"""
    g, remoteConn = get_neptune_connection()
    
    # Check if entity exists
    if not g.V(entity_id).hasNext():
        return {'error': f'Entity {entity_id} not found'}, 404

    # Get 2-hop neighborhood vertices - exclude fraudEntity vertices
    vertices = g.V(entity_id).emit().repeat(
        __.both().hasNot('fraudScore').simplePath()
    ).times(2).dedup().valueMap(True).toList()
    vertex_ids = [str(v[T.id]) for v in vertices]

    # Get edges - exclude has_fraud_score edges
    edges_data = []
    for vid in vertex_ids:
        paths = g.V(vid).outE().not_(__.hasLabel('has_fraud_score')).inV().hasId(*vertex_ids).path().toList()
        for path in paths:
            objs = path.objects
            if len(objs) >= 3:
                edges_data.append({
                    'source': str(objs[0].id),
                    'target': str(objs[2].id),
                    'label': str(objs[1].label)
                })

    # Format nodes with fraud scores
    nodes = []
    for v in vertices:
        vid = str(v[T.id])
        node = {'id': vid, 'label': get_node_label(v[T.label])}
        for key, value in v.items():
            if key not in [T.id, T.label]:
                node[str(key)] = value[0] if isinstance(value, list) and len(value) == 1 else value
        # Get fraud score via Neptune ML inference, fall back to stored score
        node['fraudScore'] = _get_fraud_score(g, vid)
        nodes.append(node)

    return {'nodes': nodes, 'edges': edges_data}

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    global _ml_available
    _ml_available = None  # Reset ML cache per invocation
    allowed_origin = os.environ.get('ALLOWED_ORIGIN', '*')
    cors_headers = {
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Request-Timestamp,X-Request-Signature',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    }
    try:
        response = app.resolve(event, context)
        if 'headers' not in response:
            response['headers'] = {}
        response['headers'].update(cors_headers)
        return response
    except Exception as e:
        logger.exception("Unhandled exception in lambda_handler")
        return {
            'statusCode': 502,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }