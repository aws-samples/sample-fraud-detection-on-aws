# Nested Stack Architecture

This directory contains the refactored infrastructure using AWS CloudFormation nested stacks for better modularity and maintainability.

## Structure

```
infrastructure/
├── main.yaml                    # Root stack (orchestrates all nested stacks)
├── stacks/
│   ├── helpers.yaml             # S3 prefix list lookup custom resource
│   ├── network.yaml             # VPC, subnets, NAT gateway, IGW
│   ├── security-groups.yaml     # All security groups with inline rules
│   ├── vpc-endpoints.yaml       # Interface VPC endpoints for AWS services (9 endpoints)
│   ├── iam.yaml                 # IAM roles and policies
│   ├── cognito.yaml             # Cognito User Pool for authentication
│   ├── waf.yaml                 # WAF with rate limiting and OWASP rules
│   ├── storage.yaml             # S3 bucket and Neptune cluster (with IAM auth)
│   ├── batch.yaml               # AWS Batch for Neptune export (with IAM auth)
│   ├── lambda.yaml              # All Lambda functions (14 total, with reserved concurrency)
│   ├── api.yaml                 # API Gateway with routes (22 endpoints, request validation)
│   ├── frontend.yaml            # CloudFront distribution (with security headers)
│   └── ml-pipeline.yaml         # Step Functions ML training pipeline
└── api-specs/
    └── fraud-detection-api.yaml # OpenAPI 3.0 specification

```

## Benefits Over Monolithic Template

### 1. **Modularity**
- Each stack is focused on a single concern
- Easier to understand and modify
- Can be developed and tested independently

### 2. **Reusability**
- Network stack can be reused across projects
- IAM roles can be shared
- API patterns can be templated

### 3. **Faster Updates**
- Update only the stack that changed
- No need to redeploy entire infrastructure
- Reduced risk of unintended changes

### 4. **Better Organization**
- Security groups consolidated with inline rules (reduced from 20+ resources to 4)
- AWS IAM policies shared via managed policies
- Clear dependency chain

### 5. **Parallel Deployment**
- AWS CloudFormation deploys independent stacks in parallel
- Faster overall deployment time

### 6. **Easier Troubleshooting**
- Stack-specific errors are isolated
- AWS CloudFormation events are easier to read
- Can delete/recreate individual stacks

## Stack Dependencies

```
main.yaml
├── HelpersStack (no dependencies)
├── NetworkStack (no dependencies)
├── SecurityGroupsStack (depends on: Network, Helpers)
├── VPCEndpointsStack (depends on: Network, SecurityGroups)
├── IAMStack (no dependencies)
├── CognitoStack (no dependencies)
├── WAFStack (no dependencies)
├── StorageStack (depends on: Network, SecurityGroups, IAM) - Neptune with IAM auth
├── BatchStack (depends on: Network, SecurityGroups, IAM) - Export with IAM auth
├── LambdaStack (depends on: Network, SecurityGroups, IAM, Storage, Batch) - 14 functions with reserved concurrency
├── APIStack (depends on: Lambda, Cognito, WAF) - 22 endpoints with request validation
├── FrontendStack (depends on: API) - CloudFront with security headers
└── MLPipelineStack (depends on: IAM, Lambda, Storage)
```

## Key Improvements

### Security Groups
**Before**: 20+ separate ingress/egress rule resources  
**After**: 4 security groups with inline rules

### IAM Roles
**Before**: Duplicate policies in Neptune and SageMaker roles  
**After**: Shared managed policy referenced by both roles

### API Gateway
**Before**: 21 separate route resources  
**After**: Still 21 routes (required by HTTP API), but with OpenAPI spec for documentation

### Template Size
**Before**: 63KB monolithic template  
**After**: 
- Main: ~5KB
- Largest nested stack: ~8KB
- Total: ~45KB (more readable, better organized)

## Deployment

### Deploy with Nested Stacks
```bash
./deploy.sh
```

### What the Script Does
1. Creates S3 bucket for templates and Lambda code
2. Uploads all nested stack templates to S3
3. Packages and uploads Lambda functions
4. Deploys main stack (which deploys all nested stacks)
5. Populates Neptune with sample data
6. Starts ML training pipeline

### Undeploy
```bash
./undeploy.sh
```

## Production Readiness Improvements

