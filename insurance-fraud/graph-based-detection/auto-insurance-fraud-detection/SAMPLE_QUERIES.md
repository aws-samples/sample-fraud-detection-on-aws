# Sample Neptune Queries for Auto Insurance Fraud Detection

This document provides Python queries to interact with the Neptune graph database for fraud detection analysis. These queries correspond to the API endpoints in the fraud detection Lambda function.

## Setup

```python
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from gremlin_python.process.traversal import P, Order, T
from gremlin_python.process.graph_traversal import __
import pandas as pd

# Connect to Neptune
neptune_endpoint = "auto-insurance-fraud-cluster.cluster-cvsvm4o9ealh.us-east-1.neptune.amazonaws.com"
remoteConn = DriverRemoteConnection(
    f"wss://{neptune_endpoint}:8182/gremlin",
    'g',
    transport_factory=lambda: AiohttpTransport()
)
g = traversal().withRemote(remoteConn)
```

## 1. Claims Management

### List All Claims

```python
# Get all claims with basic information
claims = g.V().hasLabel('claim') \
    .project('claimId', 'amount', 'status', 'fraudScore') \
    .by(__.id_()) \
    .by(__.values('amount')) \
    .by(__.values('status')) \
    .by(__.values('fraudScore')) \
    .limit(20).toList()

df = pd.DataFrame(claims)
print(df)
```

### Get Specific Claim Details

```python
# Get details for a specific claim
claim_id = "claim-12345"  # Replace with actual claim ID

claim_details = g.V(claim_id) \
    .elementMap().next()

print(claim_details)
```

### Get Claimant's Claims History

```python
# Get all claims for a specific claimant
claimant_id = "claimant-001"  # Replace with actual claimant ID

claimant_claims = g.V(claimant_id) \
    .out('filed_claim') \
    .project('claimId', 'amount', 'status', 'fraudScore') \
    .by(__.id_()) \
    .by(__.values('amount')) \
    .by(__.values('status')) \
    .by(__.values('fraudScore')) \
    .toList()

df = pd.DataFrame(claimant_claims)
print(f"Total claims: {len(claimant_claims)}")
print(df)
```

## 2. Claimant Risk Analysis

### High Risk Claimants

```python
# Find claimants with high fraud risk (fraud score > 0.7)
high_risk_claimants = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').has('fraudScore', P.gt(0.7))) \
    .project('claimantId', 'name', 'totalClaims', 'avgFraudScore', 'highRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.out('filed_claim').count()) \
    .by(__.out('filed_claim').values('fraudScore').mean()) \
    .by(__.out('filed_claim').has('fraudScore', P.gt(0.7)).count()) \
    .order().by(__.select('avgFraudScore'), Order.desc) \
    .limit(10).toList()

df = pd.DataFrame(high_risk_claimants)
print("HIGH RISK CLAIMANTS:")
print(df)
```

### Low Risk Claimants

```python
# Find claimants with low fraud risk (fraud score < 0.3)
low_risk_claimants = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').has('fraudScore', P.lt(0.3))) \
    .project('claimantId', 'name', 'totalClaims', 'avgFraudScore', 'lowRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.out('filed_claim').count()) \
    .by(__.out('filed_claim').values('fraudScore').mean()) \
    .by(__.out('filed_claim').has('fraudScore', P.lt(0.3)).count()) \
    .order().by(__.select('avgFraudScore'), Order.asc) \
    .limit(10).toList()

df = pd.DataFrame(low_risk_claimants)
print("LOW RISK CLAIMANTS:")
print(df)
```

### Claimant Risk Score Calculation

```python
# Calculate comprehensive risk score for a claimant
claimant_id = "claimant-001"  # Replace with actual claimant ID

claims = g.V(claimant_id).out('filed_claim') \
    .valueMap('fraudScore', 'status', 'amount').toList()

if claims:
    fraud_scores = [c.get('fraudScore', [0.5])[0] for c in claims if c.get('fraudScore')]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.5
    
    rejected_claims = sum(1 for c in claims if c.get('status', [''])[0] == 'rejected')
    rejection_rate = rejected_claims / len(claims)
    
    total_amount = sum(c.get('amount', [0])[0] for c in claims)
    
    risk_score = (avg_fraud_score * 0.6) + (rejection_rate * 0.4)
    
    print(f"Claimant ID: {claimant_id}")
    print(f"Risk Score: {risk_score:.3f}")
    print(f"Total Claims: {len(claims)}")
    print(f"Rejected Claims: {rejected_claims}")
    print(f"Rejection Rate: {rejection_rate:.3f}")
    print(f"Average Fraud Score: {avg_fraud_score:.3f}")
    print(f"Total Claim Amount: ${total_amount:.2f}")
```

## 3. Claim Velocity Analysis

### High Velocity Claimants

