# Quick Deploy to AWS ECS/Fargate

**Fastest way to get ilminate-mcp running on AWS**

---

## Prerequisites Check

```bash
# 1. AWS CLI configured?
aws sts get-caller-identity

# 2. Docker running?
docker ps

# 3. Node.js installed?
node --version  # Should be 18+

# 4. Dependencies installed?
cd ilminate-mcp
npm install
```

---

## Quick Start (Automated)

### Option A: Interactive Setup Script

```bash
# Run the complete setup script
./setup-ecs.sh
```

This script will:
1. ✅ Find your VPC and subnets
2. ✅ Create security groups
3. ✅ Create IAM roles
4. ✅ Set up Secrets Manager
5. ✅ Build and push Docker images
6. ✅ Create ECS services

**Just follow the prompts!**

---

## Quick Start (Manual - Step by Step)

### Step 1: Set Environment Variables

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=ilminate-mcp
```

### Step 2: Run Deployment Script

```bash
./deploy-aws.sh
```

This builds Docker images and pushes to ECR.

### Step 3: Get Your VPC Info

```bash
# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
echo "VPC: $VPC_ID"

# Get Subnets
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text)
SUBNET_1=$(echo $SUBNETS | cut -d' ' -f1)
SUBNET_2=$(echo $SUBNETS | cut -d' ' -f2 || echo $SUBNET_1)
echo "Subnets: $SUBNET_1, $SUBNET_2"
```

### Step 4: Create Security Group

```bash
SG_ID=$(aws ec2 create-security-group \
  --group-name ilminate-mcp-sg \
  --description "Security group for ilminate MCP" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Allow traffic
VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].CidrBlock' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8888 --cidr $VPC_CIDR
aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol -1 --cidr 0.0.0.0/0
```

### Step 5: Create ECS Services

```bash
# APEX Bridge
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name apex-bridge \
  --task-definition ilminate-apex-bridge \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"

# MCP Server
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name mcp-server \
  --task-definition ilminate-mcp-server \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"
```

---

## Verify Deployment

```bash
# Check services
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services apex-bridge mcp-server \
  --query 'services[*].[serviceName,status,runningCount]' \
  --output table

# View logs
aws logs tail /ecs/ilminate-apex-bridge --follow
aws logs tail /ecs/ilminate-mcp-server --follow
```

---

## Troubleshooting

### Service won't start?
```bash
# Check events
aws ecs describe-services --cluster $CLUSTER_NAME --services apex-bridge --query 'services[0].events[:5]' --output table

# Check logs
aws logs tail /ecs/ilminate-apex-bridge --since 10m
```

### Can't connect?
- Check security groups allow traffic
- Verify tasks are running: `aws ecs list-tasks --cluster $CLUSTER_NAME`
- Check CloudWatch logs for errors

---

## What's Next?

1. **Configure Secrets Manager** with your API keys
2. **Set up CloudWatch Alarms** for monitoring
3. **Configure Auto-Scaling** if needed
4. **Integrate with existing ilminate services**

See `ECS_SETUP_GUIDE.md` for detailed instructions.

---

**Ready?** Run `./setup-ecs.sh` and follow the prompts!

