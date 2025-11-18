# 🚀 Deploy Now - Quick Instructions

## Instance Ready!

**EC2 Instance:** `i-0072a64945db7c13f`  
**Public IP:** `44.215.126.5`  
**Status:** ✅ Running

---

## Deploy in 2 Steps

### Step 1: Provide SSH Key Path

The deployment script needs your SSH private key. The key pair name is `wazuh`.

**Find your key:**
```bash
# Check common locations
ls -la ~/.ssh/*.pem
ls -la ~/.ssh/wazuh*
ls -la ~/Downloads/*.pem
```

**Or download from AWS (if you have access):**
```bash
# Note: AWS doesn't store private keys, so you need the .pem file
# If you don't have it, you'll need to:
# 1. Create a new key pair, OR
# 2. Use an existing key you have
```

### Step 2: Run Deployment

```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"

# Set your SSH key path
export EC2_INSTANCE_IP="44.215.126.5"
export EC2_SSH_KEY="~/.ssh/your-key.pem"  # Replace with actual path

# Deploy
./deploy-to-ec2.sh
```

---

## Alternative: Manual Deployment

If you prefer to deploy manually:

### 1. SSH to Instance

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@44.215.126.5
```

### 2. On EC2 Instance

```bash
# Wait for user-data script to finish (check logs)
sudo tail -f /var/log/user-data.log

# Once done, create directory
sudo mkdir -p /opt/ilminate-mcp
sudo chown ec2-user:ec2-user /opt/ilminate-mcp
```

### 3. From Your Local Machine

```bash
# Build and copy files
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
npm run build

# Copy files (replace key path)
rsync -avz --exclude node_modules --exclude .git \
  -e "ssh -i ~/.ssh/your-key.pem" \
  ./ ec2-user@44.215.126.5:/opt/ilminate-mcp/
```

### 4. Back on EC2 Instance

```bash
# Install dependencies
cd /opt/ilminate-mcp
npm install --production
cd bridge
pip3 install -r requirements.txt

# Start services
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions
```

---

## Test Deployment

```bash
# Test health endpoint
curl http://44.215.126.5:8888/health

# Should return: {"status":"healthy","apex_available":true,"apex_initialized":true}
```

---

## Need Help?

**If you don't have the SSH key:**
1. Create a new key pair in AWS Console
2. Download the .pem file
3. Update the deployment script with the new key path

**Or use AWS Systems Manager Session Manager** (if configured):
```bash
aws ssm start-session --target i-0072a64945db7c13f
```

---

**Ready?** Provide your SSH key path and run the deployment script! 🚀