```python
# Find claimants with high claim velocity (5+ claims)
high_velocity_claimants = g.V().hasLabel('claimant') \
    .filter_(__.out('filed_claim').count().is_(P.gte(5))) \
    .project('claimantId', 'name', 'totalClaims', 'avgFraudScore') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.out('filed_claim').count()) \
    .by(__.out('filed_claim').values('fraudScore').mean()) \
    .order().by(__.select('totalClaims'), Order.desc) \
    .limit(10).toList()

df = pd.DataFrame(high_velocity_claimants)
print("HIGH VELOCITY CLAIMANTS (5+ claims):")
print(df)
```

### Low Velocity Claimants

```python
# Find claimants with low claim velocity (1-2 claims)
low_velocity_claimants = g.V().hasLabel('claimant') \
    .filter_(__.out('filed_claim').count().is_(P.lte(2))) \
    .project('claimantId', 'name', 'totalClaims', 'avgFraudScore') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.out('filed_claim').count()) \
    .by(__.out('filed_claim').values('fraudScore').mean()) \
    .order().by(__.select('totalClaims'), Order.asc) \
    .limit(10).toList()

df = pd.DataFrame(low_velocity_claimants)
print("LOW VELOCITY CLAIMANTS (1-2 claims):")
print(df)
```

### Detailed Claim Velocity Analysis

```python
# Analyze claim filing frequency for a specific claimant
claimant_id = "claimant-001"  # Replace with actual claimant ID

claims = g.V(claimant_id).out('filed_claim') \
    .valueMap('timestamp', 'amount', 'fraudScore').toList()

if len(claims) >= 2:
    claims_sorted = sorted(claims, key=lambda x: x.get('timestamp', [0])[0])
    timestamps = [c.get('timestamp', [0])[0] for c in claims_sorted]
    
    # Calculate time intervals between claims (in days)
    intervals = []
    for i in range(1, len(timestamps)):
        interval_days = (timestamps[i] - timestamps[i-1]) / 86400
        intervals.append(interval_days)
    
    avg_interval = sum(intervals) / len(intervals) if intervals else 0
    min_interval = min(intervals) if intervals else 0
    
    # Velocity score: claims per year
    time_span_years = (timestamps[-1] - timestamps[0]) / (86400 * 365)
    claims_per_year = len(claims) / time_span_years if time_span_years > 0 else len(claims)
    
    print(f"Claimant ID: {claimant_id}")
    print(f"Total Claims: {len(claims)}")
    print(f"Claims Per Year: {claims_per_year:.2f}")
    print(f"Average Interval (days): {avg_interval:.1f}")
    print(f"Shortest Interval (days): {min_interval:.1f}")
    print(f"Velocity Risk: {'HIGH' if claims_per_year > 5 or min_interval < 30 else 'MEDIUM' if claims_per_year > 3 else 'LOW'}")
```

## 4. Repair Shop Analysis

### High Fraud Repair Shops

```python
# Find repair shops with high fraud involvement
high_fraud_shops = g.V().hasLabel('repairShop') \
    .project('shopId', 'name', 'totalClaims', 'avgFraudScore', 'highRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('repaired_at').count()) \
    .by(__.in_('repaired_at').values('fraudScore').mean()) \
    .by(__.in_('repaired_at').has('fraudScore', P.gt(0.7)).count()) \
    .where(__.select('avgFraudScore').is_(P.gt(0.6))) \
    .order().by(__.select('avgFraudScore'), Order.desc) \
    .limit(10).toList()

df = pd.DataFrame(high_fraud_shops)
print("HIGH FRAUD REPAIR SHOPS:")
print(df)
```

### Low Fraud Repair Shops

```python
# Find repair shops with low fraud involvement
low_fraud_shops = g.V().hasLabel('repairShop') \
    .project('shopId', 'name', 'totalClaims', 'avgFraudScore', 'lowRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('repaired_at').count()) \
    .by(__.in_('repaired_at').values('fraudScore').mean()) \
    .by(__.in_('repaired_at').has('fraudScore', P.lt(0.3)).count()) \
    .where(__.select('avgFraudScore').is_(P.lt(0.4))) \
    .order().by(__.select('avgFraudScore'), Order.asc) \
    .limit(10).toList()

df = pd.DataFrame(low_fraud_shops)
print("LOW FRAUD REPAIR SHOPS:")
print(df)
```

### Repair Shop Statistics

