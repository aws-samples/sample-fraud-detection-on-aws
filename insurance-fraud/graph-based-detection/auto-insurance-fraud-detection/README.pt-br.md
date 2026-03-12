[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)<br />
[![es-sp](https://img.shields.io/badge/lang-es--sp-green.svg)](README.es-sp.md)

# Detecção de Fraude em Seguros de Auto com Amazon Neptune ML

Esta solução demonstra a detecção de fraude em seguros de auto usando Amazon Neptune ML para identificar anéis de colisão, oficinas suspeitas e testemunhas profissionais.

## Início Rápido

Implante o sistema completo de detecção de fraude em **3 passos simples**:

```bash
# 1. Navegue até o diretório
cd auto-insurance-fraud-detection

# 2. (Opcional) Configure sua região e perfil AWS
export AWS_REGION=us-east-1  # Padrão: us-east-1
export AWS_PROFILE=default   # Padrão: default

# 3. Execute o script de implantação
./scripts/deploy.sh
```

**É isso!** O script leva ~16 minutos e implanta tudo automaticamente usando stacks aninhados do CloudFormation.

### O Que Você Obtém

Após a conclusão da implantação, você terá:
- ✅ API de detecção de fraude totalmente operacional com 22 endpoints
- ✅ **Autenticação Cognito** - Controle de acesso seguro baseado em JWT com cookies httpOnly
- ✅ **Aplicação web frontend** - Painel interativo de detecção de fraude com armazenamento seguro de tokens
- ✅ **Proteção WAF** - Limitação de taxa, OWASP Top 10, proteção contra injeção SQL
- ✅ **Suporte completo CORS** - Todos os endpoints têm métodos OPTIONS configurados
- ✅ **Autenticação IAM do Neptune** - Acesso ao banco de dados via credenciais IAM (sem senhas)
- ✅ **Segurança Lambda** - Concorrência reservada e registro estruturado com Powertools
- ✅ **Cabeçalhos de Segurança CloudFront** - Proteção HSTS, CSP, X-Frame-Options
- ✅ Banco de dados de grafos Neptune com 2000 sinistros de seguros de amostra
- ✅ 14 funções Lambda para detecção de fraude, treinamento ML e autenticação
- ✅ API Gateway com validação de solicitações e endpoints autenticados
- ✅ Pipeline de treinamento ML com Step Functions
- ✅ **Zero acesso à internet da VPC** - Todo o tráfego via endpoints VPC

### Autenticação Obrigatória

Todos os endpoints da API requerem autenticação. Crie um usuário no Cognito:

```bash
# Criar usuário
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username usuario@empresa.com \
  --message-action SUPPRESS

# Definir senha permanente
aws cognito-idp admin-set-user-password \
  --user-pool-id <USER_POOL_ID> \
  --username usuario@empresa.com \
  --password SuaSenha123! \
  --permanent
```

Ou use a página de login do frontend em `frontend/login.html`.

# Chamar API com o token
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  https://SEU-API-ENDPOINT/prod/analytics/fraud-trends
```

**Opções do Script:**
```bash
./scripts/authenticate.sh [OPÇÕES]

Opções:
  -u, --username <email>    Email do usuário (obrigatório)
  -p, --password <pass>     Senha do usuário (opcional, gera aleatória se não fornecida)
  --region <region>         Região AWS (padrão: $AWS_REGION ou us-east-1)
  --profile <profile>       Perfil AWS (padrão: $AWS_PROFILE ou default)
  --output <file>           Arquivo de saída do token (padrão: .auth-token)
  --create-only             Apenas criar usuário, não autenticar
  --token-only              Apenas obter token para usuário existente
  -h, --help                Mostrar mensagem de ajuda
```

**Exemplos:**
```bash
# Apenas criar usuário sem autenticar
./scripts/authenticate.sh -u usuario@empresa.com -p MinhaPass123! --create-only

# Obter token para usuário existente
./scripts/authenticate.sh -u usuario@empresa.com -p MinhaPass123! --token-only

# Usar em região diferente
./scripts/authenticate.sh -u usuario@empresa.com --region eu-west-1
```

## Arquitetura

Esta solução usa uma **arquitetura modular de stacks aninhados** com segurança de nível empresarial:

**Serviços Principais:**
- **Amazon Neptune** - Banco de dados de grafos armazenando sinistros, segurados, veículos, acidentes, oficinas e testemunhas (com autenticação IAM)
- **Neptune ML** - Modelo de Rede Neural de Grafos (GNN) para previsão de fraude
- **AWS Lambda** - 14 funções serverless para API, população de dados e pipeline ML (com concorrência reservada)
- **AWS Step Functions** - Orquestração do pipeline de treinamento ML
- **Amazon API Gateway** - API REST com 22 endpoints autenticados e validação de solicitações
- **AWS Batch** - Trabalhos de exportação de dados do Neptune (com autenticação IAM)
- **Amazon S3** - Armazenamento de dados de treinamento ML e modelos
- **Amazon SageMaker** - Treinamento de modelos ML e endpoints de inferência
- **Amazon CloudFront** - Entrega de conteúdo com cabeçalhos de segurança

**Segurança e Autenticação:**
- **Amazon Cognito** - Autenticação de usuários com tokens JWT e cookies httpOnly
- **AWS WAF** - Firewall de aplicações web com limitação de taxa e proteção OWASP Top 10
- **VPC Endpoints** - Sem acesso à internet da VPC, todo o tráfego via endpoints privados (12 endpoints)
- **Security Groups** - Acesso de rede com privilégio mínimo
- **Autenticação IAM** - Neptune e Lambda usam credenciais IAM
- **Cabeçalhos de Segurança CloudFront** - HSTS, CSP, X-Frame-Options, X-Content-Type-Options

**Infraestrutura:** 11 stacks aninhados do CloudFormation para modularidade e manutenibilidade

![Diagrama de Arquitetura](generated-diagrams/architecture.png)

Veja [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) para exemplos de consultas de detecção de fraude.

## Recursos de Segurança

### Segurança de Nível Empresarial (11 Melhorias Implementadas)

Esta solução implementa práticas recomendadas de segurança abrangentes:

**1. Autenticação e Autorização**
- **Amazon Cognito** - Autenticação baseada em JWT para todos os endpoints da API
- **Autenticação IAM de Banco de Dados** - Neptune usa credenciais IAM (sem senhas de banco de dados)
- **Armazenamento Seguro de Tokens** - Tokens armazenados em memória com backup de cookies httpOnly
- **Validade de Tokens** - 1 hora (ID/Acesso), 30 dias (Atualização)
- **Política de Senhas Fortes** - Aplicada pelo Cognito

**2. Segurança de API**
- **Validação de Solicitações** - API Gateway valida todos os corpos de solicitações POST
- **Limites de Tamanho de Solicitação** - Previne cargas úteis de grande tamanho
- **Configuração CORS** - Configurada corretamente para acesso do frontend
- **Limitação de Taxa** - 2.000 solicitações por 5 minutos por IP (WAF)

**3. Firewall de Aplicações Web (WAF)**
- **Proteção OWASP Top 10** - XSS, CSRF, injeção SQL
- **Detecção de Bots** - Bloqueia solicitações sem User-Agent
- **Registro de Solicitações** - Retenção de 30 dias no CloudWatch

**4. Segurança de Rede**
- **Zero Acesso à Internet** - Todos os recursos em sub-redes privadas
- **VPC Endpoints** - Conectividade privada aos serviços AWS (12 endpoints)
- **Security Groups** - Regras de acesso com privilégio mínimo
- **Criptografia** - TLS em trânsito, criptografia em repouso

**5. Segurança Lambda**
- **Concorrência Reservada** - 50 execuções concorrentes por função (previne esgotamento de recursos)
- **AWS Lambda Powertools** - Registro estruturado para todas as funções
- **IAM de Privilégio Mínimo** - Funções IAM específicas por função

**6. Segurança do Frontend**
- **Cabeçalhos de Segurança CloudFront** - HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Manipulação Segura de Cookies** - Cookies httpOnly para armazenamento de tokens
- **Endpoint de Logout** - Terminação adequada de sessão

**7. Segurança de Infraestrutura**
- **Sem Credenciais Codificadas** - Todas as senhas usam Secrets Manager ou marcadores de parâmetros
- **Saídas do CloudFormation** - Configuração do frontend auto-gerada a partir das saídas do stack
- **Implantação Automatizada** - Reduz erros de configuração manual

## Implantação

### Implantação Automatizada (Recomendado)

A maneira mais fácil de implantar é usando o script fornecido:

```bash
./scripts/deploy.sh
```

**O que o script faz:**
1. Implanta o stack do CloudFormation (~15-20 minutos)
2. Implanta todo o código das funções Lambda (~1 minuto)
3. Popula o Neptune com 2.000 sinistros de amostra (~3 minutos)
4. **Inicia o pipeline de treinamento ML** (~1-2 horas em segundo plano)
5. Fornece o endpoint da API e resumo da implantação

**Tempo total de implantação: ~16 minutos**  
**Tempo de treinamento ML: 1-2 horas (executa em segundo plano)**

**Importante:** Após a conclusão da implantação:
- ✅ 9 endpoints de algoritmos de grafos funcionam imediatamente
- ⏳ 5 endpoints alimentados por ML estarão disponíveis após a conclusão do treinamento (1-2 horas)

### Opções de Configuração

Configure variáveis de ambiente antes de executar o script:

```bash
# Implantar em uma região diferente
export AWS_REGION=us-east-2

# Usar um perfil específico da AWS
export AWS_PROFILE=meu-perfil

# Então implantar
./scripts/deploy.sh
```

### Pré-requisitos

- AWS CLI configurado com credenciais apropriadas
- Permissões para criar stacks do CloudFormation, funções Lambda, clusters Neptune, VPCs, User Pools do Cognito
- ~20 minutos para implantação

### Limpeza

Para remover todos os recursos implantados:

```bash
./scripts/undeploy.sh
```

### Atualização para Produção

A configuração padrão usa **db.t3.medium** para custo-benefício (~$195/mês). Para cargas de trabalho de produção:

```bash
# Implantar com instância Neptune de nível de produção
aws cloudformation update-stack \
  --stack-name auto-insurance-fraud-detection \
  --use-previous-template \
  --parameters ParameterKey=NeptuneInstanceClass,ParameterValue=db.r5.large \
  --capabilities CAPABILITY_NAMED_IAM
```

**Por que atualizar?**
- db.t3.medium usa créditos de CPU (pode limitar sob carga sustentada)
- db.r5.large fornece desempenho consistente
- Melhor para cargas de trabalho de treinamento ML
- Custo: +$280/mês (~$475/mês total)

## O Que É Implantado

**Infraestrutura (11 Stacks Aninhados):**
- Cluster Amazon Neptune (db.t3.medium) com ML habilitado e autenticação IAM
- User Pool do Amazon Cognito para autenticação
- AWS WAF com 5 regras de proteção
- VPC com sub-redes privadas e 12 endpoints VPC
- 14 funções AWS Lambda (com concorrência reservada e registro Powertools)
- API Gateway com autorizador JWT, validação de solicitações e 22 endpoints (incluindo logout)
- Pipeline de treinamento ML com Step Functions
- AWS Batch para exportação do Neptune (com autenticação IAM)
- Bucket S3 para Neptune ML (com políticas de ciclo de vida)
- Funções IAM com políticas de privilégio mínimo
- Security groups com regras inline
- Distribuição CloudFront com cabeçalhos de segurança

**Dados de Amostra:**
- 1.000 segurados
- 1.500 veículos
- 200 oficinas de reparação (10% suspeitas)
- 150 provedores médicos (13% suspeitos)
- 300 testemunhas (20% profissionais)
- 250 advogados (20% corruptos)
- 200 empresas de reboque (20% corruptas)
- 2.000 sinistros de seguros (40% fraudulentos)
- Passageiros variáveis (passageiros falsos em sinistros fraudulentos)

## Endpoints da API (22 no Total)

Todos os endpoints requerem autenticação JWT via cabeçalho `Authorization: Bearer <token>`.

### Autenticação (2 endpoints)
- `POST /auth/login` - Autenticar usuário e obter token JWT
- `POST /auth/logout` - Fazer logout e limpar sessão

### Gerenciamento de Sinistros (6 endpoints)
- `POST /claims` - Enviar sinistro com detecção de fraude ML
- `GET /claims/{claim_id}` - Obter detalhes do sinistro
- `GET /claimants/{claimant_id}/claims` - Obter histórico de sinistros do segurado
- `GET /claimants/{claimant_id}/risk-score` - Obter pontuação de risco alimentada por ML
- `GET /claimants/{claimant_id}/claim-velocity` - Analisar frequência de sinistros
- `GET /claimants/{claimant_id}/fraud-analysis` - Análise abrangente de fraude

### Padrões de Fraude (4 endpoints)
- `GET /fraud-patterns/collision-rings` - Detectar 6 tipos de fraude de anéis de colisão (acidentes encenados, swoop & squat, passageiros falsos, colisões de papel, advogados corruptos, empresas de reboque corruptas)
- `GET /fraud-patterns/professional-witnesses` - Encontrar testemunhas repetidas
- `GET /fraud-patterns/collusion-indicators` - Identificar conluio
- `GET /fraud-patterns/cross-claim-patterns` - Fraude entre sinistros

### Redes de Fraude (4 endpoints)
- `GET /fraud-networks/influential-claimants` - Encontrar centros de rede
- `GET /fraud-networks/organized-rings` - Detectar fraude organizada
- `GET /fraud-networks/connections` - Mapear conexões de fraudadores
- `GET /fraud-networks/isolated-rings` - Encontrar grupos de fraude isolados

### Analítica (4 endpoints)
- `GET /analytics/fraud-trends` - Tendências de fraude ao longo do tempo
- `GET /analytics/geographic-hotspots` - Concentração geográfica de fraude
- `GET /analytics/claim-amount-anomalies` - Detecção de anomalias alimentada por ML
- `GET /analytics/temporal-patterns` - Padrões de fraude baseados em tempo

### Análise de Entidades (3 endpoints)
- `GET /repair-shops/{shop_id}/statistics` - Estatísticas de fraude da oficina
- `GET /repair-shops/fraud-hubs` - Identificar oficinas centro de fraude
- `GET /vehicles/{vehicle_id}/fraud-history` - Histórico de fraude do veículo
- `GET /medical-providers/{provider_id}/fraud-analysis` - Análise de fraude do provedor

## Capacidades de Detecção de Fraude

O sistema detecta 16 tipos de fraude de seguros usando algoritmos de grafos e ML:

**Padrões de Anéis de Colisão (6 tipos):**
1. **Acidentes Encenados** - Segurados compartilhando veículos, testemunhas e oficinas
2. **Swoop & Squat** - Manobras de colisão traseira direcionadas a vítimas
3. **Passageiros Falsos** - Jump-ins reivindicando lesões falsas
4. **Colisões de Papel** - Acidentes fantasma com relatórios policiais não verificados
5. **Advogados Corruptos** - Escritórios de advocacia direcionando clientes a anéis de fraude
6. **Empresas de Reboque Corruptas** - Operadores de reboque direcionando vítimas a oficinas fraudulentas

**Padrões de Fraude de Rede (7 tipos):**
7. **Testemunhas Profissionais** - Mesma testemunha em múltiplos sinistros não relacionados
8. **Anéis de Fraude Organizados** - Redes de fraude densamente conectadas
9. **Oficinas Centro de Fraude** - Oficinas conectando múltiplos anéis
10. **Triângulos de Conluio** - Esquemas de fraude de três vias
11. **Anéis Isolados** - Operações de fraude independentes
12. **Fraude de Provedores Médicos** - Esquemas de faturamento inflado
13. **Padrões Entre Sinistros** - Relações de fraude habituais

**Padrões de Analítica e ML (3 tipos):**
14. **Velocidade de Sinistros** - Apresentadores de sinistros em série
15. **Pontos Quentes Geográficos** - Concentração regional de fraude
16. **Anomalias de Valor de Sinistros** - Valores de sinistros inflados detectados por ML

Veja [API_DOCUMENTATION.md](API_DOCUMENTATION.md) para documentação detalhada de endpoints.

## Modelo de Grafos

### Vértices
- **Claimant** - Titulares de apólices de seguros
- **Vehicle** - Veículos segurados (vin, make, year, plate, ownerId)
- **Claim** - Sinistros de seguros
- **Accident** - Eventos de acidentes (com accidentType, maneuverType, policeVerified)
- **RepairShop** - Instalações de reparação de autos
- **MedicalProvider** - Provedores de assistência médica
- **Witness** - Testemunhas de acidentes
- **Attorney** - Representantes legais
- **TowCompany** - Operadores de reboques
- **Passenger** - Passageiros de acidentes
- **fraudEntity** - Nó alvo de ML vinculado às entidades suspeitas (RepairShop, MedicalProvider, Witness, Attorney, TowCompany, Claim, Passenger) via aresta `has_fraud_score`; armazena a propriedade `fraudScore` utilizada para treinar o modelo de regressão do Neptune ML

### Arestas
- **owns** - Segurado possui Veículo
- **filed_claim** - Segurado apresentou Sinistro
- **for_accident** - Sinistro por Acidente
- **involved_vehicle** - Acidente envolveu Veículo
- **repaired_at** - Sinistro reparado na Oficina
- **treated_by** - Segurado ou Passageiro tratado por Provedor Médico
- **witnessed_by** - Acidente testemunhado por Testemunha
- **represented_by** - Segurado representado por Advogado
- **towed_by** - Veículo rebocado por Empresa de Reboque
- **passenger_in** - Passageiro no Acidente
- **claimed_injury** - Passageiro reivindicou lesão no Sinistro
- **has_fraud_score** - Entidade de domínio vinculada ao seu nó alvo fraudEntity de ML

## Uso da API

Após a implantação, use o endpoint da API para detectar fraude:

```bash
# Obter endpoint da API da saída da implantação
API_ENDPOINT="https://SEU-API-ENDPOINT/prod"

# Obter tendências de fraude
curl $API_ENDPOINT/analytics/fraud-trends

# Detectar anéis de colisão
curl $API_ENDPOINT/fraud-patterns/collision-rings

# Encontrar segurados influentes
curl $API_ENDPOINT/fraud-networks/influential-claimants

# Analisar risco de segurado específico
curl $API_ENDPOINT/claimants/{claimant-id}/risk-score
```

Veja [API_DOCUMENTATION.md](API_DOCUMENTATION.md) para todos os 21 endpoints com documentação detalhada.

## Pipeline de Treinamento ML

O script de implantação inicia automaticamente o pipeline de treinamento ML, que leva 1-2 horas para ser concluído.

**Monitorar o pipeline:**
```bash
# Obter ARN de execução da saída da implantação, então:
aws stepfunctions describe-execution \
  --execution-arn SEU-EXECUTION-ARN \
  --region us-east-1
```

**Quais endpoints requerem treinamento ML?**
- ✅ **Funcionam imediatamente** (Algoritmos de grafos - 9 endpoints): collision-rings, professional-witnesses, influential-claimants, organized-rings, fraud-hubs, connections, collusion-indicators, isolated-rings, cross-claim-patterns
- ⏳ **Disponíveis após o treinamento** (Alimentados por ML - 5 endpoints): submit-claim (pontuação de fraude), risk-score, vehicle-fraud-history, medical-provider-fraud-analysis, claim-amount-anomalies

**Você pode testar os endpoints de algoritmos de grafos imediatamente. Os endpoints alimentados por ML estarão disponíveis assim que o treinamento for concluído (~1-2 horas).**

O pipeline também é executado automaticamente a cada 15 dias via EventBridge para retreinar modelos com novos dados de fraude.

## Limpeza

Para remover todos os recursos implantados:

```bash
# Configure sua região e perfil
export AWS_REGION=us-east-1
export AWS_PROFILE=default

# Execute o script de desimplantação
./scripts/undeploy.sh
```

O script cuida da limpeza de:
- Buckets S3 (incluindo objetos versionados)
- Endpoints VPC (incluindo endpoints gerenciados pelo GuardDuty)
- Interfaces de rede (aguarda liberação)
- NAT Gateways
- Security groups
- Stack do CloudFormation e todos os recursos

## Estimativa de Custos

Custos mensais aproximados (us-east-1) com configuração padrão:

**Computação e Banco de Dados:**
- Neptune db.t3.medium: ~$70/mês (730 horas × $0.096/hora)
- Lambda (14 funções): ~$5/mês (1M invocações, 512MB, 3s média)
- AWS Batch: ~$2/mês (trabalhos de exportação mensais)

**Rede:**
- VPC Endpoints (12): ~$84/mês (12 × $7/mês cada)
- CloudFront: ~$1/mês (primeiro 1TB grátis, depois $0.085/GB)

**API e Segurança:**
- API Gateway: ~$3.50/1M solicitações
- Cognito: Grátis (primeiros 50K MAUs)
- WAF: ~$16/mês ($5 base + $1/regra × 5 + 10M solicitações)

**Armazenamento e ML:**
- Armazenamento S3: ~$1/mês (dados Neptune ML)
- SageMaker: ~$2/mês (ml.m5.xlarge para treinamento, sob demanda)
- CloudWatch Logs: ~$5/mês (5GB ingestão + retenção)

**Total: ~$190/mês**

**Dicas de Otimização de Custos:**
- Use db.t3.medium para dev/test (~$70/mês)
- Atualize para db.r5.large para produção (~$350/mês) para desempenho consistente
- Reduza endpoints VPC se nem todos os serviços forem usados
- Ajuste concorrência reservada do Lambda com base na carga real
- Use políticas de ciclo de vida S3 para arquivar dados antigos de treinamento ML

**Atualização de Produção:**
Para cargas de trabalho de produção, considere:
- Neptune db.r5.large: ~$350/mês (sem limitações de crédito de CPU)
- Custo total de produção: ~$480/mês

*Os custos variam por região e uso. O cluster Neptune é o principal impulsionador de custos (~35% do total).*

## Exemplo de Cliente Python

```python
import boto3
import requests

# Inicializar cliente Cognito
cognito = boto3.client('cognito-idp', region_name='us-east-1')

# Fazer login
response = cognito.admin_initiate_auth(
    UserPoolId='SEU_USER_POOL_ID',
    ClientId='SEU_CLIENT_ID',
    AuthFlow='ADMIN_USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'usuario@empresa.com',
        'PASSWORD': 'SenhaSegura123!'
    }
)

token = response['AuthenticationResult']['IdToken']

# Chamar API de detecção de fraude
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'https://SUA-API/prod/claims',
    headers=headers,
    json={
        'claimAmount': 8500.00,
        'claimantId': 'claimant-12345',
        'vehicleId': 'vehicle-67890',
        'repairShopId': 'shop-abc123'
    }
)

