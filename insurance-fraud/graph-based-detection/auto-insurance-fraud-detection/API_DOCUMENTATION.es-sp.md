[![en](https://img.shields.io/badge/lang-en-blue.svg)](API_DOCUMENTATION.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](API_DOCUMENTATION.pt-br.md)

# Documentación de la API de Detección de Fraude en Seguros de Automóviles - Amazon Neptune ML

Referencia completa para los 44 endpoints de la API de detección de fraude.

## Tabla de Contenidos

- [Información General](#información-general)
  - [URL Base](#url-base)
  - [Autenticación](#autenticación)
  - [Envoltura de Respuesta](#envoltura-de-respuesta)
  - [Formato de Respuesta de Grafo](#formato-de-respuesta-de-grafo)
  - [Manejo de Errores](#manejo-de-errores)
- [Autenticación (3 endpoints)](#endpoints-de-autenticación)
  - [1. Iniciar Sesión](#1-iniciar-sesión)
  - [2. Cerrar Sesión](#2-cerrar-sesión)
  - [3. Refrescar Token](#3-refrescar-token)
- [Reclamos (4 endpoints)](#reclamos)
  - [4. Enviar Reclamo](#4-enviar-reclamo)
  - [5. Listar Reclamos](#5-listar-reclamos)
  - [6. Obtener Detalles del Reclamo](#6-obtener-detalles-del-reclamo)
  - [7. Obtener Grafo de Vecindad del Reclamo](#7-obtener-grafo-de-vecindad-del-reclamo)
- [Reclamantes (6 endpoints)](#reclamantes)
  - [8. Listar Reclamantes](#8-listar-reclamantes)
  - [9. Obtener Detalles del Reclamante](#9-obtener-detalles-del-reclamante)
  - [10. Obtener Historial de Reclamos del Reclamante](#10-obtener-historial-de-reclamos-del-reclamante)
  - [11. Obtener Puntuación de Riesgo del Reclamante](#11-obtener-puntuación-de-riesgo-del-reclamante)
  - [12. Analizar Velocidad de Reclamos](#12-analizar-velocidad-de-reclamos)
  - [13. Análisis Integral de Fraude](#13-análisis-integral-de-fraude)
- [Anillos de Colisión (6 endpoints)](#anillos-de-colisión)
  - [14. Accidentes Simulados](#14-accidentes-simulados)
  - [15. Swoop & Squat](#15-swoop--squat)
  - [16. Pasajeros Infiltrados](#16-pasajeros-infiltrados)
  - [17. Colisiones de Papel](#17-colisiones-de-papel)
  - [18. Abogados Corruptos](#18-abogados-corruptos)
  - [19. Empresas de Grúa Corruptas](#19-empresas-de-grúa-corruptas)
- [Fraude de Red (8 endpoints)](#fraude-de-red)
  - [20. Testigos Profesionales](#20-testigos-profesionales)
  - [21. Anillos Organizados](#21-anillos-organizados)
  - [22. Centros de Fraude](#22-centros-de-fraude)
  - [23. Indicadores de Colusión](#23-indicadores-de-colusión)
  - [24. Anillos Aislados](#24-anillos-aislados)
  - [25. Patrones Entre Reclamos](#25-patrones-entre-reclamos)
  - [26. Vecindad del Proveedor Médico](#26-vecindad-del-proveedor-médico)
  - [27. Análisis de Fraude del Proveedor Médico](#27-análisis-de-fraude-del-proveedor-médico)
- [Análisis Avanzado (2 endpoints)](#análisis-avanzado)
  - [28. Reclamantes Influyentes](#28-reclamantes-influyentes)
  - [29. Conexiones entre Estafadores](#29-conexiones-entre-estafadores)
- [Consulta de Entidades (4 endpoints)](#consulta-de-entidades)
  - [30. Vecindad del Taller](#30-vecindad-del-taller)
  - [31. Estadísticas del Taller](#31-estadísticas-del-taller)
  - [32. Vecindad del Vehículo](#32-vecindad-del-vehículo)
  - [33. Historial de Fraude del Vehículo](#33-historial-de-fraude-del-vehículo)
- [Analítica (4 endpoints)](#analítica)
  - [34. Tendencias de Fraude](#34-tendencias-de-fraude)
  - [35. Puntos Calientes Geográficos](#35-puntos-calientes-geográficos)
  - [36. Anomalías en Montos de Reclamos](#36-anomalías-en-montos-de-reclamos)
  - [37. Patrones Temporales](#37-patrones-temporales)
- [Listas de Entidades (7 endpoints)](#listas-de-entidades)
  - [38. Listar Abogados](#38-listar-abogados)
  - [39. Listar Testigos](#39-listar-testigos)
  - [40. Listar Pasajeros](#40-listar-pasajeros)
  - [41. Listar Empresas de Grúa](#41-listar-empresas-de-grúa)
  - [42. Listar Proveedores Médicos](#42-listar-proveedores-médicos)
  - [43. Listar Talleres](#43-listar-talleres)
  - [44. Listar Vehículos](#44-listar-vehículos)
- [Límites de Tasa](#límites-de-tasa)
- [Mejores Prácticas](#mejores-prácticas)
- [Soporte](#soporte)

---

## Información General

### URL Base

Todos los endpoints se sirven desde la URL del API Gateway emitida en el momento del despliegue, con el formato:

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

Puede recuperar el valor exacto desde la salida del despliegue o desde CloudFormation:

```bash
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### Autenticación

Todos los endpoints excepto las tres operaciones `/auth/*` requieren una sesión válida. La autenticación se realiza enviando un JSON Web Token (JWT) emitido por el Amazon Cognito User Pool desplegado con la solución en una **cookie de sesión `httpOnly`** llamada `__Host-fraud_detection_token`. La cookie es establecida por `POST /auth/login` y está marcada como `HttpOnly; Secure; SameSite=None` para que no pueda ser accedida desde JavaScript ejecutándose en el navegador (hardening contra XSS).

**Clientes de navegador** no necesitan manipular la cookie — esta fluye automáticamente en cada solicitud subsiguiente cuando se usa `credentials: 'include'`.

**Clientes no-navegador** (curl, Python, etc.) deben guardar la cookie después del login y enviarla en cada solicitud:

```
Cookie: __Host-fraud_detection_token=eyJraWQiOi...
```

**Inicie sesión mediante el script auxiliar (guarda la cookie en `.auth-cookie`):**

```bash
./scripts/authenticate.sh -u user@company.com -p YourPassword123! --token-only
```

**Vigencias de tokens:**

| Token | Validez |
|-------|---------|
| ID token | 1 hora |
| Access token | 1 hora |
| Refresh token | 30 días |

Los tokens próximos a expirar deben refrescarse mediante `POST /auth/refresh` (endpoint 3) en lugar de reautenticarse.

### Envoltura de Respuesta

Las respuestas exitosas se devuelven como JSON con el estado HTTP `200`. Las respuestas de error siguen la misma estructura JSON pero con un estado `4xx`/`5xx` y un campo `error`:

```json
{
  "error": "Claimant not found"
}
```

### Formato de Respuesta de Grafo

Los endpoints que devuelven un grafo (la mayoría de los endpoints de detección de fraude) siguen una envoltura común `{ nodes, edges }`:

```json
{
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "type": "claimant|claim|accident|vehicle|repairShop|medicalProvider|witness|attorney|towCompany|passenger",
      "name": "string (opcional)",
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

Endpoints específicos pueden agregar propiedades adicionales a los nodos (p. ej., `staged`, `maneuverType`, `appearances`) — vea el esquema de respuesta de cada endpoint para más detalles.

### Manejo de Errores

| HTTP | Significado | Causa típica |
|------|-------------|--------------|
| `200` | Éxito | Solicitud procesada, el cuerpo contiene el resultado |
| `400` | Solicitud incorrecta | Cuerpo JSON mal formado o campo requerido faltante en un `POST` |
| `401` | No autorizado | JWT faltante, mal formado o expirado |
| `403` | Prohibido | JWT es válido pero WAF bloqueó la solicitud (límite de tasa, detección de bots) o la ruta no existe |
| `404` | No encontrado | La entidad referenciada (reclamante, reclamo, vehículo, proveedor, taller) no existe |
| `500` | Error interno | Excepción de Lambda (p. ej., error Gremlin inesperado). El cuerpo de respuesta contiene `{"error": "...", "message": "..."}` con detalle |

Todas las respuestas de error incluyen encabezados CORS para que sean correctamente expuestas a los clientes navegador.

---

## Endpoints de Autenticación

### 1. Iniciar Sesión

Intercambia credenciales por un token JWT.

**Endpoint:** `POST /auth/login`

**Autenticación:** Ninguna (así es como obtiene un token)

**Cuerpo de Solicitud:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `username` | string | Sí | Nombre de usuario Cognito (email) |
| `password` | string | Sí | Contraseña del usuario |

**Ejemplo de Solicitud:**

```bash
curl -X POST https://YOUR-API/prod/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@company.com","password":"YourPassword123!"}'
```

**Ejemplo de Respuesta:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "refreshToken": "eyJjdHkiOiJKV1Qi...",
  "expiresIn": 3600
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `token` | string | El ID token. Clientes de navegador pueden ignorar este valor — el servidor también establece automáticamente la cookie httpOnly `__Host-fraud_detection_token`. Clientes no-navegador pueden usar este valor para construir manualmente un encabezado `Cookie: __Host-fraud_detection_token=<token>` |
| `refreshToken` | string | Token de larga duración para usar con `/auth/refresh` |
| `expiresIn` | integer | Segundos hasta que el ID token expire (siempre 3600) |

**Efectos Secundarios:** Se establece una cookie `httpOnly` llamada `__Host-fraud_detection_token` en la respuesta para clientes navegador.

**Errores:**

- `400 Bad Request` — username o password faltante
- `401 Unauthorized` — credenciales inválidas o usuario no confirmado

---

### 2. Cerrar Sesión

Invalida la sesión activa y limpia la cookie.

**Endpoint:** `POST /auth/logout`

**Autenticación:** Bearer JWT

**Cuerpo de Solicitud:** Ninguno

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/auth/logout
```

**Ejemplo de Respuesta:**

```json
{
  "message": "Logged out successfully"
}
```

**Efectos Secundarios:** Se borra la cookie `__Host-fraud_detection_token`.

**Errores:**

- `401 Unauthorized` — JWT faltante o inválido

---

### 3. Refrescar Token

Intercambia un refresh token por un ID token nuevo.

**Endpoint:** `POST /auth/refresh`

**Autenticación:** Ninguna (el refresh token mismo es la credencial)

**Cuerpo de Solicitud:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `refreshToken` | string | Sí | El refresh token emitido previamente por `/auth/login` |

**Ejemplo de Solicitud:**

```bash
curl -X POST https://YOUR-API/prod/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refreshToken\":\"$REFRESH_TOKEN\"}"
```

**Ejemplo de Respuesta:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "expiresIn": 3600
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `token` | string | Nuevo ID token |
| `expiresIn` | integer | Segundos hasta que este nuevo token expire |

**Errores:**

- `400 Bad Request` — `refreshToken` faltante
- `401 Unauthorized` — refresh token expirado o revocado

---

## Reclamos

### 4. Enviar Reclamo

Envía un nuevo reclamo de seguro y recibe una puntuación de fraude en tiempo real por Neptune ML.

**Endpoint:** `POST /claims`

**Autenticación:** Bearer JWT (más firma HMAC opcional para socios de integración — vea los encabezados `X-Request-Timestamp` / `X-Request-Signature`)

**Cuerpo de Solicitud:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `claimAmount` | number | Sí | Monto del reclamo en USD |
| `claimantId` | string | Sí | ID del vértice Claimant existente |
| `vehicleId` | string | Sí | ID del vértice Vehicle existente |
| `repairShopId` | string | No | ID de RepairShop opcional |
| `witnessId` | string | No | ID de Witness opcional |
| `status` | string | No | Estado inicial (por defecto: `approved`) |

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/claims \
  -H "Content-Type: application/json" \
  -d '{"claimAmount":12500,"claimantId":"claimant-abc","vehicleId":"vehicle-xyz"}'
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimId` | string | ID del vértice Claim recién creado |
| `fraudScore` | number (0–1) | Probabilidad de fraude derivada por ML (inferencia inductiva mediante Neptune ML); fallback heurístico si ML no está disponible |
| `riskLevel` | string | `low` (< 0.5), `medium` (0.5–0.7), `high` (> 0.7) |
| `message` | string | Estado legible para humanos |
| `mlModel` | string | Identificador del modelo |
| `recommendation` | string | Acción sugerida |

**Errores:**

- `400 Bad Request` — falta `claimAmount`, `claimantId` o `vehicleId`
- `404 Not Found` — reclamante o vehículo referenciado no existe
- `500 Internal Server Error` — falla de escritura Neptune

---

### 5. Listar Reclamos

Listar todos los reclamos en el grafo.

**Endpoint:** `GET /claims`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claims
```

**Ejemplo de Respuesta:**

```json
{
  "claims": [
    {"id": "abc-123", "amount": 8500.00, "date": 1713283200},
    {"id": "def-456", "amount": 3200.50, "date": 1713366000}
  ]
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claims[].id` | string | ID del vértice Claim |
| `claims[].amount` | number | Monto del reclamo en USD |
| `claims[].date` | integer | Timestamp Unix epoch |

**Errores:**

- `401 Unauthorized` — JWT faltante o inválido

---

### 6. Obtener Detalles del Reclamo

Recupera un único reclamo.

**Endpoint:** `GET /claims/{claim_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| `claim_id` | string | ID del vértice Claim |

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimId` | string | ID del vértice Claim |
| `amount` | number | Monto del reclamo en USD |
| `status` | string | `approved`, `pending`, `rejected` |
| `claimDate` | integer | Unix epoch |
| `isFraud` | boolean | Etiqueta de verdad de campo (para datos demo) |
| `fraudScore` | number (0–1) | Puntuación de fraude de ML o datos almacenados |

**Errores:**

- `404 Not Found` — `claim_id` no está en el grafo

---

### 7. Obtener Grafo de Vecindad del Reclamo

Recupera un reclamo junto con su vecindad completa — accidente, vehículos, pasajeros, taller, testigos, reclamante, y cualquier proveedor médico o abogado conectado.

**Endpoint:** `GET /claims/{claim_id}/graph`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claim_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123/graph
```

**Respuesta:** Envoltura de grafo (vea [Formato de Respuesta de Grafo](#formato-de-respuesta-de-grafo)). Típicamente 8–20 nodos.

**Esquema de Respuesta:**

Envoltura de grafo estándar con tipos de nodo incluyendo `claim`, `accident`, `vehicle`, `repairShop`, `witness`, `claimant`, `passenger`, `medicalProvider`, `attorney`, `towCompany`. Los tipos de aristas incluyen `filed_claim`, `for_accident`, `involved_vehicle`, `repaired_at`, `witnessed_by`, `passenger_in`, `claimed_injury`, `treated_by`, `represented_by`, `towed_by`.

**Errores:**

- `404 Not Found` — `claim_id` no está en el grafo

---

## Reclamantes

### 8. Listar Reclamantes

Listar todos los reclamantes que han presentado al menos un reclamo.

**Endpoint:** `GET /claimants`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claimants
```

**Ejemplo de Respuesta:**

```json
{
  "claimants": [
    {"id": "clm-abc", "name": "Claimant 12"},
    {"id": "clm-def", "name": "Claimant 37"}
  ]
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimants[].id` | string | ID del vértice Claimant |
| `claimants[].name` | string | Nombre legible |

**Nota:** Los reclamantes con cero aristas `filed_claim` se excluyen — esto es intencional para que los dropdowns de la UI (Análisis de Fraude, Velocidad de Reclamos, etc.) nunca muestren entidades que devolverían resultados vacíos.

---

### 9. Obtener Detalles del Reclamante

Recupera un único reclamante.

**Endpoint:** `GET /claimants/{claimant_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc
```

**Ejemplo de Respuesta:**

```json
{
  "claimantId": "clm-abc",
  "name": "Claimant 12",
  "fraudScore": 0.42
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimantId` | string | ID del vértice Claimant |
| `name` | string | Nombre del reclamante |
| `fraudScore` | number | Puntuación de fraude a nivel reclamante |

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

### 10. Obtener Historial de Reclamos del Reclamante

Listar todos los reclamos presentados por un reclamante.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claims
```

**Ejemplo de Respuesta:**

```json
{
  "claimantId": "clm-abc",
  "claims": [
    {"claimId": "c1", "amount": 8500.00, "status": "approved", "claimDate": 1713283200, "fraudScore": 0.12},
    {"claimId": "c2", "amount": 12500.00, "status": "approved", "claimDate": 1715880000, "fraudScore": 0.88}
  ]
}
```

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimantId` | string | ID del vértice Claimant |
| `claims[]` | array | Lista de los reclamos del reclamante (misma forma que endpoint 6 pero abreviada) |

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

### 11. Obtener Puntuación de Riesgo del Reclamante

Calcula una puntuación de riesgo de fraude para un reclamante basada en historial de reclamos + señales derivadas por ML.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/risk-score
```

**Ejemplo de Respuesta (reclamante con historial):**

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

**Ejemplo de Respuesta (sin historial):**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimantId` | string | ID del vértice Claimant |
| `riskScore` | number (0–1) | Puntuación de fraude del reclamante (inferencia inductiva ML, fallback heurístico) |
| `totalClaims` | integer | Número de reclamos presentados |
| `rejectedClaims` | integer | Reclamos con `status = 'rejected'` |
| `rejectionRate` | number (0–1) | `rejectedClaims / totalClaims` |
| `totalClaimAmount` | number | Suma de todos los montos de reclamos |
| `message` | string | Presente solo cuando `totalClaims = 0` |

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

### 12. Analizar Velocidad de Reclamos

Detectar presentación de reclamos anormalmente frecuente usando análisis de series temporales sobre fechas de reclamos.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claim-velocity
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `claimantId` | string | ID del vértice Claimant |
| `totalClaims` | integer | Número de reclamos presentados |
| `claimsPerYear` | number | Tasa de reclamos anualizada |
| `averageIntervalDays` | number | Brecha media entre reclamos consecutivos |
| `shortestIntervalDays` | number | Brecha mínima — brechas muy cortas indican presentación en ráfaga |
| `velocityRisk` | number (0–1) | Puntuación de inferencia inductiva ML (fallback: `min(claimsPerYear/10, 1.0)`) |
| `riskLevel` | string | `low`, `medium`, `high` |

**Respuesta especial para reclamantes con < 2 reclamos:**

```json
{
  "claimantId": "clm-abc",
  "totalClaims": 1,
  "velocityRisk": "low",
  "message": "Insufficient claim history"
}
```

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

### 13. Análisis Integral de Fraude

Devuelve un grafo completo de red de fraude para un reclamante: reclamos, accidentes, vehículos, talleres, testigos, proveedores médicos, abogados, empresas de grúa y pasajeros. Usado por la UI de Análisis de Fraude para dirigir los flujos de trabajo del investigador.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/fraud-analysis
```

**Respuesta:** Envoltura de grafo estándar (vea [Formato de Respuesta de Grafo](#formato-de-respuesta-de-grafo)). Típicamente devuelve la vecindad completa de 2 saltos del reclamante, incluyendo entidades de anillo de fraude conectadas con puntuaciones de fraude elevadas renderizadas como nodos con contorno rojo.

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

## Anillos de Colisión

### 14. Accidentes Simulados

Detecta pares de reclamantes cuyos accidentes simulados comparten un Vehicle, Witness o RepairShop. Cada Accident devuelto tiene `maneuverType != 'normal'` o `policeVerified = false`, y cada anillo se devuelve con la entidad pivote compartida en el medio.

**Endpoint:** `GET /collision-rings/staged-accidents`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/staged-accidents
```

**Respuesta:** Envoltura de grafo. Los nodos Accident llevan propiedades adicionales:

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `maneuverType` | string | `swoop-squat`, `sudden-stop` o `normal` |
| `policeVerified` | boolean | Si el accidente tiene un reporte policial verificado |
| `staged` | boolean | Siempre `true` para accidentes devueltos por este endpoint |

---

### 15. Swoop & Squat

Detecta vehículos involucrados en 2 o más accidentes traseros simulados (`maneuverType` en `swoop-squat` o `sudden-stop`). Expone vehículos "utilería" reutilizados en choques deliberados.

**Endpoint:** `GET /collision-rings/swoop-and-squat`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/swoop-and-squat
```

**Respuesta:** Envoltura de grafo centrada en nodos Vehicle de múltiples accidentes, sus Accidents, Claims y Claimants.

---

### 16. Pasajeros Infiltrados

Expone accidentes con pasajeros falsos "jump-in" presentando reclamos por lesiones. Cada Passenger se enriquece con métricas agregadas para revelar jump-ins seriales.

**Endpoint:** `GET /collision-rings/stuffed-passengers`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/stuffed-passengers
```

**Respuesta:** Envoltura de grafo. Los nodos Passenger llevan:

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `appearances` | integer | Número de accidentes distintos a los que el pasajero está vinculado vía `passenger_in` |
| `injuryClaims` | integer | Número de aristas `claimed_injury` desde este pasajero |
| `totalClaimed` | number | Suma de todos los montos de reclamos por lesiones |

Los pasajeros con `appearances ≥ 2` se renderizan como nodos más grandes — la firma de "jump-in serial". Los nodos de proveedor médico se adjuntan mediante `treated_by` para que el rastro del dinero de las lesiones falsas sea visible.

---

### 17. Colisiones de Papel

Detecta accidentes no verificados con evidencia escasa — `policeVerified = false` Y ≤1 testigo Y ≤1 vehículo.

**Endpoint:** `GET /collision-rings/paper-collisions`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/paper-collisions
```

**Respuesta:** Envoltura de grafo. Se incluyen explícitamente cadenas escasas de testigos/vehículos para que la "evidencia escasa" sea visualmente aparente.

---

### 18. Abogados Corruptos

Detecta abogados con `fraudScore ≥ 0.7` que representan a dos o más reclamantes, junto con los reclamantes que representan y los reclamos de esos reclamantes.

**Endpoint:** `GET /collision-rings/corrupt-attorneys`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-attorneys
```

**Respuesta:** Envoltura de grafo centrada en nodos Attorney corruptos con aristas Claimant → Claim radiando hacia afuera.

---

### 19. Empresas de Grúa Corruptas

Detecta empresas de grúa con `fraudScore ≥ 0.7` que remolcan vehículos en 2+ accidentes. Incluye la cadena completa: Tow → Vehicle → Accident → Claim → RepairShop para que el patrón de direccionamiento sea visible.

**Endpoint:** `GET /collision-rings/corrupt-tow-companies`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-tow-companies
```

**Respuesta:** Envoltura de grafo incluyendo nodos TowCompany, Vehicle, Accident, Claim, RepairShop y Claimant.

---

## Fraude de Red

### 20. Testigos Profesionales

Detecta testigos que aparecen en 3+ accidentes distintos — el patrón del "testigo profesional".

**Endpoint:** `GET /network-fraud/professional-witnesses`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/professional-witnesses
```

**Respuesta:** Envoltura de grafo. Ruta por testigo: `Witness ← witnessed_by ← Accident ← for_accident ← Claim ← filed_claim ← Claimant`.

---

### 21. Anillos Organizados

Detecta comunidades densamente conectadas de reclamantes. La membresía del anillo se descubre mediante Vehicle compartido (`owns` ↔ `owns`) o RepairShop compartido (`filed_claim` → `repaired_at`). El sub-grafo devuelto expone todas las entidades compartidas — proveedores médicos, abogados, testigos, empresas de grúa — como evidencia corroborativa.

**Endpoint:** `GET /network-fraud/organized-rings`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/organized-rings
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `algorithm` | string | Descripción del algoritmo de detección de comunidades |
| `totalCommunities` | integer | Total de anillos descubiertos |
| `rings[]` | array | Hasta 9 anillos principales por tamaño/puntuación |
| `rings[].communitySize` | integer | Número de reclamantes en el anillo |
| `rings[].averageFraudScore` | number | Media de fraudScore entre los miembros del anillo |
| `rings[].riskLevel` | string | `low`, `medium`, `high` |
| `rings[].graph` | object | Envoltura de grafo por anillo |

---

### 22. Centros de Fraude

Clasifica los principales talleres, proveedores médicos y abogados por amplitud de reclamantes conectados, y calcula una "puntuación de colusión" — la fracción de esos reclamantes que también comparten al menos otra entidad con un par en el hub.

**Endpoint:** `GET /network-fraud/fraud-hubs`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/fraud-hubs
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

Claves de nivel superior: `repairShop`, `medicalProvider`, `attorney`. Cada una tiene un array `hubs` (hasta 5 por categoría) con:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nombre de la entidad hub |
| `uniqueClaimants` | integer | Reclamantes distintos conectados a este hub |
| `collusionScore` | number (0–1) | Fracción de reclamantes que comparten otra entidad con un par del anillo |
| `graph` | object | Sub-grafo anclado en el hub |

---

### 23. Indicadores de Colusión

Expone talleres con 5+ reclamantes convergiendo mediante `Claim → repaired_at`. Revela patrones tipo triángulos de colusión.

**Endpoint:** `GET /network-fraud/collusion-indicators`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/collusion-indicators
```

**Respuesta:** Envoltura de grafo con hubs RepairShop, nodos Claim intermedios y los Claimants detrás de cada reclamo.

---

### 24. Anillos Aislados

Detecta componentes de fraude independientes — sub-grafos pequeños y autocontenidos sin puentes con la red de fraude más amplia. Opera en dos modos:

**Modo 1 — Lista resumen (sin parámetros de consulta):** Devuelve una lista de todos los componentes aislados.

**Endpoint:** `GET /network-fraud/isolated-rings`

**Modo 2 — Grafo por entidad (parámetros de consulta):** Devuelve el anillo aislado específico para una entidad.

**Endpoint:** `GET /network-fraud/isolated-rings?id={entity_id}&type={entity_type}`

**Autenticación:** Bearer JWT

**Parámetros de Consulta (Modo 2):**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| `id` | string | ID de la entidad |
| `type` | string | Uno de: `claimant`, `claim`, `repair-shop`, `vehicle`, `medical-provider`, `attorney`, `witness`, `passenger`, `tow-company` |

**Ejemplo de Solicitud (Modo 1):**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/isolated-rings
```

**Ejemplo de Respuesta (Modo 1):**

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

**Ejemplo de Solicitud (Modo 2):**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/network-fraud/isolated-rings?id=clm-abc&type=claimant"
```

**Respuesta (Modo 2):** Envoltura de grafo para el anillo específico.

---

### 25. Patrones Entre Reclamos

Para un reclamante dado, calcula métricas de diversidad y un grafo de 2 saltos mostrando entidades aguas abajo (RepairShop, Witness, MedicalProvider) que reaparecen entre múltiples reclamos — la firma de "fraude habitual".

**Endpoint:** `GET /network-fraud/cross-claim-patterns/{claimant_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `claimant_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/cross-claim-patterns/clm-abc
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `metrics.totalClaims` | integer | Número de reclamos presentados |
| `metrics.uniqueRepairShops` | integer | Talleres distintos usados entre reclamos |
| `metrics.uniqueWitnesses` | integer | Testigos distintos entre reclamos |
| `metrics.uniqueProviders` | integer | Proveedores médicos distintos |
| `metrics.shopDiversity` | number | `uniqueRepairShops / totalClaims` |
| `metrics.witnessDiversity` | number | `uniqueWitnesses / totalClaims` |
| `metrics.redFlags` | object | Banderas booleanas para sameShopAlways, sameWitnessAlways, lowDiversity |
| `nodes`, `edges` | array | Envoltura de grafo (vea [Formato de Respuesta de Grafo](#formato-de-respuesta-de-grafo)) |

**Errores:**

- `404 Not Found` — `claimant_id` no está en el grafo

---

### 26. Vecindad del Proveedor Médico

Devuelve el grafo de vecindad de 1 salto de un proveedor médico.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `provider_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc
```

**Respuesta:** Envoltura de grafo — proveedor en el centro con Claimants, Passengers y Claims conectados vía `treated_by`.

**Errores:**

- `404 Not Found` — `provider_id` no está en el grafo

---

### 27. Análisis de Fraude del Proveedor Médico

Calcula métricas de fraude para un proveedor médico usando Neptune ML + estadísticas agregadas de reclamos.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}/fraud-analysis`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `provider_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc/fraud-analysis
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `providerId` | string | ID del vértice del proveedor |
| `name` | string | Nombre del proveedor |
| `totalClaims` | integer | Reclamos vía `treated_by` |
| `uniqueClaimants` | integer | Reclamantes distintos alcanzados |
| `highFraudClaims` | integer | Reclamos con fraudScore > 0.7 |
| `averageFraudScore` | number | Media fraudScore entre reclamos |
| `mlRiskScore` | number | Inferencia inductiva de Neptune ML sobre el nodo del proveedor |
| `networkConnections` | integer | Centralidad de grado (alcance vía reclamos) |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleanos para banderas rojas basadas en reglas |

**Errores:**

- `404 Not Found` — `provider_id` no está en el grafo

---

## Análisis Avanzado

### 28. Reclamantes Influyentes

Clasifica reclamantes por PageRank aproximado (calculado mediante puntuación de conexiones de 1 salto). Expone reclamantes que están en el centro de muchas entidades adyacentes al fraude.

**Endpoint:** `GET /advanced-analysis/influential-claimants`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/advanced-analysis/influential-claimants
```

**Ejemplo de Respuesta:**

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

### 29. Conexiones entre Estafadores

Encuentra el camino más corto entre dos entidades en la red de fraude. Útil para investigadores razonando sobre cómo dos reclamantes o entidades ostensiblemente no relacionados están realmente conectados.

**Endpoint:** `GET /advanced-analysis/connections?source={id}&target={id}`

**Autenticación:** Bearer JWT

**Parámetros de Consulta:**

| Nombre | Tipo | Descripción |
|--------|------|-------------|
| `source` | string | ID de entidad origen |
| `target` | string | ID de entidad destino |

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/advanced-analysis/connections?source=clm-abc&target=clm-def"
```

**Respuesta:** Envoltura de grafo conteniendo el camino más corto — típicamente 2–6 saltos — con aristas del camino etiquetadas por su tipo.

**Sin parámetros de consulta:** devuelve un grafo muestreado de reclamantes con puntuación de fraude alta con sus interconexiones.

**Errores:**

- `404 Not Found` — `source` o `target` no está en el grafo

---

## Consulta de Entidades

### 30. Vecindad del Taller

Devuelve la vecindad de 1 salto de un taller — los Claims reparados allí, más los Claimants detrás de esos reclamos.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `shop_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc
```

**Respuesta:** Envoltura de grafo.

**Errores:**

- `404 Not Found` — `shop_id` no está en el grafo

---

### 31. Estadísticas del Taller

Calcula estadísticas agregadas del taller: total de reclamos, tasa de fraude, ingresos totales.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}/statistics`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `shop_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc/statistics
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `shopId` | string | ID del vértice del taller |
| `name` | string | Nombre del taller |
| `totalClaims` | integer | Reclamos vía `repaired_at` |
| `averageClaimAmount` | number | Monto medio del reclamo |
| `totalRevenue` | number | Suma de montos de reclamos |
| `highFraudClaims` | integer | Reclamos con fraudScore > 0.7 |
| `fraudRate` | number (0–1) | `highFraudClaims / totalClaims` |
| `averageFraudScore` | number | Media fraudScore |
| `riskLevel` | string | `low`, `medium`, `high` |

**Errores:**

- `404 Not Found` — `shop_id` no está en el grafo

---

### 32. Vecindad del Vehículo

Devuelve la vecindad de 1 salto de un vehículo — accidentes en los que estuvo involucrado, su propietario, y los reclamos de esos accidentes.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `vehicle_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc
```

**Respuesta:** Envoltura de grafo.

**Errores:**

- `404 Not Found` — `vehicle_id` no está en el grafo

---

### 33. Historial de Fraude del Vehículo

Analiza el historial de reclamos de un vehículo y calcula una puntuación de riesgo ML.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}/fraud-history`

**Autenticación:** Bearer JWT

**Parámetros de Ruta:** `vehicle_id` (string)

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc/fraud-history
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `vehicleId` | string | ID del vértice Vehicle |
| `make` | string | Marca del vehículo |
| `year` | integer | Año del modelo |
| `totalClaims` | integer | Reclamos donde este vehículo estuvo involucrado |
| `highFraudClaims` | integer | Reclamos con fraudScore > 0.7 |
| `averageFraudScore` | number | Media fraudScore entre reclamos |
| `mlRiskScore` | number | Inferencia inductiva de Neptune ML sobre el vehículo |
| `uniqueOwners` | integer | Reclamantes distintos que poseyeron este vehículo |
| `uniqueRepairShops` | integer | Talleres distintos donde se reparó este vehículo |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleanos para banderas rojas basadas en reglas |

**Respuesta especial para vehículos sin reclamos:**

```json
{"vehicleId": "veh-abc", "make": "Nissan", "year": 2021, "totalClaims": 0, "riskLevel": "unknown"}
```

**Errores:**

- `404 Not Found` — `vehicle_id` no está en el grafo

---

## Analítica

### 34. Tendencias de Fraude

Estadísticas agregadas de fraude entre todos los reclamos.

**Endpoint:** `GET /analytics/fraud-trends`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/fraud-trends
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `totalClaims` | integer | Reclamos totales en el grafo |
| `approvedClaims` | integer | Reclamos con estado `approved` |
| `rejectedClaims` | integer | Reclamos con estado `rejected` |
| `pendingClaims` | integer | Reclamos con estado `pending` |
| `highFraudClaims` | integer | Reclamos con fraudScore > 0.7 |
| `fraudRate` | number | `highFraudClaims / totalClaims` |
| `totalClaimAmount` | number | Suma de todos los montos de reclamos |
| `estimatedFraudExposure` | number | Suma de montos de reclamos marcados como fraude |

---

### 35. Puntos Calientes Geográficos

Detecta puntos calientes de fraude geográfico agrupando accidentes y entidades por código postal. Devuelve clusters a nivel de código postal con coordenadas, densidad de fraude, entidades vinculadas y un grafo de red de la zona de fraude principal.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/geographic-hotspots
```

**Ejemplo de Respuesta (abreviado):**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `zones[]` | array | Códigos postales ordenados por densidad de fraude (descendente) |
| `zones[].zipCode` | string | Código postal |
| `zones[].latitude` | number | Latitud promedio de accidentes en esta zona |
| `zones[].longitude` | number | Longitud promedio de accidentes en esta zona |
| `zones[].totalAccidents` | integer | Total de accidentes en este código postal |
| `zones[].fraudAccidents` | integer | Accidentes vinculados a fraude en este código postal |
| `zones[].fraudDensity` | number | Proporción de fraude sobre total de accidentes (0.0–1.0) |
| `hotspotEntities` | object | Entidades sospechosas ubicadas en zonas de fraude principales |
| `hotspotEntities.repairShops[]` | array | Talleres en zonas de fraude con puntuaciones de fraude |
| `hotspotEntities.medicalProviders[]` | array | Proveedores médicos en zonas de fraude |
| `hotspotEntities.towCompanies[]` | array | Compañías de grúa en zonas de fraude |
| `graph` | object | Datos de visualización de red para la zona de fraude principal |
| `graph.nodes[]` | array | Nodos con id, tipo, etiqueta, fraudScore, coordenadas |
| `graph.edges[]` | array | Aristas con source, target, tipo |
| `insight` | string | Resumen legible de la zona de fraude principal |

---

### 36. Anomalías en Montos de Reclamos

Detecta reclamos con montos anormalmente altos mediante análisis estadístico (z-score) y análisis potenciado por ML.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/claim-amount-anomalies
```

**Ejemplo de Respuesta:**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `algorithm` | string | Descripción del algoritmo |
| `statistics.meanAmount` | number | Monto medio del reclamo |
| `statistics.standardDeviation` | number | Desviación estándar de montos de reclamos |
| `statistics.totalClaims` | integer | Tamaño de la muestra |
| `anomaliesDetected` | integer | Anomalías totales (abs(z-score) > 2) |
| `highRiskAnomalies[]` | array | Reclamos con z-score > 3 Y mlAnomalyScore > 0.7 |
| `allAnomalies[]` | array | Todas las anomalías |
| `allAnomalies[].zScore` | number | Z-score estadístico |
| `allAnomalies[].mlAnomalyScore` | number | Puntuación de anomalía de Neptune ML |
| `allAnomalies[].anomalyType` | string | `unusually_high` o `unusually_low` |
| `allAnomalies[].riskLevel` | string | `low`, `medium`, `high` |

---

### 37. Patrones Temporales

Analiza patrones de presentación de reclamos a lo largo del tiempo — agregados semanales y mensuales, ráfagas detectadas.

**Endpoint:** `GET /analytics/temporal-patterns`

**Autenticación:** Bearer JWT

**Ejemplo de Solicitud:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/temporal-patterns
```

**Ejemplo de Respuesta (abreviado):**

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

**Esquema de Respuesta:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `monthlyTrends[]` | array | Datos mensuales de reclamos/tasa de fraude |
| `weekdayPatterns` | object | Conteos de reclamos por día de semana |
| `anomalousBursts[]` | array | Ventanas de tiempo detectadas con tasa de reclamos mucho mayor de lo esperado |

---

## Listas de Entidades

Cada uno de estos endpoints devuelve una lista simple para poblar los dropdowns de la UI. La forma de respuesta es idéntica por tipo de entidad.

### 38. Listar Abogados

**Endpoint:** `GET /attorneys`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "attorneys": [
    {"id": "atty-1", "name": "Attorney 0"},
    {"id": "atty-2", "name": "Attorney 1"}
  ]
}
```

---

### 39. Listar Testigos

**Endpoint:** `GET /witnesses`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "witnesses": [
    {"id": "wit-1", "name": "Witness 0"}
  ]
}
```

---

### 40. Listar Pasajeros

**Endpoint:** `GET /passengers`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "passengers": [
    {"id": "pas-1", "name": "Passenger abc12345"},
    {"id": "pas-2", "name": "Serial Jump-in 9f25c880"}
  ]
}
```

---

### 41. Listar Empresas de Grúa

**Endpoint:** `GET /tow-companies`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "towCompanies": [
    {"id": "tow-1", "name": "Tow Company 0"}
  ]
}
```

---

### 42. Listar Proveedores Médicos

**Endpoint:** `GET /medical-providers`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "medicalProviders": [
    {"id": "prov-1", "name": "Dr. Provider 0"}
  ]
}
```

---

### 43. Listar Talleres

**Endpoint:** `GET /repair-shops`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "repairShops": [
    {"id": "shop-1", "name": "Repair Shop 0"}
  ]
}
```

---

### 44. Listar Vehículos

**Endpoint:** `GET /vehicles`

**Autenticación:** Bearer JWT

**Ejemplo de Respuesta:**

```json
{
  "vehicles": [
    {"id": "veh-1", "vin": "VIN0000000000", "make": "Toyota", "year": 2020}
  ]
}
```

---

## Límites de Tasa

Todos los endpoints están protegidos por AWS WAF con:

- **Límite de tasa global:** 2,000 solicitudes por ventana de 5 minutos, por IP origen
- **Detección de bots:** Solicitudes sin encabezado `User-Agent` son bloqueadas
- **Reglas administradas OWASP Top 10:** Inyección SQL, XSS y otros ataques comunes
- **Límites de tamaño de solicitud:** Cuerpos POST > 8 KB son rechazados

Exceder el límite de tasa devuelve un `403 Forbidden` con un mensaje de respuesta de WAF.

## Mejores Prácticas

- **Reutilice JWTs entre solicitudes.** La emisión de tokens es costosa; almacene en caché el token en su cliente durante su vigencia de 1 hora.
- **Refresque proactivamente.** Llame a `POST /auth/refresh` al ~90% de la vigencia del token en lugar de esperar un `401`.
- **Respete la paginación.** Los endpoints de grafo limitan el número de anillos/comunidades devueltas por rendimiento. Si necesita el dataset completo para analítica, consulte el clúster Neptune subyacente directamente o solicite una ejecución de exportación Step Functions.
- **Trate los valores fraudScore como probabilidades.** No son clasificadores calibrados; úselos como señal de ranking.
- **No asuma que `mlRiskScore` > 0.** Si el entrenamiento de Neptune ML aún está en progreso (primeras 1–2 horas después del despliegue), los endpoints ML se degradan elegantemente a heurísticas y devuelven 0 o valores de fallback.
- **Los clientes navegador deben enviar `credentials: 'include'`** para que la ruta de autenticación por cookie `httpOnly` funcione. La configuración CORS de la API lo requiere.

## Soporte

- **Solución de problemas:** revise los logs de CloudWatch bajo `/aws/lambda/auto-insurance-fraud-detect-FraudDetectionFunction-*`
- **Logs de WAF:** `/aws/wafv2/auto-insurance-fraud-detection-WAF`
- **Logs de API Gateway:** `/aws/apigateway/auto-insurance-fraud-detection-API`
- **Pipeline Neptune ML:** consola Step Functions → `auto-insurance-fraud-detection-MLPipelineStack-*-MLPipeline`
- **Consultas de muestra:** vea [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md)
- **Código del frontend:** vea [frontend/README.md](frontend/README.md)