```python
# Get detailed statistics for a specific repair shop
shop_id = "shop-001"  # Replace with actual shop ID

shop = g.V(shop_id).valueMap(True).next()
claims = g.V(shop_id).in_('repaired_at') \
    .valueMap('fraudScore', 'status', 'amount').toList()

if claims:
    fraud_scores = [c.get('fraudScore', [0.5])[0] for c in claims if c.get('fraudScore')]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.5
    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)
    
    print(f"Repair Shop ID: {shop_id}")
    print(f"Name: {shop.get('name', ['Unknown'])[0]}")
    print(f"Total Claims: {len(claims)}")
    print(f"Average Fraud Score: {avg_fraud_score:.3f}")
    print(f"High Fraud Claims: {high_fraud_claims}")
    print(f"High Fraud Rate: {(high_fraud_claims / len(claims)):.3f}")
```

## 5. Vehicle Analysis

### High Risk Vehicles

```python
# Find vehicles with high fraud risk
high_risk_vehicles = g.V().hasLabel('vehicle') \
    .project('vehicleId', 'make', 'model', 'year', 'totalClaims', 'avgFraudScore') \
    .by(__.id_()) \
    .by(__.values('make')) \
    .by(__.values('model')) \
    .by(__.values('year')) \
    .by(__.in_('for_vehicle').count()) \
    .by(__.in_('for_vehicle').values('fraudScore').mean()) \
    .where(__.select('avgFraudScore').is_(P.gt(0.6))) \
    .order().by(__.select('avgFraudScore'), Order.desc) \
    .limit(10).toList()

df = pd.DataFrame(high_risk_vehicles)
print("HIGH RISK VEHICLES:")
print(df)
```

### Low Risk Vehicles

```python
# Find vehicles with low fraud risk
low_risk_vehicles = g.V().hasLabel('vehicle') \
    .project('vehicleId', 'make', 'model', 'year', 'totalClaims', 'avgFraudScore') \
    .by(__.id_()) \
    .by(__.values('make')) \
    .by(__.values('model')) \
    .by(__.values('year')) \
    .by(__.in_('for_vehicle').count()) \
    .by(__.in_('for_vehicle').values('fraudScore').mean()) \
    .where(__.select('avgFraudScore').is_(P.lt(0.4))) \
    .order().by(__.select('avgFraudScore'), Order.asc) \
    .limit(10).toList()

df = pd.DataFrame(low_risk_vehicles)
print("LOW RISK VEHICLES:")
print(df)
```

### Vehicle Fraud History

```python
# Analyze vehicle's claim history and fraud risk
vehicle_id = "vehicle-001"  # Replace with actual vehicle ID

vehicle = g.V(vehicle_id).valueMap(True).next()
claims = g.V(vehicle_id).in_('for_vehicle') \
    .valueMap('fraudScore', 'status', 'amount', 'timestamp').toList()

if claims:
    fraud_scores = [c.get('fraudScore', [0.5])[0] for c in claims if c.get('fraudScore')]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.5
    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)
    
    owners = g.V(vehicle_id).in_('owns').dedup().count().next()
    repair_shops = g.V(vehicle_id).in_('for_vehicle').out('repaired_at').dedup().count().next()
    
    print(f"Vehicle ID: {vehicle_id}")
    print(f"Make: {vehicle.get('make', ['Unknown'])[0]}")
    print(f"Model: {vehicle.get('model', ['Unknown'])[0]}")
    print(f"Year: {vehicle.get('year', [0])[0]}")
    print(f"Total Claims: {len(claims)}")
    print(f"High Fraud Claims: {high_fraud_claims}")
    print(f"Average Fraud Score: {avg_fraud_score:.3f}")
    print(f"Different Owners: {owners}")
    print(f"Different Repair Shops: {repair_shops}")
    print(f"Risk Level: {'HIGH' if avg_fraud_score > 0.7 else 'MEDIUM' if avg_fraud_score > 0.5 else 'LOW'}")
```

## 6. Medical Provider Analysis

### High Risk Medical Providers

```python
# Find medical providers with high fraud risk
high_risk_providers = g.V().hasLabel('medicalProvider') \
    .project('providerId', 'name', 'totalClaims', 'avgFraudScore', 'highRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('treated_by').count()) \
    .by(__.in_('treated_by').values('fraudScore').mean()) \
    .by(__.in_('treated_by').has('fraudScore', P.gt(0.7)).count()) \
    .where(__.select('avgFraudScore').is_(P.gt(0.6))) \
    .order().by(__.select('avgFraudScore'), Order.desc) \
    .limit(10).toList()

df = pd.DataFrame(high_risk_providers)
print("HIGH RISK MEDICAL PROVIDERS:")
print(df)
```

### Low Risk Medical Providers

```python
# Find medical providers with low fraud risk
low_risk_providers = g.V().hasLabel('medicalProvider') \
    .project('providerId', 'name', 'totalClaims', 'avgFraudScore', 'lowRiskClaims') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('treated_by').count()) \
    .by(__.in_('treated_by').values('fraudScore').mean()) \
    .by(__.in_('treated_by').has('fraudScore', P.lt(0.3)).count()) \
    .where(__.select('avgFraudScore').is_(P.lt(0.4))) \
    .order().by(__.select('avgFraudScore'), Order.asc) \
    .limit(10).toList()

df = pd.DataFrame(low_risk_providers)
print("LOW RISK MEDICAL PROVIDERS:")
print(df)
```

