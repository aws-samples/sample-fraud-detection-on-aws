#!/bin/bash
set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
STACK_NAME="auto-insurance-fraud-detection"
CLOUDFRONT_WAF_STACK="auto-insurance-cloudfront-waf"

echo "🗑️  Auto Insurance Fraud Detection - Undeploy Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Stack: $STACK_NAME"
echo ""
echo "⚠️  This will DELETE all resources."
echo ""

ACCOUNT_ID=$(aws sts get-caller-identity --profile $PROFILE --query 'Account' --output text)

# Step 1: Empty and delete S3 buckets (versioned)
echo "🪣 Step 1/5: Emptying S3 buckets..."
for BUCKET in "neptune-ml-auto-insurance-${ACCOUNT_ID}-${REGION}" "cf-templates-auto-insurance-${ACCOUNT_ID}-${REGION}" "fraud-detection-frontend-${ACCOUNT_ID}-${REGION}" "fraud-detection-frontend-logs-${ACCOUNT_ID}-${REGION}" "neptune-ml-logs-${ACCOUNT_ID}-${REGION}"; do
  if aws s3api head-bucket --bucket $BUCKET --profile $PROFILE --region $REGION 2>/dev/null; then
    echo "  → Emptying $BUCKET (this may take a while for versioned buckets)..."

    # Delete all object versions in batches
    while true; do
      VERSIONS=$(aws s3api list-object-versions --bucket $BUCKET --profile $PROFILE --region $REGION \
        --max-items 1000 --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null)

      if [ "$(echo "$VERSIONS" | jq '.Objects | length')" -eq 0 ] || [ "$(echo "$VERSIONS" | jq '.Objects')" == "null" ]; then
        break
      fi

      echo "$VERSIONS" | aws s3api delete-objects --bucket $BUCKET --delete file:///dev/stdin --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
    done

    # Delete all delete markers in batches
    while true; do
      MARKERS=$(aws s3api list-object-versions --bucket $BUCKET --profile $PROFILE --region $REGION \
        --max-items 1000 --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null)

      if [ "$(echo "$MARKERS" | jq '.Objects | length')" -eq 0 ] || [ "$(echo "$MARKERS" | jq '.Objects')" == "null" ]; then
        break
      fi

      echo "$MARKERS" | aws s3api delete-objects --bucket $BUCKET --delete file:///dev/stdin --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
    done

    # Delete bucket
    aws s3 rb s3://$BUCKET --profile $PROFILE --region $REGION 2>/dev/null || true
    echo "  ✓ $BUCKET deleted"
  fi
done
echo "✅ S3 buckets cleaned up!"
echo ""

# Get VPC ID from NetworkStack outputs
VPC_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
  --profile $PROFILE --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' --output text 2>/dev/null || echo "")

