#!/bin/bash
# Deploy ilminate-agent to EC2 directly from Git repository
# No manual copying needed - clones directly from Git

set -e

# Configuration
INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"
AGENT_REPO="${ILMINATE_AGENT_REPO}"
AGENT_BRANCH="${ILMINATE_AGENT_BRANCH:-main}"
REMOTE_DIR="/opt/ilminate-agent"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Deploying ilminate-agent from Git Repository"
echo "Instance: $INSTANCE_IP"
echo "Repository: ${AGENT_REPO:-'NOT SET'}"
echo "Branch: $AGENT_BRANCH"
echo ""

# Check if repo URL provided
if [ -z "$AGENT_REPO" ]; then
    echo -e "${RED}❌ Error: ILMINATE_AGENT_REPO not set${NC}"
    echo ""
    echo "Usage:"
    echo "  export ILMINATE_AGENT_REPO='https://github.com/your-org/ilminate-agent.git'"
    echo "  export ILMINATE_AGENT_BRANCH='main'  # Optional, defaults to main"
    echo "  export EC2_INSTANCE_IP='54.237.174.195'  # Optional"
    echo "  ./deploy-agent-from-git.sh"
    echo ""
    echo "For private repos (SSH):"
    echo "  export ILMINATE_AGENT_REPO='git@github.com:your-org/ilminate-agent.git'"
    echo "  ./deploy-agent-from-git.sh"
    echo ""
    exit 1
fi

# Step 1: Clone or Update ilminate-agent
echo "1️⃣  Cloning/updating ilminate-agent from Git..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

cd /opt

# Clean up any old backups first
sudo rm -rf ilminate-agent.backup.* 2>/dev/null || true

# Backup existing if exists and has content
BACKUP_DIR=""
if [ -d "ilminate-agent" ] && [ "\$(ls -A ilminate-agent 2>/dev/null)" ]; then
    echo "Backing up existing ilminate-agent..."
    BACKUP_DIR="ilminate-agent.backup.\$(date +%Y%m%d_%H%M%S)"
    sudo mv ilminate-agent "\$BACKUP_DIR" || true
elif [ -d "ilminate-agent" ]; then
    # Empty directory - just remove it
    echo "Removing empty ilminate-agent directory..."
    sudo rm -rf ilminate-agent || true
fi

# Remove existing directory if clone fails
cleanup_on_error() {
    if [ -n "\$BACKUP_DIR" ] && [ -d "\$BACKUP_DIR" ]; then
        echo "Restoring backup..."
        sudo rm -rf ilminate-agent 2>/dev/null || true
        sudo mv "\$BACKUP_DIR" ilminate-agent || true
    fi
}

# Clone repository to /tmp first (avoids permission issues)
echo "Cloning ilminate-agent from Git..."
TEMP_DIR="/tmp/ilminate-agent-\$\$"
rm -rf "\$TEMP_DIR" 2>/dev/null || true

if [[ "$AGENT_REPO" == git@* ]]; then
    # SSH URL - need to ensure SSH key is available
    echo "Using SSH clone (ensure SSH key is configured)..."
    if git clone "$AGENT_REPO" "\$TEMP_DIR" 2>&1; then
        echo "✅ Clone successful"
    else
        echo "❌ Git clone failed. Check SSH key or use HTTPS URL."
        cleanup_on_error
        exit 1
    fi
else
    # HTTPS URL - try with branch first, then without if empty repo
    if git clone -b "$AGENT_BRANCH" "$AGENT_REPO" "\$TEMP_DIR" 2>&1; then
        echo "✅ Clone successful"
    elif git clone "$AGENT_REPO" "\$TEMP_DIR" 2>&1; then
        echo "✅ Clone successful (empty repository - no branch specified)"
    else
        echo "❌ Git clone failed. Repository may be private or URL incorrect."
        echo "For private repos, use:"
        echo "  - SSH: git@github.com:user/repo.git (requires SSH key setup)"
        echo "  - HTTPS with token: https://TOKEN@github.com/user/repo.git"
        cleanup_on_error
        exit 1
    fi
fi

# Move to final location
sudo rm -rf ilminate-agent 2>/dev/null || true
sudo mv "\$TEMP_DIR" ilminate-agent || {
    echo "❌ Failed to move to /opt/ilminate-agent"
    cleanup_on_error
    exit 1
}

# Set permissions
sudo chown -R $REMOTE_USER:$REMOTE_USER ilminate-agent

# If updating existing, pull latest
if [ -d "ilminate-agent/.git" ]; then
    cd ilminate-agent
    git checkout "$AGENT_BRANCH" 2>/dev/null || true
    git pull origin "$AGENT_BRANCH" 2>/dev/null || echo "Already up to date"
fi

echo "✅ Repository cloned/updated"
ENDSSH

# Step 2: Install dependencies
echo ""
echo "2️⃣  Installing Python dependencies..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

cd $REMOTE_DIR

# Check for requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip3 install -r requirements.txt --user || pip3 install -r requirements.txt
else
    echo -e "${YELLOW}⚠️  No requirements.txt found${NC}"
    echo "Installing common dependencies..."
    pip3 install pyyaml requests numpy scikit-learn --user || pip3 install pyyaml requests numpy scikit-learn
fi

echo "✅ Dependencies installed"
ENDSSH

# Step 3: Verify structure
echo ""
echo "3️⃣  Verifying structure..."
VERIFY_RESULT=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << 'ENDSSH'
cd /opt/ilminate-agent

# Check for apex_detection_engine.py
if [ -f "plugins/apex_detection_engine.py" ]; then
    echo "✅ Found: plugins/apex_detection_engine.py"
elif [ -f "apex_detection_engine.py" ]; then
    echo "⚠️  Found: apex_detection_engine.py (not in plugins/)"
    echo "Creating plugins directory..."
    mkdir -p plugins
    mv apex_detection_engine.py plugins/ 2>/dev/null || true
else
    echo "❌ apex_detection_engine.py not found"
    echo "Available files:"
    find . -name "*apex*" -type f | head -5
    exit 1
fi

# Test Python import
python3 << PYTHON_TEST
import sys
sys.path.insert(0, '/opt/ilminate-agent')
try:
    from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict
    print("✅ Python import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
PYTHON_TEST
ENDSSH
)

if [ $? -eq 0 ]; then
    echo "$VERIFY_RESULT"
    echo "✅ Structure verified"
else
    echo -e "${RED}❌ Verification failed${NC}"
    echo "$VERIFY_RESULT"
    exit 1
fi

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

HEALTH_RESPONSE=$(curl -s http://$INSTANCE_IP:8888/health 2>&1 || echo "{}")

if echo "$HEALTH_RESPONSE" | grep -q "apex_available.*true"; then
    echo -e "${GREEN}✅ APEX Bridge is healthy!${NC}"
    echo ""
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${YELLOW}⚠️  Health check response:${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
    echo ""
    echo "Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs apex-bridge'"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Verify: curl http://$INSTANCE_IP:8888/health"
echo "2. Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs apex-bridge'"
echo "3. Update later: Just run this script again (it will pull latest)"
echo ""