### Implemented in Wave 1 (Current)
✅ Nested stack architecture  
✅ Inline security group rules  
✅ Shared IAM policies  
✅ OpenAPI specification  
✅ API throttling (5000 burst, 2000 rate)  
✅ CloudWatch Logs for API Gateway  
✅ S3 lifecycle policies (90-day retention)  
✅ Neptune backup retention (7 days)  
✅ DeletionPolicy: Retain on S3 and Neptune  
✅ Removed hardcoded role names  
✅ **No internet access from VPC** - All traffic via VPC endpoints  
✅ **ECR Public VPC endpoint** - Secure access to public container images  
✅ **Neptune export JAR from S3** - No public downloads  
✅ **WAF for API Gateway** - Rate limiting, OWASP Top 10, SQL injection protection  

### Planned for Wave 2
⏳ KMS encryption keys  
⏳ CloudWatch alarms  
⏳ Second NAT Gateway for HA  
⏳ VPC Flow Logs  
⏳ Lambda reserved concurrency  
⏳ Cost allocation tags  

### Planned for Wave 3
⏳ Multi-region support  
⏳ Disaster recovery automation  
⏳ Enhanced monitoring dashboard  
⏳ Automated testing pipeline  

## OpenAPI Specification

The API is now documented using OpenAPI 3.0 format:
- Location: `infrastructure/api-specs/fraud-detection-api.yaml`
- Includes request validation schemas
- Can be imported into Postman, Swagger UI, or API testing tools
- Enables automatic client SDK generation

### Using the OpenAPI Spec

**Import into Postman:**
```bash
# File → Import → Select fraud-detection-api.yaml
```

**Generate Python client:**
```bash
openapi-generator-cli generate \
  -i infrastructure/api-specs/fraud-detection-api.yaml \
  -g python \
  -o ./client
```

**View in Swagger UI:**
```bash
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/api/fraud-detection-api.yaml \
  -v $(pwd)/infrastructure/api-specs:/api \
  swaggerapi/swagger-ui
```

## Updating Individual Stacks

### Update Lambda Functions Only
```bash
# Package and upload new Lambda code
LAMBDA_CODE_VERSION=$(date +%Y%m%d%H%M%S)
# ... package functions ...

# Update Lambda stack
aws cloudformation update-stack \
  --stack-name auto-insurance-fraud-detection-LambdaStack-XXXXX \
  --use-previous-template \
  --parameters ParameterKey=LambdaCodeVersion,ParameterValue=$LAMBDA_CODE_VERSION
```

### Update API Routes
```bash
# Modify infrastructure/stacks/api.yaml
# Upload to S3
aws s3 cp infrastructure/stacks/api.yaml s3://$TEMPLATE_BUCKET/stacks/

# Update main stack (will update API nested stack)
aws cloudformation update-stack \
  --stack-name auto-insurance-fraud-detection \
  --use-previous-template
```

## Monitoring

### View Stack Status
```bash
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].StackStatus'
```

### View Nested Stack Events
```bash
# List all nested stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `auto-insurance`)].StackName'

# View events for specific nested stack
aws cloudformation describe-stack-events \
  --stack-name auto-insurance-fraud-detection-NetworkStack-XXXXX
```

## Cost Optimization

The nested stack architecture enables:
- **Selective deployment**: Only deploy what you need for dev/test
- **Easy teardown**: Delete expensive resources (Amazon Neptune) while keeping network
- **Resource tagging**: Better cost allocation per stack

### Deploy Network Only (for testing)
```bash
aws cloudformation deploy \
  --stack-name test-network \
  --template-file infrastructure/stacks/network.yaml
```

## Troubleshooting

### Stack Creation Failed
1. Check which nested stack failed:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name auto-insurance-fraud-detection \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
   ```

2. View detailed error for that nested stack

3. Fix the issue in the nested template

4. Delete the main stack and redeploy

### Update Failed
- AWS CloudFormation will automatically rollback
- Check events to see what failed
- Fix and retry update

### Circular Dependencies
- The stack order in main.yaml is carefully designed
- Don't modify DependsOn unless you understand the dependency chain

## Migration from Monolithic Template

If you have an existing deployment using `infrastructure.yaml`:

1. **Don't migrate in-place** - Deploy nested stacks as a new stack
2. **Export data from old Neptune** if needed
3. **Update DNS/endpoints** to point to new API
4. **Delete old stack** after validation

## Support

For issues with nested stacks:
1. Check CloudFormation events for the specific nested stack
2. Review the template for that stack in `infrastructure/stacks/`
3. Verify parameter passing from main.yaml
4. Check IAM permissions for CloudFormation service role