### Medical Provider Fraud Analysis

```python
# Analyze medical provider fraud patterns
provider_id = "provider-001"  # Replace with actual provider ID

provider = g.V(provider_id).valueMap(True).next()
claims = g.V(provider_id).in_('treated_by') \
    .valueMap('fraudScore', 'status', 'amount').toList()

if claims:
    fraud_scores = [c.get('fraudScore', [0.5])[0] for c in claims if c.get('fraudScore')]
    avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.5
    high_fraud_claims = sum(1 for score in fraud_scores if score > 0.7)
    
    unique_claimants = g.V(provider_id).in_('treated_by').in_('filed_claim').dedup().count().next()
    network_connections = g.V(provider_id).in_('treated_by').in_('filed_claim') \
        .out('filed_claim').out('repaired_at').dedup().count().next()
    
    print(f"Provider ID: {provider_id}")
    print(f"Name: {provider.get('name', ['Unknown'])[0]}")
    print(f"Total Claims: {len(claims)}")
    print(f"Unique Claimants: {unique_claimants}")
    print(f"High Fraud Claims: {high_fraud_claims}")
    print(f"Average Fraud Score: {avg_fraud_score:.3f}")
    print(f"Network Connections: {network_connections}")
    print(f"Risk Level: {'HIGH' if avg_fraud_score > 0.7 else 'MEDIUM' if avg_fraud_score > 0.5 else 'LOW'}")
```

## 7. Fraud Pattern Detection

### Collision Rings (Enhanced - 6 Pattern Types)

```python
# Detect comprehensive collision ring patterns

# Pattern 1: Staged Accidents (shared vehicles/shops/witnesses)
staged_accidents = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').count().is_(P.gt(3))) \
    .project('claimantId', 'sharedVehicles', 'sharedShops', 'sharedWitnesses') \
    .by(T.id) \
    .by(__.out('owns').in_('owns').dedup().count()) \
    .by(__.out('filed_claim').out('repaired_at').in_('repaired_at').in_('filed_claim').dedup().count()) \
    .by(__.out('filed_claim').out('for_accident').out('witnessed_by').in_('witnessed_by').in_('for_accident').in_('filed_claim').dedup().count()) \
    .toList()

staged = [r for r in staged_accidents if r['sharedVehicles'] >= 2 or r['sharedShops'] >= 5 or r['sharedWitnesses'] >= 3]
print(f"Staged Accidents: {len(staged)}")

# Pattern 2: Swoop & Squat (rear-end collision maneuvers)
swoop_squat = g.V().hasLabel('accident') \
    .has('maneuverType', P.within('swoop-squat', 'sudden-stop')) \
    .project('accidentId', 'maneuverType', 'claimCount', 'policeVerified') \
    .by(T.id) \
    .by('maneuverType') \
    .by(__.in_('for_accident').count()) \
    .by('policeVerified') \
    .toList()

swoop = [r for r in swoop_squat if r['claimCount'] >= 2]
print(f"Swoop & Squat: {len(swoop)}")

# Pattern 3: Stuffed Passengers (jump-ins)
stuffed_passengers = g.V().hasLabel('passenger') \
    .where(__.out('passenger_in').count().is_(P.gt(2))) \
    .project('passengerId', 'accidentCount', 'fraudScore') \
    .by(T.id) \
    .by(__.out('passenger_in').count()) \
    .by('fraudScore') \
    .toList()

print(f"Stuffed Passengers: {len(stuffed_passengers)}")

# Pattern 4: Paper Collisions (unverified police reports)
paper_collisions = g.V().hasLabel('accident') \
    .has('policeVerified', False) \
    .where(__.in_('for_accident').has('fraudScore', P.gt(0.7)).count().is_(P.gt(0))) \
    .project('accidentId', 'location', 'claimCount') \
    .by(T.id) \
    .by('location') \
    .by(__.in_('for_accident').count()) \
    .toList()

print(f"Paper Collisions: {len(paper_collisions)}")

# Pattern 5: Corrupt Attorneys
corrupt_attorneys = g.V().hasLabel('attorney') \
    .where(__.in_('represented_by').count().is_(P.gt(5))) \
    .project('attorneyId', 'name', 'clientCount', 'fraudScore') \
    .by(T.id) \
    .by('name') \
    .by(__.in_('represented_by').count()) \
    .by('fraudScore') \
    .toList()

corrupt_atty = [r for r in corrupt_attorneys if r['fraudScore'] > 0.6]
print(f"Corrupt Attorneys: {len(corrupt_atty)}")

# Pattern 6: Corrupt Tow Companies
corrupt_tow = g.V().hasLabel('towCompany') \
    .where(__.in_('towed_by').count().is_(P.gt(5))) \
    .project('towCompanyId', 'name', 'towCount', 'fraudScore') \
    .by(T.id) \
    .by('name') \
    .by(__.in_('towed_by').count()) \
    .by('fraudScore') \
    .toList()

corrupt_tow_co = [r for r in corrupt_tow if r['fraudScore'] > 0.6]
print(f"Corrupt Tow Companies: {len(corrupt_tow_co)}")

# Summary
print(f"\nTotal Collision Ring Patterns Detected:")
print(f"  Staged Accidents: {len(staged)}")
print(f"  Swoop & Squat: {len(swoop)}")
print(f"  Stuffed Passengers: {len(stuffed_passengers)}")
print(f"  Paper Collisions: {len(paper_collisions)}")
print(f"  Corrupt Attorneys: {len(corrupt_atty)}")
print(f"  Corrupt Tow Companies: {len(corrupt_tow_co)}")
```

