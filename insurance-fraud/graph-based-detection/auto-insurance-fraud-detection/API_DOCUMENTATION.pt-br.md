[![en](https://img.shields.io/badge/lang-en-blue.svg)](API_DOCUMENTATION.md)
[![es-sp](https://img.shields.io/badge/lang-es--sp-green.svg)](API_DOCUMENTATION.es-sp.md)

# Documentação da API de Detecção de Fraude em Seguros de Automóveis - Amazon Neptune ML

Referência completa para os 44 endpoints da API de detecção de fraude.

## Índice

- [Informações Gerais](#informações-gerais)
  - [URL Base](#url-base)
  - [Autenticação](#autenticação)
  - [Envelope de Resposta](#envelope-de-resposta)
  - [Formato de Resposta de Grafo](#formato-de-resposta-de-grafo)
  - [Tratamento de Erros](#tratamento-de-erros)
- [Autenticação (3 endpoints)](#endpoints-de-autenticação)
  - [1. Login](#1-login)
  - [2. Logout](#2-logout)
  - [3. Renovar Token](#3-renovar-token)
- [Sinistros (4 endpoints)](#sinistros)
  - [4. Enviar Sinistro](#4-enviar-sinistro)
  - [5. Listar Sinistros](#5-listar-sinistros)
  - [6. Obter Detalhes do Sinistro](#6-obter-detalhes-do-sinistro)
  - [7. Obter Grafo de Vizinhança do Sinistro](#7-obter-grafo-de-vizinhança-do-sinistro)
- [Segurados (6 endpoints)](#segurados)
  - [8. Listar Segurados](#8-listar-segurados)
  - [9. Obter Detalhes do Segurado](#9-obter-detalhes-do-segurado)
  - [10. Obter Histórico de Sinistros do Segurado](#10-obter-histórico-de-sinistros-do-segurado)
  - [11. Obter Pontuação de Risco do Segurado](#11-obter-pontuação-de-risco-do-segurado)
  - [12. Analisar Velocidade de Sinistros](#12-analisar-velocidade-de-sinistros)
  - [13. Análise Abrangente de Fraude](#13-análise-abrangente-de-fraude)
- [Anéis de Colisão (6 endpoints)](#anéis-de-colisão)
  - [14. Acidentes Forjados](#14-acidentes-forjados)
  - [15. Swoop & Squat](#15-swoop--squat)
  - [16. Passageiros Plantados](#16-passageiros-plantados)
  - [17. Colisões de Papel](#17-colisões-de-papel)
  - [18. Advogados Corruptos](#18-advogados-corruptos)
  - [19. Empresas de Reboque Corruptas](#19-empresas-de-reboque-corruptas)
- [Fraude de Rede (8 endpoints)](#fraude-de-rede)
  - [20. Testemunhas Profissionais](#20-testemunhas-profissionais)
  - [21. Anéis Organizados](#21-anéis-organizados)
  - [22. Centros de Fraude](#22-centros-de-fraude)
  - [23. Indicadores de Conluio](#23-indicadores-de-conluio)
  - [24. Anéis Isolados](#24-anéis-isolados)
  - [25. Padrões Entre Sinistros](#25-padrões-entre-sinistros)
  - [26. Vizinhança do Provedor Médico](#26-vizinhança-do-provedor-médico)
  - [27. Análise de Fraude do Provedor Médico](#27-análise-de-fraude-do-provedor-médico)
- [Análise Avançada (2 endpoints)](#análise-avançada)
  - [28. Segurados Influentes](#28-segurados-influentes)
  - [29. Conexões entre Fraudadores](#29-conexões-entre-fraudadores)
- [Consulta de Entidades (4 endpoints)](#consulta-de-entidades)
  - [30. Vizinhança da Oficina](#30-vizinhança-da-oficina)
  - [31. Estatísticas da Oficina](#31-estatísticas-da-oficina)
  - [32. Vizinhança do Veículo](#32-vizinhança-do-veículo)
  - [33. Histórico de Fraude do Veículo](#33-histórico-de-fraude-do-veículo)
- [Analítica (4 endpoints)](#analítica)
  - [34. Tendências de Fraude](#34-tendências-de-fraude)
  - [35. Pontos Quentes Geográficos](#35-pontos-quentes-geográficos)
  - [36. Anomalias em Valores de Sinistros](#36-anomalias-em-valores-de-sinistros)
  - [37. Padrões Temporais](#37-padrões-temporais)
- [Listas de Entidades (7 endpoints)](#listas-de-entidades)
  - [38. Listar Advogados](#38-listar-advogados)
  - [39. Listar Testemunhas](#39-listar-testemunhas)
  - [40. Listar Passageiros](#40-listar-passageiros)
  - [41. Listar Empresas de Reboque](#41-listar-empresas-de-reboque)
  - [42. Listar Provedores Médicos](#42-listar-provedores-médicos)
  - [43. Listar Oficinas](#43-listar-oficinas)
  - [44. Listar Veículos](#44-listar-veículos)
- [Limites de Taxa](#limites-de-taxa)
- [Boas Práticas](#boas-práticas)
- [Suporte](#suporte)

---

## Informações Gerais

### URL Base

Todos os endpoints são servidos a partir da URL do API Gateway emitida no momento do deploy, com o formato:

```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

Você pode recuperar o valor exato a partir da saída do deploy ou do CloudFormation:

```bash
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### Autenticação

Todos os endpoints exceto as três operações `/auth/*` requerem uma sessão válida. A autenticação é realizada enviando um JSON Web Token (JWT) emitido pelo Amazon Cognito User Pool implantado com a solução em um **cookie de sessão `httpOnly`** chamado `__Host-fraud_detection_token`. O cookie é definido por `POST /auth/login` e é marcado como `HttpOnly; Secure; SameSite=None` para que não possa ser acessado por JavaScript executando no navegador (hardening contra XSS).

**Clientes de navegador** não precisam manipular o cookie — ele flui automaticamente em cada requisição subsequente quando `credentials: 'include'` é usado.

**Clientes não-navegador** (curl, Python, etc.) devem salvar o cookie após o login e enviá-lo em cada requisição:

```
Cookie: __Host-fraud_detection_token=eyJraWQiOi...
```

**Faça login via o script auxiliar (salva o cookie em `.auth-cookie`):**

```bash
./scripts/authenticate.sh -u user@company.com -p YourPassword123! --token-only
```

**Vigência dos tokens:**

| Token | Validade |
|-------|----------|
| ID token | 1 hora |
| Access token | 1 hora |
| Refresh token | 30 dias |

Tokens próximos do vencimento devem ser renovados via `POST /auth/refresh` (endpoint 3) em vez de reautenticar.

### Envelope de Resposta

Respostas bem-sucedidas são retornadas como JSON com status HTTP `200`. Respostas de erro seguem a mesma estrutura JSON mas com status `4xx`/`5xx` e um campo `error`:

```json
{
  "error": "Claimant not found"
}
```

### Formato de Resposta de Grafo

Endpoints que retornam um grafo (a maioria dos endpoints de detecção de fraude) seguem um envelope comum `{ nodes, edges }`:

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

Endpoints específicos podem adicionar propriedades extras aos nós (p. ex., `staged`, `maneuverType`, `appearances`) — veja o esquema de resposta de cada endpoint para detalhes.

### Tratamento de Erros

| HTTP | Significado | Causa típica |
|------|-------------|--------------|
| `200` | Sucesso | Requisição processada, corpo contém o resultado |
| `400` | Requisição inválida | Corpo JSON mal formado ou campo obrigatório faltando em um `POST` |
| `401` | Não autorizado | JWT ausente, mal formado ou expirado |
| `403` | Proibido | JWT é válido mas WAF bloqueou a requisição (limite de taxa, detecção de bots) ou a rota não existe |
| `404` | Não encontrado | Entidade referenciada (segurado, sinistro, veículo, provedor, oficina) não existe |
| `500` | Erro interno | Exceção de Lambda (p. ex., erro Gremlin inesperado). O corpo da resposta contém `{"error": "...", "message": "..."}` com detalhe |

Todas as respostas de erro incluem cabeçalhos CORS para que sejam corretamente expostas a clientes navegador.

---

## Endpoints de Autenticação

### 1. Login

Troca credenciais por um token JWT.

**Endpoint:** `POST /auth/login`

**Autenticação:** Nenhuma (é assim que você obtém um token)

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `username` | string | Sim | Nome de usuário Cognito (email) |
| `password` | string | Sim | Senha do usuário |

**Exemplo de Requisição:**

```bash
curl -X POST https://YOUR-API/prod/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@company.com","password":"YourPassword123!"}'
```

**Exemplo de Resposta:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "refreshToken": "eyJjdHkiOiJKV1Qi...",
  "expiresIn": 3600
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `token` | string | O ID token. Clientes de navegador podem ignorar este valor — o servidor também define o cookie httpOnly `__Host-fraud_detection_token` automaticamente. Clientes não-navegador podem usar este valor para construir um header `Cookie: __Host-fraud_detection_token=<token>` manualmente |
| `refreshToken` | string | Token de longa duração para usar com `/auth/refresh` |
| `expiresIn` | integer | Segundos até o ID token expirar (sempre 3600) |

**Efeitos Colaterais:** Um cookie `httpOnly` chamado `__Host-fraud_detection_token` é definido na resposta para clientes navegador.

**Erros:**

- `400 Bad Request` — username ou password faltando
- `401 Unauthorized` — credenciais inválidas ou usuário não confirmado

---

### 2. Logout

Invalida a sessão ativa e limpa o cookie.

**Endpoint:** `POST /auth/logout`

**Autenticação:** Bearer JWT

**Corpo da Requisição:** Nenhum

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/auth/logout
```

**Exemplo de Resposta:**

```json
{
  "message": "Logged out successfully"
}
```

**Efeitos Colaterais:** O cookie `__Host-fraud_detection_token` é apagado.

**Erros:**

- `401 Unauthorized` — JWT ausente ou inválido

---

### 3. Renovar Token

Troca um refresh token por um ID token novo.

**Endpoint:** `POST /auth/refresh`

**Autenticação:** Nenhuma (o próprio refresh token é a credencial)

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `refreshToken` | string | Sim | O refresh token emitido previamente por `/auth/login` |

**Exemplo de Requisição:**

```bash
curl -X POST https://YOUR-API/prod/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refreshToken\":\"$REFRESH_TOKEN\"}"
```

**Exemplo de Resposta:**

```json
{
  "token": "eyJraWQiOiJHdVh2...",
  "expiresIn": 3600
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `token` | string | Novo ID token |
| `expiresIn` | integer | Segundos até esse novo token expirar |

**Erros:**

- `400 Bad Request` — `refreshToken` faltando
- `401 Unauthorized` — refresh token expirado ou revogado

---

## Sinistros

### 4. Enviar Sinistro

Envia um novo sinistro de seguro e recebe uma pontuação de fraude em tempo real via Neptune ML.

**Endpoint:** `POST /claims`

**Autenticação:** Bearer JWT (mais assinatura HMAC opcional para parceiros de integração — veja os cabeçalhos `X-Request-Timestamp` / `X-Request-Signature`)

**Corpo da Requisição:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `claimAmount` | number | Sim | Valor do sinistro em USD |
| `claimantId` | string | Sim | ID do vértice Claimant existente |
| `vehicleId` | string | Sim | ID do vértice Vehicle existente |
| `repairShopId` | string | Não | ID opcional de RepairShop |
| `witnessId` | string | Não | ID opcional de Witness |
| `status` | string | Não | Status inicial (padrão: `approved`) |

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie -X POST https://YOUR-API/prod/claims \
  -H "Content-Type: application/json" \
  -d '{"claimAmount":12500,"claimantId":"claimant-abc","vehicleId":"vehicle-xyz"}'
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimId` | string | ID do vértice Claim recém-criado |
| `fraudScore` | number (0–1) | Probabilidade de fraude derivada por ML (inferência indutiva via Neptune ML); fallback heurístico se ML estiver indisponível |
| `riskLevel` | string | `low` (< 0.5), `medium` (0.5–0.7), `high` (> 0.7) |
| `message` | string | Status legível para humanos |
| `mlModel` | string | Identificador do modelo |
| `recommendation` | string | Ação sugerida |

**Erros:**

- `400 Bad Request` — falta `claimAmount`, `claimantId` ou `vehicleId`
- `404 Not Found` — segurado ou veículo referenciado não existe
- `500 Internal Server Error` — falha de escrita no Neptune

---

### 5. Listar Sinistros

Listar todos os sinistros no grafo.

**Endpoint:** `GET /claims`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claims
```

**Exemplo de Resposta:**

```json
{
  "claims": [
    {"id": "abc-123", "amount": 8500.00, "date": 1713283200},
    {"id": "def-456", "amount": 3200.50, "date": 1713366000}
  ]
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claims[].id` | string | ID do vértice Claim |
| `claims[].amount` | number | Valor do sinistro em USD |
| `claims[].date` | integer | Timestamp Unix epoch |

**Erros:**

- `401 Unauthorized` — JWT ausente ou inválido

---

### 6. Obter Detalhes do Sinistro

Recupera um único sinistro.

**Endpoint:** `GET /claims/{claim_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| `claim_id` | string | ID do vértice Claim |

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimId` | string | ID do vértice Claim |
| `amount` | number | Valor do sinistro em USD |
| `status` | string | `approved`, `pending`, `rejected` |
| `claimDate` | integer | Unix epoch |
| `isFraud` | boolean | Rótulo de verdade (para dados demo) |
| `fraudScore` | number (0–1) | Pontuação de fraude de ML ou dados armazenados |

**Erros:**

- `404 Not Found` — `claim_id` não está no grafo

---

### 7. Obter Grafo de Vizinhança do Sinistro

Recupera um sinistro junto com sua vizinhança completa — acidente, veículos, passageiros, oficina, testemunhas, segurado e quaisquer provedores médicos ou advogados conectados.

**Endpoint:** `GET /claims/{claim_id}/graph`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claim_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claims/abc-123/graph
```

**Resposta:** Envelope de grafo (veja [Formato de Resposta de Grafo](#formato-de-resposta-de-grafo)). Tipicamente 8–20 nós.

**Esquema de Resposta:**

Envelope de grafo padrão com tipos de nó incluindo `claim`, `accident`, `vehicle`, `repairShop`, `witness`, `claimant`, `passenger`, `medicalProvider`, `attorney`, `towCompany`. Tipos de arestas incluem `filed_claim`, `for_accident`, `involved_vehicle`, `repaired_at`, `witnessed_by`, `passenger_in`, `claimed_injury`, `treated_by`, `represented_by`, `towed_by`.

**Erros:**

- `404 Not Found` — `claim_id` não está no grafo

---

## Segurados

### 8. Listar Segurados

Listar todos os segurados que apresentaram pelo menos um sinistro.

**Endpoint:** `GET /claimants`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie https://YOUR-API/prod/claimants
```

**Exemplo de Resposta:**

```json
{
  "claimants": [
    {"id": "clm-abc", "name": "Claimant 12"},
    {"id": "clm-def", "name": "Claimant 37"}
  ]
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimants[].id` | string | ID do vértice Claimant |
| `claimants[].name` | string | Nome legível |

**Nota:** Segurados com zero arestas `filed_claim` são excluídos — isso é intencional para que os dropdowns da UI (Análise de Fraude, Velocidade de Sinistros, etc.) nunca mostrem entidades que retornariam resultados vazios.

---

### 9. Obter Detalhes do Segurado

Recupera um único segurado.

**Endpoint:** `GET /claimants/{claimant_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc
```

**Exemplo de Resposta:**

```json
{
  "claimantId": "clm-abc",
  "name": "Claimant 12",
  "fraudScore": 0.42
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimantId` | string | ID do vértice Claimant |
| `name` | string | Nome do segurado |
| `fraudScore` | number | Pontuação de fraude em nível de segurado |

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

### 10. Obter Histórico de Sinistros do Segurado

Listar todos os sinistros apresentados por um segurado.

**Endpoint:** `GET /claimants/{claimant_id}/claims`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claims
```

**Exemplo de Resposta:**

```json
{
  "claimantId": "clm-abc",
  "claims": [
    {"claimId": "c1", "amount": 8500.00, "status": "approved", "claimDate": 1713283200, "fraudScore": 0.12},
    {"claimId": "c2", "amount": 12500.00, "status": "approved", "claimDate": 1715880000, "fraudScore": 0.88}
  ]
}
```

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimantId` | string | ID do vértice Claimant |
| `claims[]` | array | Lista dos sinistros do segurado (mesmo formato do endpoint 6 mas abreviado) |

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

### 11. Obter Pontuação de Risco do Segurado

Calcula uma pontuação de risco de fraude para um segurado baseada no histórico de sinistros + sinais derivados por ML.

**Endpoint:** `GET /claimants/{claimant_id}/risk-score`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/risk-score
```

**Exemplo de Resposta (segurado com histórico):**

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

**Exemplo de Resposta (sem histórico):**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimantId` | string | ID do vértice Claimant |
| `riskScore` | number (0–1) | Pontuação de fraude do segurado (inferência indutiva ML, fallback heurístico) |
| `totalClaims` | integer | Número de sinistros apresentados |
| `rejectedClaims` | integer | Sinistros com `status = 'rejected'` |
| `rejectionRate` | number (0–1) | `rejectedClaims / totalClaims` |
| `totalClaimAmount` | number | Soma de todos os valores de sinistros |
| `message` | string | Presente apenas quando `totalClaims = 0` |

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

### 12. Analisar Velocidade de Sinistros

Detecta apresentação de sinistros anormalmente frequente usando análise de séries temporais sobre datas de sinistros.

**Endpoint:** `GET /claimants/{claimant_id}/claim-velocity`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/claim-velocity
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `claimantId` | string | ID do vértice Claimant |
| `totalClaims` | integer | Número de sinistros apresentados |
| `claimsPerYear` | number | Taxa anualizada de sinistros |
| `averageIntervalDays` | number | Intervalo médio entre sinistros consecutivos |
| `shortestIntervalDays` | number | Intervalo mínimo — intervalos muito curtos indicam apresentação em rajada |
| `velocityRisk` | number (0–1) | Pontuação de inferência indutiva ML (fallback: `min(claimsPerYear/10, 1.0)`) |
| `riskLevel` | string | `low`, `medium`, `high` |

**Resposta especial para segurados com < 2 sinistros:**

```json
{
  "claimantId": "clm-abc",
  "totalClaims": 1,
  "velocityRisk": "low",
  "message": "Insufficient claim history"
}
```

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

### 13. Análise Abrangente de Fraude

Retorna um grafo completo de rede de fraude para um segurado: sinistros, acidentes, veículos, oficinas, testemunhas, provedores médicos, advogados, empresas de reboque e passageiros. Usado pela UI de Análise de Fraude para conduzir os fluxos de trabalho do investigador.

**Endpoint:** `GET /claimants/{claimant_id}/fraud-analysis`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/claimants/clm-abc/fraud-analysis
```

**Resposta:** Envelope de grafo padrão (veja [Formato de Resposta de Grafo](#formato-de-resposta-de-grafo)). Tipicamente retorna a vizinhança completa de 2 saltos do segurado, incluindo entidades de anel de fraude conectadas com pontuações de fraude elevadas renderizadas como nós com contorno vermelho.

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

## Anéis de Colisão

### 14. Acidentes Forjados

Detecta pares de segurados cujos acidentes forjados compartilham um Vehicle, Witness ou RepairShop. Cada Accident retornado tem `maneuverType != 'normal'` ou `policeVerified = false`, e cada anel é retornado com a entidade pivot compartilhada no meio.

**Endpoint:** `GET /collision-rings/staged-accidents`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/staged-accidents
```

**Resposta:** Envelope de grafo. Os nós Accident carregam propriedades adicionais:

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `maneuverType` | string | `swoop-squat`, `sudden-stop` ou `normal` |
| `policeVerified` | boolean | Se o acidente tem um boletim de ocorrência verificado |
| `staged` | boolean | Sempre `true` para acidentes retornados por este endpoint |

---

### 15. Swoop & Squat

Detecta veículos envolvidos em 2 ou mais acidentes traseiros forjados (`maneuverType` em `swoop-squat` ou `sudden-stop`). Expõe veículos "utilitários" reutilizados em batidas deliberadas.

**Endpoint:** `GET /collision-rings/swoop-and-squat`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/swoop-and-squat
```

**Resposta:** Envelope de grafo centrado em nós Vehicle de múltiplos acidentes, seus Accidents, Claims e Claimants.

---

### 16. Passageiros Plantados

Expõe acidentes com passageiros falsos "jump-in" apresentando sinistros por lesões. Cada Passenger é enriquecido com métricas agregadas para revelar jump-ins seriais.

**Endpoint:** `GET /collision-rings/stuffed-passengers`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/stuffed-passengers
```

**Resposta:** Envelope de grafo. Os nós Passenger carregam:

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `appearances` | integer | Número de acidentes distintos aos quais o passageiro está vinculado via `passenger_in` |
| `injuryClaims` | integer | Número de arestas `claimed_injury` deste passageiro |
| `totalClaimed` | number | Soma de todos os valores de sinistros por lesões |

Passageiros com `appearances ≥ 2` são renderizados como nós maiores — a assinatura de "jump-in serial". Nós de provedor médico são anexados via `treated_by` para que o rastro do dinheiro das lesões falsas seja visível.

---

### 17. Colisões de Papel

Detecta acidentes não verificados com evidência escassa — `policeVerified = false` E ≤1 testemunha E ≤1 veículo.

**Endpoint:** `GET /collision-rings/paper-collisions`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/paper-collisions
```

**Resposta:** Envelope de grafo. Cadeias escassas de testemunhas/veículos são incluídas explicitamente para que a "evidência escassa" seja visualmente aparente.

---

### 18. Advogados Corruptos

Detecta advogados com `fraudScore ≥ 0.7` que representam dois ou mais segurados, junto com os segurados que representam e os sinistros desses segurados.

**Endpoint:** `GET /collision-rings/corrupt-attorneys`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-attorneys
```

**Resposta:** Envelope de grafo centrado em nós Attorney corruptos com arestas Claimant → Claim radiando para fora.

---

### 19. Empresas de Reboque Corruptas

Detecta empresas de reboque com `fraudScore ≥ 0.7` que rebocam veículos em 2+ acidentes. Inclui a cadeia completa: Tow → Vehicle → Accident → Claim → RepairShop para que o padrão de direcionamento seja visível.

**Endpoint:** `GET /collision-rings/corrupt-tow-companies`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/collision-rings/corrupt-tow-companies
```

**Resposta:** Envelope de grafo incluindo nós TowCompany, Vehicle, Accident, Claim, RepairShop e Claimant.

---

## Fraude de Rede

### 20. Testemunhas Profissionais

Detecta testemunhas que aparecem em 3+ acidentes distintos — o padrão da "testemunha profissional".

**Endpoint:** `GET /network-fraud/professional-witnesses`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/professional-witnesses
```

**Resposta:** Envelope de grafo. Caminho por testemunha: `Witness ← witnessed_by ← Accident ← for_accident ← Claim ← filed_claim ← Claimant`.

---

### 21. Anéis Organizados

Detecta comunidades densamente conectadas de segurados. A filiação ao anel é descoberta via Vehicle compartilhado (`owns` ↔ `owns`) ou RepairShop compartilhado (`filed_claim` → `repaired_at`). O sub-grafo retornado expõe todas as entidades compartilhadas — provedores médicos, advogados, testemunhas, empresas de reboque — como evidência corroborativa.

**Endpoint:** `GET /network-fraud/organized-rings`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/organized-rings
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `algorithm` | string | Descrição do algoritmo de detecção de comunidades |
| `totalCommunities` | integer | Total de anéis descobertos |
| `rings[]` | array | Até 9 anéis principais por tamanho/pontuação |
| `rings[].communitySize` | integer | Número de segurados no anel |
| `rings[].averageFraudScore` | number | Média de fraudScore entre os membros do anel |
| `rings[].riskLevel` | string | `low`, `medium`, `high` |
| `rings[].graph` | object | Envelope de grafo por anel |

---

### 22. Centros de Fraude

Classifica as principais oficinas, provedores médicos e advogados pela amplitude de segurados conectados, e calcula uma "pontuação de conluio" — a fração desses segurados que também compartilham pelo menos outra entidade com um par no hub.

**Endpoint:** `GET /network-fraud/fraud-hubs`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/fraud-hubs
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

Chaves de nível superior: `repairShop`, `medicalProvider`, `attorney`. Cada uma tem um array `hubs` (até 5 por categoria) com:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Nome da entidade hub |
| `uniqueClaimants` | integer | Segurados distintos conectados a este hub |
| `collusionScore` | number (0–1) | Fração de segurados que compartilham outra entidade com um par do anel |
| `graph` | object | Sub-grafo ancorado no hub |

---

### 23. Indicadores de Conluio

Expõe oficinas com 5+ segurados convergindo via `Claim → repaired_at`. Revela padrões tipo triângulos de conluio.

**Endpoint:** `GET /network-fraud/collusion-indicators`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/collusion-indicators
```

**Resposta:** Envelope de grafo com hubs RepairShop, nós Claim intermediários e os Claimants por trás de cada sinistro.

---

### 24. Anéis Isolados

Detecta componentes de fraude independentes — sub-grafos pequenos e autocontidos sem pontes para a rede de fraude mais ampla. Opera em dois modos:

**Modo 1 — Lista resumo (sem parâmetros de consulta):** Retorna uma lista de todos os componentes isolados.

**Endpoint:** `GET /network-fraud/isolated-rings`

**Modo 2 — Grafo por entidade (parâmetros de consulta):** Retorna o anel isolado específico para uma entidade.

**Endpoint:** `GET /network-fraud/isolated-rings?id={entity_id}&type={entity_type}`

**Autenticação:** Bearer JWT

**Parâmetros de Consulta (Modo 2):**

| Nome | Tipo | Descrição |
|------|------|-----------|
| `id` | string | ID da entidade |
| `type` | string | Um de: `claimant`, `claim`, `repair-shop`, `vehicle`, `medical-provider`, `attorney`, `witness`, `passenger`, `tow-company` |

**Exemplo de Requisição (Modo 1):**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/isolated-rings
```

**Exemplo de Resposta (Modo 1):**

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

**Exemplo de Requisição (Modo 2):**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/network-fraud/isolated-rings?id=clm-abc&type=claimant"
```

**Resposta (Modo 2):** Envelope de grafo para o anel específico.

---

### 25. Padrões Entre Sinistros

Para um segurado dado, calcula métricas de diversidade e um grafo de 2 saltos mostrando entidades a jusante (RepairShop, Witness, MedicalProvider) que reaparecem em múltiplos sinistros — a assinatura de "fraude habitual".

**Endpoint:** `GET /network-fraud/cross-claim-patterns/{claimant_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `claimant_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/cross-claim-patterns/clm-abc
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `metrics.totalClaims` | integer | Número de sinistros apresentados |
| `metrics.uniqueRepairShops` | integer | Oficinas distintas usadas entre sinistros |
| `metrics.uniqueWitnesses` | integer | Testemunhas distintas entre sinistros |
| `metrics.uniqueProviders` | integer | Provedores médicos distintos |
| `metrics.shopDiversity` | number | `uniqueRepairShops / totalClaims` |
| `metrics.witnessDiversity` | number | `uniqueWitnesses / totalClaims` |
| `metrics.redFlags` | object | Flags booleanas para sameShopAlways, sameWitnessAlways, lowDiversity |
| `nodes`, `edges` | array | Envelope de grafo (veja [Formato de Resposta de Grafo](#formato-de-resposta-de-grafo)) |

**Erros:**

- `404 Not Found` — `claimant_id` não está no grafo

---

### 26. Vizinhança do Provedor Médico

Retorna o grafo de vizinhança de 1 salto de um provedor médico.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `provider_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc
```

**Resposta:** Envelope de grafo — provedor no centro com Claimants, Passengers e Claims conectados via `treated_by`.

**Erros:**

- `404 Not Found` — `provider_id` não está no grafo

---

### 27. Análise de Fraude do Provedor Médico

Calcula métricas de fraude para um provedor médico usando Neptune ML + estatísticas agregadas de sinistros.

**Endpoint:** `GET /network-fraud/medical-providers/{provider_id}/fraud-analysis`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `provider_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/network-fraud/medical-providers/prov-abc/fraud-analysis
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `providerId` | string | ID do vértice do provedor |
| `name` | string | Nome do provedor |
| `totalClaims` | integer | Sinistros via `treated_by` |
| `uniqueClaimants` | integer | Segurados distintos alcançados |
| `highFraudClaims` | integer | Sinistros com fraudScore > 0.7 |
| `averageFraudScore` | number | Média fraudScore entre sinistros |
| `mlRiskScore` | number | Inferência indutiva do Neptune ML sobre o nó do provedor |
| `networkConnections` | integer | Centralidade de grau (alcance via sinistros) |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleanos para flags vermelhas baseadas em regras |

**Erros:**

- `404 Not Found` — `provider_id` não está no grafo

---

## Análise Avançada

### 28. Segurados Influentes

Classifica segurados por PageRank aproximado (calculado via pontuação de conexões de 1 salto). Expõe segurados que estão no centro de muitas entidades adjacentes à fraude.

**Endpoint:** `GET /advanced-analysis/influential-claimants`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/advanced-analysis/influential-claimants
```

**Exemplo de Resposta:**

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

### 29. Conexões entre Fraudadores

Encontra o caminho mais curto entre duas entidades na rede de fraude. Útil para investigadores raciocinando sobre como dois segurados ou entidades ostensivamente não relacionados estão de fato conectados.

**Endpoint:** `GET /advanced-analysis/connections?source={id}&target={id}`

**Autenticação:** Bearer JWT

**Parâmetros de Consulta:**

| Nome | Tipo | Descrição |
|------|------|-----------|
| `source` | string | ID da entidade de origem |
| `target` | string | ID da entidade de destino |

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  "https://YOUR-API/prod/advanced-analysis/connections?source=clm-abc&target=clm-def"
```

**Resposta:** Envelope de grafo contendo o caminho mais curto — tipicamente 2–6 saltos — com arestas do caminho rotuladas por seu tipo.

**Sem parâmetros de consulta:** retorna um grafo amostrado de segurados com alta pontuação de fraude com suas interconexões.

**Erros:**

- `404 Not Found` — `source` ou `target` não está no grafo

---

## Consulta de Entidades

### 30. Vizinhança da Oficina

Retorna a vizinhança de 1 salto de uma oficina — os Claims reparados lá, mais os Claimants por trás desses sinistros.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `shop_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc
```

**Resposta:** Envelope de grafo.

**Erros:**

- `404 Not Found` — `shop_id` não está no grafo

---

### 31. Estatísticas da Oficina

Calcula estatísticas agregadas da oficina: total de sinistros, taxa de fraude, receita total.

**Endpoint:** `GET /entity-lookup/repair-shops/{shop_id}/statistics`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `shop_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/repair-shops/shop-abc/statistics
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `shopId` | string | ID do vértice da oficina |
| `name` | string | Nome da oficina |
| `totalClaims` | integer | Sinistros via `repaired_at` |
| `averageClaimAmount` | number | Valor médio do sinistro |
| `totalRevenue` | number | Soma de valores de sinistros |
| `highFraudClaims` | integer | Sinistros com fraudScore > 0.7 |
| `fraudRate` | number (0–1) | `highFraudClaims / totalClaims` |
| `averageFraudScore` | number | Média fraudScore |
| `riskLevel` | string | `low`, `medium`, `high` |

**Erros:**

- `404 Not Found` — `shop_id` não está no grafo

---

### 32. Vizinhança do Veículo

Retorna a vizinhança de 1 salto de um veículo — acidentes em que esteve envolvido, seu proprietário e os sinistros desses acidentes.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `vehicle_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc
```

**Resposta:** Envelope de grafo.

**Erros:**

- `404 Not Found` — `vehicle_id` não está no grafo

---

### 33. Histórico de Fraude do Veículo

Analisa o histórico de sinistros de um veículo e calcula uma pontuação de risco ML.

**Endpoint:** `GET /entity-lookup/vehicles/{vehicle_id}/fraud-history`

**Autenticação:** Bearer JWT

**Parâmetros de Caminho:** `vehicle_id` (string)

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/entity-lookup/vehicles/veh-abc/fraud-history
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `vehicleId` | string | ID do vértice Vehicle |
| `make` | string | Marca do veículo |
| `year` | integer | Ano do modelo |
| `totalClaims` | integer | Sinistros em que este veículo esteve envolvido |
| `highFraudClaims` | integer | Sinistros com fraudScore > 0.7 |
| `averageFraudScore` | number | Média fraudScore entre sinistros |
| `mlRiskScore` | number | Inferência indutiva do Neptune ML sobre o veículo |
| `uniqueOwners` | integer | Segurados distintos que possuíram este veículo |
| `uniqueRepairShops` | integer | Oficinas distintas onde este veículo foi reparado |
| `riskLevel` | string | `low`, `medium`, `high` |
| `suspicionIndicators` | object | Booleanos para flags vermelhas baseadas em regras |

**Resposta especial para veículos sem sinistros:**

```json
{"vehicleId": "veh-abc", "make": "Nissan", "year": 2021, "totalClaims": 0, "riskLevel": "unknown"}
```

**Erros:**

- `404 Not Found` — `vehicle_id` não está no grafo

---

## Analítica

### 34. Tendências de Fraude

Estatísticas agregadas de fraude em todos os sinistros.

**Endpoint:** `GET /analytics/fraud-trends`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/fraud-trends
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `totalClaims` | integer | Sinistros totais no grafo |
| `approvedClaims` | integer | Sinistros com status `approved` |
| `rejectedClaims` | integer | Sinistros com status `rejected` |
| `pendingClaims` | integer | Sinistros com status `pending` |
| `highFraudClaims` | integer | Sinistros com fraudScore > 0.7 |
| `fraudRate` | number | `highFraudClaims / totalClaims` |
| `totalClaimAmount` | number | Soma de todos os valores de sinistros |
| `estimatedFraudExposure` | number | Soma de valores de sinistros marcados como fraude |

---

### 35. Pontos Quentes Geográficos

Detecta pontos quentes de fraude geográfica agrupando acidentes e entidades por CEP. Retorna clusters a nível de CEP com coordenadas, densidade de fraude, entidades vinculadas e um grafo de rede da zona de fraude principal.

**Endpoint:** `GET /analytics/geographic-hotspots`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/geographic-hotspots
```

**Exemplo de Resposta (abreviado):**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `zones[]` | array | CEPs ordenados por densidade de fraude (decrescente) |
| `zones[].zipCode` | string | Código postal |
| `zones[].latitude` | number | Latitude média dos acidentes nesta zona |
| `zones[].longitude` | number | Longitude média dos acidentes nesta zona |
| `zones[].totalAccidents` | integer | Total de acidentes neste CEP |
| `zones[].fraudAccidents` | integer | Acidentes vinculados a fraude neste CEP |
| `zones[].fraudDensity` | number | Proporção de fraude sobre total de acidentes (0.0–1.0) |
| `hotspotEntities` | object | Entidades suspeitas localizadas nas zonas de fraude principais |
| `hotspotEntities.repairShops[]` | array | Oficinas em zonas de fraude com pontuações de fraude |
| `hotspotEntities.medicalProviders[]` | array | Provedores médicos em zonas de fraude |
| `hotspotEntities.towCompanies[]` | array | Empresas de reboque em zonas de fraude |
| `graph` | object | Dados de visualização de rede para a zona de fraude principal |
| `graph.nodes[]` | array | Nós com id, tipo, rótulo, fraudScore, coordenadas |
| `graph.edges[]` | array | Arestas com source, target, tipo |
| `insight` | string | Resumo legível da zona de fraude principal |

---

### 36. Anomalias em Valores de Sinistros

Detecta sinistros com valores anormalmente altos via análise estatística (z-score) e análise alimentada por ML.

**Endpoint:** `GET /analytics/claim-amount-anomalies`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/claim-amount-anomalies
```

**Exemplo de Resposta:**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `algorithm` | string | Descrição do algoritmo |
| `statistics.meanAmount` | number | Valor médio do sinistro |
| `statistics.standardDeviation` | number | Desvio padrão dos valores de sinistros |
| `statistics.totalClaims` | integer | Tamanho da amostra |
| `anomaliesDetected` | integer | Anomalias totais (abs(z-score) > 2) |
| `highRiskAnomalies[]` | array | Sinistros com z-score > 3 E mlAnomalyScore > 0.7 |
| `allAnomalies[]` | array | Todas as anomalias |
| `allAnomalies[].zScore` | number | Z-score estatístico |
| `allAnomalies[].mlAnomalyScore` | number | Pontuação de anomalia do Neptune ML |
| `allAnomalies[].anomalyType` | string | `unusually_high` ou `unusually_low` |
| `allAnomalies[].riskLevel` | string | `low`, `medium`, `high` |

---

### 37. Padrões Temporais

Analisa padrões de apresentação de sinistros ao longo do tempo — agregados semanais e mensais, rajadas detectadas.

**Endpoint:** `GET /analytics/temporal-patterns`

**Autenticação:** Bearer JWT

**Exemplo de Requisição:**

```bash
curl -b .auth-cookie \
  https://YOUR-API/prod/analytics/temporal-patterns
```

**Exemplo de Resposta (abreviado):**

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

**Esquema de Resposta:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `monthlyTrends[]` | array | Dados mensais de sinistros/taxa de fraude |
| `weekdayPatterns` | object | Contagens de sinistros por dia da semana |
| `anomalousBursts[]` | array | Janelas de tempo detectadas com taxa de sinistros muito maior que o esperado |

---

## Listas de Entidades

Cada um destes endpoints retorna uma lista simples para popular os dropdowns da UI. O formato de resposta é idêntico por tipo de entidade.

### 38. Listar Advogados

**Endpoint:** `GET /attorneys`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "attorneys": [
    {"id": "atty-1", "name": "Attorney 0"},
    {"id": "atty-2", "name": "Attorney 1"}
  ]
}
```

---

### 39. Listar Testemunhas

**Endpoint:** `GET /witnesses`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "witnesses": [
    {"id": "wit-1", "name": "Witness 0"}
  ]
}
```

---

### 40. Listar Passageiros

**Endpoint:** `GET /passengers`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "passengers": [
    {"id": "pas-1", "name": "Passenger abc12345"},
    {"id": "pas-2", "name": "Serial Jump-in 9f25c880"}
  ]
}
```

---

### 41. Listar Empresas de Reboque

**Endpoint:** `GET /tow-companies`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "towCompanies": [
    {"id": "tow-1", "name": "Tow Company 0"}
  ]
}
```

---

### 42. Listar Provedores Médicos

**Endpoint:** `GET /medical-providers`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "medicalProviders": [
    {"id": "prov-1", "name": "Dr. Provider 0"}
  ]
}
```

---

### 43. Listar Oficinas

**Endpoint:** `GET /repair-shops`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "repairShops": [
    {"id": "shop-1", "name": "Repair Shop 0"}
  ]
}
```

---

### 44. Listar Veículos

**Endpoint:** `GET /vehicles`

**Autenticação:** Bearer JWT

**Exemplo de Resposta:**

```json
{
  "vehicles": [
    {"id": "veh-1", "vin": "VIN0000000000", "make": "Toyota", "year": 2020}
  ]
}
```

---

## Limites de Taxa

Todos os endpoints são protegidos pelo AWS WAF com:

- **Limite de taxa global:** 2.000 requisições por janela de 5 minutos, por IP de origem
- **Detecção de bots:** Requisições sem cabeçalho `User-Agent` são bloqueadas
- **Regras gerenciadas OWASP Top 10:** Injeção SQL, XSS e outros ataques comuns
- **Limites de tamanho de requisição:** Corpos POST > 8 KB são rejeitados

Exceder o limite de taxa retorna um `403 Forbidden` com uma mensagem de resposta do WAF.

## Boas Práticas

- **Reutilize JWTs entre requisições.** A emissão de tokens é cara; armazene em cache o token em seu cliente durante sua vigência de 1 hora.
- **Renove proativamente.** Chame `POST /auth/refresh` a ~90% da vigência do token em vez de esperar por um `401`.
- **Respeite a paginação.** Os endpoints de grafo limitam o número de anéis/comunidades retornados por desempenho. Se precisar do dataset completo para analítica, consulte o cluster Neptune subjacente diretamente ou solicite uma execução de exportação Step Functions.
- **Trate valores fraudScore como probabilidades.** Não são classificadores calibrados; use-os como sinal de ranking.
- **Não assuma que `mlRiskScore` > 0.** Se o treinamento do Neptune ML ainda estiver em progresso (primeiras 1–2 horas após o deploy), os endpoints ML degradam elegantemente para heurísticas e retornam 0 ou valores de fallback.
- **Clientes navegador devem enviar `credentials: 'include'`** para que o caminho de autenticação por cookie `httpOnly` funcione. A configuração CORS da API requer isso.

## Suporte

- **Troubleshooting:** verifique os logs do CloudWatch em `/aws/lambda/auto-insurance-fraud-detect-FraudDetectionFunction-*`
- **Logs do WAF:** `/aws/wafv2/auto-insurance-fraud-detection-WAF`
- **Logs do API Gateway:** `/aws/apigateway/auto-insurance-fraud-detection-API`
- **Pipeline Neptune ML:** console Step Functions → `auto-insurance-fraud-detection-MLPipelineStack-*-MLPipeline`
- **Consultas de amostra:** veja [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md)
- **Código do frontend:** veja [frontend/README.md](frontend/README.md)
