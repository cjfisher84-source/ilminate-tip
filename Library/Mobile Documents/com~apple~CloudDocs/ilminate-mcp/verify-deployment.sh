#!/bin/bash
# Verify ilminate-mcp deployment status

set -e

INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"

echo "🔍 Verifying ilminate-mcp Deployment"
echo "Instance: $INSTANCE_IP"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_passed=0
check_failed=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((check_passed++))
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        ((check_failed++))
        return 1
    fi
}

# 1. Check PM2 services
echo "1️⃣  Checking PM2 Services..."
PM2_STATUS=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP 'pm2 status --no-color' 2>&1)

if echo "$PM2_STATUS" | grep -q "mcp-server.*online"; then
    check "MCP Server is online"
else
    check "MCP Server is online" && false
fi

if echo "$PM2_STATUS" | grep -q "apex-bridge.*online"; then
    check "APEX Bridge is online"
else
    if echo "$PM2_STATUS" | grep -q "apex-bridge.*errored"; then
        echo -e "${YELLOW}⚠️  APEX Bridge is errored (likely needs ilminate-agent)${NC}"
        ((check_failed++))
    else
        check "APEX Bridge is online" && false
    fi
fi

# 2. Check ilminate-agent
echo ""
echo "2️⃣  Checking ilminate-agent..."
if ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP 'test -d /opt/ilminate-agent' 2>/dev/null; then
    check "ilminate-agent directory exists"
    
    if ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP 'test -f /opt/ilminate-agent/plugins/apex_detection_engine.py' 2>/dev/null; then
        check "apex_detection_engine.py exists"
    else
        check "apex_detection_engine.py exists" && false
    fi
else
    check "ilminate-agent directory exists" && false
fi

# 3. Test Python import
echo ""
echo "3️⃣  Testing Python Import..."
IMPORT_TEST=$(ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP 'python3 << EOF
import sys
sys.path.insert(0, "/opt/ilminate-agent")
try:
    from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
EOF
' 2>&1)

if echo "$IMPORT_TEST" | grep -q "SUCCESS"; then
    check "Python import works"
else
    check "Python import works" && false
fi

# 4. Test APEX Bridge health endpoint
echo ""
echo "4️⃣  Testing APEX Bridge Health..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://$INSTANCE_IP:8888/health 2>&1 || echo -e "\n000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    check "APEX Bridge health endpoint responds"
    
    if echo "$HEALTH_BODY" | grep -q '"apex_available".*true'; then
        check "APEX is available"
    else
        check "APEX is available" && false
    fi
    
    if echo "$HEALTH_BODY" | grep -q '"apex_initialized".*true'; then
        check "APEX is initialized"
    else
        check "APEX is initialized" && false
    fi
else
    check "APEX Bridge health endpoint responds" && false
fi

# 5. Test MCP Server
echo ""
echo "5️⃣  Testing MCP Server..."
MCP_RESPONSE=$(curl -s -w "\n%{http_code}" http://$INSTANCE_IP:3000 2>&1 || echo -e "\n000")
MCP_CODE=$(echo "$MCP_RESPONSE" | tail -1)

if [ "$MCP_CODE" = "200" ] || [ "$MCP_CODE" = "404" ] || [ "$MCP_CODE" = "405" ]; then
    check "MCP Server responds"
else
    check "MCP Server responds" && false
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Verification Summary"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Passed: $check_passed${NC}"
echo -e "${RED}❌ Failed: $check_failed${NC}"
echo ""

if [ $check_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Deployment is healthy.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. See details above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Deploy ilminate-agent: ./deploy-ilminate-agent.sh"
    echo "  • Restart services: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 restart all'"
    echo "  • Check logs: ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs'"
    exit 1
fi

