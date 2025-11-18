# AWS Deployment Guide for ilminate-mcp

**Answer**: AWS does **NOT** have a native MCP service. You need to build and deploy your own.

---

## AWS MCP Status

### ❌ No Native AWS MCP Service
- AWS does not provide a managed MCP (Model Context Protocol) service
- MCP is an open protocol from Anthropic, not an AWS service
- You must deploy your own MCP server

### ✅ AWS Marketplace MCP Servers (Third-Party)
AWS Marketplace has some third-party MCP servers:
- CircleCI MCP Server
- CloudFix Pricing Server MCP
- Wiz MCP Server

**But**: These are specific use cases, not general-purpose MCP infrastructure.

---

## Recommended AWS Deployment Architecture

Since your ilminate infrastructure is already on AWS, here's the best approach:

### Option 1: ECS/Fargate (Recommended) ⭐

**Best for**: Production deployment with existing AWS infrastructure

```
┌─────────────────────────────────────────┐
│   AWS ECS/Fargate                       │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   MCP Server Container            │  │
│  │   (Node.js)                       │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
│  ┌──────────────▼────────────────────┐  │
│  │   APEX Bridge Container           │  │
│  │   (Python Flask)                  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   Application Load Balancer       │  │
│  │   (for HTTP access)               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   Existing ilminate Infrastructure      │
│   - Lambda Functions                    │
│   - API Gateway                         │
│   - DynamoDB                            │
│   - S3                                  │
└─────────────────────────────────────────┘
```

**Why ECS/Fargate?**
- ✅ Works with stdio MCP transport (containers can run processes)
- ✅ Integrates with existing AWS infrastructure
- ✅ Auto-scaling capabilities
- ✅ Managed service (no EC2 management)
- ✅ Cost-effective for long-running services

### Option 2: EC2 Instance

**Best for**: Simple deployment, full control

**Why EC2?**
- ✅ Full control over environment
- ✅ Easy to debug
- ✅ Can run both MCP server and APEX Bridge on same instance
- ❌ You manage the instance (updates, security, etc.)

### Option 3: Lambda + API Gateway (Not Recommended)

**Why NOT Lambda?**
- ❌ MCP stdio transport doesn't work well with Lambda
- ❌ Would need HTTP adapter (adds complexity)
- ❌ APEX Bridge (Python Flask) needs persistent process
- ❌ Cold starts affect performance
- ❌ 15-minute timeout limit

**However**: Could use Lambda for HTTP-based MCP clients if you add HTTP transport.

---

## Deployment Steps: ECS/Fargate (Recommended)

### Step 1: Create Docker Images

#### Dockerfile for MCP Server

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy built application
COPY dist ./dist

# Expose port (for health checks)
EXPOSE 3000

# Start MCP server
CMD ["node", "dist/index.js"]
```

#### Dockerfile for APEX Bridge

Create `bridge/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY apex_bridge.py .

# Expose port
EXPOSE 8888

# Start bridge service
CMD ["python3", "apex_bridge.py"]
```

### Step 2: Build and Push to ECR

```bash
# Create ECR repositories
aws ecr create-repository --repository-name ilminate-mcp-server
aws ecr create-repository --repository-name ilminate-apex-bridge

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push MCP server
docker build -t ilminate-mcp-server .
docker tag ilminate-mcp-server:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-mcp-server:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-mcp-server:latest

