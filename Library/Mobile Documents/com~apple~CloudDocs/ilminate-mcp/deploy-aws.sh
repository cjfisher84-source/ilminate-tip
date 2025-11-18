#!/bin/bash
# AWS Deployment Script for ilminate-mcp

set -e

# Configuration
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
CLUSTER_NAME=${CLUSTER_NAME:-ilminate-mcp}

echo "🚀 Deploying ilminate-mcp to AWS"
echo "Region: ${REGION}"
echo "Account: ${ACCOUNT_ID}"
echo ""

# Step 1: Create ECR repositories
echo "📦 Creating ECR repositories..."
aws ecr describe-repositories --repository-names ilminate-mcp-server --region ${REGION} 2>/dev/null || \
  aws ecr create-repository --repository-name ilminate-mcp-server --region ${REGION}

aws ecr describe-repositories --repository-names ilminate-apex-bridge --region ${REGION} 2>/dev/null || \
  aws ecr create-repository --repository-name ilminate-apex-bridge --region ${REGION}

# Step 2: Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_BASE}

# Step 3: Build and push MCP Server
echo "🏗️  Building MCP Server..."
npm run build
docker build -t ilminate-mcp-server .
docker tag ilminate-mcp-server:latest ${ECR_BASE}/ilminate-mcp-server:latest
docker push ${ECR_BASE}/ilminate-mcp-server:latest

# Step 4: Build and push APEX Bridge
echo "🏗️  Building APEX Bridge..."
cd bridge
docker build -t ilminate-apex-bridge .
docker tag ilminate-apex-bridge:latest ${ECR_BASE}/ilminate-apex-bridge:latest
docker push ${ECR_BASE}/ilminate-apex-bridge:latest
cd ..

# Step 5: Create CloudWatch log groups
echo "📊 Creating CloudWatch log groups..."
aws logs create-log-group --log-group-name /ecs/ilminate-mcp-server --region ${REGION} 2>/dev/null || true
aws logs create-log-group --log-group-name /ecs/ilminate-apex-bridge --region ${REGION} 2>/dev/null || true

# Step 6: Update task definitions with actual image URIs
echo "📝 Updating task definitions..."
sed "s|<account-id>|${ACCOUNT_ID}|g; s|<region>|${REGION}|g" ecs/mcp-server-task.json > /tmp/mcp-server-task.json
sed "s|<account-id>|${ACCOUNT_ID}|g; s|<region>|${REGION}|g" ecs/apex-bridge-task.json > /tmp/apex-bridge-task.json

# Step 7: Register task definitions
echo "📋 Registering task definitions..."
aws ecs register-task-definition --cli-input-json file:///tmp/mcp-server-task.json --region ${REGION}
aws ecs register-task-definition --cli-input-json file:///tmp/apex-bridge-task.json --region ${REGION}

# Step 8: Create ECS cluster (if doesn't exist)
echo "🏭 Creating ECS cluster..."
aws ecs describe-clusters --clusters ${CLUSTER_NAME} --region ${REGION} 2>/dev/null || \
  aws ecs create-cluster --cluster-name ${CLUSTER_NAME} --region ${REGION}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Update ecs/*-task.json with your VPC subnets and security groups"
echo "2. Create ECS services:"
echo "   aws ecs create-service --cluster ${CLUSTER_NAME} --service-name apex-bridge --task-definition ilminate-apex-bridge --desired-count 1 --launch-type FARGATE --network-configuration ..."
echo "   aws ecs create-service --cluster ${CLUSTER_NAME} --service-name mcp-server --task-definition ilminate-mcp-server --desired-count 1 --launch-type FARGATE --network-configuration ..."
echo ""
echo "See AWS_DEPLOYMENT.md for detailed instructions."

