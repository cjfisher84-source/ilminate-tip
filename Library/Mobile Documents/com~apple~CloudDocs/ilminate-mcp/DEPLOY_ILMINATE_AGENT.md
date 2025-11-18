# Deploy ilminate-agent to EC2

**Fix the APEX Bridge error by deploying ilminate-agent**

---

## What's Needed

The APEX Bridge expects `ilminate-agent` at `/opt/ilminate-agent` (sibling to `/opt/ilminate-mcp`).

**Required structure:**
```
/opt/
├── ilminate-mcp/
│   └── bridge/
│       └── apex_bridge.py  (looks for ../ilminate-agent)
└── ilminate-agent/
    ├── plugins/
    │   └── apex_detection_engine.py
    └── config/
        └── apex-detection-engine.yml (optional)
```

---

## Option 1: Automated Deployment (Recommended)

### Step 1: Set Your Repository URL

```bash
# If ilminate-agent is a Git repository
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"

# OR if it's a private repo, use SSH
export ILMINATE_AGENT_REPO="git@github.com:your-org/ilminate-agent.git"
```

### Step 2: Run Deployment Script

```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
./deploy-ilminate-agent.sh
```

**The script will:**
1. SSH to EC2 instance
2. Clone ilminate-agent repository
3. Install Python dependencies
4. Restart APEX Bridge service
5. Verify deployment

---

## Option 2: Manual Deployment

### Step 1: SSH to EC2 Instance

```bash
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195
```

### Step 2: Clone ilminate-agent

```bash
cd /opt

# Clone repository (replace with your repo URL)
git clone https://github.com/your-org/ilminate-agent.git ilminate-agent

# OR if you have the code locally, copy it
# From your local machine:
# rsync -avz --exclude .git \
#   -e "ssh -i ~/.ssh/ilminate-mcp-key.pem" \
#   /path/to/ilminate-agent/ ec2-user@54.237.174.195:/opt/ilminate-agent/
```

### Step 3: Install Dependencies

```bash
cd /opt/ilminate-agent

# Install Python dependencies
pip3 install -r requirements.txt

# If requirements.txt doesn't exist, install common dependencies:
pip3 install pyyaml requests numpy scikit-learn torch  # Add others as needed
```

### Step 4: Verify Structure

```bash
# Check that required files exist
ls -la /opt/ilminate-agent/plugins/apex_detection_engine.py
ls -la /opt/ilminate-agent/config/apex-detection-engine.yml  # Optional
```

### Step 5: Restart APEX Bridge

```bash
# Restart PM2 service
pm2 restart apex-bridge

# Check logs
pm2 logs apex-bridge --lines 50
```

### Step 6: Test

```bash
# Test health endpoint
curl http://localhost:8888/health

# Should return:
# {
#   "status": "healthy",
#   "apex_available": true,
#   "apex_initialized": true
# }
```

---

## Option 3: Deploy from Local Machine

If you have `ilminate-agent` locally:

### Step 1: Package ilminate-agent

```bash
# On your local machine
cd /path/to/ilminate-agent
tar -czf ilminate-agent.tar.gz --exclude=.git --exclude=__pycache__ --exclude="*.pyc" .
```

### Step 2: Copy to EC2

```bash
# Copy to EC2
scp -i ~/.ssh/ilminate-mcp-key.pem \
  ilminate-agent.tar.gz \
  ec2-user@54.237.174.195:/tmp/

# SSH and extract
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 << 'EOF'
cd /opt
sudo mkdir -p ilminate-agent
sudo chown ec2-user:ec2-user ilminate-agent
cd ilminate-agent
tar -xzf /tmp/ilminate-agent.tar.gz
pip3 install -r requirements.txt
pm2 restart apex-bridge
EOF
```

---

## Troubleshooting

### Error: "No module named 'plugins'"

**Cause:** `ilminate-agent` not found or wrong path.

**Fix:**
```bash
# Verify path
ls -la /opt/ilminate-agent/plugins/

# Check Python path in bridge
ssh ec2-user@54.237.174.195
python3 -c "import sys; sys.path.insert(0, '/opt/ilminate-agent'); from plugins.apex_detection_engine import APEXDetectionEngine"
```

### Error: "NameError: name 'APEXDetectionEngine' is not defined"

**Cause:** Import failed but code still references it.

**Fix:** The bridge code needs to handle the import error better. Check logs:
```bash
pm2 logs apex-bridge --err
```

### Error: Missing Dependencies

**Fix:**
```bash
cd /opt/ilminate-agent
pip3 install -r requirements.txt

# If requirements.txt missing, install common ones:
pip3 install pyyaml requests numpy scikit-learn
```

### APEX Bridge Still Shows Error

**Check:**
1. Verify ilminate-agent is at `/opt/ilminate-agent`
2. Check that `plugins/apex_detection_engine.py` exists
3. Restart bridge: `pm2 restart apex-bridge`
4. Check logs: `pm2 logs apex-bridge`

---

## Verify Deployment

```bash
# Test from local machine
curl http://54.237.174.195:8888/health

# Expected response:
{
  "status": "healthy",
  "apex_available": true,
  "apex_initialized": true
}
```

---

## Next Steps

Once `ilminate-agent` is deployed:

1. ✅ APEX Bridge will initialize successfully
2. ✅ MCP tools can use APEX detection engine
3. ✅ Email analysis, domain reputation, etc. will work

**The MCP server will automatically use the bridge when available!**