### Professional Witnesses

```python
# Detect professional witnesses (fake witnesses for hire)
witnesses = g.V().hasLabel('witness') \
    .project('witnessId', 'name', 'claimCount', 'professional') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('witnessed_by').count()) \
    .by(__.values('professional')) \
    .order().by(__.select('claimCount'), Order.desc) \
    .limit(20).toList()

professional_witnesses = [
    {
        'witnessId': str(w['witnessId']),
        'name': w['name'],
        'claimCount': w['claimCount'],
        'isProfessional': w.get('professional', False),
        'suspicionLevel': 'high' if w['claimCount'] > 10 else 'medium' if w['claimCount'] > 5 else 'low'
    }
    for w in witnesses if w['claimCount'] > 3
]

df = pd.DataFrame(professional_witnesses)
print(f"Total Suspicious Witnesses: {len(professional_witnesses)}")
print(df)
```

### Influential Claimants (Fraud Ring Organizers)

```python
# Identify most connected claimants who may be organizing fraud rings
claimants = g.V().hasLabel('claimant') \
    .project('claimantId', 'name', 'claimCount', 'connectionScore') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.out('filed_claim').count()) \
    .by(
        __.union(
            __.out('owns'),
            __.out('filed_claim').out('repaired_at'),
            __.out('filed_claim').out('witnessed_by')
        ).dedup().count()
    ) \
    .order().by(__.select('connectionScore'), Order.desc) \
    .limit(20).toList()

influential = [
    {
        'claimantId': str(c['claimantId']),
        'name': c['name'],
        'claimCount': c['claimCount'],
        'connectionScore': c['connectionScore'],
        'influenceLevel': 'high' if c['connectionScore'] > 10 else 'medium' if c['connectionScore'] > 5 else 'low'
    }
    for c in claimants
]

df = pd.DataFrame(influential)
print("TOP INFLUENTIAL CLAIMANTS:")
print(df)
```

### Organized Fraud Rings

```python
# Detect organized fraud rings - groups of claimants working together
seed_claimants = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').count().is_(P.gt(2))) \
    .limit(50).toList()

communities = []
for seed in seed_claimants:
    seed_id = str(seed.id)
    
    # Find 2-hop neighborhood
    community_members = g.V(seed_id).union(
        __.out('owns').in_('owns'),
        __.out('filed_claim').out('repaired_at').in_('repaired_at').in_('filed_claim'),
        __.out('filed_claim').out('witnessed_by').in_('witnessed_by').in_('filed_claim')
    ).dedup().where(__.is_(P.neq(seed))).limit(10).toList()
    
    if len(community_members) >= 3:
        member_ids = [seed_id] + [str(m.id) for m in community_members]
        fraud_scores = g.V(*member_ids).out('filed_claim').values('fraudScore').toList()
        avg_fraud = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0
        
        communities.append({
            'seedClaimant': seed_id,
            'communitySize': len(community_members) + 1,
            'members': member_ids[:5],
            'averageFraudScore': round(avg_fraud, 3),
            'riskLevel': 'high' if avg_fraud > 0.7 else 'medium' if avg_fraud > 0.5 else 'low'
        })

communities.sort(key=lambda x: (x['communitySize'], x['averageFraudScore']), reverse=True)

df = pd.DataFrame(communities[:10])
print(f"Total Communities: {len(communities)}")
print("SUSPICIOUS COMMUNITIES:")
print(df)
```

### Fraud Hub Repair Shops

