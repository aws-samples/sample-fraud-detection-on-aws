#!/bin/bash

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
STACK_NAME="auto-insurance-fraud-detection"
OUTPUT_FILE=".auth-cookie"

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
      echo "Authenticates against the API via /auth/login and stores the returned"
      echo "httpOnly session cookie in a curl-compatible cookie jar file."
      echo ""
      echo "Options:"
      echo "  -u, --username <email>    User email (required)"
      echo "  -p, --password <pass>     User password (optional, generates random if not provided)"
      echo "  --region <region>         AWS region (default: \$AWS_REGION or us-east-1)"
      echo "  --profile <profile>       AWS profile (default: \$AWS_PROFILE or default)"
      echo "  --output <file>           Cookie jar output file (default: .auth-cookie)"
      echo "  --create-only             Only create user, don't authenticate"
      echo "  --token-only              Only log in for existing user (reuses --output)"
      echo "  -h, --help                Show this help message"
      echo ""
      echo "After authentication, call the API with:"
      echo "  curl -b .auth-cookie https://YOUR-API/prod/analytics/fraud-trends"
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

# Get Cognito + API configuration from CloudFormation
echo "📋 Retrieving stack configuration..."
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

API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --profile $PROFILE \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$USER_POOL_ID" ] || [ -z "$CLIENT_ID" ] || [ -z "$API_ENDPOINT" ]; then
  echo "❌ Error: Could not retrieve configuration from stack (UserPoolId, UserPoolClientId, APIEndpoint)"
  exit 1
fi

echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID:    $CLIENT_ID"
echo "  API Endpoint: $API_ENDPOINT"
echo ""

# Helper: log in via /auth/login and save the Set-Cookie to a cookie jar
login_and_save_cookie() {
  local _user=$1
  local _pass=$2
  local _out=$3

  local http_code
  http_code=$(curl -s -c "$_out" -o /tmp/login.$$.json -w "%{http_code}" \
    -X POST "$API_ENDPOINT/auth/login" \
    -H "Content-Type: application/json" \
    --data "$(printf '{"username":"%s","password":"%s"}' "$_user" "$_pass")")

  if [ "$http_code" != "200" ]; then
    echo "❌ Authentication failed (HTTP $http_code)"
    cat /tmp/login.$$.json 2>/dev/null
    rm -f /tmp/login.$$.json
    return 1
  fi

  rm -f /tmp/login.$$.json

  if ! grep -q "__Host-fraud_detection_token" "$_out" 2>/dev/null; then
    echo "❌ Login succeeded but no auth cookie was returned"
    return 1
  fi
  return 0
}

# Token-only mode
if [ "$TOKEN_ONLY" = true ]; then
  if [ -z "$PASSWORD" ]; then
    echo "❌ Error: Password required for --token-only mode"
    exit 1
  fi

  echo "🔑 Authenticating user..."
  if ! login_and_save_cookie "$USERNAME" "$PASSWORD" "$OUTPUT_FILE"; then
    exit 1
  fi

  echo "✅ Cookie saved to $OUTPUT_FILE"
  echo ""
  echo "Call the API with:"
  echo "  curl -b $OUTPUT_FILE $API_ENDPOINT/analytics/fraud-trends"
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

# Log in and save cookie
echo "🔑 Authenticating user..."
if ! login_and_save_cookie "$USERNAME" "$PASSWORD" "$OUTPUT_FILE"; then
  exit 1
fi

echo "✅ Authentication successful!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Authentication Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Cookie jar saved to: $OUTPUT_FILE"
echo ""
echo "Call the API with:"
echo "  curl -b $OUTPUT_FILE $API_ENDPOINT/analytics/fraud-trends"