# Build and push APEX Bridge
cd bridge
docker build -t ilminate-apex-bridge .
docker tag ilminate-apex-bridge:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-apex-bridge:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-apex-bridge:latest
```

### Step 3: Create ECS Task Definitions

#### MCP Server Task Definition

Create `ecs/mcp-server-task.json`:

```json
{
  "family": "ilminate-mcp-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "mcp-server",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-mcp-server:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APEX_BRIDGE_URL",
          "value": "http://apex-bridge:8888"
        },
        {
          "name": "LOG_LEVEL",
          "value": "info"
        }
      ],
      "secrets": [
        {
          "name": "APEX_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:ilminate/apex-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ilminate-mcp-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### APEX Bridge Task Definition

Create `ecs/apex-bridge-task.json`:

```json
{
  "family": "ilminate-apex-bridge",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "apex-bridge",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ilminate-apex-bridge:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8888,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APEX_BRIDGE_PORT",
          "value": "8888"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ilminate-apex-bridge",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 4: Create ECS Service

```bash
# Register task definitions
aws ecs register-task-definition --cli-input-json file://ecs/mcp-server-task.json
aws ecs register-task-definition --cli-input-json file://ecs/apex-bridge-task.json

# Create ECS cluster (if doesn't exist)
aws ecs create-cluster --cluster-name ilminate-mcp

# Create services
aws ecs create-service \
  --cluster ilminate-mcp \
  --service-name apex-bridge \
  --task-definition ilminate-apex-bridge \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

aws ecs create-service \
  --cluster ilminate-mcp \
  --service-name mcp-server \
  --task-definition ilminate-mcp-server \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Step 5: Create Application Load Balancer (Optional)

For HTTP access to MCP server (if adding HTTP transport):

```bash
# Create ALB target groups
aws elbv2 create-target-group \
  --name ilminate-mcp-server \
  --protocol HTTP \
  --port 3000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health

# Create ALB listener
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=<target-group-arn>
```

---

## Alternative: EC2 Deployment (Simpler)

### Step 1: Launch EC2 Instance

```bash
# Use existing ilminate infrastructure patterns
# Instance type: t3.medium or larger
# AMI: Amazon Linux 2023 or Ubuntu 22.04
```

### Step 2: Install Dependencies

```bash
# On EC2 instance
sudo yum update -y
sudo yum install -y nodejs npm python3 python3-pip git

# Clone repositories
git clone <ilminate-agent-repo>
git clone <ilminate-mcp-repo>
```

### Step 3: Setup Services

```bash
# Install MCP server
cd ilminate-mcp
npm install
npm run build

# Install APEX Bridge
cd bridge
pip3 install -r requirements.txt
```

### Step 4: Create Systemd Services

#### `/etc/systemd/system/apex-bridge.service`:

```ini
[Unit]
Description=APEX Bridge Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ilminate-mcp/bridge
Environment="APEX_BRIDGE_PORT=8888"
ExecStart=/usr/bin/python3 apex_bridge.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=ilminate MCP Server
After=network.target apex-bridge.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/ilminate-mcp
Environment="APEX_BRIDGE_URL=http://localhost:8888"
ExecStart=/usr/bin/node dist/index.js
Restart=always

[Install]
WantedBy=multi-user.target
```

### Step 5: Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable apex-bridge mcp-server
sudo systemctl start apex-bridge
sudo systemctl start mcp-server

# Check status
sudo systemctl status apex-bridge
sudo systemctl status mcp-server
```

---

## Integration with Existing ilminate Infrastructure

### Connect to Existing Services

Update `.env` or ECS task definitions with your existing AWS endpoints:

```bash
# Use existing API Gateway endpoints
APEX_API_URL=https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com/prod
PORTAL_API_URL=https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com/prod/portal
EMAIL_API_URL=https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com/prod/email

# Use Secrets Manager for API keys
# Reference in ECS task definition or EC2 user-data
```

### Use Existing VPC/Subnets

- Deploy in same VPC as ilminate infrastructure
- Use existing security groups
- Connect to existing DynamoDB tables
- Use existing IAM roles

---

## Cost Estimation

### ECS/Fargate (Recommended)
- **MCP Server**: ~$15-30/month (0.5 vCPU, 1GB RAM, 24/7)
- **APEX Bridge**: ~$30-60/month (1 vCPU, 2GB RAM, 24/7)
- **ALB**: ~$16/month (if using)
- **Total**: ~$60-110/month

### EC2
- **t3.medium**: ~$30/month
- **Data transfer**: Minimal
- **Total**: ~$30-40/month

### Lambda (Not Recommended)
- Would be cheaper (~$5-10/month) but doesn't work well for MCP

---

## Security Considerations

1. **Secrets Management**
   - Use AWS Secrets Manager for API keys
   - Reference secrets in ECS task definitions
   - Use IAM roles for service access

2. **Network Security**
   - Deploy in private subnets
   - Use security groups to restrict access
   - Use VPC endpoints for AWS services

3. **Authentication**
   - Enable API key authentication
   - Use AWS Cognito for user authentication
   - Implement rate limiting

---

## Monitoring

### CloudWatch Integration

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/ilminate-mcp-server
aws logs create-log-group --log-group-name /ecs/ilminate-apex-bridge

# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name mcp-server-cpu-high \
  --alarm-description "MCP Server CPU utilization high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

---

## Recommendation

**Use ECS/Fargate** because:
1. ✅ Integrates with existing AWS infrastructure
2. ✅ Auto-scaling capabilities
3. ✅ Managed service (less maintenance)
4. ✅ Works with stdio MCP transport
5. ✅ Cost-effective for production
6. ✅ Easy to update/deploy

**Start with EC2** if:
- You want quick testing
- You prefer full control
- You're already managing EC2 instances

---

## Next Steps

1. **Choose deployment method** (ECS/Fargate recommended)
2. **Create Docker images** (if using ECS)
3. **Set up ECR repositories**
4. **Create ECS task definitions**
5. **Deploy services**
6. **Configure CloudWatch monitoring**
7. **Test integration with existing services**

---

**Need help?** Check your existing `ilminate-infrastructure` repo for deployment patterns you're already using.

