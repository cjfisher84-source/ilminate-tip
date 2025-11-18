#!/bin/bash
# Complete ECS/Fargate Setup Script for ilminate-mcp
# This script sets up everything needed for AWS deployment

set -e

echo "🚀 ilminate-mcp ECS/Fargate Setup"
echo "=================================="
echo ""

# Configuration
REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-ilminate-mcp}

# Get AWS account info
echo "📋 Checking AWS configuration..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Error: AWS CLI not configured or no credentials found"
    echo "   Run: aws configure"
    exit 1
fi

echo "✅ AWS Account: $ACCOUNT_ID"
echo "✅ Region: $REGION"
echo ""

# Step 1: Get VPC and Subnet Information
echo "🔍 Finding VPC and Subnet information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $REGION 2>/dev/null || echo "")

if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
    echo "⚠️  No default VPC found. Please provide VPC ID:"
    read -p "VPC ID: " VPC_ID
fi

echo "✅ Using VPC: $VPC_ID"

# Get subnets
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region $REGION)
SUBNET_COUNT=$(echo $SUBNETS | wc -w | xargs)

if [ "$SUBNET_COUNT" -lt 2 ]; then
    echo "⚠️  Warning: Need at least 2 subnets for high availability"
    echo "   Found: $SUBNET_COUNT subnet(s)"
    echo "   Subnets: $SUBNETS"
fi

SUBNET_1=$(echo $SUBNETS | cut -d' ' -f1)
SUBNET_2=$(echo $SUBNETS | cut -d' ' -f2 || echo $SUBNET_1)

echo "✅ Using Subnets: $SUBNET_1, $SUBNET_2"
echo ""

# Step 2: Create Security Group
echo "🔒 Creating Security Group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name ilminate-mcp-sg \
  --description "Security group for ilminate MCP services" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=ilminate-mcp-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $REGION)

echo "✅ Security Group: $SG_ID"

# Get VPC CIDR
VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock' --output text --region $REGION)

# Add ingress rules (idempotent)
echo "   Adding ingress rules..."
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8888 \
  --cidr $VPC_CIDR \
  --region $REGION 2>/dev/null || echo "   Port 8888 already allowed"

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr $VPC_CIDR \
  --region $REGION 2>/dev/null || echo "   Port 3000 already allowed"

# Add egress rule
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --protocol -1 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "   Egress already allowed"

echo ""

# Step 3: Create IAM Roles
echo "👤 Creating IAM Roles..."

# Task Execution Role
echo "   Creating task execution role..."
aws iam get-role --role-name ecsTaskExecutionRole --region $REGION >/dev/null 2>&1 || \
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' >/dev/null

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  2>/dev/null || echo "   Policy already attached"

# Task Role for MCP Server
echo "   Creating MCP server task role..."
aws iam get-role --role-name ilminate-mcp-server-task-role --region $REGION >/dev/null 2>&1 || \
aws iam create-role \
  --role-name ilminate-mcp-server-task-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' >/dev/null

# Create inline policy for Secrets Manager
cat > /tmp/mcp-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ],
    "Resource": "arn:aws:secretsmanager:${REGION}:${ACCOUNT_ID}:secret:ilminate/*"
  }]
}
EOF

aws iam put-role-policy \
  --role-name ilminate-mcp-server-task-role \
  --policy-name SecretsManagerAccess \
  --policy-document file:///tmp/mcp-secrets-policy.json \
  2>/dev/null || echo "   Policy already exists"

echo "✅ IAM roles created"
echo ""

# Step 4: Create Secrets (with prompts)
echo "🔐 Setting up Secrets Manager..."
echo "   You'll be prompted to create secrets (or skip if they exist)"
echo ""

read -p "Create apex-api-key secret? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Enter APEX API key: " APEX_KEY
    echo
    aws secretsmanager create-secret \
      --name ilminate/apex-api-key \
      --secret-string "$APEX_KEY" \
      --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
      --secret-id ilminate/apex-api-key \
      --secret-string "$APEX_KEY" \
      --region $REGION >/dev/null
    echo "✅ apex-api-key secret created/updated"
fi