# If not found in outputs, try to get from NetworkStack directly
if [ -z "$VPC_ID" ]; then
  NETWORK_STACK=$(aws cloudformation describe-stack-resources --stack-name $STACK_NAME \
    --profile $PROFILE --region $REGION --query 'StackResources[?LogicalResourceId==`NetworkStack`].PhysicalResourceId' --output text 2>/dev/null || echo "")
  if [ -n "$NETWORK_STACK" ]; then
    VPC_ID=$(aws cloudformation describe-stacks --stack-name $NETWORK_STACK \
      --profile $PROFILE --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' --output text 2>/dev/null || echo "")
  fi
fi

# Step 2: Delete VPC endpoints (including GuardDuty-managed)
echo "🔌 Step 2/5: Deleting VPC endpoints..."
if [ -n "$VPC_ID" ]; then
  ENDPOINTS=$(aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" \
    --profile $PROFILE --region $REGION --query 'VpcEndpoints[*].VpcEndpointId' --output text 2>/dev/null || echo "")
  if [ -n "$ENDPOINTS" ]; then
    for EP in $ENDPOINTS; do
      echo "  → Deleting $EP"
      aws ec2 delete-vpc-endpoints --vpc-endpoint-ids $EP --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
    done
    
    # Wait for VPC endpoints to be fully deleted
    echo "  → Waiting for VPC endpoints to be deleted..."
    sleep 10
    
    # Wait for network interfaces to be released
    echo "  → Waiting for network interfaces to be released..."
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
      ENI_COUNT=$(aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" "Name=status,Values=in-use,available" \
        --profile $PROFILE --region $REGION --query 'length(NetworkInterfaces)' --output text 2>/dev/null || echo "0")
      if [ "$ENI_COUNT" -eq "0" ]; then
        echo "  ✓ All network interfaces released"
        break
      fi
      echo "  → Still waiting... ($ENI_COUNT ENIs remaining)"
      sleep 5
      WAITED=$((WAITED + 5))
    done
  fi
fi
echo "✅ VPC endpoints deleted!"
echo ""

# Step 3: Delete NAT Gateways
echo "🌐 Step 3/5: Deleting NAT Gateways..."
if [ -n "$VPC_ID" ]; then
  NAT_GWS=$(aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available,pending" \
    --profile $PROFILE --region $REGION --query 'NatGateways[*].NatGatewayId' --output text 2>/dev/null || echo "")
  for NAT in $NAT_GWS; do
    echo "  → Deleting $NAT"
    aws ec2 delete-nat-gateway --nat-gateway-id $NAT --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
  done
  # Wait for NAT Gateways to be deleted (they take time)
  if [ -n "$NAT_GWS" ]; then
    echo "  → Waiting for NAT Gateway deletion..."
    for NAT in $NAT_GWS; do
      aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT --profile $PROFILE --region $REGION 2>/dev/null || true
    done
  fi
fi
echo "✅ NAT Gateways deleted!"
echo ""

# Step 4: Delete security groups (including GuardDuty managed)
echo "🔒 Step 4/5: Cleaning up security groups..."
if [ -n "$VPC_ID" ]; then
  # Wait for ENIs to be released
  sleep 10

  SGs=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" \
    --profile $PROFILE --region $REGION --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null || echo "")

  # First, revoke all rules to break circular dependencies
  for SG in $SGs; do
    echo "  → Clearing rules from $SG"
    # Revoke ingress
    INGRESS=$(aws ec2 describe-security-groups --group-ids $SG --profile $PROFILE --region $REGION \
      --query 'SecurityGroups[0].IpPermissions' --output json 2>/dev/null)
    if [ "$INGRESS" != "[]" ] && [ "$INGRESS" != "null" ] && [ -n "$INGRESS" ]; then
      echo "$INGRESS" | aws ec2 revoke-security-group-ingress --group-id $SG --ip-permissions file:///dev/stdin \
        --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
    fi
    # Revoke egress
    EGRESS=$(aws ec2 describe-security-groups --group-ids $SG --profile $PROFILE --region $REGION \
      --query 'SecurityGroups[0].IpPermissionsEgress' --output json 2>/dev/null)
    if [ "$EGRESS" != "[]" ] && [ "$EGRESS" != "null" ] && [ -n "$EGRESS" ]; then
      echo "$EGRESS" | aws ec2 revoke-security-group-egress --group-id $SG --ip-permissions file:///dev/stdin \
        --profile $PROFILE --region $REGION > /dev/null 2>&1 || true
    fi
  done

  # Now delete the security groups
  for SG in $SGs; do
    echo "  → Deleting $SG"
    aws ec2 delete-security-group --group-id $SG --profile $PROFILE --region $REGION 2>/dev/null || true
  done
fi
echo "✅ Security groups cleaned up!"
echo ""

# Step 5: Delete CloudFormation stack with retry logic
echo "☁️  Step 5/5: Deleting CloudFormation stack..."
MAX_RETRIES=2
RETRY_COUNT=0

while [ $RETRY_COUNT -le $MAX_RETRIES ]; do
  if [ $RETRY_COUNT -gt 0 ]; then
    echo ""
    echo "🔄 Retry attempt $RETRY_COUNT/$MAX_RETRIES..."
    echo "  → Waiting for remaining resources to be released..."
    
    # Wait for VPC endpoints to finish deleting
    if [ -n "$VPC_ID" ]; then
      MAX_WAIT=120
      WAITED=0
      while [ $WAITED -lt $MAX_WAIT ]; do
        VPC_EP_COUNT=$(aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" \
          --profile $PROFILE --region $REGION --query 'length(VpcEndpoints[?State!=`deleted`])' --output text 2>/dev/null || echo "0")
        
        if [ "$VPC_EP_COUNT" -eq "0" ]; then
          break
        fi
        
        if [ $WAITED -eq 0 ]; then
          echo "  → Waiting for VPC endpoints ($VPC_EP_COUNT remaining)..."
        fi
        sleep 10
        WAITED=$((WAITED + 10))
      done
      
      # Wait for network interfaces to be released
      WAITED=0
      while [ $WAITED -lt $MAX_WAIT ]; do
        ENI_COUNT=$(aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" \
          --profile $PROFILE --region $REGION --query 'length(NetworkInterfaces)' --output text 2>/dev/null || echo "0")
        
        if [ "$ENI_COUNT" -eq "0" ]; then
          break
        fi
        
        if [ $WAITED -eq 0 ]; then
          echo "  → Waiting for network interfaces ($ENI_COUNT remaining)..."
        fi
        sleep 10
        WAITED=$((WAITED + 10))
      done
    fi
  fi
  
  aws cloudformation delete-stack --stack-name $STACK_NAME --profile $PROFILE --region $REGION 2>/dev/null || true
  echo "  → Waiting for stack deletion (this may take 10-15 minutes)..."
  
  if aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --profile $PROFILE --region $REGION 2>/dev/null; then
    echo "✅ Stack deleted successfully!"
    break
  fi
  
  # Check status
  STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE --region $REGION \
    --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DELETED")
  
  if [ "$STATUS" == "DELETED" ] || echo "$STATUS" | grep -q "does not exist"; then
    echo "✅ Stack deleted successfully!"
    break
  elif [ "$STATUS" == "DELETE_FAILED" ]; then
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo "⚠️  Stack deletion failed, will retry..."
      RETRY_COUNT=$((RETRY_COUNT + 1))
    else
      echo ""
      echo "❌ Stack deletion failed after $MAX_RETRIES retries."
      echo ""
      echo "Failed resources:"
      aws cloudformation describe-stack-events --stack-name $STACK_NAME --profile $PROFILE --region $REGION \
        --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table 2>/dev/null || true
      exit 1
    fi
  else
    echo "⚠️  Unexpected status: $STATUS"
    break
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Undeploy Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 6: Delete CloudFront WAF stack from us-east-1
echo "🛡️  Step 6/6: Deleting CloudFront WAF from us-east-1..."
aws cloudformation delete-stack --stack-name $CLOUDFRONT_WAF_STACK --profile $PROFILE --region us-east-1 2>/dev/null || true
aws cloudformation wait stack-delete-complete --stack-name $CLOUDFRONT_WAF_STACK --profile $PROFILE --region us-east-1 2>/dev/null || true
echo "✅ CloudFront WAF deleted!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Complete Undeploy Finished!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
