#!/bin/bash
# Deploy ilminate-agent to EC2 from local repository
# Run this script from the ilminate-agent repository directory

set -e

# Configuration
INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"
REMOTE_DIR="/opt/ilminate-agent"
LOCAL_DIR="${PWD}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Deploying ilminate-agent to EC2"
echo "Instance: $INSTANCE_IP"
echo "Source: $LOCAL_DIR"
echo "Destination: $REMOTE_DIR"
echo ""

# Check if we're in ilminate-agent directory
if [ ! -f "plugins/apex_detection_engine.py" ] && [ ! -f "apex_detection_engine.py" ]; then
    echo -e "${YELLOW}⚠️  Warning: apex_detection_engine.py not found in current directory${NC}"
    echo "Make sure you're running this from the ilminate-agent repository"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Create remote directory
echo "1️⃣  Creating remote directory..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e
sudo mkdir -p $REMOTE_DIR
sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR
echo "✅ Directory created"
ENDSSH

# Step 2: Sync files
echo ""
echo "2️⃣  Syncing files to EC2..."
rsync -avz \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude="*.pyc" \
  --exclude=.venv \
  --exclude=venv \
  --exclude=node_modules \
  --exclude="*.log" \
  --exclude=".env" \
  --exclude=".env.*" \
  --exclude="*.swp" \
  --exclude="*.swo" \
  --exclude="*~" \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  "$LOCAL_DIR/" $REMOTE_USER@$INSTANCE_IP:$REMOTE_DIR/

echo "✅ Files synced"
echo ""

# Step 3: Install dependencies
echo "3️⃣  Installing Python dependencies..."
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

# Step 4: Verify structure
echo ""
echo "4️⃣  Verifying structure..."
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

# Step 5: Restart APEX Bridge
echo ""
echo "5️⃣  Restarting APEX Bridge..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

echo "Restarting apex-bridge..."
pm2 restart apex-bridge || pm2 start ecosystem.config.cjs --only apex-bridge

echo "Waiting for service to start..."
sleep 3

echo "✅ APEX Bridge restarted"
ENDSSH

# Step 6: Test health endpoint
echo ""
echo "6️⃣  Testing health endpoint..."
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

# Step 7: Final status check
echo ""
echo "7️⃣  Final status check..."
PM2_STATUS=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP 'pm2 status --no-color' 2>&1)

if echo "$PM2_STATUS" | grep -q "apex-bridge.*online"; then
    echo -e "${GREEN}✅ APEX Bridge is online${NC}"
else
    echo -e "${YELLOW}⚠️  APEX Bridge status:${NC}"
    echo "$PM2_STATUS" | grep apex-bridge || echo "Not found in PM2"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Verify: curl http://$INSTANCE_IP:8888/health"
echo "2. Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs apex-bridge'"
echo "3. View status: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 status'"
echo ""

