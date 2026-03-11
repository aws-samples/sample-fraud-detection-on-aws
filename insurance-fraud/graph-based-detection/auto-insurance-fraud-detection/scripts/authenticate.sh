#!/bin/bash

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
STACK_NAME="auto-insurance-fraud-detection"
OUTPUT_FILE=".auth-token"

# Parse arguments
CREATE_ONLY=false
TOKEN_ONLY=false
USERNAME=""
PASSWORD=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -u|--username)
      USERNAME="$2"
      shift 2
      ;;
    -p|--password)
      PASSWORD="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --create-only)
      CREATE_ONLY=true
      shift
      ;;
    --token-only)
      TOKEN_ONLY=true
      shift
      ;;
    -h|--help)
      echo "Usage: ./authenticate.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -u, --username <email>    User email (required)"
      echo "  -p, --password <pass>     User password (optional, generates random if not provided)"
      echo "  --region <region>         AWS region (default: \$AWS_REGION or us-east-1)"
      echo "  --profile <profile>       AWS profile (default: \$AWS_PROFILE or default)"
      echo "  --output <file>           Token output file (default: .auth-token)"
      echo "  --create-only             Only create user, don't authenticate"
      echo "  --token-only              Only get token for existing user"
      echo "  -h, --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$USERNAME" ]; then
  echo "Error: Username is required. Use -u or --username"
  exit 1
fi

echo "🔐 Auto Insurance Fraud Detection - Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Username: $USERNAME"
echo ""

# Get Cognito configuration from CloudFormation
echo "📋 Retrieving Cognito configuration..."
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text 2>/dev/null)

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$USER_POOL_ID" ] || [ -z "$CLIENT_ID" ]; then
  echo "❌ Error: Could not retrieve Cognito configuration from stack"
  exit 1
fi

echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo ""

# Token-only mode
if [ "$TOKEN_ONLY" = true ]; then
  if [ -z "$PASSWORD" ]; then
    echo "❌ Error: Password required for --token-only mode"
    exit 1
  fi
  
  echo "🔑 Authenticating user..."
  TOKEN=$(aws cognito-idp admin-initiate-auth \
    --auth-flow ADMIN_USER_PASSWORD_AUTH \
    --client-id $CLIENT_ID \
    --user-pool-id $USER_POOL_ID \
    --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD \
    --region $REGION \
    --profile $PROFILE \
    --query 'AuthenticationResult.IdToken' \
    --output text 2>/dev/null)
  
  if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
    echo "❌ Authentication failed"
    exit 1
  fi
  
  echo "$TOKEN" > "$OUTPUT_FILE"
  echo "✅ Token saved to $OUTPUT_FILE"
  echo ""
  echo "JWT Token:"
  echo "$TOKEN"
  exit 0
fi

# Check if user exists
USER_EXISTS=$(aws cognito-idp admin-get-user \
  --user-pool-id $USER_POOL_ID \
  --username $USERNAME \
  --profile $PROFILE \
  --region $REGION 2>/dev/null && echo "true" || echo "false")

# Create user if doesn't exist
if [ "$USER_EXISTS" = "false" ]; then
  echo "👤 Creating user..."
  
  # Generate password if not provided
  if [ -z "$PASSWORD" ]; then
    PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    PASSWORD="${PASSWORD}Aa1!"
    echo "  Generated password: $PASSWORD"
  fi
  
  aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username $USERNAME \
    --user-attributes Name=email,Value=$USERNAME \
    --temporary-password TempPass123! \
    --profile $PROFILE \
    --region $REGION > /dev/null
  
  aws cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username $USERNAME \
    --password $PASSWORD \
    --permanent \
    --profile $PROFILE \
    --region $REGION > /dev/null
  
  echo "✅ User created successfully"
else
  echo "✅ User already exists"
  
  if [ -z "$PASSWORD" ]; then
    echo "❌ Error: Password required for existing user"
    exit 1
  fi
fi
echo ""

# Exit if create-only mode
if [ "$CREATE_ONLY" = true ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🎉 User Created!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Username: $USERNAME"
  echo "Password: $PASSWORD"
  exit 0
fi

# Authenticate and get token
echo "🔑 Authenticating user..."
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --user-pool-id $USER_POOL_ID \
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD \
  --region $REGION \
  --profile $PROFILE \
  --query 'AuthenticationResult.IdToken' \
  --output text 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
  echo "❌ Authentication failed. Check username and password."
  exit 1
fi

# Save token
echo "$TOKEN" > "$OUTPUT_FILE"

echo "✅ Authentication successful!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Authentication Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Token saved to: $OUTPUT_FILE"
echo ""
echo "JWT Token:"
echo "$TOKEN"
