# 🚀 Ready to Deploy to AWS ECS/Fargate!

**Everything is set up and ready for Option 1 deployment**

---

## ✅ What's Ready

### Prerequisites Verified
- ✅ AWS CLI installed and configured
- ✅ Docker installed and running  
- ✅ Node.js dependencies installed
- ✅ Project builds successfully

### Deployment Files Created
- ✅ `Dockerfile` - MCP Server container
- ✅ `bridge/Dockerfile` - APEX Bridge container
- ✅ `ecs/mcp-server-task.json` - ECS task definition
- ✅ `ecs/apex-bridge-task.json` - ECS task definition
- ✅ `deploy-aws.sh` - Automated deployment script
- ✅ `setup-ecs.sh` - Complete setup script (interactive)

### Documentation
- ✅ `AWS_DEPLOYMENT.md` - Complete deployment guide
- ✅ `ECS_SETUP_GUIDE.md` - Step-by-step ECS setup
- ✅ `QUICK_DEPLOY.md` - Quick reference

---

## 🎯 Quick Start (Choose One)

### Option A: Interactive Setup (Easiest) ⭐

```bash
./setup-ecs.sh
```

**This will:**
- Find your VPC/subnets automatically
- Create security groups
- Set up IAM roles
- Create secrets (with prompts)
- Build and push Docker images
- Create ECS services

**Just follow the prompts!**

### Option B: Manual Steps

```bash
# 1. Set region
export AWS_REGION=us-east-1
export CLUSTER_NAME=ilminate-mcp

# 2. Build and push images
./deploy-aws.sh

# 3. Create services (see QUICK_DEPLOY.md)
```

---

## 📋 Pre-Deployment Checklist

Before running `setup-ecs.sh`, make sure:

- [ ] AWS credentials configured (`aws configure`)
- [ ] You have permissions to create:
  - [ ] ECR repositories
  - [ ] ECS clusters and services
  - [ ] Security groups
  - [ ] IAM roles
  - [ ] Secrets Manager secrets
- [ ] You know your VPC ID (or have a default VPC)
- [ ] You have API keys ready (for Secrets Manager)

---

## 🏃 Run It Now!

### Step 1: Run Setup Script

```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
./setup-ecs.sh
```

### Step 2: Follow Prompts

The script will ask:
- VPC ID (or use default)
- Create secrets? (y/n)
- API keys (if creating secrets)
- Build Docker images? (y/n)
- Create ECS services? (y/n)

### Step 3: Verify

```bash
# Check services are running
aws ecs describe-services \
  --cluster ilminate-mcp \
  --services apex-bridge mcp-server \
  --query 'services[*].[serviceName,status,runningCount]' \
  --output table

# View logs
aws logs tail /ecs/ilminate-apex-bridge --follow
```

---

## 📊 What Gets Created

### AWS Resources

1. **ECR Repositories**
   - `ilminate-mcp-server`
   - `ilminate-apex-bridge`

2. **ECS Cluster**
   - `ilminate-mcp`

3. **ECS Services**
   - `apex-bridge` (1 task)
   - `mcp-server` (1 task)

4. **Security Group**
   - `ilminate-mcp-sg` (ports 8888, 3000)

5. **IAM Roles**
   - `ecsTaskExecutionRole`
   - `ilminate-mcp-server-task-role`

6. **Secrets Manager**
   - `ilminate/apex-api-key`
   - `ilminate/portal-api-key`
   - `ilminate/siem-password`

7. **CloudWatch Log Groups**
   - `/ecs/ilminate-mcp-server`
   - `/ecs/ilminate-apex-bridge`

---

## 💰 Estimated Costs

- **ECS Fargate**: ~$60-110/month
  - MCP Server: ~$15-30/month (0.5 vCPU, 1GB)
  - APEX Bridge: ~$30-60/month (1 vCPU, 2GB)
- **ECR Storage**: ~$1-2/month
- **CloudWatch Logs**: ~$5-10/month
- **Secrets Manager**: ~$0.40/month per secret

**Total**: ~$70-125/month

---

## 🔧 After Deployment

### Update Task Definitions

If you need to change configuration:

```bash
# Edit task definition JSON files
# Then re-register:
aws ecs register-task-definition --cli-input-json file://ecs/mcp-server-task.json

# Update service to use new task definition:
aws ecs update-service \
  --cluster ilminate-mcp \
  --service-name mcp-server \
  --task-definition ilminate-mcp-server \
  --force-new-deployment
```

### Scale Services

```bash
# Scale up
aws ecs update-service \
  --cluster ilminate-mcp \
  --service-name apex-bridge \
  --desired-count 2

# Scale down
aws ecs update-service \
  --cluster ilminate-mcp \
  --service-name apex-bridge \
  --desired-count 1
```

### View Logs

```bash
# Follow logs
aws logs tail /ecs/ilminate-apex-bridge --follow

# View recent logs
aws logs tail /ecs/ilminate-mcp-server --since 1h
```

---

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check service events
aws ecs describe-services \
  --cluster ilminate-mcp \
  --services apex-bridge \
  --query 'services[0].events[:5]' \
  --output table

# Check task stopped reason
TASK_ARN=$(aws ecs list-tasks --cluster ilminate-mcp --service-name apex-bridge --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster ilminate-mcp --tasks $TASK_ARN --query 'tasks[0].stoppedReason'
```

### Container Exits Immediately

```bash
# Check logs for errors
aws logs tail /ecs/ilminate-apex-bridge --since 10m

# Common issues:
# - Cannot find ilminate-agent directory
# - Missing environment variables
# - Port conflicts
```

### Cannot Connect

- Verify security group allows traffic
- Check tasks are running: `aws ecs list-tasks --cluster ilminate-mcp`
- Verify VPC/subnet configuration

---

## 📚 Documentation

- **`AWS_DEPLOYMENT.md`** - Complete deployment guide
- **`ECS_SETUP_GUIDE.md`** - Detailed step-by-step
- **`QUICK_DEPLOY.md`** - Quick reference
- **`TESTING_GUIDE.md`** - Testing instructions

---

## ✅ Ready to Deploy!

Run this command to start:

```bash
./setup-ecs.sh
```

**The script will guide you through everything!**

---

**Questions?** Check the documentation files or AWS console for detailed logs.

