# ECS/Fargate Deployment Guide - Step by Step

**Complete guide to deploy ilminate-mcp on AWS ECS/Fargate**

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed and running
- [ ] AWS account with appropriate permissions
- [ ] Existing VPC and subnets (or create new ones)
- [ ] Security groups configured
- [ ] IAM roles created (or we'll create them)

---

## Step 1: Verify Prerequisites

### Check AWS CLI
```bash
aws --version
aws sts get-caller-identity
```

### Check Docker
```bash
docker --version
docker ps
```

### Check Node.js
```bash
node --version  # Should be 18+
npm --version
```

---

## Step 2: Configure AWS Settings

### Set Environment Variables

```bash
# Set your AWS region
export AWS_REGION=us-east-1  # Change to your preferred region

# Set cluster name
export CLUSTER_NAME=ilminate-mcp

# Verify account ID
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"
echo "Region: $AWS_REGION"
```

### Get Your VPC Information

```bash
# List your VPCs
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table

# List subnets
aws ec2 describe-subnets --query 'Subnets[*].[SubnetId,VpcId,AvailabilityZone,CidrBlock]' --output table

# Note down:
# - VPC ID
# - At least 2 subnet IDs (for high availability)
# - Security group ID (or create new one)
```

---

## Step 3: Create Security Groups

### Create Security Group for MCP Services

```bash
# Get your VPC ID first
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "Using VPC: $VPC_ID"

# Create security group for MCP services
SG_ID=$(aws ec2 create-security-group \
  --group-name ilminate-mcp-sg \
  --description "Security group for ilminate MCP services" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

echo "Security Group ID: $SG_ID"

# Allow inbound HTTP from VPC
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8888 \
  --cidr $(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock' --output text)

# Allow inbound HTTP for MCP server (if using HTTP transport)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr $(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock' --output text)

# Allow outbound traffic
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --protocol -1 \
  --cidr 0.0.0.0/0
```

---

## Step 4: Create IAM Roles

### Create Task Execution Role

```bash
# Create trust policy
cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role (if doesn't exist)
aws iam get-role --role-name ecsTaskExecutionRole 2>/dev/null || \
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file:///tmp/ecs-trust-policy.json

# Attach managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Create Task Role for MCP Server

```bash
# Create task role
cat > /tmp/mcp-task-role-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name ilminate-mcp-server-task-role \
  --assume-role-policy-document file:///tmp/mcp-task-role-trust.json

# Create policy for accessing Secrets Manager
cat > /tmp/mcp-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:ilminate/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name ilminate-mcp-server-task-role \
  --policy-name SecretsManagerAccess \
  --policy-document file:///tmp/mcp-secrets-policy.json
```

---

## Step 5: Create Secrets in Secrets Manager

### Store API Keys

```bash
# Create secrets (replace with your actual values)
aws secretsmanager create-secret \
  --name ilminate/apex-api-key \
  --secret-string "your-apex-api-key-here" \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name ilminate/portal-api-key \
  --secret-string "your-portal-api-key-here" \
  --region $AWS_REGION

aws secretsmanager create-secret \
  --name ilminate/siem-password \
  --secret-string "your-siem-password-here" \
  --region $AWS_REGION
```

---

## Step 6: Update Task Definitions

### Update with Your Values

Edit `ecs/mcp-server-task.json`:
- Replace `<account-id>` with your account ID
- Replace `<region>` with your region
- Update task role ARNs if different

Edit `ecs/apex-bridge-task.json`:
- Replace `<account-id>` with your account ID
- Replace `<region>` with your region

---

## Step 7: Run Deployment Script

```bash
# Make script executable
chmod +x deploy-aws.sh

# Set environment variables
export AWS_REGION=us-east-1
export CLUSTER_NAME=ilminate-mcp

# Run deployment
./deploy-aws.sh
```

This will:
1. Create ECR repositories
2. Build Docker images
3. Push images to ECR
4. Create CloudWatch log groups
5. Register task definitions

---

## Step 8: Create ECS Services

### Get Your Subnet IDs

```bash
# Get subnet IDs in your VPC
SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[*].SubnetId' \
  --output text)

echo "Subnets: $SUBNETS"
SUBNET_1=$(echo $SUBNETS | cut -d' ' -f1)
SUBNET_2=$(echo $SUBNETS | cut -d' ' -f2)
```

### Create APEX Bridge Service

```bash
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name apex-bridge \
  --task-definition ilminate-apex-bridge \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION
```

### Create MCP Server Service

```bash
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name mcp-server \
  --task-definition ilminate-mcp-server \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION
```

---

## Step 9: Verify Deployment

### Check Service Status

```bash
# Check services
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services apex-bridge mcp-server \
  --region $AWS_REGION \
  --query 'services[*].[serviceName,status,runningCount,desiredCount]' \
  --output table

# Check tasks
aws ecs list-tasks \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION

# Get task details
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name apex-bridge --region $AWS_REGION --query 'taskArns[0]' --output text)
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $TASK_ARN \
  --region $AWS_REGION \
  --query 'tasks[0].[lastStatus,healthStatus,containers[0].name]' \
  --output table
```

### Check Logs

```bash
# View APEX Bridge logs
aws logs tail /ecs/ilminate-apex-bridge --follow --region $AWS_REGION

# View MCP Server logs
aws logs tail /ecs/ilminate-mcp-server --follow --region $AWS_REGION
```

### Test Health Endpoints

```bash
# Get task IP address
TASK_IP=$(aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name apex-bridge --query 'taskArns[0]' --output text) \
  --region $AWS_REGION \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

# Test health endpoint
curl http://$TASK_IP:8888/health
```

---

## Step 10: Configure Auto-Scaling (Optional)

### Create Auto-Scaling Target

```bash
# For APEX Bridge
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER_NAME/apex-bridge \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3 \
  --region $AWS_REGION

# For MCP Server
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/$CLUSTER_NAME/mcp-server \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3 \
  --region $AWS_REGION
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service events
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services apex-bridge \
  --region $AWS_REGION \
  --query 'services[0].events[:5]' \
  --output table

# Check task stopped reason
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks <task-arn> \
  --region $AWS_REGION \
  --query 'tasks[0].stoppedReason'
```

### Container Exits Immediately

```bash
# Check logs
aws logs tail /ecs/ilminate-apex-bridge --since 10m --region $AWS_REGION

# Common issues:
# - Missing environment variables
# - Cannot connect to ilminate-agent
# - Port conflicts
```

### Cannot Connect to APEX Bridge

```bash
# Verify security group allows traffic
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --region $AWS_REGION

# Check task is running
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks <task-arn> \
  --region $AWS_REGION \
  --query 'tasks[0].lastStatus'
```

---

## Next Steps

1. **Set up CloudWatch Alarms** for monitoring
2. **Configure Application Load Balancer** (if using HTTP transport)
3. **Set up CI/CD** for automated deployments
4. **Configure backup** for task definitions
5. **Set up cost alerts** in AWS Budgets

---

## Quick Reference

### Useful Commands

```bash
# Update service (after code changes)
aws ecs update-service --cluster $CLUSTER_NAME --service-name apex-bridge --force-new-deployment

# Scale service
aws ecs update-service --cluster $CLUSTER_NAME --service-name apex-bridge --desired-count 2

# Stop service
aws ecs update-service --cluster $CLUSTER_NAME --service-name apex-bridge --desired-count 0

# Delete service
aws ecs delete-service --cluster $CLUSTER_NAME --service-name apex-bridge --force
```

---

**Ready to deploy!** Follow these steps in order, and you'll have ilminate-mcp running on AWS ECS/Fargate.

