# EC2 Deployment Guide (No Docker Required)

**Alternative to ECS/Fargate - Deploy directly on EC2**

---

## Why EC2 Instead of Docker?

- ✅ **No Docker required** - Run Node.js and Python directly
- ✅ **Simpler setup** - No container images to build
- ✅ **Easier debugging** - Direct access to services
- ✅ **Lower cost** - ~$30-40/month vs $60-110/month
- ✅ **Full control** - Manage the instance yourself

---

## Prerequisites

- AWS CLI configured
- EC2 instance (or launch new one)
- SSH access to EC2
- Node.js 18+ and Python 3.8+ on EC2

---

## Step 1: Launch EC2 Instance

### Option A: Use Existing Instance

If you already have an EC2 instance:
```bash
# Note your instance details
INSTANCE_ID="i-1234567890abcdef0"
REGION="us-east-1"
```

### Option B: Launch New Instance

```bash
# Launch t3.medium instance (recommended)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-name \
  --security-group-ids sg-12345678 \
  --subnet-id subnet-12345678 \
  --user-data file://ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ilminate-mcp}]'
```

**Recommended Instance:**
- **Type**: t3.medium or t3.large
- **OS**: Amazon Linux 2023 or Ubuntu 22.04
- **Storage**: 20GB minimum
- **Security Group**: Allow SSH (port 22) and HTTP (ports 3000, 8888)

---

## Step 2: Create User Data Script

Create `ec2-user-data.sh`:

```bash
#!/bin/bash
# EC2 User Data Script - Installs dependencies on instance startup

# Update system
yum update -y  # For Amazon Linux
# OR
# apt-get update && apt-get upgrade -y  # For Ubuntu

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install Python 3 and pip
yum install -y python3 python3-pip git

# Install PM2 for process management
npm install -g pm2

# Create application directory
mkdir -p /opt/ilminate-mcp
chown ec2-user:ec2-user /opt/ilminate-mcp

# Clone repositories (or use your deployment method)
# This assumes you'll deploy code via S3, CodeDeploy, or manual copy
```

---

## Step 3: Deploy Code to EC2

### Option A: Deploy via S3

```bash
# 1. Package code
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
npm run build
tar -czf ilminate-mcp.tar.gz dist/ package.json src/ bridge/

# 2. Upload to S3
aws s3 cp ilminate-mcp.tar.gz s3://your-bucket/ilminate-mcp.tar.gz

# 3. Download on EC2
# SSH to instance, then:
aws s3 cp s3://your-bucket/ilminate-mcp.tar.gz /opt/ilminate-mcp/
cd /opt/ilminate-mcp
tar -xzf ilminate-mcp.tar.gz
```

### Option B: Deploy via Git

```bash
# On EC2 instance:
cd /opt
git clone <your-git-repo-url> ilminate-mcp
cd ilminate-mcp
npm install
npm run build
```

### Option C: Deploy via rsync/SCP

```bash
# From your local machine:
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
npm run build

# Copy to EC2
rsync -avz --exclude node_modules --exclude .git \
  ./ ec2-user@your-instance-ip:/opt/ilminate-mcp/
```

---

## Step 4: Setup on EC2 Instance

### SSH to Instance

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

### Install Dependencies

```bash
# Install Node.js (if not in user-data)
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
sudo yum install -y nodejs

# Install Python dependencies
cd /opt/ilminate-mcp/bridge
pip3 install -r requirements.txt

# Install Node.js dependencies
cd /opt/ilminate-mcp
npm install --production
```

### Setup ilminate-agent

```bash
# Clone ilminate-agent (or copy from S3)
cd /opt
git clone <ilminate-agent-repo-url> ilminate-agent
# OR copy from your local machine

# Install ilminate-agent dependencies
cd ilminate-agent
pip3 install -r requirements.txt
```

---

## Step 5: Create Systemd Services

### APEX Bridge Service

Create `/etc/systemd/system/apex-bridge.service`:

```ini
[Unit]
Description=APEX Bridge Service for ilminate-mcp
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/ilminate-mcp/bridge
Environment="APEX_BRIDGE_PORT=8888"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /opt/ilminate-mcp/bridge/apex_bridge.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### MCP Server Service

Create `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=ilminate MCP Server
After=network.target apex-bridge.service
Requires=apex-bridge.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/ilminate-mcp
Environment="APEX_BRIDGE_URL=http://localhost:8888"
Environment="NODE_ENV=production"
Environment="LOG_LEVEL=info"
ExecStart=/usr/bin/node /opt/ilminate-mcp/dist/index.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable apex-bridge
sudo systemctl enable mcp-server

# Start services
sudo systemctl start apex-bridge
sudo systemctl start mcp-server

# Check status
sudo systemctl status apex-bridge
sudo systemctl status mcp-server
```

---

## Step 6: Configure Environment Variables

Create `/opt/ilminate-mcp/.env`:

```bash
# APEX Bridge
APEX_BRIDGE_URL=http://localhost:8888
APEX_BRIDGE_PORT=8888

