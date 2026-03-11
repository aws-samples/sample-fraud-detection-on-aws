[![es-sp](https://img.shields.io/badge/lang-es--sp-green.svg)](API_DOCUMENTATION.es-sp.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](API_DOCUMENTATION.pt-br.md)

# Auto Insurance Fraud Detection API Documentation - Amazon Neptune ML

Complete reference for all 22 fraud detection API endpoints.

## Table of Contents

- [Authentication](#authentication)
- [Claims Management (6 endpoints)](#claims-management)
- [Fraud Patterns (4 endpoints)](#fraud-patterns)
- [Fraud Networks (4 endpoints)](#fraud-networks)
- [Analytics (4 endpoints)](#analytics)
- [Entity Analysis (3 endpoints)](#entity-analysis)
- [Error Handling](#error-handling)

## Authentication

All endpoints require JWT authentication via Cognito.

### Get Authentication Token

```bash
# Create user and get token
./scripts/authenticate.sh -u user@company.com

# Use token in requests
export AUTH_TOKEN=$(cat .auth-token)
curl -H "Authorization: Bearer $AUTH_TOKEN" https://API_ENDPOINT/prod/endpoint
```

**Token Validity:**
- ID Token: 1 hour
- Access Token: 1 hour
- Refresh Token: 30 days

---

## Claims Management

### 1. Submit Claim

Submit a new insurance claim with real-time fraud detection.

**Endpoint:** `POST /claims`

**Request Body:**
```json
{
  "claimAmount": 8500.00,
  "claimantId": "claimant-12345",
  "vehicleId": "vehicle-67890",
  "repairShopId": "shop-abc123"
}
```

**Response:**
```json
{
  "claimId": "claim-uuid",
  "fraudScore": 0.85,
  "status": "pending",
  "riskLevel": "high",
  "timestamp": 1704067200
}
```

**Fraud Detection:**
- Uses Neptune ML for real-time prediction
- Analyzes repair shop fraud history
- Checks claimant claim patterns
- Detects amount anomalies

---

### 2. Get Claim Details

Retrieve detailed information about a specific claim.

**Endpoint:** `GET /claims/{claim_id}`

**Response:**
```json
{
  "claimId": "claim-12345",
  "amount": 8500.00,
  "status": "approved",
  "fraudScore": 0.45,
  "timestamp": 1704067200,
  "claimant": {
    "id": "claimant-67890",
    "name": "John Doe"
  },
  "vehicle": {
    "id": "vehicle-abc",
    "vin": "VIN1234567890"
  },
  "repairShop": {
    "id": "shop-xyz",
    "name": "Auto Repair Shop"
  }
}
```

---

### 3. Get Claimant's Claims History

Retrieve all claims filed by a specific claimant.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Response:**
```json
{
  "claimantId": "claimant-12345",
  "totalClaims": 5,
  "claims": [
    {
      "claimId": "claim-001",
      "amount": 5000.00,
      "fraudScore": 0.3,
      "status": "approved",
      "date": "2024-01-15"
    },
    {
      "claimId": "claim-002",
      "amount": 8500.00,
      "fraudScore": 0.85,
      "status": "pending",
      "date": "2024-02-20"
    }
  ]
}
```

---

### 4. Get Claimant Risk Score

Get ML-powered risk assessment for a claimant.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Response:**
```json
{
  "claimantId": "claimant-12345",
  "riskScore": 0.78,
  "riskLevel": "high",
  "factors": {
    "claimFrequency": 0.8,
    "averageFraudScore": 0.65,
    "suspiciousConnections": 3,
    "claimVelocity": 0.9
  },
  "recommendation": "Enhanced review required"
}
```

**Requires:** Neptune ML training completed

---

### 5. Analyze Claim Velocity

Analyze how frequently a claimant files claims.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Response:**
```json
{
  "claimantId": "claimant-12345",
  "totalClaims": 8,
  "claimsPerYear": 4.5,
  "averageIntervalDays": 81.2,
  "shortestIntervalDays": 15,
  "mlVelocityScore": 0.82,
  "velocityRisk": "high",
  "redFlags": {
    "rapidFiling": true,
    "highFrequency": false,
    "suspiciousPattern": true
  }
}
```

**Algorithm:** Time-series pattern detection

---

### 6. Comprehensive Fraud Analysis

Deep dive analysis showing all fraud indicators for a claimant.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Response:**
```json
{
  "claimantId": "claimant-12345",
  "averageFraudScore": 0.72,
  "totalClaims": 6,
  "repairShops": [
    {
      "shopId": "shop-001",
      "name": "Quick Fix Auto",
      "totalClaims": 45,
      "fraudRate": 0.68
    }
  ],
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "Jane Smith",
      "totalAccidentsWitnessed": 12,
      "isProfessional": true
    }
  ],
  "medicalProviders": [
    {
      "providerId": "provider-001",
      "name": "Dr. Johnson",
      "fraudScore": 0.75
    }
  ],
  "connectedFraudsters": [
    {
      "claimantId": "claimant-789",
      "connectionType": "shared_vehicle",
      "fraudScore": 0.88
    }
  ]
}
```

---

## Fraud Patterns

### 7. Detect Collision Rings

Identify 6 types of collision ring fraud patterns.

**Endpoint:** `GET /fraud-patterns/collision-rings`

**Response:**
```json
{
  "totalDetected": 50,
  "highSuspicion": 46,
  "mediumSuspicion": 4,
  "patterns": {
    "stagedAccidents": 18,
    "swoopAndSquat": 2,
    "stuffedPassengers": 5,
    "paperCollisions": 27,
    "corruptAttorneys": 3,
    "corruptTowCompanies": 2
  },
  "detectedRings": [
    {
      "type": "staged_accident",
      "claimantId": "claimant-123",
      "sharedVehicles": 3,
      "sharedShops": 8,
      "sharedWitnesses": 5,
      "suspicionLevel": "high"
    },
    {
      "type": "paper_collision",
      "accidentId": "accident-456",
      "location": "Downtown",
      "claimCount": 4,
      "suspicionLevel": "high"
    }
  ]
}
```

**Fraud Types Detected:**
1. **Staged Accidents** - Shared vehicles/shops/witnesses
2. **Swoop & Squat** - Rear-end collision maneuvers
3. **Stuffed Passengers** - Jump-ins claiming fake injuries
4. **Paper Collisions** - Unverified police reports
5. **Corrupt Attorneys** - Steering clients to fraud rings
6. **Corrupt Tow Companies** - Steering victims to fraud shops

**Algorithm:** Multi-hop graph traversal with pattern matching

---

### 8. Find Professional Witnesses

Identify witnesses appearing in multiple unrelated claims.

**Endpoint:** `GET /fraud-patterns/professional-witnesses`

**Response:**
```json
{
  "totalSuspiciousWitnesses": 8,
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "John Smith",
      "claimCount": 15,
      "isProfessional": true,
      "suspicionLevel": "high"
    },
    {
      "witnessId": "witness-002",
      "name": "Jane Doe",
      "claimCount": 8,
      "isProfessional": true,
      "suspicionLevel": "medium"
    }
  ]
}
```

**Algorithm:** Witness frequency analysis

---

### 9. Detect Collusion Indicators

Find three-way collusion between claimants, vehicles, and repair shops.

**Endpoint:** `GET /fraud-patterns/collusion-indicators`

**Response:**
```json
{
  "algorithm": "Triangle Counting",
  "totalTrianglesDetected": 45,
  "claimantsInTriangles": 12,
  "topCollusionRisks": [
    {
      "claimantId": "claimant-123",
      "triangleCount": 8,
      "collusionRisk": "high"
    }
  ],
  "insight": "Triangles indicate closed loops of collusion between claimants, vehicles, and repair shops"
}
```

**Algorithm:** Triangle counting in graph

---

### 10. Cross-Claim Pattern Analysis

Identify claimants who always use the same entities.

**Endpoint:** `GET /fraud-patterns/cross-claim-patterns`

**Response:**
```json
{
  "algorithm": "Cross-Claim Pattern Analysis + Neptune ML",
  "totalSuspiciousPatterns": 15,
  "highRiskPatterns": [
    {
      "claimantId": "claimant-123",
      "totalClaims": 6,
      "uniqueRepairShops": 1,
      "uniqueWitnesses": 1,
      "shopDiversity": 0.167,
      "witnessDiversity": 0.167,
      "mlPatternScore": 0.89,
      "suspicionLevel": "high",
      "redFlags": {
        "sameShopAlways": true,
        "sameWitnessAlways": true,
        "lowDiversity": true
      }
    }
  ]
}
```

**Algorithm:** Diversity scoring + Neptune ML

---

## Fraud Networks

### 11. Find Influential Claimants

Identify network hubs who may be organizing fraud rings.

**Endpoint:** `GET /fraud-networks/influential-claimants`

**Response:**
```json
{
  "algorithm": "PageRank-style Connection Analysis",
  "topInfluencers": [
    {
      "claimantId": "claimant-123",
      "name": "John Doe",
      "claimCount": 12,
      "connectionScore": 45,
      "influenceLevel": "critical"
    }
  ]
}
```

**Algorithm:** PageRank-style centrality analysis

---

### 12. Detect Organized Fraud Rings

Find densely connected groups working together.

**Endpoint:** `GET /fraud-networks/organized-rings`

**Response:**
```json
{
  "algorithm": "Community Detection (2-hop neighborhood analysis)",
  "totalCommunities": 8,
  "suspiciousCommunities": [
    {
      "seedClaimant": "claimant-123",
      "communitySize": 7,
      "members": ["claimant-123", "claimant-456", "claimant-789"],
      "averageFraudScore": 0.82,
      "riskLevel": "high"
    }
  ]
}
```

**Algorithm:** Community detection via 2-hop traversal

---

### 13. Identify Fraud Hub Shops

Find repair shops connecting multiple fraud networks.

**Endpoint:** `GET /repair-shops/fraud-hubs`

**Response:**
```json
{
  "algorithm": "Betweenness Centrality (connection bridging score)",
  "topCentralRepairShops": [
    {
      "repairShopId": "shop-001",
      "name": "Quick Fix Auto",
      "uniqueClaimants": 45,
      "totalClaims": 120,
      "centralityScore": 78,
      "bridgingRole": "critical"
    }
  ]
}
```

**Algorithm:** Betweenness centrality

---

### 14. Map Fraudster Connections

Find shortest paths between suspected fraudsters.

**Endpoint:** `GET /fraud-networks/connections`

**Response:**
```json
{
  "algorithm": "Shortest Path",
  "fraudNetworkConnections": [
    {
      "source": "claimant-123",
      "target": "claimant-456",
      "pathLength": 3,
      "connectionType": "direct"
    }
  ],
  "insight": "Short paths between high-fraud claimants indicate organized fraud rings"
}
```

**Algorithm:** Shortest path finding

---

### 15. Find Isolated Fraud Rings

Identify independent fraud operations.

**Endpoint:** `GET /fraud-networks/isolated-rings`

**Response:**
```json
{
  "algorithm": "Connected Components",
  "totalComponents": 12,
  "largestComponent": {
    "componentId": 1,
    "size": 15,
    "members": ["claimant-001", "claimant-002"],
    "averageFraudScore": 0.78,
    "isolationLevel": "connected",
    "riskLevel": "high"
  },
  "suspiciousComponents": [
    {
      "componentId": 2,
      "size": 8,
      "averageFraudScore": 0.85,
      "riskLevel": "high"
    }
  ]
}
```

**Algorithm:** Connected components analysis

---

## Analytics

### 16. Get Fraud Trends

High-level fraud statistics and trends.

**Endpoint:** `GET /analytics/fraud-trends`

**Response:**
```json
{
  "totalClaims": 200,
  "approvedClaims": 120,
  "rejectedClaims": 80,
  "highFraudClaims": 85,
  "fraudRate": 0.425,
  "averageFraudScore": 0.512,
  "suspiciousRepairShops": 12
}
```

---

### 17. Detect Geographic Hotspots

Find areas with high fraud concentration.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Response:**
```json
{
  "algorithm": "Geographic Clustering (K-means approximation)",
  "totalHotspots": 8,
  "criticalHotspots": [
    {
      "repairShopId": "shop-001",
      "name": "Downtown Auto",
      "claimVolume": 45,
      "averageFraudScore": 0.82,
      "clusterSize": 12,
      "hotspotLevel": "critical"
    }
  ]
}
```

**Algorithm:** Geographic clustering

---

### 18. Detect Claim Amount Anomalies

Find claims with unusually high or low amounts.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Response:**
```json
{
  "algorithm": "Statistical Anomaly Detection + Neptune ML",
  "statistics": {
    "meanAmount": 5250.50,
    "standardDeviation": 2100.25,
    "totalClaims": 200
  },
  "anomaliesDetected": 15,
  "highRiskAnomalies": [
    {
      "claimId": "claim-123",
      "amount": 15000.00,
      "zScore": 4.65,
      "fraudScore": 0.88,
      "mlAnomalyScore": 0.92,
      "anomalyType": "unusually_high",
      "riskLevel": "high"
    }
  ]
}
```

**Algorithm:** Z-score analysis + Neptune ML

**Requires:** Neptune ML training completed

---

### 19. Analyze Temporal Patterns

Detect time-based fraud patterns.

**Endpoint:** `GET /analytics/temporal-patterns`

**Response:**
```json
{
  "algorithm": "Temporal Pattern Analysis",
  "hourlyPatterns": [
    {
      "hour": 14,
      "claimCount": 25,
      "averageFraudScore": 0.78,
      "suspicionLevel": "high"
    }
  ],
  "suspiciousHours": [14, 15, 22],
  "rapidFilers": [
    {
      "claimantId": "claimant-123",
      "claimCount": 8,
      "suspicionLevel": "high"
    }
  ]
}
```

**Algorithm:** Temporal analysis

---

## Entity Analysis

### 20. Get Repair Shop Statistics

Detailed fraud statistics for a repair shop.

**Endpoint:** `GET /repair-shops/{shop_id}/statistics`

**Response:**
```json
{
  "repairShopId": "shop-001",
  "name": "Quick Fix Auto",
  "totalClaims": 120,
  "highFraudClaims": 85,
  "fraudRate": 0.708,
  "averageClaimAmount": 7500.00,
  "uniqueClaimants": 45,
  "suspiciousIndicators": {
    "highFraudRate": true,
    "highClaimVolume": true,
    "lowClaimantDiversity": false
  }
}
```

---

### 21. Analyze Vehicle Fraud History

Get fraud history and risk assessment for a vehicle.

**Endpoint:** `GET /vehicles/{vehicle_id}/fraud-history`

**Response:**
```json
{
  "vehicleId": "vehicle-123",
  "vin": "VIN1234567890",
  "totalClaims": 8,
  "highFraudClaims": 6,
  "fraudRate": 0.75,
  "mlRiskScore": 0.88,
  "owners": [
    {
      "claimantId": "claimant-001",
      "claimCount": 5,
      "fraudScore": 0.82
    }
  ],
  "riskLevel": "high",
  "recommendation": "Enhanced inspection required"
}
```

**Requires:** Neptune ML training completed

---

### 22. Analyze Medical Provider Fraud

Assess fraud patterns for medical providers.

**Endpoint:** `GET /medical-providers/{provider_id}/fraud-analysis`

**Response:**
```json
{
  "providerId": "provider-001",
  "name": "Dr. Smith Clinic",
  "totalClaims": 65,
  "highFraudClaims": 48,
  "fraudRate": 0.738,
  "averageBillingAmount": 3500.00,
  "mlFraudScore": 0.85,
  "suspiciousPatterns": {
    "inflatedBilling": true,
    "highFraudRate": true,
    "repeatedClaimants": true
  },
  "riskLevel": "high"
}
```

**Requires:** Neptune ML training completed

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing or invalid token)
- `404` - Not Found (entity doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "timestamp": 1704067200
}
```

### Common Errors

**Invalid Token:**
```json
{
  "error": "Unauthorized",
  "code": "INVALID_TOKEN"
}
```

**Entity Not Found:**
```json
{
  "error": "Claimant claimant-12345 not found",
  "code": "NOT_FOUND"
}
```

**Rate Limit Exceeded:**
```json
{
  "error": "Rate limit exceeded. Maximum 2000 requests per 5 minutes.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

---

## Rate Limits

**WAF Protection:**
- 2,000 requests per 5 minutes per IP
- Automatic blocking for suspicious patterns
- OWASP Top 10 protection enabled

---

## Best Practices

1. **Cache tokens** - Reuse tokens for their 1-hour validity period
2. **Handle rate limits** - Implement exponential backoff
3. **Batch requests** - Group related queries when possible
4. **Monitor ML status** - Check if ML training is complete before using ML endpoints
5. **Error handling** - Always check response status codes

---

## Support

For issues or questions:
- Check [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) for query examples
- Review CloudWatch logs: `/aws/apigateway/auto-insurance-fraud-detection-API`
- Check WAF logs: `/aws/wafv2/auto-insurance-fraud-detection-WAF`
