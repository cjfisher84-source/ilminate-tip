#!/bin/bash
# Deploy ilminate-agent to EC2 instance

set -e

# Configuration
INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"
AGENT_REPO="${ILMINATE_AGENT_REPO}"

# Check if repo URL provided
if [ -z "$AGENT_REPO" ]; then
    echo "❌ Error: ILMINATE_AGENT_REPO not set"
    echo ""
    echo "Usage:"
    echo "  export ILMINATE_AGENT_REPO='https://github.com/your-org/ilminate-agent.git'"
    echo "  export EC2_INSTANCE_IP='54.237.174.195'  # Optional, defaults to current instance"
    echo "  ./deploy-ilminate-agent.sh"
    echo ""
    echo "Or for SSH/private repo:"
    echo "  export ILMINATE_AGENT_REPO='git@github.com:your-org/ilminate-agent.git'"
    echo "  ./deploy-ilminate-agent.sh"
    echo ""
    exit 1
fi

echo "🚀 Deploying ilminate-agent to EC2"
echo "Instance: $INSTANCE_IP"
echo "Repository: $AGENT_REPO"
echo ""

# Step 1: Clone/Update ilminate-agent
echo "1️⃣  Cloning/updating ilminate-agent..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

cd /opt

# Remove existing if exists (backup first)
if [ -d "ilminate-agent" ]; then
    echo "Backing up existing ilminate-agent..."
    sudo mv ilminate-agent ilminate-agent.backup.\$(date +%Y%m%d_%H%M%S) || true
fi

# Clone repository
echo "Cloning ilminate-agent..."
git clone $AGENT_REPO ilminate-agent || {
    echo "❌ Git clone failed. Trying with existing backup..."
    if [ -d ilminate-agent.backup.* ]; then
        sudo mv ilminate-agent.backup.* ilminate-agent
    else
        exit 1
    fi
}

# Set permissions
sudo chown -R $REMOTE_USER:$REMOTE_USER /opt/ilminate-agent

echo "✅ Repository cloned"
ENDSSH

# Step 2: Install dependencies
echo ""
echo "2️⃣  Installing Python dependencies..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

cd /opt/ilminate-agent

# Check for requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip3 install -r requirements.txt --user || pip3 install -r requirements.txt
else
    echo "⚠️  No requirements.txt found. Installing common dependencies..."
    pip3 install pyyaml requests numpy scikit-learn --user || pip3 install pyyaml requests numpy scikit-learn
fi

echo "✅ Dependencies installed"
ENDSSH

# Step 3: Verify structure
echo ""
echo "3️⃣  Verifying ilminate-agent structure..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

echo "Checking required files..."
if [ ! -f "/opt/ilminate-agent/plugins/apex_detection_engine.py" ]; then
    echo "⚠️  Warning: apex_detection_engine.py not found at expected location"
    echo "Looking for it..."
    find /opt/ilminate-agent -name "*apex*" -type f | head -5
else
    echo "✅ Found apex_detection_engine.py"
fi

# Check config (optional)
if [ -f "/opt/ilminate-agent/config/apex-detection-engine.yml" ]; then
    echo "✅ Found config file"
else
    echo "⚠️  Config file not found (optional, will use defaults)"
fi

# Test Python import
echo ""
echo "Testing Python import..."
python3 << PYTHON_TEST
import sys
sys.path.insert(0, '/opt/ilminate-agent')
try:
    from plugins.apex_detection_engine import APEXDetectionEngine
    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
PYTHON_TEST

echo "✅ Structure verified"
ENDSSH

# Step 4: Restart APEX Bridge
echo ""
echo "4️⃣  Restarting APEX Bridge..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

echo "Restarting apex-bridge..."
pm2 restart apex-bridge || pm2 start ecosystem.config.cjs --only apex-bridge

echo "Waiting for service to start..."
sleep 3

echo "✅ APEX Bridge restarted"
ENDSSH

# Step 5: Test health endpoint
echo ""
echo "5️⃣  Testing health endpoint..."
sleep 2

HEALTH_RESPONSE=$(curl -s http://$INSTANCE_IP:8888/health || echo "{}")

if echo "$HEALTH_RESPONSE" | grep -q "apex_available.*true"; then
    echo "✅ APEX Bridge is healthy!"
    echo ""
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "⚠️  Health check response:"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    echo ""
    echo "Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs apex-bridge'"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Deployment Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs apex-bridge'"
echo "2. Test endpoint: curl http://$INSTANCE_IP:8888/health"
echo "3. View status: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 status'"
echo ""

