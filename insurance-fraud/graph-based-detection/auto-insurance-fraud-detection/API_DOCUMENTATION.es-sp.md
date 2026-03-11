[![en](https://img.shields.io/badge/lang-en-blue.svg)](API_DOCUMENTATION.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](API_DOCUMENTATION.pt-br.md)

# Documentación de la API de Detección de Fraude en Seguros de Automóviles - Amazon Neptune ML

Referencia completa para los 22 endpoints de detección de fraude.

## Tabla de Contenidos

- [Autenticación](#autenticación)
- [Gestión de Reclamaciones (6 endpoints)](#gestión-de-reclamaciones)
- [Patrones de Fraude (4 endpoints)](#patrones-de-fraude)
- [Redes de Fraude (4 endpoints)](#redes-de-fraude)
- [Analítica (4 endpoints)](#analítica)
- [Análisis de Entidades (3 endpoints)](#análisis-de-entidades)
- [Manejo de Errores](#manejo-de-errores)

## Autenticación

Todos los endpoints requieren autenticación JWT vía Cognito.

### Obtener Token de Autenticación

```bash
# Crear usuario y obtener token
./scripts/authenticate.sh -u usuario@empresa.com

# Usar token en las solicitudes
export AUTH_TOKEN=$(cat .auth-token)
curl -H "Authorization: Bearer $AUTH_TOKEN" https://API_ENDPOINT/prod/endpoint
```

**Validez del Token:**
- Token ID: 1 hora
- Token de Acceso: 1 hora
- Token de Actualización: 30 días

---

## Gestión de Reclamaciones

### 1. Enviar Reclamación

Enviar una nueva reclamación de seguro con detección de fraude en tiempo real.

**Endpoint:** `POST /claims`

**Cuerpo de la Solicitud:**
```json
{
  "claimAmount": 8500.00,
  "claimantId": "claimant-12345",
  "vehicleId": "vehicle-67890",
  "repairShopId": "shop-abc123"
}
```

**Respuesta:**
```json
{
  "claimId": "claim-uuid",
  "fraudScore": 0.85,
  "status": "pending",
  "riskLevel": "high",
  "timestamp": 1704067200
}
```

**Detección de Fraude:**
- Usa Neptune ML para predicción en tiempo real
- Analiza historial de fraude del taller
- Verifica patrones de reclamaciones del reclamante
- Detecta anomalías en montos

---

### 2. Obtener Detalles de Reclamación

Recuperar información detallada sobre una reclamación específica.

**Endpoint:** `GET /claims/{claim_id}`

**Respuesta:**
```json
{
  "claimId": "claim-12345",
  "amount": 8500.00,
  "status": "approved",
  "fraudScore": 0.45,
  "timestamp": 1704067200,
  "claimant": {
    "id": "claimant-67890",
    "name": "Juan Pérez"
  },
  "vehicle": {
    "id": "vehicle-abc",
    "vin": "VIN1234567890"
  },
  "repairShop": {
    "id": "shop-xyz",
    "name": "Taller de Reparación"
  }
}
```

---

### 3. Obtener Historial de Reclamaciones del Reclamante

Recuperar todas las reclamaciones presentadas por un reclamante específico.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Respuesta:**
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
    }
  ]
}
```

---

### 4. Obtener Puntuación de Riesgo del Reclamante

Obtener evaluación de riesgo impulsada por ML para un reclamante.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Respuesta:**
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
  "recommendation": "Revisión mejorada requerida"
}
```

**Requiere:** Entrenamiento de Neptune ML completado

---

### 5. Analizar Velocidad de Reclamaciones

Analizar con qué frecuencia un reclamante presenta reclamaciones.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Respuesta:**
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

**Algoritmo:** Detección de patrones de series temporales

---

### 6. Análisis Integral de Fraude

Análisis profundo que muestra todos los indicadores de fraude para un reclamante.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Respuesta:**
```json
{
  "claimantId": "claimant-12345",
  "averageFraudScore": 0.72,
  "totalClaims": 6,
  "repairShops": [
    {
      "shopId": "shop-001",
      "name": "Reparación Rápida",
      "totalClaims": 45,
      "fraudRate": 0.68
    }
  ],
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "María García",
      "totalAccidentsWitnessed": 12,
      "isProfessional": true
    }
  ]
}
```

---

## Patrones de Fraude

### 7. Detectar Anillos de Colisión

Identificar 6 tipos de patrones de fraude de anillos de colisión.

**Endpoint:** `GET /fraud-patterns/collision-rings`

**Respuesta:**
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
  }
}
```

**Tipos de Fraude Detectados:**
1. **Accidentes Simulados** - Vehículos/talleres/testigos compartidos
2. **Swoop & Squat** - Maniobras de colisión trasera
3. **Pasajeros Falsos** - Personas que fingen lesiones
4. **Colisiones Ficticias** - Informes policiales no verificados
5. **Abogados Corruptos** - Dirigiendo clientes a anillos de fraude
6. **Empresas de Grúas Corruptas** - Dirigiendo víctimas a talleres fraudulentos

**Algoritmo:** Recorrido de grafos multi-salto con coincidencia de patrones

---

### 8. Encontrar Testigos Profesionales

Identificar testigos que aparecen en múltiples reclamaciones no relacionadas.

**Endpoint:** `GET /fraud-patterns/professional-witnesses`

**Respuesta:**
```json
{
  "totalSuspiciousWitnesses": 8,
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "Juan López",
      "claimCount": 15,
      "isProfessional": true,
      "suspicionLevel": "high"
    }
  ]
}
```

**Algoritmo:** Análisis de frecuencia de testigos

---

### 9. Detectar Indicadores de Colusión

Encontrar colusión tripartita entre reclamantes, vehículos y talleres.

**Endpoint:** `GET /fraud-patterns/collusion-indicators`

**Respuesta:**
```json
{
  "algorithm": "Conteo de Triángulos",
  "totalTrianglesDetected": 45,
  "claimantsInTriangles": 12,
  "topCollusionRisks": [
    {
      "claimantId": "claimant-123",
      "triangleCount": 8,
      "collusionRisk": "high"
    }
  ]
}
```

**Algoritmo:** Conteo de triángulos en grafo

---

### 10. Análisis de Patrones Entre Reclamaciones

Identificar reclamantes que siempre usan las mismas entidades.

**Endpoint:** `GET /fraud-patterns/cross-claim-patterns`

**Respuesta:**
```json
{
  "algorithm": "Análisis de Patrones Entre Reclamaciones + Neptune ML",
  "totalSuspiciousPatterns": 15,
  "highRiskPatterns": [
    {
      "claimantId": "claimant-123",
      "totalClaims": 6,
      "uniqueRepairShops": 1,
      "shopDiversity": 0.167,
      "mlPatternScore": 0.89,
      "suspicionLevel": "high"
    }
  ]
}
```

**Algoritmo:** Puntuación de diversidad + Neptune ML

---

## Redes de Fraude

### 11. Encontrar Reclamantes Influyentes

Identificar centros de red que pueden estar organizando anillos de fraude.

**Endpoint:** `GET /fraud-networks/influential-claimants`

**Respuesta:**
```json
{
  "algorithm": "Análisis de Conexión estilo PageRank",
  "topInfluencers": [
    {
      "claimantId": "claimant-123",
      "name": "Juan Pérez",
      "claimCount": 12,
      "connectionScore": 45,
      "influenceLevel": "critical"
    }
  ]
}
```

**Algoritmo:** Análisis de centralidad estilo PageRank

---

### 12. Detectar Anillos de Fraude Organizados

Encontrar grupos densamente conectados trabajando juntos.

**Endpoint:** `GET /fraud-networks/organized-rings`

**Respuesta:**
```json
{
  "algorithm": "Detección de Comunidades (análisis de vecindario de 2 saltos)",
  "totalCommunities": 8,
  "suspiciousCommunities": [
    {
      "seedClaimant": "claimant-123",
      "communitySize": 7,
      "averageFraudScore": 0.82,
      "riskLevel": "high"
    }
  ]
}
```

**Algoritmo:** Detección de comunidades vía recorrido de 2 saltos

---

### 13. Identificar Talleres Centro de Fraude

Encontrar talleres que conectan múltiples redes de fraude.

**Endpoint:** `GET /repair-shops/fraud-hubs`

**Respuesta:**
```json
{
  "algorithm": "Centralidad de Intermediación",
  "topCentralRepairShops": [
    {
      "repairShopId": "shop-001",
      "name": "Reparación Rápida",
      "uniqueClaimants": 45,
      "totalClaims": 120,
      "centralityScore": 78,
      "bridgingRole": "critical"
    }
  ]
}
```

**Algoritmo:** Centralidad de intermediación

---

### 14. Mapear Conexiones de Estafadores

Encontrar rutas más cortas entre sospechosos de fraude.

**Endpoint:** `GET /fraud-networks/connections`

**Respuesta:**
```json
{
  "algorithm": "Ruta Más Corta",
  "fraudNetworkConnections": [
    {
      "source": "claimant-123",
      "target": "claimant-456",
      "pathLength": 3,
      "connectionType": "direct"
    }
  ]
}
```

**Algoritmo:** Búsqueda de ruta más corta

---

### 15. Encontrar Anillos de Fraude Aislados

Identificar operaciones de fraude independientes.

**Endpoint:** `GET /fraud-networks/isolated-rings`

**Respuesta:**
```json
{
  "algorithm": "Componentes Conectados",
  "totalComponents": 12,
  "largestComponent": {
    "componentId": 1,
    "size": 15,
    "averageFraudScore": 0.78,
    "riskLevel": "high"
  }
}
```

**Algoritmo:** Análisis de componentes conectados

---

## Analítica

### 16. Obtener Tendencias de Fraude

Estadísticas de fraude de alto nivel y tendencias.

**Endpoint:** `GET /analytics/fraud-trends`

**Respuesta:**
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

### 17. Detectar Puntos Calientes Geográficos

Encontrar áreas con alta concentración de fraude.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Respuesta:**
```json
{
  "algorithm": "Agrupamiento Geográfico (aproximación K-means)",
  "totalHotspots": 8,
  "criticalHotspots": [
    {
      "repairShopId": "shop-001",
      "name": "Taller Centro",
      "claimVolume": 45,
      "averageFraudScore": 0.82,
      "hotspotLevel": "critical"
    }
  ]
}
```

**Algoritmo:** Agrupamiento geográfico

---

### 18. Detectar Anomalías en Montos de Reclamaciones

Encontrar reclamaciones con montos inusualmente altos o bajos.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Respuesta:**
```json
{
  "algorithm": "Detección de Anomalías Estadísticas + Neptune ML",
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
      "anomalyType": "unusually_high",
      "riskLevel": "high"
    }
  ]
}
```

**Algoritmo:** Análisis de puntuación Z + Neptune ML

**Requiere:** Entrenamiento de Neptune ML completado

---

### 19. Analizar Patrones Temporales

Detectar patrones de fraude basados en tiempo.

**Endpoint:** `GET /analytics/temporal-patterns`

**Respuesta:**
```json
{
  "algorithm": "Análisis de Patrones Temporales",
  "hourlyPatterns": [
    {
      "hour": 14,
      "claimCount": 25,
      "averageFraudScore": 0.78,
      "suspicionLevel": "high"
    }
  ],
  "suspiciousHours": [14, 15, 22]
}
```

**Algoritmo:** Análisis temporal

---

## Análisis de Entidades

### 20. Obtener Estadísticas del Taller

Estadísticas detalladas de fraude para un taller de reparación.

**Endpoint:** `GET /repair-shops/{shop_id}/statistics`

**Respuesta:**
```json
{
  "repairShopId": "shop-001",
  "name": "Reparación Rápida",
  "totalClaims": 120,
  "highFraudClaims": 85,
  "fraudRate": 0.708,
  "averageClaimAmount": 7500.00,
  "uniqueClaimants": 45
}
```

---

### 21. Analizar Historial de Fraude del Vehículo

Obtener historial de fraude y evaluación de riesgo para un vehículo.

**Endpoint:** `GET /vehicles/{vehicle_id}/fraud-history`

**Respuesta:**
```json
{
  "vehicleId": "vehicle-123",
  "vin": "VIN1234567890",
  "totalClaims": 8,
  "highFraudClaims": 6,
  "fraudRate": 0.75,
  "mlRiskScore": 0.88,
  "riskLevel": "high",
  "recommendation": "Inspección mejorada requerida"
}
```

**Requiere:** Entrenamiento de Neptune ML completado

---

### 22. Analizar Fraude de Proveedor Médico

Evaluar patrones de fraude para proveedores médicos.

**Endpoint:** `GET /medical-providers/{provider_id}/fraud-analysis`

**Respuesta:**
```json
{
  "providerId": "provider-001",
  "name": "Clínica Dr. García",
  "totalClaims": 65,
  "highFraudClaims": 48,
  "fraudRate": 0.738,
  "mlFraudScore": 0.85,
  "riskLevel": "high"
}
```

**Requiere:** Entrenamiento de Neptune ML completado

---

## Manejo de Errores

### Códigos de Estado HTTP

- `200` - Éxito
- `400` - Solicitud Incorrecta (parámetros inválidos)
- `401` - No Autorizado (token faltante o inválido)
- `404` - No Encontrado (la entidad no existe)
- `429` - Demasiadas Solicitudes (límite de tasa excedido)
- `500` - Error Interno del Servidor

### Formato de Respuesta de Error

```json
{
  "error": "Descripción del mensaje de error",
  "code": "CÓDIGO_ERROR",
  "timestamp": 1704067200
}
```

---

## Límites de Tasa

**Protección WAF:**
- 2,000 solicitudes por 5 minutos por IP
- Bloqueo automático para patrones sospechosos
- Protección OWASP Top 10 habilitada

---

## Mejores Prácticas

1. **Cachear tokens** - Reutilizar tokens durante su período de validez de 1 hora
2. **Manejar límites de tasa** - Implementar retroceso exponencial
3. **Agrupar solicitudes** - Agrupar consultas relacionadas cuando sea posible
4. **Monitorear estado de ML** - Verificar si el entrenamiento de ML está completo antes de usar endpoints de ML
5. **Manejo de errores** - Siempre verificar códigos de estado de respuesta

---

## Soporte

Para problemas o preguntas:
- Consulte [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) para ejemplos de consultas
- Revise los logs de CloudWatch: `/aws/apigateway/auto-insurance-fraud-detection-API`
- Verifique los logs de WAF: `/aws/wafv2/auto-insurance-fraud-detection-WAF`