```python
# Identify repair shops that connect multiple fraud networks
shops = g.V().hasLabel('repairShop') \
    .project('shopId', 'name', 'claimantCount', 'claimCount', 'centralityScore') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('repaired_at').in_('filed_claim').dedup().count()) \
    .by(__.in_('repaired_at').count()) \
    .by(
        __.in_('repaired_at').project('claimant', 'vehicle') \
            .by(__.in_('filed_claim')) \
            .by(__.out('for_vehicle')) \
            .dedup().count()
    ) \
    .order().by(__.select('centralityScore'), Order.desc) \
    .limit(20).toList()

fraud_hubs = [
    {
        'repairShopId': str(s['shopId']),
        'name': s['name'],
        'uniqueClaimants': s['claimantCount'],
        'totalClaims': s['claimCount'],
        'centralityScore': s['centralityScore'],
        'bridgingRole': 'critical' if s['centralityScore'] > 50 else 'significant' if s['centralityScore'] > 20 else 'normal'
    }
    for s in shops
]

df = pd.DataFrame(fraud_hubs)
print("FRAUD HUB REPAIR SHOPS:")
print(df)
```

### Collusion Indicators (Triangle Detection)

```python
# Detect collusion indicators using triangle counting
claimants = g.V().hasLabel('claimant').limit(30).toList()

triangles = []
for claimant in claimants:
    c_id = str(claimant.id)
    
    # Find triangles through shared resources
    triangle_count = g.V(c_id).as_('c1') \
        .out('owns').as_('v') \
        .in_('owns').where(P.neq('c1')).as_('c2') \
        .out('filed_claim').out('repaired_at').as_('shop') \
        .in_('repaired_at').in_('filed_claim').where(P.eq('c1')) \
        .count().next()
    
    if triangle_count > 0:
        triangles.append({
            'claimantId': c_id,
            'triangleCount': triangle_count,
            'collusionRisk': 'high' if triangle_count > 5 else 'medium' if triangle_count > 2 else 'low'
        })

triangles.sort(key=lambda x: x['triangleCount'], reverse=True)

df = pd.DataFrame(triangles[:10])
print(f"Total Triangles Detected: {sum(t['triangleCount'] for t in triangles)}")
print("TOP COLLUSION RISKS:")
print(df)
```

### Isolated Fraud Rings

```python
# Find isolated fraud rings - independent groups operating separately
components = []
visited = set()

claimants = g.V().hasLabel('claimant').limit(50).toList()

for claimant in claimants:
    c_id = str(claimant.id)
    if c_id in visited:
        continue
    
    # BFS to find all connected claimants
    component = g.V(c_id).repeat(
        __.union(
            __.out('owns').in_('owns'),
            __.out('filed_claim').out('repaired_at').in_('repaired_at').in_('filed_claim'),
            __.out('filed_claim').out('witnessed_by').in_('witnessed_by').in_('filed_claim')
        ).dedup()
    ).times(3).dedup().toList()
    
    component_ids = [str(v.id) for v in component]
    visited.update(component_ids)
    
    if len(component) > 3:
        fraud_scores = g.V(*component_ids).out('filed_claim').values('fraudScore').toList()
        avg_fraud = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0
        
        components.append({
            'componentId': len(components) + 1,
            'size': len(component),
            'members': component_ids[:5],
            'averageFraudScore': round(avg_fraud, 3),
            'isolationLevel': 'isolated' if len(component) < 10 else 'connected',
            'riskLevel': 'high' if avg_fraud > 0.7 and len(component) > 5 else 'medium' if avg_fraud > 0.5 else 'low'
        })

components.sort(key=lambda x: (x['size'], x['averageFraudScore']), reverse=True)

df = pd.DataFrame(components[:10])
print(f"Total Components: {len(components)}")
print("SUSPICIOUS COMPONENTS:")
print(df)
```

### Cross-Claim Patterns

```python
# Detect claimants who always use same entities (habitual pattern fraud)
claimants = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').count().is_(P.gt(2))) \
    .limit(50).toList()

patterns = []
for claimant in claimants:
    c_id = str(claimant.id)
    
    claim_count = g.V(c_id).out('filed_claim').count().next()
    repair_shops = g.V(c_id).out('filed_claim').out('repaired_at').dedup().toList()
    witnesses = g.V(c_id).out('filed_claim').out('witnessed_by').dedup().toList()
    providers = g.V(c_id).out('filed_claim').out('treated_by').dedup().toList()
    
    shop_diversity = len(repair_shops) / claim_count if claim_count > 0 else 0
    witness_diversity = len(witnesses) / claim_count if claim_count > 0 else 0
    provider_diversity = len(providers) / claim_count if claim_count > 0 else 0
    
    if claim_count >= 3 and (shop_diversity < 0.5 or witness_diversity < 0.5):
        patterns.append({
            'claimantId': c_id,
            'totalClaims': claim_count,
            'uniqueRepairShops': len(repair_shops),
            'uniqueWitnesses': len(witnesses),
            'uniqueProviders': len(providers),
            'shopDiversity': round(shop_diversity, 3),
            'witnessDiversity': round(witness_diversity, 3),
            'suspicionLevel': 'high' if shop_diversity < 0.3 else 'medium',
            'sameShopAlways': len(repair_shops) == 1 and claim_count > 2,
            'sameWitnessAlways': len(witnesses) == 1 and claim_count > 2
        })

patterns.sort(key=lambda x: x['shopDiversity'])

df = pd.DataFrame(patterns[:20])
print(f"Total Suspicious Patterns: {len(patterns)}")
print("HIGH RISK PATTERNS:")
print(df)
```

