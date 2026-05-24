[![es-sp](https://img.shields.io/badge/lang-es--sp-green.svg)](API_DOCUMENTATION.es-sp.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](API_DOCUMENTATION.pt-br.md)

# Auto Insurance Fraud Detection API Documentation - Amazon Neptune ML

Complete reference for all 44 fraud detection API endpoints.

## Table of Contents

- [General Information](#general-information)
  - [Base URL](#base-url)
  - [Authentication](#authentication)
  - [Response Envelope](#response-envelope)
  - [Graph Response Format](#graph-response-format)
  - [Error Handling](#error-handling)
- [Authentication (3 endpoints)](#authentication-endpoints)
  - [1. Login](#1-login)
  - [2. Logout](#2-logout)
  - [3. Refresh Token](#3-refresh-token)
- [Claims (4 endpoints)](#claims)
  - [4. Submit Claim](#4-submit-claim)
  - [5. List Claims](#5-list-claims)
  - [6. Get Claim Details](#6-get-claim-details)
  - [7. Get Claim Neighborhood Graph](#7-get-claim-neighborhood-graph)
- [Claimants (6 endpoints)](#claimants)
  - [8. List Claimants](#8-list-claimants)
  - [9. Get Claimant Details](#9-get-claimant-details)
  - [10. Get Claimant Claims History](#10-get-claimant-claims-history)
  - [11. Get Claimant Risk Score](#11-get-claimant-risk-score)
  - [12. Analyze Claim Velocity](#12-analyze-claim-velocity)
  - [13. Comprehensive Fraud Analysis](#13-comprehensive-fraud-analysis)
- [Collision Rings (6 endpoints)](#collision-rings)
  - [14. Staged Accidents](#14-staged-accidents)
  - [15. Swoop & Squat](#15-swoop--squat)
  - [16. Stuffed Passengers](#16-stuffed-passengers)
  - [17. Paper Collisions](#17-paper-collisions)
  - [18. Corrupt Attorneys](#18-corrupt-attorneys)
  - [19. Corrupt Tow Companies](#19-corrupt-tow-companies)
- [Network Fraud (8 endpoints)](#network-fraud)
  - [20. Professional Witnesses](#20-professional-witnesses)
  - [21. Organized Rings](#21-organized-rings)
  - [22. Fraud Hubs](#22-fraud-hubs)
  - [23. Collusion Indicators](#23-collusion-indicators)
  - [24. Isolated Rings](#24-isolated-rings)
  - [25. Cross-Claim Patterns](#25-cross-claim-patterns)
  - [26. Medical Provider Neighborhood](#26-medical-provider-neighborhood)
  - [27. Medical Provider Fraud Analysis](#27-medical-provider-fraud-analysis)
- [Advanced Analysis (2 endpoints)](#advanced-analysis)
  - [28. Influential Claimants](#28-influential-claimants)
  - [29. Fraudster Connections](#29-fraudster-connections)
- [Entity Lookup (4 endpoints)](#entity-lookup)
  - [30. Repair Shop Neighborhood](#30-repair-shop-neighborhood)
  - [31. Repair Shop Statistics](#31-repair-shop-statistics)
  - [32. Vehicle Neighborhood](#32-vehicle-neighborhood)
  - [33. Vehicle Fraud History](#33-vehicle-fraud-history)
- [Analytics (4 endpoints)](#analytics)
  - [34. Fraud Trends](#34-fraud-trends)
  - [35. Geographic Hotspots](#35-geographic-hotspots)
  - [36. Claim Amount Anomalies](#36-claim-amount-anomalies)
  - [37. Temporal Patterns](#37-temporal-patterns)
- [Entity Lists (7 endpoints)](#entity-lists)
  - [38. List Attorneys](#38-list-attorneys)
  - [39. List Witnesses](#39-list-witnesses)
  - [40. List Passengers](#40-list-passengers)
  - [41. List Tow Companies](#41-list-tow-companies)
  - [42. List Medical Providers](#42-list-medical-providers)
  - [43. List Repair Shops](#43-list-repair-shops)
  - [44. List Vehicles](#44-list-vehicles)
- [Rate Limits](#rate-limits)
- [Best Practices](#best-practices)
- [Support](#support)

---

## General Information

### Base URL

All endpoints are served from the API Gateway URL emitted at deploy time, in the form:

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

You can retrieve the exact value from the deployment output or from CloudFormation:

```bash
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### Authentication

All endpoints except the three `/auth/*` operations require a valid session. Authentication is performed by sending a JSON Web Token (JWT) issued by the Amazon Cognito User Pool deployed with the solution in an **`httpOnly` session cookie** named `__Host-fraud_detection_token`. The cookie is set by `POST /auth/login` and is marked `HttpOnly; Secure; SameSite=None` so it cannot be accessed from JavaScript running in the browser (XSS hardening).

**Browser clients** do not need to handle the cookie at all — it flows automatically on every subsequent request when `credentials: 'include'` is used.

**Non-browser clients** (curl, Python, etc.) must save the cookie after logging in and send it with every request:

```
Cookie: __Host-fraud_detection_token=eyJraWQiOi...
```

**Log in via the helper script (saves the cookie to `.auth-cookie`):**

```bash
./scripts/authenticate.sh -u user@company.com -p YourPassword123! --token-only
```

**Token lifetimes:**

| Token | Validity |
|-------|----------|
| ID token | 1 hour |
| Access token | 1 hour |
| Refresh token | 30 days |

Tokens near expiry should be refreshed via `POST /auth/refresh` (endpoint 3) rather than re-authenticating.

### Response Envelope

Successful responses are returned as JSON with HTTP status `200`. Error responses follow the same JSON shape but with a `4xx`/`5xx` status and an `error` field:

```json
{
  "error": "Claimant not found"
}
```

### Graph Response Format

Endpoints that return a graph (most fraud-detection endpoints) follow a common `{ nodes, edges }` envelope:

```json
{
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "type": "claimant|claim|accident|vehicle|repairShop|medicalProvider|witness|attorney|towCompany|passenger",
      "name": "string (optional)",
      "fraudScore": 0.73,
      "size": 12
    }
  ],
  "edges": [
    {
      "source": "nodeId",
      "target": "nodeId",
      "type": "filed_claim|for_accident|involved_vehicle|repaired_at|witnessed_by|represented_by|towed_by|passenger_in|claimed_injury|treated_by|owns"
    }
  ]
}
```

Specific endpoints may add extra properties to nodes (e.g. `staged`, `maneuverType`, `appearances`) — see each endpoint's response schema for details.

### Error Handling

| HTTP | Meaning | Typical cause |
|------|---------|---------------|
| `200` | Success | Request processed, body contains the result |
| `400` | Bad request | Malformed JSON body or missing required field on a `POST` |
| `401` | Unauthorized | Missing, malformed, or expired JWT |
| `403` | Forbidden | JWT is valid but WAF blocked the request (rate limit, bot detection) or the path does not exist |
| `404` | Not found | Referenced entity (claimant, claim, vehicle, provider, shop) does not exist |
| `500` | Internal error | Lambda exception (e.g. unexpected Gremlin error). The response body contains `{"error": "...", "message": "..."}` with detail |

All error responses include CORS headers so they are surfaced to browser clients correctly.

---

## Authentication Endpoints

### 1. Login

Exchange credentials for a JWT token.

**Endpoint:** `POST /auth/login`

**Authentication:** None (this is how you obtain a token)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Cognito username (email) |
| `password` | string | Yes | User password |

**Request Example:**

```bash
curl -X POST https://YOUR-API/prod/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@company.com","password":"YourPassword123!"}'
```

**Response Example:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "refreshToken": "eyJjdHkiOiJKV1Qi...",
  "expiresIn": 3600
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | The ID token. Browser clients can ignore this — the server also sets the `__Host-fraud_detection_token` httpOnly cookie automatically. Non-browser clients may use this value to construct a `Cookie: __Host-fraud_detection_token=<token>` header manually |
| `refreshToken` | string | Long-lived token used with `/auth/refresh` |
| `expiresIn` | integer | Seconds until the ID token expires (always 3600) |

**Side Effects:** An `httpOnly` cookie named `__Host-fraud_detection_token` is set on the response for browser clients.

**Errors:**

- `400 Bad Request` — missing username or password
- `401 Unauthorized` — invalid credentials or user not confirmed

---

### 2. Logout

Invalidate the active session and clear the cookie.

**Endpoint:** `POST /auth/logout`

**Authentication:** Bearer JWT

**Request Body:** None

**Request Example:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/auth/logout
```

**Response Example:**

```json
{
  "message": "Logged out successfully"
}
```

**Side Effects:** The `__Host-fraud_detection_token` cookie is cleared.

**Errors:**

- `401 Unauthorized` — missing or invalid JWT

---

### 3. Refresh Token

Exchange a refresh token for a fresh ID token.

**Endpoint:** `POST /auth/refresh`

**Authentication:** None (the refresh token itself is the credential)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refreshToken` | string | Yes | The refresh token previously issued by `/auth/login` |

**Request Example:**

```bash
curl -X POST https://YOUR-API/prod/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refreshToken\":\"$REFRESH_TOKEN\"}"
```

**Response Example:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "expiresIn": 3600
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | New ID token |
| `expiresIn` | integer | Seconds until this new token expires |

**Errors:**

- `400 Bad Request` — missing `refreshToken`
- `401 Unauthorized` — refresh token expired or revoked

---

## Claims

### 4. Submit Claim

Submit a new insurance claim and receive a real-time Neptune ML fraud score.

**Endpoint:** `POST /claims`

**Authentication:** Bearer JWT (plus optional HMAC signature for integration partners — see `X-Request-Timestamp` / `X-Request-Signature` headers)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claimAmount` | number | Yes | Claim amount in USD |
| `claimantId` | string | Yes | Existing Claimant vertex ID |
| `vehicleId` | string | Yes | Existing Vehicle vertex ID |
| `repairShopId` | string | No | Optional RepairShop ID |
| `witnessId` | string | No | Optional Witness ID |
| `status` | string | No | Initial status (default: `approved`) |

**Request Example:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/claims \
  -H "Content-Type: application/json" \
  -d '{"claimAmount":12500,"claimantId":"claimant-abc","vehicleId":"vehicle-xyz"}'
```

**Response Example:**

```json
{
  "claimId": "5f3a...",
  "fraudScore": 0.82,
  "riskLevel": "high",
  "message": "Claim submitted",
  "mlModel": "Neptune ML",
  "recommendation": "Escalate to investigation"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimId` | string | ID of the newly created Claim vertex |
| `fraudScore` | number (0–1) | ML-derived fraud probability (inductive inference via Neptune ML); heuristic fallback if ML is unavailable |
| `riskLevel` | string | `low` (< 0.5), `medium` (0.5–0.7), `high` (> 0.7) |
| `message` | string | Human-readable status |
| `mlModel` | string | Model identifier |
| `recommendation` | string | Suggested next action |

**Errors:**

- `400 Bad Request` — missing `claimAmount`, `claimantId`, or `vehicleId`
- `404 Not Found` — referenced claimant or vehicle does not exist
- `500 Internal Server Error` — Neptune write failure

---

### 5. List Claims

List all claims in the graph.

**Endpoint:** `GET /claims`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claims
```

**Response Example:**

```json
{
  "claims": [
    {"id": "abc-123", "amount": 8500.00, "date": 1713283200},
    {"id": "def-456", "amount": 3200.50, "date": 1713366000}
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claims[].id` | string | Claim vertex ID |
| `claims[].amount` | number | Claim amount in USD |
| `claims[].date` | integer | Unix epoch timestamp |

**Errors:**

- `401 Unauthorized` — missing or invalid JWT

---

### 6. Get Claim Details

Retrieve a single claim.

**Endpoint:** `GET /claims/{claim_id}`

**Authentication:** Bearer JWT

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `claim_id` | string | Claim vertex ID |

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123
```

**Response Example:**

```json
{
  "claimId": "abc-123",
  "amount": 8500.00,
  "status": "approved",
  "claimDate": 1713283200,
  "isFraud": true,
  "fraudScore": 0.85
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimId` | string | Claim vertex ID |
| `amount` | number | Claim amount in USD |
| `status` | string | `approved`, `pending`, `rejected` |
| `claimDate` | integer | Unix epoch |
| `isFraud` | boolean | Ground-truth label (for demo data) |
| `fraudScore` | number (0–1) | Fraud score from ML or stored data |

**Errors:**

- `404 Not Found` — `claim_id` not in graph

---

### 7. Get Claim Neighborhood Graph

Retrieve a claim together with its full neighborhood — accident, vehicles, passengers, repair shop, witnesses, claimant, and any connected medical providers or attorneys.

**Endpoint:** `GET /claims/{claim_id}/graph`

**Authentication:** Bearer JWT

**Path Parameters:** `claim_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123/graph
```

**Response:** Graph envelope (see [Graph Response Format](#graph-response-format)). Typically 8–20 nodes.

**Response Schema:**

Standard graph envelope with node types including `claim`, `accident`, `vehicle`, `repairShop`, `witness`, `claimant`, `passenger`, `medicalProvider`, `attorney`, `towCompany`. Edge types include `filed_claim`, `for_accident`, `involved_vehicle`, `repaired_at`, `witnessed_by`, `passenger_in`, `claimed_injury`, `treated_by`, `represented_by`, `towed_by`.

**Errors:**

- `404 Not Found` — `claim_id` not in graph

---

## Claimants

### 8. List Claimants

List all claimants that have filed at least one claim.

**Endpoint:** `GET /claimants`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claimants
```

**Response Example:**

```json
{
  "claimants": [
    {"id": "clm-abc", "name": "Claimant 12"},
    {"id": "clm-def", "name": "Claimant 37"}
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimants[].id` | string | Claimant vertex ID |
| `claimants[].name` | string | Human-readable name |

**Note:** Claimants with zero `filed_claim` edges are excluded — this is intentional so that downstream dropdowns (Fraud Analysis, Claim Velocity, etc.) never show entities that would return empty results.

---

### 9. Get Claimant Details

Retrieve a single claimant.

**Endpoint:** `GET /claimants/{claimant_id}`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc
```

**Response Example:**

```json
{
  "claimantId": "clm-abc",
  "name": "Claimant 12",
  "fraudScore": 0.42
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimantId` | string | Claimant vertex ID |
| `name` | string | Claimant name |
| `fraudScore` | number | Claimant-level fraud score |

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

### 10. Get Claimant Claims History

List all claims filed by a claimant.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claims
```

**Response Example:**

```json
{
  "claimantId": "clm-abc",
  "claims": [
    {"claimId": "c1", "amount": 8500.00, "status": "approved", "claimDate": 1713283200, "fraudScore": 0.12},
    {"claimId": "c2", "amount": 12500.00, "status": "approved", "claimDate": 1715880000, "fraudScore": 0.88}
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimantId` | string | Claimant vertex ID |
| `claims[]` | array | List of the claimant's claims (same shape as endpoint 6 but abridged) |

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

### 11. Get Claimant Risk Score

Compute a fraud risk score for a claimant based on claims history + ML-derived signals.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/risk-score
```

**Response Example (claimant with history):**

```json
{
  "claimantId": "clm-abc",
  "riskScore": 0.67,
  "totalClaims": 4,
  "rejectedClaims": 1,
  "rejectionRate": 0.25,
  "totalClaimAmount": 42350.00
}
```

**Response Example (no history):**

```json
{
  "claimantId": "clm-abc",
  "riskScore": 0.0,
  "totalClaims": 0,
  "rejectedClaims": 0,
  "rejectionRate": 0.0,
  "totalClaimAmount": 0.0,
  "message": "No claims history"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimantId` | string | Claimant vertex ID |
| `riskScore` | number (0–1) | Claimant fraud score (ML inductive inference, heuristic fallback) |
| `totalClaims` | integer | Number of claims filed |
| `rejectedClaims` | integer | Claims with `status = 'rejected'` |
| `rejectionRate` | number (0–1) | `rejectedClaims / totalClaims` |
| `totalClaimAmount` | number | Sum of all claim amounts |
| `message` | string | Present only when `totalClaims = 0` |

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

### 12. Analyze Claim Velocity

Detect abnormally-frequent claim filing using time-series analysis on claim dates.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claim-velocity
```

**Response Example:**

```json
{
  "claimantId": "clm-abc",
  "totalClaims": 4,
  "claimsPerYear": 4.8,
  "averageIntervalDays": 76.2,
  "shortestIntervalDays": 3.1,
  "velocityRisk": 0.48,
  "riskLevel": "medium"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `claimantId` | string | Claimant vertex ID |
| `totalClaims` | integer | Number of claims filed |
| `claimsPerYear` | number | Annualized claim rate |
| `averageIntervalDays` | number | Mean gap between consecutive claims |
| `shortestIntervalDays` | number | Minimum gap — very short gaps indicate burst filing |
| `velocityRisk` | number (0–1) | ML inductive-inference score (fallback: `min(claimsPerYear/10, 1.0)`) |
| `riskLevel` | string | `low`, `medium`, `high` |

**Special response for claimants with < 2 claims:**

```json
{
  "claimantId": "clm-abc",
  "totalClaims": 1,
  "velocityRisk": "low",
  "message": "Insufficient claim history"
}
```

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

### 13. Comprehensive Fraud Analysis

Returns a full fraud network graph for a claimant: claims, accidents, vehicles, repair shops, witnesses, medical providers, attorneys, tow companies, and passengers. Used by the Fraud Analysis UI to drive investigator workflows.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/fraud-analysis
```

**Response:** Standard graph envelope (see [Graph Response Format](#graph-response-format)). Typically returns the claimant's full 2-hop neighborhood, including any connected fraud-ring entities with elevated fraud scores rendered as red-outlined nodes.

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

## Collision Rings

### 14. Staged Accidents

Detect pairs of claimants whose staged accidents share a Vehicle, Witness, or RepairShop. Each returned Accident has `maneuverType != 'normal'` or `policeVerified = false`, and each ring is returned with the shared pivot entity in the middle.

**Endpoint:** `GET /collision-rings/staged-accidents`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/staged-accidents
```

**Response:** Graph envelope. Accident nodes carry additional properties:

| Property | Type | Description |
|----------|------|-------------|
| `maneuverType` | string | `swoop-squat`, `sudden-stop`, or `normal` |
| `policeVerified` | boolean | Whether the accident has a verified police report |
| `staged` | boolean | Always `true` for accidents returned by this endpoint |

---

### 15. Swoop & Squat

Detect vehicles involved in 2 or more staged rear-end accidents (`maneuverType` in `swoop-squat` or `sudden-stop`). Surfaces "prop" vehicles re-used across deliberate crashes.

**Endpoint:** `GET /collision-rings/swoop-and-squat`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/swoop-and-squat
```

**Response:** Graph envelope centered on multi-accident Vehicle nodes, their Accidents, Claims, and Claimants.

---

### 16. Stuffed Passengers

Surface accidents with fake "jump-in" passengers filing injury claims. Each Passenger is enriched with aggregate metrics to reveal serial jump-ins.

**Endpoint:** `GET /collision-rings/stuffed-passengers`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/stuffed-passengers
```

**Response:** Graph envelope. Passenger nodes carry:

| Property | Type | Description |
|----------|------|-------------|
| `appearances` | integer | Number of distinct accidents the passenger is linked to via `passenger_in` |
| `injuryClaims` | integer | Number of `claimed_injury` edges from this passenger |
| `totalClaimed` | number | Sum of all injury-claim amounts |

Passengers with `appearances ≥ 2` are rendered as larger nodes — the "serial jump-in" signature. Medical provider nodes are attached via `treated_by` so the fake-injury money trail is visible.

---

### 17. Paper Collisions

Detect unverified accidents with thin evidence — `policeVerified = false` AND ≤1 witness AND ≤1 vehicle.

**Endpoint:** `GET /collision-rings/paper-collisions`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/paper-collisions
```

**Response:** Graph envelope. Sparse witness/vehicle chains are explicitly included so the "thin evidence" is visually apparent.

---

### 18. Corrupt Attorneys

Detect attorneys with `fraudScore ≥ 0.7` who represent two or more claimants, together with the claimants they represent and those claimants' claims.

**Endpoint:** `GET /collision-rings/corrupt-attorneys`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-attorneys
```

**Response:** Graph envelope centered on corrupt Attorney nodes with radiating Claimant → Claim edges.

---

### 19. Corrupt Tow Companies

Detect tow companies with `fraudScore ≥ 0.7` that tow vehicles in 2+ accidents. Includes the full chain: Tow → Vehicle → Accident → Claim → RepairShop so the steering pattern is visible.

**Endpoint:** `GET /collision-rings/corrupt-tow-companies`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-tow-companies
```

**Response:** Graph envelope including TowCompany, Vehicle, Accident, Claim, RepairShop, and Claimant nodes.

---

## Network Fraud

### 20. Professional Witnesses

Detect witnesses that appear in 3+ distinct accidents — the "professional witness" pattern.

**Endpoint:** `GET /network-fraud/professional-witnesses`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/professional-witnesses
```

**Response:** Graph envelope. Path per witness: `Witness ← witnessed_by ← Accident ← for_accident ← Claim ← filed_claim ← Claimant`.

---

### 21. Organized Rings

Detect densely-connected communities of claimants. Ring membership is discovered via shared Vehicle (`owns` ↔ `owns`) or shared RepairShop (`filed_claim` → `repaired_at`). The returned sub-graph surfaces all shared entities — medical providers, attorneys, witnesses, tow companies — as corroborating evidence.

**Endpoint:** `GET /network-fraud/organized-rings`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/organized-rings
```

**Response Example:**

```json
{
  "algorithm": "Community Detection (1-hop neighborhood analysis)",
  "totalCommunities": 33,
  "rings": [
    {
      "seedClaimant": "clm-abc",
      "communitySize": 6,
      "averageFraudScore": 0.81,
      "riskLevel": "high",
      "members": ["clm-abc", "clm-def", "..."],
      "graph": {"nodes": [...], "edges": [...]}
    }
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `algorithm` | string | Description of the community-detection algorithm |
| `totalCommunities` | integer | Total rings discovered |
| `rings[]` | array | Up to 9 top rings by size/score |
| `rings[].communitySize` | integer | Number of claimants in the ring |
| `rings[].averageFraudScore` | number | Mean fraudScore across ring members |
| `rings[].riskLevel` | string | `low`, `medium`, `high` |
| `rings[].graph` | object | Per-ring graph envelope |

---

### 22. Fraud Hubs

Rank top repair shops, medical providers, and attorneys by breadth of connected claimants, and compute a "collusion score" — the fraction of those claimants that also share at least one other entity with a sibling in the hub.

**Endpoint:** `GET /network-fraud/fraud-hubs`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/fraud-hubs
```

**Response Example:**

```json
{
  "repairShop": {
    "hubs": [
      {
        "name": "Repair Shop 0",
        "uniqueClaimants": 18,
        "collusionScore": 0.72,
        "graph": {"nodes": [...], "edges": [...]}
      }
    ]
  },
  "medicalProvider": {"hubs": [...]},
  "attorney": {"hubs": [...]}
}
```

**Response Schema:**

Top-level keys: `repairShop`, `medicalProvider`, `attorney`. Each has a `hubs` array (up to 5 per category) with:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Hub entity name |
| `uniqueClaimants` | integer | Distinct claimants connected to this hub |
| `collusionScore` | number (0–1) | Fraction of claimants sharing another entity with a ring sibling |
| `graph` | object | Sub-graph rooted at the hub |

---

### 23. Collusion Indicators

Surface repair shops with 5+ claimants converging through `Claim → repaired_at`. Surfaces collusion-triangle-style patterns.

**Endpoint:** `GET /network-fraud/collusion-indicators`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/collusion-indicators
```

**Response:** Graph envelope with RepairShop hubs, intermediate Claim nodes, and the Claimants behind each claim.

---

### 24. Isolated Rings

Detect independent fraud components — small, self-contained sub-graphs with no bridges to the wider fraud network. Operates in two modes:

**Mode 1 — Summary list (no query params):** Returns a list of all isolated components.

**Endpoint:** `GET /network-fraud/isolated-rings`

**Mode 2 — Per-entity graph (query params):** Returns the specific isolated ring for an entity.

**Endpoint:** `GET /network-fraud/isolated-rings?id={entity_id}&type={entity_type}`

**Authentication:** Bearer JWT

**Query Parameters (Mode 2):**

| Name | Type | Description |
|------|------|-------------|
| `id` | string | Entity ID |
| `type` | string | One of: `claimant`, `claim`, `repair-shop`, `vehicle`, `medical-provider`, `attorney`, `witness`, `passenger`, `tow-company` |

**Request Example (Mode 1):**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/isolated-rings
```

**Response Example (Mode 1):**

```json
{
  "algorithm": "Connected Components",
  "totalComponents": 22,
  "largestComponent": {"componentId": 1, "size": 48, ...},
  "suspiciousComponents": [
    {
      "componentId": 3,
      "size": 7,
      "members": ["clm-abc", "..."],
      "averageFraudScore": 0.79,
      "isolationLevel": "isolated",
      "riskLevel": "high"
    }
  ],
  "insight": "Isolated components may represent independent fraud rings"
}
```

**Request Example (Mode 2):**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/network-fraud/isolated-rings?id=clm-abc&type=claimant"
```

**Response (Mode 2):** Graph envelope for the specific ring.

---

### 25. Cross-Claim Patterns

For a given claimant, compute diversity metrics and a 2-hop graph showing downstream entities (RepairShop, Witness, MedicalProvider) that reappear across multiple claims — the "habitual fraud" signature.

**Endpoint:** `GET /network-fraud/cross-claim-patterns/{claimant_id}`

**Authentication:** Bearer JWT

**Path Parameters:** `claimant_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/cross-claim-patterns/clm-abc
```

**Response Example:**

```json
{
  "metrics": {
    "totalClaims": 4,
    "uniqueRepairShops": 1,
    "uniqueWitnesses": 1,
    "uniqueProviders": 2,
    "shopDiversity": 0.25,
    "witnessDiversity": 0.25,
    "redFlags": {
      "sameShopAlways": true,
      "sameWitnessAlways": true,
      "lowDiversity": true
    }
  },
  "nodes": [...],
  "edges": [...]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `metrics.totalClaims` | integer | Number of claims filed |
| `metrics.uniqueRepairShops` | integer | Distinct shops used across claims |
| `metrics.uniqueWitnesses` | integer | Distinct witnesses across claims |
| `metrics.uniqueProviders` | integer | Distinct medical providers |
| `metrics.shopDiversity` | number | `uniqueRepairShops / totalClaims` |
| `metrics.witnessDiversity` | number | `uniqueWitnesses / totalClaims` |
| `metrics.redFlags` | object | Boolean flags for sameShopAlways, sameWitnessAlways, lowDiversity |
| `nodes`, `edges` | array | Graph envelope (see [Graph Response Format](#graph-response-format)) |

**Errors:**

- `404 Not Found` — `claimant_id` not in graph

---

### 26. Medical Provider Neighborhood

Return the 1-hop neighborhood graph of a medical provider.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}`

**Authentication:** Bearer JWT

**Path Parameters:** `provider_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc
```

**Response:** Graph envelope — provider at center with connected Claimants, Passengers, and Claims via `treated_by`.

**Errors:**

- `404 Not Found` — `provider_id` not in graph

---

### 27. Medical Provider Fraud Analysis

Compute fraud metrics for a medical provider using Neptune ML + aggregate claim statistics.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}/fraud-analysis`

**Authentication:** Bearer JWT

**Path Parameters:** `provider_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc/fraud-analysis
```

**Response Example:**

```json
{
  "providerId": "prov-abc",
  "name": "Dr. Provider 0",
  "totalClaims": 13,
  "uniqueClaimants": 9,
  "highFraudClaims": 7,
  "averageFraudScore": 0.61,
  "mlRiskScore": 0.78,
  "networkConnections": 24,
  "riskLevel": "high",
  "suspicionIndicators": {
    "highFraudRate": true,
    "limitedClaimants": false,
    "networkHub": true
  }
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `providerId` | string | Provider vertex ID |
| `name` | string | Provider name |
| `totalClaims` | integer | Claims via `treated_by` |
| `uniqueClaimants` | integer | Distinct claimants reached |
| `highFraudClaims` | integer | Claims with fraudScore > 0.7 |
| `averageFraudScore` | number | Mean fraudScore across claims |
| `mlRiskScore` | number | Neptune ML inductive inference on provider node |
| `networkConnections` | integer | Degree centrality (reach via claims) |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleans for rule-based red flags |

**Errors:**

- `404 Not Found` — `provider_id` not in graph

---

## Advanced Analysis

### 28. Influential Claimants

Rank claimants by approximated PageRank (computed via 1-hop connection scoring). Surfaces claimants who sit at the center of many fraud-adjacent entities.

**Endpoint:** `GET /advanced-analysis/influential-claimants`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/advanced-analysis/influential-claimants
```

**Response Example:**

```json
{
  "algorithm": "PageRank (approximated via connection scoring)",
  "topInfluentialClaimants": [
    {
      "claimantId": "clm-abc",
      "name": "Claimant 42",
      "connectionScore": 38,
      "fraudScore": 0.82,
      "riskLevel": "high"
    }
  ]
}
```

---

### 29. Fraudster Connections

Find the shortest path between two entities in the fraud network. Useful for investigators reasoning about how two ostensibly-unrelated claimants or entities are actually connected.

**Endpoint:** `GET /advanced-analysis/connections?source={id}&target={id}`

**Authentication:** Bearer JWT

**Query Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `source` | string | Source entity ID |
| `target` | string | Target entity ID |

**Request Example:**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/advanced-analysis/connections?source=clm-abc&target=clm-def"
```

**Response:** Graph envelope containing the shortest path — typically 2–6 hops — with path edges labeled by their type.

**Without query parameters:** returns a sampled graph of high-fraud-score claimants with their interconnections.

**Errors:**

- `404 Not Found` — `source` or `target` not in graph

---

## Entity Lookup

### 30. Repair Shop Neighborhood

Return a repair shop's 1-hop neighborhood — the Claims repaired there, plus the Claimants behind those claims.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}`

**Authentication:** Bearer JWT

**Path Parameters:** `shop_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc
```

**Response:** Graph envelope.

**Errors:**

- `404 Not Found` — `shop_id` not in graph

---

### 31. Repair Shop Statistics

Compute repair shop aggregate stats: total claims, fraud-rate, total revenue.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}/statistics`

**Authentication:** Bearer JWT

**Path Parameters:** `shop_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc/statistics
```

**Response Example:**

```json
{
  "shopId": "shop-abc",
  "name": "Repair Shop 0",
  "totalClaims": 18,
  "averageClaimAmount": 9823.40,
  "totalRevenue": 176821.20,
  "highFraudClaims": 12,
  "fraudRate": 0.67,
  "averageFraudScore": 0.74,
  "riskLevel": "high"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `shopId` | string | Shop vertex ID |
| `name` | string | Shop name |
| `totalClaims` | integer | Claims via `repaired_at` |
| `averageClaimAmount` | number | Mean claim amount |
| `totalRevenue` | number | Sum of claim amounts |
| `highFraudClaims` | integer | Claims with fraudScore > 0.7 |
| `fraudRate` | number (0–1) | `highFraudClaims / totalClaims` |
| `averageFraudScore` | number | Mean fraudScore |
| `riskLevel` | string | `low`, `medium`, `high` |

**Errors:**

- `404 Not Found` — `shop_id` not in graph

---

### 32. Vehicle Neighborhood

Return a vehicle's 1-hop neighborhood — accidents it was involved in, its owner, and the claims for those accidents.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}`

**Authentication:** Bearer JWT

**Path Parameters:** `vehicle_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc
```

**Response:** Graph envelope.

**Errors:**

- `404 Not Found` — `vehicle_id` not in graph

---

### 33. Vehicle Fraud History

Analyze a vehicle's claim history and compute an ML risk score.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}/fraud-history`

**Authentication:** Bearer JWT

**Path Parameters:** `vehicle_id` (string)

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc/fraud-history
```

**Response Example:**

```json
{
  "vehicleId": "veh-abc",
  "make": "Nissan",
  "year": 2021,
  "totalClaims": 3,
  "highFraudClaims": 2,
  "averageFraudScore": 0.68,
  "mlRiskScore": 0.81,
  "uniqueOwners": 2,
  "uniqueRepairShops": 1,
  "riskLevel": "high",
  "suspicionIndicators": {
    "repeatClaims": true,
    "ownerChurn": true,
    "shopLockIn": true
  }
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `vehicleId` | string | Vehicle vertex ID |
| `make` | string | Vehicle make |
| `year` | integer | Model year |
| `totalClaims` | integer | Claims where this vehicle was involved |
| `highFraudClaims` | integer | Claims with fraudScore > 0.7 |
| `averageFraudScore` | number | Mean fraudScore across claims |
| `mlRiskScore` | number | Neptune ML inductive inference on the vehicle |
| `uniqueOwners` | integer | Distinct claimants who owned this vehicle |
| `uniqueRepairShops` | integer | Distinct shops this vehicle was repaired at |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleans for rule-based red flags |

**Special response for vehicles with no claims:**

```json
{"vehicleId": "veh-abc", "make": "Nissan", "year": 2021, "totalClaims": 0, "riskLevel": "unknown"}
```

**Errors:**

- `404 Not Found` — `vehicle_id` not in graph

---

## Analytics

### 34. Fraud Trends

Aggregate fraud statistics across all claims.

**Endpoint:** `GET /analytics/fraud-trends`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/fraud-trends
```

**Response Example:**

```json
{
  "totalClaims": 2020,
  "approvedClaims": 2020,
  "rejectedClaims": 0,
  "pendingClaims": 0,
  "highFraudClaims": 59,
  "fraudRate": 0.02,
  "totalClaimAmount": 7589863.11,
  "estimatedFraudExposure": 2276958.93
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `totalClaims` | integer | Total claims in the graph |
| `approvedClaims` | integer | Claims with status `approved` |
| `rejectedClaims` | integer | Claims with status `rejected` |
| `pendingClaims` | integer | Claims with status `pending` |
| `highFraudClaims` | integer | Claims with fraudScore > 0.7 |
| `fraudRate` | number | `highFraudClaims / totalClaims` |
| `totalClaimAmount` | number | Sum of all claim amounts |
| `estimatedFraudExposure` | number | Sum of fraud-flagged claim amounts |

---

### 35. Geographic Hotspots

Detect geographic fraud hotspots by clustering accidents and entities by zip code. Returns zip-code-level clusters with coordinates, fraud density, linked entities, and a network graph of the top fraud zone.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/geographic-hotspots
```

**Response Example (abridged):**

```json
{
  "zones": [
    {
      "zipCode": "33142",
      "latitude": 25.823165,
      "longitude": -80.207243,
      "totalAccidents": 15,
      "fraudAccidents": 14,
      "fraudDensity": 0.933
    }
  ],
  "hotspotEntities": {
    "repairShops": [
      {
        "id": "uuid",
        "name": "Repair Shop 3",
        "latitude": 25.821,
        "longitude": -80.215,
        "zipCode": "33142",
        "fraudScore": 0.89,
        "type": "repairShop"
      }
    ],
    "medicalProviders": [...],
    "towCompanies": [...]
  },
  "graph": {
    "nodes": [
      {"id": "uuid", "type": "accident", "label": "Accident (2026-04-12)", "latitude": 25.82, "longitude": -80.21, "size": 8, "fraudScore": 0.0},
      {"id": "uuid", "type": "claim", "label": "Claim", "size": 7, "fraudScore": 0.92},
      {"id": "uuid", "type": "repairShop", "label": "Repair Shop", "size": 12, "fraudScore": 0.94}
    ],
    "edges": [
      {"source": "claim-uuid", "target": "accident-uuid", "type": "for_accident"},
      {"source": "claim-uuid", "target": "shop-uuid", "type": "repaired_at"}
    ]
  },
  "insight": "Top fraud zone: ZIP 33142 with 93% fraud density"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `zones[]` | array | ZIP codes sorted by fraud density (descending) |
| `zones[].zipCode` | string | ZIP code |
| `zones[].latitude` | number | Average latitude of accidents in this zone |
| `zones[].longitude` | number | Average longitude of accidents in this zone |
| `zones[].totalAccidents` | integer | Total accidents in this ZIP |
| `zones[].fraudAccidents` | integer | Fraud-linked accidents in this ZIP |
| `zones[].fraudDensity` | number | Ratio of fraud to total accidents (0.0–1.0) |
| `hotspotEntities` | object | Suspicious entities located in top fraud zones |
| `hotspotEntities.repairShops[]` | array | Repair shops in fraud zones with fraud scores |
| `hotspotEntities.medicalProviders[]` | array | Medical providers in fraud zones |
| `hotspotEntities.towCompanies[]` | array | Tow companies in fraud zones |
| `graph` | object | Network visualization data for the top fraud zone |
| `graph.nodes[]` | array | Nodes with id, type, label, fraudScore, coordinates |
| `graph.edges[]` | array | Edges with source, target, type |
| `insight` | string | Human-readable summary of the top fraud zone |

---

### 36. Claim Amount Anomalies

Detect claims with abnormally high amounts via statistical (z-score) and ML-powered analysis.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/claim-amount-anomalies
```

**Response Example:**

```json
{
  "algorithm": "Statistical Anomaly Detection + Neptune ML",
  "statistics": {
    "meanAmount": 3757.37,
    "standardDeviation": 2142.10,
    "totalClaims": 2020
  },
  "anomaliesDetected": 59,
  "highRiskAnomalies": [],
  "allAnomalies": [
    {
      "claimId": "abc-123",
      "amount": 17407.07,
      "zScore": 6.37,
      "fraudScore": 0.0,
      "mlAnomalyScore": 0.0,
      "anomalyType": "unusually_high",
      "riskLevel": "medium"
    }
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `algorithm` | string | Algorithm description |
| `statistics.meanAmount` | number | Mean claim amount |
| `statistics.standardDeviation` | number | Std-dev of claim amounts |
| `statistics.totalClaims` | integer | Sample size |
| `anomaliesDetected` | integer | Total anomalies (abs(z-score) > 2) |
| `highRiskAnomalies[]` | array | Claims with z-score > 3 AND mlAnomalyScore > 0.7 |
| `allAnomalies[]` | array | All anomalies |
| `allAnomalies[].zScore` | number | Statistical z-score |
| `allAnomalies[].mlAnomalyScore` | number | Neptune ML anomaly score |
| `allAnomalies[].anomalyType` | string | `unusually_high` or `unusually_low` |
| `allAnomalies[].riskLevel` | string | `low`, `medium`, `high` |

---

### 37. Temporal Patterns

Analyze claim filing patterns over time — weekly and monthly aggregates, detected bursts.

**Endpoint:** `GET /analytics/temporal-patterns`

**Authentication:** Bearer JWT

**Request Example:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/temporal-patterns
```

**Response Example (abridged):**

```json
{
  "monthlyTrends": [
    {"month": "2024-01", "totalClaims": 168, "fraudClaims": 4, "fraudRate": 0.024},
    {"month": "2024-02", "totalClaims": 142, "fraudClaims": 3, "fraudRate": 0.021}
  ],
  "weekdayPatterns": {
    "Monday": 312, "Tuesday": 289, "...": "..."
  },
  "anomalousBursts": [
    {"startDate": "2024-06-10", "endDate": "2024-06-13", "claimCount": 42, "expected": 14}
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `monthlyTrends[]` | array | Monthly claim/fraud rate data |
| `weekdayPatterns` | object | Claim counts per weekday |
| `anomalousBursts[]` | array | Detected time windows with claim rate much higher than expected |

---

## Entity Lists

Each of these endpoints returns a simple list for populating UI dropdowns. Response shape is identical per entity type.

### 38. List Attorneys

**Endpoint:** `GET /attorneys`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "attorneys": [
    {"id": "atty-1", "name": "Attorney 0"},
    {"id": "atty-2", "name": "Attorney 1"}
  ]
}
```

---

### 39. List Witnesses

**Endpoint:** `GET /witnesses`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "witnesses": [
    {"id": "wit-1", "name": "Witness 0"}
  ]
}
```

---

### 40. List Passengers

**Endpoint:** `GET /passengers`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "passengers": [
    {"id": "pas-1", "name": "Passenger abc12345"},
    {"id": "pas-2", "name": "Serial Jump-in 9f25c880"}
  ]
}
```

---

### 41. List Tow Companies

**Endpoint:** `GET /tow-companies`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "towCompanies": [
    {"id": "tow-1", "name": "Tow Company 0"}
  ]
}
```

---

### 42. List Medical Providers

**Endpoint:** `GET /medical-providers`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "medicalProviders": [
    {"id": "prov-1", "name": "Dr. Provider 0"}
  ]
}
```

---

### 43. List Repair Shops

**Endpoint:** `GET /repair-shops`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "repairShops": [
    {"id": "shop-1", "name": "Repair Shop 0"}
  ]
}
```

---

### 44. List Vehicles

**Endpoint:** `GET /vehicles`

**Authentication:** Bearer JWT

**Response Example:**

```json
{
  "vehicles": [
    {"id": "veh-1", "vin": "VIN0000000000", "make": "Toyota", "year": 2020}
  ]
}
```

---

## Rate Limits

All endpoints are protected by AWS WAF with:

- **Global rate limit:** 2,000 requests per 5-minute window, per source IP
- **Bot detection:** Requests without a `User-Agent` header are blocked
- **OWASP Top 10 managed rules:** SQL injection, XSS, and other common attacks
- **Request-size limits:** POST bodies > 8 KB are rejected

Exceeding the rate limit returns a `403 Forbidden` with a WAF response message.

## Best Practices

- **Reuse JWTs across requests.** Token issuance is expensive; cache the token in your client for its 1-hour lifetime.
- **Refresh proactively.** Call `POST /auth/refresh` at ~90% of token lifetime rather than waiting for a `401`.
- **Respect pagination.** Graph endpoints cap the number of returned rings/communities for performance. If you need the full dataset for analytics, query the underlying Neptune cluster directly or request a Step Functions export run.
- **Treat fraudScore values as probability-like.** They're not calibrated classifiers; use them as a ranking signal.
- **Don't assume `mlRiskScore` > 0.** If Neptune ML training is still in progress (first 1–2 hours after deploy), ML endpoints degrade gracefully to heuristics and return 0 or fallback values.
- **Browser clients must send `credentials: 'include'`** to get the `httpOnly` cookie authentication path working. The API's CORS configuration requires it.

## Support

- **Troubleshooting:** check CloudWatch logs under `/aws/lambda/auto-insurance-fraud-detect-FraudDetectionFunction-*`
- **WAF logs:** `/aws/wafv2/auto-insurance-fraud-detection-WAF`
- **API Gateway logs:** `/aws/apigateway/auto-insurance-fraud-detection-API`
- **Neptune ML pipeline:** Step Functions console → `auto-insurance-fraud-detection-MLPipelineStack-*-MLPipeline`
- **Sample queries:** see [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md)
- **Frontend code:** see [frontend/README.md](frontend/README.md)
