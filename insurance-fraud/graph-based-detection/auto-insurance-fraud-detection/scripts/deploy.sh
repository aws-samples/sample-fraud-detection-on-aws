#!/bin/bash
set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
STACK_NAME="auto-insurance-fraud-detection"
CLOUDFRONT_WAF_STACK="auto-insurance-cloudfront-waf"

# Detect pip or pip3
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "❌ Error: Neither pip nor pip3 found. Please install Python pip."
    exit 1
fi

# Update pip
echo "🔧 Updating pip..."
$PIP_CMD install --upgrade pip --quiet 2>/dev/null || true

echo "🚀 Auto Insurance Fraud Detection - Deployment Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Stack: $STACK_NAME"
echo ""

# Get account ID and set up S3 bucket
ACCOUNT_ID=$(aws sts get-caller-identity --profile $PROFILE --query 'Account' --output text)
TEMPLATE_BUCKET="cf-templates-auto-insurance-${ACCOUNT_ID}-${REGION}"
LAMBDA_CODE_VERSION=$(date +%Y%m%d%H%M%S)

# Step 0: Deploy CloudFront WAF in us-east-1 (required for CloudFront)
echo "🛡️  Step 0/6: Deploying CloudFront WAF in us-east-1..."
echo "  (CloudFront WAF must be in us-east-1 regardless of deployment region)"

aws cloudformation deploy \
  --stack-name $CLOUDFRONT_WAF_STACK \
  --template-file infrastructure/stacks/cloudfront-waf.yaml \
  --profile $PROFILE \
  --region us-east-1 \
  --no-fail-on-empty-changeset

# Get WAF WebACL ARN
CLOUDFRONT_WAF_ARN=$(aws cloudformation describe-stacks \
  --stack-name $CLOUDFRONT_WAF_STACK \
  --profile $PROFILE \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`WebACLArn`].OutputValue' \
  --output text)

echo "  ✓ CloudFront WAF ARN: $CLOUDFRONT_WAF_ARN"
echo "✅ CloudFront WAF deployed!"
echo ""

# Create S3 bucket for templates and Lambda code
echo "📦 Step 1/6: Creating S3 bucket for templates..."
aws s3 mb s3://$TEMPLATE_BUCKET --profile $PROFILE --region $REGION 2>/dev/null || true
echo "✅ S3 bucket ready!"
echo ""

# Upload nested stack templates
echo "📤 Step 2/6: Uploading nested stack templates and Neptune export JAR..."
aws s3 sync infrastructure/stacks/ s3://$TEMPLATE_BUCKET/stacks/ \
  --profile $PROFILE \
  --region $REGION \
  --delete \
  --quiet

# Upload API specs
aws s3 cp infrastructure/api-specs/ s3://$TEMPLATE_BUCKET/api-specs/ \
  --recursive \
  --profile $PROFILE \
  --region $REGION \
  --quiet

# Download and upload Neptune export JAR to S3 (for Batch jobs)
if [ ! -f /tmp/neptune-export.jar ] || [ $(stat -f%z /tmp/neptune-export.jar 2>/dev/null || echo 0) -lt 60000000 ]; then
  echo "  → Downloading Neptune export JAR (189MB, may take a few minutes)..."
  curl --max-time 1800 --connect-timeout 30 --retry 3 --retry-delay 5 --progress-bar \
    https://s3.amazonaws.com/aws-neptune-customer-samples/neptune-export/bin/v2.latest/neptune-export.jar \
    -o /tmp/neptune-export.jar
else
  echo "  → Using cached Neptune export JAR..."
fi

echo "  → Uploading Neptune export JAR to S3..."
aws s3 cp /tmp/neptune-export.jar s3://$TEMPLATE_BUCKET/neptune-export/neptune-export.jar \
  --profile $PROFILE \
  --region $REGION \
  --quiet
echo "✅ Templates and JAR uploaded!"
echo ""

# Package and upload Lambda functions
echo "📦 Step 3/6: Packaging and uploading Lambda functions..."

