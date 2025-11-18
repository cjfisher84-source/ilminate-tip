# EC2 Quick Deploy (No Docker)

**Fastest way to deploy without Docker**

---

## Quick Steps

### 1. Launch EC2 Instance

```bash
# Get your key name and security group
KEY_NAME="your-key-name"
SG_ID="sg-12345678"
SUBNET_ID="subnet-12345678"

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --user-data file://ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ilminate-mcp}]'
```

### 2. Wait for Instance to Start

```bash
# Get instance ID from output above
INSTANCE_ID="i-1234567890abcdef0"

# Wait for running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance IP: $INSTANCE_IP"
```

### 3. Deploy Code

```bash
# From your local machine
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
npm run build

# Copy to EC2 (replace with your key and IP)
rsync -avz --exclude node_modules --exclude .git \
  -e "ssh -i ~/.ssh/your-key.pem" \
  ./ ec2-user@$INSTANCE_IP:/opt/ilminate-mcp/
```

### 4. Setup on EC2

```bash
# SSH to instance
ssh -i ~/.ssh/your-key.pem ec2-user@$INSTANCE_IP

# Install dependencies
cd /opt/ilminate-mcp
npm install --production

cd bridge
pip3 install -r requirements.txt

# Create logs directory
mkdir -p /opt/ilminate-mcp/logs

# Start with PM2
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions to enable on boot
```

### 5. Configure Security Group

```bash
# Allow HTTP traffic
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

### 6. Test

```bash
# Test health endpoint
curl http://$INSTANCE_IP:8888/health

# Should return: {"status":"healthy","apex_available":true,"apex_initialized":true}
```

---

## Using Systemd Instead of PM2

### Create Service Files

Copy service files from `EC2_DEPLOYMENT.md` to `/etc/systemd/system/`:

```bash
sudo cp apex-bridge.service /etc/systemd/system/
sudo cp mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable apex-bridge mcp-server
sudo systemctl start apex-bridge mcp-server
```

---

## Automated Deployment Script

Create `deploy-to-ec2.sh`:

```bash
#!/bin/bash
set -e

INSTANCE_IP="${EC2_INSTANCE_IP:-your-instance-ip}"
SSH_KEY="${EC2_SSH_KEY:-~/.ssh/your-key.pem}"
REMOTE_USER="ec2-user"

echo "🚀 Deploying ilminate-mcp to EC2"
echo "Instance: $INSTANCE_IP"
echo ""

# Build
echo "1️⃣  Building..."
npm run build

# Copy files
echo "2️⃣  Copying files to EC2..."
rsync -avz --exclude node_modules --exclude .git --exclude dist \
  -e "ssh -i $SSH_KEY" \
  ./ $REMOTE_USER@$INSTANCE_IP:/opt/ilminate-mcp/

# Setup on EC2
echo "3️⃣  Setting up on EC2..."
ssh -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP << 'ENDSSH'
cd /opt/ilminate-mcp
npm install --production
cd bridge
pip3 install -r requirements.txt --user
mkdir -p logs

# Restart PM2
pm2 restart ecosystem.config.js || pm2 start ecosystem.config.js
pm2 save
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test: curl http://$INSTANCE_IP:8888/health"
```

**Make executable:**
```bash
chmod +x deploy-to-ec2.sh
```

**Run:**
```bash
export EC2_INSTANCE_IP=your-instance-ip
export EC2_SSH_KEY=~/.ssh/your-key.pem
./deploy-to-ec2.sh
```

---

## Cost

- **t3.medium**: ~$30/month
- **t3.large**: ~$60/month (if needed)

**Much cheaper than ECS/Fargate!**

---

## Maintenance

### Update Code

```bash
./deploy-to-ec2.sh  # Re-runs deployment
```

### View Logs

```bash
ssh ec2-user@$INSTANCE_IP
pm2 logs
# OR
sudo journalctl -u apex-bridge -f
sudo journalctl -u mcp-server -f
```

### Restart Services

```bash
ssh ec2-user@$INSTANCE_IP
pm2 restart all
# OR
sudo systemctl restart apex-bridge mcp-server
```

---

**Ready?** Follow the Quick Steps above! 🚀