read -p "Create portal-api-key secret? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Enter Portal API key: " PORTAL_KEY
    echo
    aws secretsmanager create-secret \
      --name ilminate/portal-api-key \
      --secret-string "$PORTAL_KEY" \
      --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
      --secret-id ilminate/portal-api-key \
      --secret-string "$PORTAL_KEY" \
      --region $REGION >/dev/null
    echo "✅ portal-api-key secret created/updated"
fi

read -p "Create siem-password secret? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Enter SIEM password: " SIEM_PASS
    echo
    aws secretsmanager create-secret \
      --name ilminate/siem-password \
      --secret-string "$SIEM_PASS" \
      --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
      --secret-id ilminate/siem-password \
      --secret-string "$SIEM_PASS" \
      --region $REGION >/dev/null
    echo "✅ siem-password secret created/updated"
fi

echo ""

# Step 5: Update Task Definitions
echo "📝 Updating task definitions with your values..."

# Update task definitions
sed "s|<account-id>|${ACCOUNT_ID}|g; s|<region>|${REGION}|g" ecs/mcp-server-task.json > /tmp/mcp-server-task.json
sed "s|<account-id>|${ACCOUNT_ID}|g; s|<region>|${REGION}|g" ecs/apex-bridge-task.json > /tmp/apex-bridge-task.json

echo "✅ Task definitions updated"
echo ""

# Step 6: Run Deployment Script
echo "🚀 Running deployment script..."
echo "   This will build Docker images and push to ECR"
echo ""

read -p "Continue with Docker build and ECR push? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./deploy-aws.sh
else
    echo "⏭️  Skipping Docker build. Run './deploy-aws.sh' manually later."
fi

echo ""

# Step 7: Create ECS Services
echo "🏭 Creating ECS Services..."
echo ""

read -p "Create ECS services now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create APEX Bridge service
    echo "   Creating apex-bridge service..."
    aws ecs create-service \
      --cluster $CLUSTER_NAME \
      --service-name apex-bridge \
      --task-definition ilminate-apex-bridge \
      --desired-count 1 \
      --launch-type FARGATE \
      --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
      --region $REGION 2>/dev/null || \
    aws ecs update-service \
      --cluster $CLUSTER_NAME \
      --service-name apex-bridge \
      --task-definition ilminate-apex-bridge \
      --region $REGION >/dev/null
    
    echo "✅ apex-bridge service created/updated"
    
    # Create MCP Server service
    echo "   Creating mcp-server service..."
    aws ecs create-service \
      --cluster $CLUSTER_NAME \
      --service-name mcp-server \
      --task-definition ilminate-mcp-server \
      --desired-count 1 \
      --launch-type FARGATE \
      --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
      --region $REGION 2>/dev/null || \
    aws ecs update-service \
      --cluster $CLUSTER_NAME \
      --service-name mcp-server \
      --task-definition ilminate-mcp-server \
      --region $REGION >/dev/null
    
    echo "✅ mcp-server service created/updated"
else
    echo "⏭️  Skipping service creation. Run these commands manually:"
    echo ""
    echo "aws ecs create-service \\"
    echo "  --cluster $CLUSTER_NAME \\"
    echo "  --service-name apex-bridge \\"
    echo "  --task-definition ilminate-apex-bridge \\"
    echo "  --desired-count 1 \\"
    echo "  --launch-type FARGATE \\"
    echo "  --network-configuration \"awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}\" \\"
    echo "  --region $REGION"
    echo ""
    echo "aws ecs create-service \\"
    echo "  --cluster $CLUSTER_NAME \\"
    echo "  --service-name mcp-server \\"
    echo "  --task-definition ilminate-mcp-server \\"
    echo "  --desired-count 1 \\"
    echo "  --launch-type FARGATE \\"
    echo "  --network-configuration \"awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}\" \\"
    echo "  --region $REGION"
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📊 Next Steps:"
echo "1. Check service status:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services apex-bridge mcp-server --region $REGION"
echo ""
echo "2. View logs:"
echo "   aws logs tail /ecs/ilminate-apex-bridge --follow --region $REGION"
echo "   aws logs tail /ecs/ilminate-mcp-server --follow --region $REGION"
echo ""
echo "3. See ECS_SETUP_GUIDE.md for detailed instructions and troubleshooting"
echo ""