package_and_upload() {
  local dir=$1
  local name=$2
  
  # Clean up any existing deployment.zip
  rm -f "$dir/deployment.zip"
  
  if [ -f "$dir/requirements.txt" ] && [ -s "$dir/requirements.txt" ]; then
    echo "  → Packaging $name (with dependencies)"
    (cd "$dir" && rm -rf package && \
     $PIP_CMD install -r requirements.txt -t package --quiet && \
     cp lambda_function.py package/ && \
     cd package && zip -rq ../deployment.zip . && \
     cd .. && rm -rf package)
  else
    echo "  → Packaging $name"
    (cd "$dir" && zip -q deployment.zip lambda_function.py)
  fi
  
  aws s3 cp "$dir/deployment.zip" \
    "s3://$TEMPLATE_BUCKET/lambda-code/$LAMBDA_CODE_VERSION/$name.zip" \
    --profile $PROFILE \
    --region $REGION \
    --quiet
  
  # Clean up deployment.zip after upload
  rm -f "$dir/deployment.zip"
}

package_and_upload "lambda-functions/populate-graph" "populate-graph"
package_and_upload "lambda-functions/authenticate-user" "authenticate-user"
package_and_upload "lambda-functions/neptune-pipeline/request-quotas" "request-quotas"
package_and_upload "lambda-functions/neptune-pipeline/check-quota-status" "check-quota-status"
package_and_upload "lambda-functions/neptune-pipeline/start-neptune-export" "start-neptune-export"
package_and_upload "lambda-functions/neptune-pipeline/check-neptune-export" "check-neptune-export"
package_and_upload "lambda-functions/neptune-pipeline/process-exported-data" "process-exported-data"
package_and_upload "lambda-functions/neptune-pipeline/check-processing-status" "check-processing-status"
package_and_upload "lambda-functions/neptune-pipeline/validate-training-data" "validate-training-data"
package_and_upload "lambda-functions/neptune-pipeline/train-model" "train-model"
package_and_upload "lambda-functions/neptune-pipeline/check-training-status" "check-training-status"
package_and_upload "lambda-functions/neptune-pipeline/test-model-performance" "test-model-performance"
package_and_upload "lambda-functions/neptune-pipeline/deploy-endpoint" "deploy-endpoint"
package_and_upload "lambda-functions/neptune-pipeline/update-fraud-config" "update-fraud-config"
package_and_upload "lambda-functions/fraud-detection" "fraud-detection"

echo "✅ Lambda packages uploaded!"
echo ""

# Deploy main CloudFormation stack
echo "☁️  Step 4/6: Deploying CloudFormation stack (nested stacks)..."
echo "  This will take ~15-20 minutes..."
echo ""

aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file infrastructure/main.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile $PROFILE \
  --region $REGION \
  --parameter-overrides \
    TemplateBucket=$TEMPLATE_BUCKET \
    LambdaCodeBucket=$TEMPLATE_BUCKET \
    LambdaCodeVersion=$LAMBDA_CODE_VERSION \
    CloudFrontWebACLArn=$CLOUDFRONT_WAF_ARN \
    AllowedOrigin="*"

echo "✅ CloudFormation stack deployed!"
echo ""

# Get deployment outputs
echo "📋 Retrieving deployment information..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text)

USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text)

# Re-deploy to set the real AllowedOrigin now that CloudFront URL is known
echo "🔒 Step 4b/6: Updating CORS AllowedOrigin with CloudFront URL..."
aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file infrastructure/main.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile $PROFILE \
  --region $REGION \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    TemplateBucket=$TEMPLATE_BUCKET \
    LambdaCodeBucket=$TEMPLATE_BUCKET \
    LambdaCodeVersion=$LAMBDA_CODE_VERSION \
    CloudFrontWebACLArn=$CLOUDFRONT_WAF_ARN \
    AllowedOrigin=$CLOUDFRONT_URL
echo "✅ CORS AllowedOrigin updated!"

# Deploy frontend
echo "🌐 Step 5/6: Deploying frontend to S3 and CloudFront..."

# Generate frontend config from CloudFormation outputs
./scripts/generate-frontend-config.sh "$STACK_NAME" "$REGION" "$PROFILE"

# Upload frontend files to S3
aws s3 sync frontend/ s3://${FRONTEND_BUCKET}/ \
  --profile $PROFILE \
  --region $REGION \
  --delete \
  --exclude "README.md"

echo "✅ Frontend deployed!"
echo ""

# Create new API Gateway deployment so updated CORS headers take effect
echo "🔄 Creating new API Gateway deployment..."
API_ID=$(echo $API_ENDPOINT | sed 's|https://||;s|\.execute-api.*||')
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Deployment with AllowedOrigin=$CLOUDFRONT_URL" \
  --region $REGION --profile $PROFILE \
  --query 'id' --output text 2>/dev/null && echo "✅ API Gateway deployed with correct CORS origin!" || echo "⚠️  API Gateway deployment skipped"

