# Quick Fix: APEX Bridge Error

**Fastest way to fix the APEX Bridge error**

---

## The Problem

APEX Bridge can't find `ilminate-agent` because it's not deployed on EC2.

**Error:** `No module named 'plugins'` or `NameError: name 'APEXDetectionEngine' is not defined`

---

## Quick Fix (3 Steps)

### Step 1: Set Your Repository URL

```bash
# Replace with your actual ilminate-agent repository URL
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"

# OR if private repo (SSH):
export ILMINATE_AGENT_REPO="git@github.com:your-org/ilminate-agent.git"
```

### Step 2: Run Deployment Script

```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"
./deploy-ilminate-agent.sh
```

**That's it!** The script will:
- Clone ilminate-agent to `/opt/ilminate-agent`
- Install dependencies
- Restart APEX Bridge
- Verify it works

### Step 3: Verify

```bash
# Test health endpoint
curl http://54.237.174.195:8888/health

# Should show:
# {
#   "status": "healthy",
#   "apex_available": true,
#   "apex_initialized": true
# }
```

---

## Alternative: Manual Fix

If you don't have a Git repository:

### Option A: Copy from Local Machine

```bash
# On your local machine (if you have ilminate-agent locally)
cd /path/to/ilminate-agent
tar -czf /tmp/ilminate-agent.tar.gz --exclude=.git --exclude=__pycache__ .

# Copy to EC2
scp -i ~/.ssh/ilminate-mcp-key.pem /tmp/ilminate-agent.tar.gz ec2-user@54.237.174.195:/tmp/

# Extract on EC2
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

### Option B: Create Minimal Structure

If you just need to test, create a minimal structure:

```bash
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 << 'EOF'
mkdir -p /opt/ilminate-agent/plugins
mkdir -p /opt/ilminate-agent/config

# Create minimal apex_detection_engine.py
cat > /opt/ilminate-agent/plugins/apex_detection_engine.py << 'PYTHON'
class APEXVerdict:
    def __init__(self):
        self.action = "allow"
        self.threat_level = "LOW"
        self.risk_score = 0.0

class APEXDetectionEngine:
    def __init__(self, config):
        self.config = config
    
    async def analyze_email(self, email_data):
        return APEXVerdict()
PYTHON

pm2 restart apex-bridge
EOF
```

**Note:** This is just a stub - you'll need the real implementation for actual detection.

---

## What the Script Does

1. **Clones ilminate-agent** to `/opt/ilminate-agent`
2. **Installs dependencies** from `requirements.txt`
3. **Verifies structure** (checks for `plugins/apex_detection_engine.py`)
4. **Restarts APEX Bridge** via PM2
5. **Tests health endpoint** to confirm it works

---

## Troubleshooting

### "Git clone failed"

**If private repo:** Make sure your SSH key is added to GitHub/GitLab, or use HTTPS with credentials.

**If repo doesn't exist:** Use Option A or B above to copy files manually.

### "Import still fails"

Check logs:
```bash
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 'pm2 logs apex-bridge --lines 50'
```

Verify path:
```bash
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 'ls -la /opt/ilminate-agent/plugins/'
```

### "Dependencies missing"

Install manually:
```bash
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195
cd /opt/ilminate-agent
pip3 install pyyaml requests numpy scikit-learn torch
pm2 restart apex-bridge
```

---

## Success!

Once fixed, you'll see:
- ✅ APEX Bridge status: `online` (not `errored`)
- ✅ Health endpoint returns `apex_available: true`
- ✅ MCP tools can use APEX detection engine

**Run the script and you're done!** 🚀