# Cross-Repo Integration URLs
APEX_API_URL=http://localhost:3000
PORTAL_API_URL=http://localhost:3001
SIEM_API_URL=http://localhost:55000
EMAIL_API_URL=http://localhost:3002
SANDBOX_API_URL=http://localhost:3003

# API Keys (store securely)
APEX_API_KEY=your-key-here
PORTAL_API_KEY=your-key-here
SIEM_API_USER=wazuh
SIEM_API_PASSWORD=your-password
EMAIL_API_KEY=your-key-here
SANDBOX_API_KEY=your-key-here

# Logging
LOG_LEVEL=info
```

**Secure the .env file:**
```bash
chmod 600 /opt/ilminate-mcp/.env
```

---

## Step 7: Configure Security Group

```bash
# Allow inbound traffic
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 8888 \
  --cidr 0.0.0.0/0  # Or restrict to your IP

aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 3000 \
  --cidr 0.0.0.0/0  # Or restrict to your IP
```

---

## Step 8: Verify Deployment

### Check Services

```bash
# Check service status
sudo systemctl status apex-bridge
sudo systemctl status mcp-server

# View logs
sudo journalctl -u apex-bridge -f
sudo journalctl -u mcp-server -f
```

### Test Health Endpoints

```bash
# Get instance public IP
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Test APEX Bridge
curl http://$INSTANCE_IP:8888/health

# Should return: {"status":"healthy","apex_available":true,"apex_initialized":true}
```

---

## Alternative: Use PM2 Instead of Systemd

### Install PM2

```bash
npm install -g pm2
```

### Create PM2 Ecosystem File

Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'apex-bridge',
      script: 'python3',
      args: 'bridge/apex_bridge.py',
      cwd: '/opt/ilminate-mcp',
      env: {
        APEX_BRIDGE_PORT: '8888',
        PYTHONUNBUFFERED: '1'
      },
      autorestart: true,
      watch: false
    },
    {
      name: 'mcp-server',
      script: 'dist/index.js',
      cwd: '/opt/ilminate-mcp',
      env: {
        APEX_BRIDGE_URL: 'http://localhost:8888',
        NODE_ENV: 'production'
      },
      autorestart: true,
      watch: false
    }
  ]
};
```

### Start with PM2

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Enable PM2 on boot
```

---

## Cost Comparison

### EC2 Deployment
- **t3.medium**: ~$30/month
- **t3.large**: ~$60/month (if more resources needed)
- **Data transfer**: Minimal
- **Total**: ~$30-60/month

### vs ECS/Fargate
- **ECS Fargate**: ~$60-110/month
- **EC2**: ~$30-60/month
- **Savings**: ~50% cheaper

---

## Maintenance

### Update Code

```bash
# SSH to instance
ssh ec2-user@your-instance-ip

# Pull updates (if using Git)
cd /opt/ilminate-mcp
git pull
npm install
npm run build

# Restart services
sudo systemctl restart apex-bridge
sudo systemctl restart mcp-server
```

### View Logs

```bash
# Systemd logs
sudo journalctl -u apex-bridge -n 100
sudo journalctl -u mcp-server -n 100

# Or PM2 logs
pm2 logs apex-bridge
pm2 logs mcp-server
```

### Monitor Resources

```bash
# CPU/Memory usage
top
htop  # If installed

# Disk usage
df -h

# Process status
ps aux | grep -E "(apex|mcp)"
```

---

## Automation Script

Create `deploy-to-ec2.sh`:

```bash
#!/bin/bash
# Deploy ilminate-mcp to EC2

INSTANCE_IP="your-instance-ip"
SSH_KEY="your-key.pem"
REMOTE_USER="ec2-user"

echo "Building..."
npm run build

echo "Copying files to EC2..."
rsync -avz --exclude node_modules --exclude .git \
  -e "ssh -i $SSH_KEY" \
  ./ $REMOTE_USER@$INSTANCE_IP:/opt/ilminate-mcp/

echo "Installing dependencies on EC2..."
ssh -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP << 'EOF'
cd /opt/ilminate-mcp
npm install --production
cd bridge
pip3 install -r requirements.txt
sudo systemctl restart apex-bridge
sudo systemctl restart mcp-server
EOF

echo "✅ Deployment complete!"
```

---

## Advantages of EC2 Deployment

✅ **No Docker required**  
✅ **Simpler setup**  
✅ **Easier debugging**  
✅ **Lower cost**  
✅ **Direct file access**  
✅ **Full control**

---

## Ready to Deploy?

1. **Launch EC2 instance** (or use existing)
2. **SSH to instance**
3. **Follow steps above**
4. **Start services**

**See `EC2_QUICK_DEPLOY.md` for condensed steps.**

