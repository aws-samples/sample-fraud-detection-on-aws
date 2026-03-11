[![en](https://img.shields.io/badge/lang-en-blue.svg)](API_DOCUMENTATION.md)
[![es-sp](https://img.shields.io/badge/lang-es--sp-green.svg)](API_DOCUMENTATION.es-sp.md)

# Documentação da API de Detecção de Fraude em Seguros de Automóveis - Amazon Neptune ML

Referência completa para todos os 22 endpoints de detecção de fraude.

## Índice

- [Autenticação](#autenticação)
- [Gestão de Sinistros (6 endpoints)](#gestão-de-sinistros)
- [Padrões de Fraude (4 endpoints)](#padrões-de-fraude)
- [Redes de Fraude (4 endpoints)](#redes-de-fraude)
- [Análise (4 endpoints)](#análise)
- [Análise de Entidades (3 endpoints)](#análise-de-entidades)
- [Tratamento de Erros](#tratamento-de-erros)

## Autenticação

Todos os endpoints requerem autenticação JWT via Cognito.

### Obter Token de Autenticação

```bash
# Criar usuário e obter token
./scripts/authenticate.sh -u usuario@empresa.com

# Usar token nas requisições
export AUTH_TOKEN=$(cat .auth-token)
curl -H "Authorization: Bearer $AUTH_TOKEN" https://API_ENDPOINT/prod/endpoint
```

**Validade do Token:**
- Token ID: 1 hora
- Token de Acesso: 1 hora
- Token de Atualização: 30 dias

---

## Gestão de Sinistros

### 1. Enviar Sinistro

Enviar um novo sinistro de seguro com detecção de fraude em tempo real.

**Endpoint:** `POST /claims`

**Corpo da Requisição:**
```json
{
  "claimAmount": 8500.00,
  "claimantId": "claimant-12345",
  "vehicleId": "vehicle-67890",
  "repairShopId": "shop-abc123"
}
```

**Resposta:**
```json
{
  "claimId": "claim-uuid",
  "fraudScore": 0.85,
  "status": "pending",
  "riskLevel": "high",
  "timestamp": 1704067200
}
```

**Detecção de Fraude:**
- Usa Neptune ML para previsão em tempo real
- Analisa histórico de fraude da oficina
- Verifica padrões de sinistros do reclamante
- Detecta anomalias em valores

---

### 2. Obter Detalhes do Sinistro

Recuperar informações detalhadas sobre um sinistro específico.

**Endpoint:** `GET /claims/{claim_id}`

**Resposta:**
```json
{
  "claimId": "claim-12345",
  "amount": 8500.00,
  "status": "approved",
  "fraudScore": 0.45,
  "timestamp": 1704067200,
  "claimant": {
    "id": "claimant-67890",
    "name": "João Silva"
  },
  "vehicle": {
    "id": "vehicle-abc",
    "vin": "VIN1234567890"
  },
  "repairShop": {
    "id": "shop-xyz",
    "name": "Oficina de Reparos"
  }
}
```

---

### 3. Obter Histórico de Sinistros do Reclamante

Recuperar todos os sinistros apresentados por um reclamante específico.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Resposta:**
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

### 4. Obter Pontuação de Risco do Reclamante

Obter avaliação de risco impulsionada por ML para um reclamante.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Resposta:**
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
  "recommendation": "Revisão aprimorada necessária"
}
```

**Requer:** Treinamento do Neptune ML concluído

---

### 5. Analisar Velocidade de Sinistros

Analisar com que frequência um reclamante apresenta sinistros.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Resposta:**
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

**Algoritmo:** Detecção de padrões de séries temporais

---

### 6. Análise Abrangente de Fraude

Análise profunda mostrando todos os indicadores de fraude para um reclamante.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Resposta:**
```json
{
  "claimantId": "claimant-12345",
  "averageFraudScore": 0.72,
  "totalClaims": 6,
  "repairShops": [
    {
      "shopId": "shop-001",
      "name": "Reparos Rápidos",
      "totalClaims": 45,
      "fraudRate": 0.68
    }
  ],
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "Maria Santos",
      "totalAccidentsWitnessed": 12,
      "isProfessional": true
    }
  ]
}
```

---

## Padrões de Fraude

### 7. Detectar Anéis de Colisão

Identificar 6 tipos de padrões de fraude de anéis de colisão.

**Endpoint:** `GET /fraud-patterns/collision-rings`

**Resposta:**
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
1. **Acidentes Simulados** - Veículos/oficinas/testemunhas compartilhados
2. **Swoop & Squat** - Manobras de colisão traseira
3. **Passageiros Falsos** - Pessoas fingindo lesões
4. **Colisões Fictícias** - Relatórios policiais não verificados
5. **Advogados Corruptos** - Direcionando clientes para anéis de fraude
6. **Empresas de Reboque Corruptas** - Direcionando vítimas para oficinas fraudulentas

**Algoritmo:** Percurso de grafos multi-salto com correspondência de padrões

---

### 8. Encontrar Testemunhas Profissionais

Identificar testemunhas que aparecem em múltiplos sinistros não relacionados.

**Endpoint:** `GET /fraud-patterns/professional-witnesses`

**Resposta:**
```json
{
  "totalSuspiciousWitnesses": 8,
  "witnesses": [
    {
      "witnessId": "witness-001",
      "name": "João Costa",
      "claimCount": 15,
      "isProfessional": true,
      "suspicionLevel": "high"
    }
  ]
}
```

**Algoritmo:** Análise de frequência de testemunhas

---

### 9. Detectar Indicadores de Conluio

Encontrar conluio tripartite entre reclamantes, veículos e oficinas.

**Endpoint:** `GET /fraud-patterns/collusion-indicators`

**Resposta:**
```json
{
  "algorithm": "Contagem de Triângulos",
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

**Algoritmo:** Contagem de triângulos em grafo

---

### 10. Análise de Padrões Entre Sinistros

Identificar reclamantes que sempre usam as mesmas entidades.

**Endpoint:** `GET /fraud-patterns/cross-claim-patterns`

**Resposta:**
```json
{
  "algorithm": "Análise de Padrões Entre Sinistros + Neptune ML",
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

**Algoritmo:** Pontuação de diversidade + Neptune ML

---

## Redes de Fraude

### 11. Encontrar Reclamantes Influentes

Identificar centros de rede que podem estar organizando anéis de fraude.

**Endpoint:** `GET /fraud-networks/influential-claimants`

**Resposta:**
```json
{
  "algorithm": "Análise de Conexão estilo PageRank",
  "topInfluencers": [
    {
      "claimantId": "claimant-123",
      "name": "João Silva",
      "claimCount": 12,
      "connectionScore": 45,
      "influenceLevel": "critical"
    }
  ]
}
```

**Algoritmo:** Análise de centralidade estilo PageRank

---

### 12. Detectar Anéis de Fraude Organizados

Encontrar grupos densamente conectados trabalhando juntos.

**Endpoint:** `GET /fraud-networks/organized-rings`

**Resposta:**
```json
{
  "algorithm": "Detecção de Comunidades (análise de vizinhança de 2 saltos)",
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

**Algoritmo:** Detecção de comunidades via percurso de 2 saltos

---

### 13. Identificar Oficinas Centro de Fraude

Encontrar oficinas que conectam múltiplas redes de fraude.

**Endpoint:** `GET /repair-shops/fraud-hubs`

**Resposta:**
```json
{
  "algorithm": "Centralidade de Intermediação",
  "topCentralRepairShops": [
    {
      "repairShopId": "shop-001",
      "name": "Reparos Rápidos",
      "uniqueClaimants": 45,
      "totalClaims": 120,
      "centralityScore": 78,
      "bridgingRole": "critical"
    }
  ]
}
```

**Algoritmo:** Centralidade de intermediação

---

### 14. Mapear Conexões de Fraudadores

Encontrar caminhos mais curtos entre suspeitos de fraude.

**Endpoint:** `GET /fraud-networks/connections`

**Resposta:**
```json
{
  "algorithm": "Caminho Mais Curto",
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

**Algoritmo:** Busca de caminho mais curto

---

### 15. Encontrar Anéis de Fraude Isolados

Identificar operações de fraude independentes.

**Endpoint:** `GET /fraud-networks/isolated-rings`

**Resposta:**
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

**Algoritmo:** Análise de componentes conectados

---

## Análise

### 16. Obter Tendências de Fraude

Estatísticas de fraude de alto nível e tendências.

**Endpoint:** `GET /analytics/fraud-trends`

**Resposta:**
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

### 17. Detectar Pontos Quentes Geográficos

Encontrar áreas com alta concentração de fraude.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Resposta:**
```json
{
  "algorithm": "Agrupamento Geográfico (aproximação K-means)",
  "totalHotspots": 8,
  "criticalHotspots": [
    {
      "repairShopId": "shop-001",
      "name": "Oficina Centro",
      "claimVolume": 45,
      "averageFraudScore": 0.82,
      "hotspotLevel": "critical"
    }
  ]
}
```

**Algoritmo:** Agrupamento geográfico

---

### 18. Detectar Anomalias em Valores de Sinistros

Encontrar sinistros com valores incomumente altos ou baixos.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Resposta:**
```json
{
  "algorithm": "Detecção de Anomalias Estatísticas + Neptune ML",
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

**Algoritmo:** Análise de pontuação Z + Neptune ML

**Requer:** Treinamento do Neptune ML concluído

---

### 19. Analisar Padrões Temporais

Detectar padrões de fraude baseados em tempo.

**Endpoint:** `GET /analytics/temporal-patterns`

**Resposta:**
```json
{
  "algorithm": "Análise de Padrões Temporais",
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

**Algoritmo:** Análise temporal

---

## Análise de Entidades

### 20. Obter Estatísticas da Oficina

Estatísticas detalhadas de fraude para uma oficina de reparos.

**Endpoint:** `GET /repair-shops/{shop_id}/statistics`

**Resposta:**
```json
{
  "repairShopId": "shop-001",
  "name": "Reparos Rápidos",
  "totalClaims": 120,
  "highFraudClaims": 85,
  "fraudRate": 0.708,
  "averageClaimAmount": 7500.00,
  "uniqueClaimants": 45
}
```

---

### 21. Analisar Histórico de Fraude do Veículo

Obter histórico de fraude e avaliação de risco para um veículo.

**Endpoint:** `GET /vehicles/{vehicle_id}/fraud-history`

**Resposta:**
```json
{
  "vehicleId": "vehicle-123",
  "vin": "VIN1234567890",
  "totalClaims": 8,
  "highFraudClaims": 6,
  "fraudRate": 0.75,
  "mlRiskScore": 0.88,
  "riskLevel": "high",
  "recommendation": "Inspeção aprimorada necessária"
}
```

**Requer:** Treinamento do Neptune ML concluído

---

### 22. Analisar Fraude de Provedor Médico

Avaliar padrões de fraude para provedores médicos.

**Endpoint:** `GET /medical-providers/{provider_id}/fraud-analysis`

**Resposta:**
```json
{
  "providerId": "provider-001",
  "name": "Clínica Dr. Silva",
  "totalClaims": 65,
  "highFraudClaims": 48,
  "fraudRate": 0.738,
  "mlFraudScore": 0.85,
  "riskLevel": "high"
}
```

**Requer:** Treinamento do Neptune ML concluído

---

## Tratamento de Erros

### Códigos de Status HTTP

- `200` - Sucesso
- `400` - Requisição Incorreta (parâmetros inválidos)
- `401` - Não Autorizado (token ausente ou inválido)
- `404` - Não Encontrado (a entidade não existe)
- `429` - Muitas Requisições (limite de taxa excedido)
- `500` - Erro Interno do Servidor

### Formato de Resposta de Erro

```json
{
  "error": "Descrição da mensagem de erro",
  "code": "CÓDIGO_ERRO",
  "timestamp": 1704067200
}
```

---

## Limites de Taxa

**Proteção WAF:**
- 2.000 requisições por 5 minutos por IP
- Bloqueio automático para padrões suspeitos
- Proteção OWASP Top 10 habilitada

---

## Melhores Práticas

1. **Cachear tokens** - Reutilizar tokens durante seu período de validade de 1 hora
2. **Lidar com limites de taxa** - Implementar recuo exponencial
3. **Agrupar requisições** - Agrupar consultas relacionadas quando possível
4. **Monitorar status de ML** - Verificar se o treinamento de ML está completo antes de usar endpoints de ML
5. **Tratamento de erros** - Sempre verificar códigos de status de resposta

---

## Suporte

Para problemas ou dúvidas:
- Consulte [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) para exemplos de consultas
- Revise os logs do CloudWatch: `/aws/apigateway/auto-insurance-fraud-detection-API`
- Verifique os logs do WAF: `/aws/wafv2/auto-insurance-fraud-detection-WAF`