## 8. Analytics and Trends

### Fraud Trends Overview

```python
# Get fraud analytics and trends
total_claims = g.V().hasLabel('claim').count().next()
high_fraud_claims = g.V().hasLabel('claim').has('fraudScore', P.gt(0.7)).count().next()
rejected_claims = g.V().hasLabel('claim').has('status', 'rejected').count().next()
approved_claims = g.V().hasLabel('claim').has('status', 'approved').count().next()

fraud_scores = g.V().hasLabel('claim').values('fraudScore').toList()
avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0

suspicious_shops = g.V().hasLabel('repairShop').has('suspicious', True).count().next()

print("FRAUD TRENDS:")
print(f"Total Claims: {total_claims}")
print(f"Approved Claims: {approved_claims}")
print(f"Rejected Claims: {rejected_claims}")
print(f"High Fraud Claims: {high_fraud_claims}")
print(f"Fraud Rate: {(high_fraud_claims / total_claims):.3f}" if total_claims > 0 else "N/A")
print(f"Average Fraud Score: {avg_fraud_score:.3f}")
print(f"Suspicious Repair Shops: {suspicious_shops}")
```

### Geographic Fraud Hotspots

```python
# Detect geographic fraud hotspots using clustering
hotspots = g.V().hasLabel('repairShop') \
    .project('shopId', 'name', 'claimCount', 'avgFraudScore', 'clusterSize') \
    .by(__.id_()) \
    .by(__.values('name')) \
    .by(__.in_('repaired_at').count()) \
    .by(__.in_('repaired_at').values('fraudScore').mean()) \
    .by(
        __.in_('repaired_at').in_('filed_claim') \
            .out('filed_claim').out('repaired_at').dedup().count()
    ) \
    .order().by(__.select('avgFraudScore'), Order.desc) \
    .limit(20).toList()

geographic_clusters = [
    {
        'repairShopId': str(h['shopId']),
        'name': h['name'],
        'claimVolume': h['claimCount'],
        'averageFraudScore': round(h['avgFraudScore'], 3),
        'clusterSize': h['clusterSize'],
        'hotspotLevel': 'critical' if h['avgFraudScore'] > 0.7 and h['claimCount'] > 20 
                       else 'high' if h['avgFraudScore'] > 0.6 else 'medium'
    }
    for h in hotspots if h['avgFraudScore'] > 0.5
]

df = pd.DataFrame(geographic_clusters[:10])
print(f"Total Hotspots: {len(geographic_clusters)}")
print("GEOGRAPHIC FRAUD HOTSPOTS:")
print(df)
```

### Claim Amount Anomalies

```python
# Detect anomalous claim amounts using statistical analysis
claims = g.V().hasLabel('claim').elementMap('amount', 'fraudScore').toList()

if len(claims) >= 10:
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
        
        fraud_score = claim.get('fraudScore', 0.5)
        if isinstance(fraud_score, list):
            fraud_score = fraud_score[0] if fraud_score else 0.5
        
        claim_id = str(claim[T.id])
        z_score = (amount - mean_amount) / std_dev if std_dev > 0 else 0
        
        if abs(z_score) > 2:
            anomalies.append({
                'claimId': claim_id,
                'amount': round(amount, 2),
                'zScore': round(z_score, 2),
                'fraudScore': round(fraud_score, 3),
                'anomalyType': 'unusually_high' if z_score > 0 else 'unusually_low',
                'riskLevel': 'high' if fraud_score > 0.7 and abs(z_score) > 3 else 'medium'
            })
    
    anomalies.sort(key=lambda x: abs(x['zScore']), reverse=True)
    
    print("STATISTICS:")
    print(f"Mean Amount: ${mean_amount:.2f}")
    print(f"Standard Deviation: ${std_dev:.2f}")
    print(f"Total Claims: {len(claims)}")
    print(f"\nANOMALIES DETECTED: {len(anomalies)}")
    
    df = pd.DataFrame(anomalies[:20])
    print(df)
```

### Temporal Fraud Patterns

