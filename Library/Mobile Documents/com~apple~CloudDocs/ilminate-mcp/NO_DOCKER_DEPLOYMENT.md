# No Docker Deployment Guide

**Deploy ilminate-mcp without Docker - EC2 Direct Deployment**

---

## ✅ Solution: EC2 Direct Deployment

Since Docker isn't available, we'll deploy directly to EC2:

- ✅ **No Docker required** - Run Node.js and Python natively
- ✅ **Simpler setup** - Direct file deployment
- ✅ **Lower cost** - ~$30-40/month vs $60-110/month
- ✅ **Easier debugging** - Direct access to services

---

## 🚀 Quick Start

### Option 1: Automated Script (Easiest)

```bash
# 1. Set your EC2 instance IP
export EC2_INSTANCE_IP=your-instance-ip-here
export EC2_SSH_KEY=~/.ssh/your-key.pem  # Optional, defaults to ~/.ssh/id_rsa

# 2. Run deployment
./deploy-to-ec2.sh
```

**That's it!** The script will:
- Build the application
- Copy files to EC2
- Install dependencies
- Start services with PM2

### Option 2: Manual Steps

See `EC2_QUICK_DEPLOY.md` for step-by-step instructions.

---

## 📋 Prerequisites

### On Your Local Machine
- ✅ AWS CLI configured
- ✅ SSH key for EC2 access
- ✅ Node.js installed (for building)

### On EC2 Instance
- Node.js 18+ (installed via user-data script)
- Python 3.8+ (installed via user-data script)
- PM2 (installed automatically)

---

## 🏗️ Launch EC2 Instance (If Needed)

### Quick Launch Command

```bash
# Set your values
KEY_NAME="your-key-name"
SG_ID="sg-12345678"  # Your security group
SUBNET_ID="subnet-12345678"  # Your subnet

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --user-data file://ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ilminate-mcp}]'

# Get instance IP
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=ilminate-mcp" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance IP: $INSTANCE_IP"
export EC2_INSTANCE_IP=$INSTANCE_IP
```

---

## 📝 Deployment Steps

### Step 1: Prepare Local Code

```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
npm run build  # Already done ✅
```

### Step 2: Deploy to EC2

```bash
# Set instance IP
export EC2_INSTANCE_IP=your-instance-ip

# Run deployment script
./deploy-to-ec2.sh
```

### Step 3: Configure Security Group

```bash
# Allow HTTP traffic
SG_ID="sg-12345678"  # Your security group ID

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8888 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr 0.0.0.0/0
```

### Step 4: Test

```bash
# Test health endpoint
curl http://$EC2_INSTANCE_IP:8888/health

# Should return: {"status":"healthy","apex_available":true,"apex_initialized":true}
```

---

## 🔧 Manual Setup (If Script Doesn't Work)

### SSH to Instance

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@$EC2_INSTANCE_IP
```

### Install Dependencies

```bash
# Install Node.js (if not installed)
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
sudo yum install -y nodejs

# Install Python dependencies
cd /opt/ilminate-mcp/bridge
pip3 install -r requirements.txt

# Install Node.js dependencies
cd /opt/ilminate-mcp
npm install --production
```

### Start Services

```bash
# Install PM2
npm install -g pm2

# Start services
cd /opt/ilminate-mcp
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions
```

---

## 📊 Monitoring

### Check Service Status

```bash
ssh ec2-user@$EC2_INSTANCE_IP 'pm2 status'
```

### View Logs

```bash
ssh ec2-user@$EC2_INSTANCE_IP 'pm2 logs'
```

### Restart Services

```bash
ssh ec2-user@$EC2_INSTANCE_IP 'pm2 restart all'
```

---

## 💰 Cost

- **t3.medium**: ~$30/month
- **t3.large**: ~$60/month (if more resources needed)

**Much cheaper than ECS/Fargate!**

---

## 🔄 Updates

To update code:

```bash
# Just re-run the deployment script
export EC2_INSTANCE_IP=your-instance-ip
./deploy-to-ec2.sh
```

The script will:
- Rebuild
- Copy new files
- Restart services

---

## 📚 Documentation

- **`EC2_DEPLOYMENT.md`** - Complete EC2 deployment guide
- **`EC2_QUICK_DEPLOY.md`** - Quick reference
- **`deploy-to-ec2.sh`** - Automated deployment script

---

## ✅ Ready to Deploy!

**Run this:**

```bash
export EC2_INSTANCE_IP=your-instance-ip
./deploy-to-ec2.sh
```

**No Docker needed!** 🎉