aws apigateway flush-stage-cache \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION --profile $PROFILE 2>/dev/null || true
echo ""

# Populate Neptune Graph
echo "🌱 Step 6/6: Populating Neptune graph with sample data..."

# Get actual function name from CloudFormation outputs
POPULATE_FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --profile $PROFILE \
  --query 'Stacks[0].Outputs[?OutputKey==`PopulateGraphFunctionName`].OutputValue' \
  --output text)
  
# Invoke with longer timeout (Lambda has 15 min timeout)
aws lambda invoke \
  --function-name $POPULATE_FUNCTION_NAME \
  --profile $PROFILE \
  --region $REGION \
  --cli-read-timeout 300 \
  --cli-binary-format raw-in-base64-out \
  --payload '{}' \
  /tmp/populate-response.json

POPULATE_RESULT=$(cat /tmp/populate-response.json 2>/dev/null)

echo ""

# Get remaining deployment outputs
echo "📋 Retrieving remaining deployment information..."
NEPTUNE_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`NeptuneClusterEndpoint`].OutputValue' \
  --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

# Start ML training pipeline
echo "🎓 Starting ML training pipeline..."
EXECUTION_ARN=$(aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --profile $PROFILE \
  --region $REGION \
  --input "{\"neptuneEndpoint\":\"$NEPTUNE_ENDPOINT\",\"s3Bucket\":\"$S3_BUCKET\",\"targetProperty\":\"fraudScore\"}" \
  --query 'executionArn' \
  --output text 2>&1)

echo "✅ ML training pipeline started successfully!"
echo "   Execution ARN: $EXECUTION_ARN"
echo "   Note: Training takes 1-2 hours to complete"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Deployment Summary:"
echo "  Region:           $REGION"
echo "  API Endpoint:     $API_ENDPOINT"
echo "  CloudFront URL:   $CLOUDFRONT_URL"
echo "  Neptune Endpoint: $NEPTUNE_ENDPOINT"
echo "  S3 Bucket:        $S3_BUCKET"
echo ""
echo "🔐 Authentication (Cognito):"
echo "  User Pool ID:     $USER_POOL_ID"
echo "  Client ID:        $USER_POOL_CLIENT_ID"
echo ""
echo "👤 Create First User:"
echo "  aws cognito-idp admin-create-user \\"
echo "    --user-pool-id $USER_POOL_ID \\"
echo "    --username user@company.com \\"
echo "    --user-attributes Name=email,Value=user@company.com \\"
echo "    --temporary-password <YOUR_TEMPORARY_PASSWORD> \\"
echo "    --region $REGION --profile $PROFILE"
echo ""
echo "  aws cognito-idp admin-set-user-password \\"
echo "    --user-pool-id $USER_POOL_ID \\"
echo "    --username user@company.com \\"
echo "    --password <YOUR_SECURE_PASSWORD> \\"
echo "    --permanent \\"
echo "    --region $REGION --profile $PROFILE"
echo ""
echo "🎓 ML Training Pipeline:"
echo "  Status:           Running (takes 1-2 hours)"
echo "  Execution ARN:    $EXECUTION_ARN"
echo ""
echo "🧪 Test API (Requires Authentication):"
echo "  # Get token"
echo "  TOKEN=\$(aws cognito-idp admin-initiate-auth \\"
echo "    --auth-flow ADMIN_USER_PASSWORD_AUTH \\"
echo "    --client-id $USER_POOL_CLIENT_ID \\"
echo "    --user-pool-id $USER_POOL_ID \\"
echo "    --auth-parameters USERNAME=user@company.com,PASSWORD=SecurePassword123! \\"
echo "    --region $REGION --profile $PROFILE \\"
echo "    --query 'AuthenticationResult.IdToken' --output text)"
echo ""
echo "  # Call API"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" \\"
echo "    $API_ENDPOINT/analytics/fraud-trends"
echo ""
echo "📈 Monitor ML Pipeline:"
echo "  aws stepfunctions describe-execution \\"
echo "    --execution-arn $EXECUTION_ARN \\"
echo "    --region $REGION \\"
echo "    --profile $PROFILE"