```python
# Detect time-based fraud patterns
claims = g.V().hasLabel('claim').valueMap('timestamp', 'fraudScore', 'amount').toList()

if len(claims) >= 10:
    # Group by time of day (hour)
    hourly_fraud = {}
    for claim in claims:
        timestamp = claim.get('timestamp', [0])[0]
        fraud_score = claim.get('fraudScore', [0.5])[0]
        
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
            'averageFraudScore': round(data['total_fraud'] / data['count'], 3),
            'suspicionLevel': 'high' if data['total_fraud'] / data['count'] > 0.7 
                            else 'medium' if data['total_fraud'] / data['count'] > 0.5 else 'low'
        }
        for hour, data in hourly_fraud.items()
    ]
    
    hourly_patterns.sort(key=lambda x: x['averageFraudScore'], reverse=True)
    
    # Find rapid-fire claimants
    rapid_filers = g.V().hasLabel('claimant') \
        .where(__.out('filed_claim').count().is_(P.gt(2))) \
        .project('claimantId', 'claimCount') \
        .by(__.id_()) \
        .by(__.out('filed_claim').count()) \
        .order().by(__.select('claimCount'), Order.desc) \
        .limit(10).toList()
    
    print("HOURLY PATTERNS:")
    df_hourly = pd.DataFrame(hourly_patterns[:10])
    print(df_hourly)
    
    print("\nRAPID FILERS:")
    rapid_filers_formatted = [
        {
            'claimantId': str(r['claimantId']),
            'claimCount': r['claimCount'],
            'suspicionLevel': 'high' if r['claimCount'] > 5 else 'medium'
        }
        for r in rapid_filers
    ]
    df_rapid = pd.DataFrame(rapid_filers_formatted)
    print(df_rapid)
```

## 9. Network Analysis

### Fraudster Connections (Shortest Path)

```python
# Find shortest connection path between high-fraud claimants
high_fraud_claimants = g.V().hasLabel('claimant') \
    .where(__.out('filed_claim').has('fraudScore', P.gt(0.8))) \
    .limit(10).toList()

if len(high_fraud_claimants) >= 2:
    paths = []
    
    for i in range(min(3, len(high_fraud_claimants) - 1)):
        source = high_fraud_claimants[i]
        target = high_fraud_claimants[i + 1]
        
        # Find path through shared entities
        try:
            path = g.V(source.id).repeat(
                __.bothE().otherV().simplePath()
            ).until(
                __.hasId(target.id)
            ).limit(1).path().by(T.id).by('label').toList()
            
            if path:
                paths.append({
                    'source': str(source.id),
                    'target': str(target.id),
                    'pathLength': len(path[0]) // 2 if path else 0,
                    'connectionType': 'direct' if len(path[0]) <= 5 else 'indirect'
                })
        except:
            pass
    
    df = pd.DataFrame(paths)
    print("FRAUD NETWORK CONNECTIONS:")
    print(df)
    print("\nInsight: Short paths between high-fraud claimants indicate organized fraud rings")
```

## 10. Cleanup

```python
# Always close the connection when done
remoteConn.close()
print("Connection closed.")
```

## Usage Tips

1. **Replace IDs**: Replace placeholder IDs (e.g., `claimant-001`, `vehicle-001`) with actual IDs from your Neptune database.

2. **Adjust Thresholds**: Modify fraud score thresholds (e.g., `P.gt(0.7)`, `P.lt(0.3)`) based on your specific use case.

3. **Limit Results**: Use `.limit()` to control the number of results returned and avoid overwhelming your notebook.

4. **Error Handling**: Add try-except blocks for production use:
   ```python
   try:
       result = g.V(entity_id).elementMap().next()
   except StopIteration:
       print(f"Entity {entity_id} not found")
   except Exception as e:
       print(f"Error: {str(e)}")
   ```

5. **Performance**: For large datasets, consider:
   - Using `.has()` filters early in the traversal
   - Limiting intermediate results with `.limit()`
   - Creating indices on frequently queried properties

6. **Visualization**: Use pandas DataFrames for easy visualization:
   ```python
   import matplotlib.pyplot as plt
   
   df = pd.DataFrame(results)
   df.plot(kind='bar', x='name', y='avgFraudScore')
   plt.show()
   ```

## Common Patterns

### Filter by Property
```python
g.V().hasLabel('claim').has('fraudScore', P.gt(0.7))
```

### Count Results
```python
g.V().hasLabel('claimant').count().next()
```

### Traverse Relationships
```python
g.V(claimant_id).out('filed_claim').out('repaired_at')
```

### Aggregate Data
```python
g.V().hasLabel('claim').values('amount').mean().next()
```

### Sort Results
```python
.order().by(__.select('fraudScore'), Order.desc)
```

### Deduplicate
```python
.dedup()
```

## Additional Resources

- [Gremlin Documentation](https://tinkerpop.apache.org/docs/current/reference/)
- [Neptune Gremlin Implementation](https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-gremlin.html)
- [Neptune ML Documentation](https://docs.aws.amazon.com/neptune/latest/userguide/machine-learning.html)