print(f"Pontuação de Fraude: {response.json()['fraudScore']}")
```

## Documentação

- **[SAMPLE_QUERIES.md](SAMPLE_QUERIES.md)** - Exemplos de consultas de detecção de fraude
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Documentação detalhada de endpoints
- **[infrastructure/README.md](infrastructure/README.md)** - Detalhes da arquitetura de stacks aninhados
- **[infrastructure/api-specs/](infrastructure/api-specs/)** - Especificação OpenAPI 3.0
- **[frontend/README.md](frontend/README.md)** - Guia de configuração e uso do frontend
- **[generated-diagrams/](generated-diagrams/)** - Visualizações de padrões de fraude:
  - `staged_accident_ring.png` - Anéis de fraude compartilhando veículos, oficinas e testemunhas
  - `swoop_and_squat.png` - Manobras coordenadas de colisão traseira
  - `stuffed_passengers.png` - Passageiros falsos (jump-ins) reivindicando lesões
  - `paper_collision.png` - Acidentes fantasma com documentação falsa
  - `corrupt_attorney.png` - Advogados direcionando clientes a anéis de fraude
  - `corrupt_tow_company.png` - Empresas de reboque direcionando vítimas a oficinas fraudulentas
  - `collision_ring_patterns_overview.png` - Visão abrangente de todos os 6 padrões de anéis de colisão
  - Mais 13 visualizações adicionais de padrões de fraude

## Suporte

Para problemas ou perguntas:
1. Verifique a saída da implantação para User Pool ID e Client ID do Cognito
2. Revise [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) para exemplos de consultas
3. Verifique eventos do stack do CloudFormation para problemas de implantação
4. Veja logs do API Gateway no CloudWatch: `/aws/apigateway/auto-insurance-fraud-detection-API`
5. Veja logs do WAF no CloudWatch: `/aws/wafv2/auto-insurance-fraud-detection-WAF`

## Licença

Este código de amostra está disponível sob a licença MIT-0. Veja o arquivo LICENSE.
