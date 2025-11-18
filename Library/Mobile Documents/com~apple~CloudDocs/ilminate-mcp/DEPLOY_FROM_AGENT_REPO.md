# Deploy ilminate-agent to EC2

**Instructions for deploying from the ilminate-agent repository**

---

## 🎯 What Needs to Happen

The APEX Bridge on EC2 expects `ilminate-agent` at `/opt/ilminate-agent`. You need to:

1. **Copy ilminate-agent** to EC2 at `/opt/ilminate-agent`
2. **Install Python dependencies** from `requirements.txt`
3. **Verify structure** (plugins/apex_detection_engine.py exists)
4. **Restart APEX Bridge** so it can import the modules

---

## 🚀 Option 1: Automated Script (Easiest)

### From ilminate-agent Repository:

```bash
# Make sure you're in ilminate-agent directory
cd /path/to/ilminate-agent

# Copy the deploy script (or create it - see below)
# Then run:
./deploy-to-ec2.sh
```

**The script will:**
- Package ilminate-agent
- Copy to EC2 via rsync
- Install dependencies
- Restart APEX Bridge
- Verify deployment

---

## 📝 Option 2: Manual Steps

### Step 1: Package ilminate-agent

```bash
# From ilminate-agent directory
cd /path/to/ilminate-agent

# Create tarball (exclude unnecessary files)
tar -czf /tmp/ilminate-agent.tar.gz \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude="*.pyc" \
  --exclude=.venv \
  --exclude=venv \
  --exclude=node_modules \
  .
```

### Step 2: Copy to EC2

```bash
# Set your EC2 details
INSTANCE_IP="54.237.174.195"
SSH_KEY="~/.ssh/ilminate-mcp-key.pem"

# Copy tarball
scp -i $SSH_KEY /tmp/ilminate-agent.tar.gz \
  ec2-user@$INSTANCE_IP:/tmp/
```

### Step 3: Extract and Install on EC2

```bash
# SSH to EC2
ssh -i $SSH_KEY ec2-user@$INSTANCE_IP

# Extract ilminate-agent
cd /opt
sudo mkdir -p ilminate-agent
sudo chown ec2-user:ec2-user ilminate-agent
cd ilminate-agent
tar -xzf /tmp/ilminate-agent.tar.gz

# Install dependencies
pip3 install -r requirements.txt --user || pip3 install -r requirements.txt

# Verify structure
ls -la plugins/apex_detection_engine.py

# Restart APEX Bridge
pm2 restart apex-bridge

# Check status
pm2 status
curl http://localhost:8888/health
```

---

## 🔧 Option 3: Direct rsync (Best for Development)

### From ilminate-agent Repository:

```bash
# Set EC2 details
INSTANCE_IP="54.237.174.195"
SSH_KEY="~/.ssh/ilminate-mcp-key.pem"

# Sync files (excludes .git, __pycache__, etc.)
rsync -avz \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude="*.pyc" \
  --exclude=.venv \
  --exclude=venv \
  --exclude=node_modules \
  --exclude="*.log" \
  -e "ssh -i $SSH_KEY" \
  ./ ec2-user@$INSTANCE_IP:/opt/ilminate-agent/

# SSH and install dependencies
ssh -i $SSH_KEY ec2-user@$INSTANCE_IP << 'EOF'
cd /opt/ilminate-agent
pip3 install -r requirements.txt --user || pip3 install -r requirements.txt
pm2 restart apex-bridge
pm2 logs apex-bridge --lines 20
EOF
```

---

## ✅ Verification

After deployment, verify:

```bash
# Test health endpoint
curl http://54.237.174.195:8888/health

# Expected response:
# {
#   "status": "healthy",
#   "apex_available": true,
#   "apex_initialized": true
# }

# Check PM2 status
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 'pm2 status'

# Should show:
# ✅ apex-bridge    online
# ✅ mcp-server     online
```

---

## 📋 Required Structure

The APEX Bridge expects this structure:

```
/opt/ilminate-agent/
├── plugins/
│   └── apex_detection_engine.py    ← REQUIRED
├── config/
│   └── apex-detection-engine.yml   ← Optional (uses defaults if missing)
└── requirements.txt                 ← For dependencies
```

---

## 🐛 Troubleshooting

### "No module named 'plugins'"

**Check:**
```bash
ssh ec2-user@54.237.174.195 'ls -la /opt/ilminate-agent/plugins/'
```

**Fix:** Ensure ilminate-agent is at `/opt/ilminate-agent` (not `/opt/ilminate-agent/ilminate-agent`)

### "Import failed"

**Check Python path:**
```bash
ssh ec2-user@54.237.174.195 'python3 -c "import sys; sys.path.insert(0, \"/opt/ilminate-agent\"); from plugins.apex_detection_engine import APEXDetectionEngine; print(\"OK\")"'
```

### APEX Bridge still errored

**Check logs:**
```bash
ssh ec2-user@54.237.174.195 'pm2 logs apex-bridge --lines 50'
```

**Restart:**
```bash
ssh ec2-user@54.237.174.195 'pm2 restart apex-bridge'
```

---

## 🎯 Quick Command Reference

```bash
# From ilminate-agent repo - Quick deploy
INSTANCE_IP="54.237.174.195"
SSH_KEY="~/.ssh/ilminate-mcp-key.pem"

rsync -avz --exclude=.git --exclude=__pycache__ --exclude="*.pyc" \
  -e "ssh -i $SSH_KEY" \
  ./ ec2-user@$INSTANCE_IP:/opt/ilminate-agent/ && \
ssh -i $SSH_KEY ec2-user@$INSTANCE_IP \
  'cd /opt/ilminate-agent && pip3 install -r requirements.txt && pm2 restart apex-bridge'
```

---

**Ready?** Use the automated script below or follow manual steps! 🚀

