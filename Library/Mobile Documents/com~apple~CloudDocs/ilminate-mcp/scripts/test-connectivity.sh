#!/bin/bash
# Test ilminate MCP Server Connectivity
# Tests all components and integrations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🧪 Testing ilminate MCP Server Connectivity..."
echo ""

# Load environment variables
if [ -f "$REPO_DIR/.env" ]; then
    export $(cat "$REPO_DIR/.env" | grep -v '^#' | xargs)
fi

APEX_BRIDGE_URL=${APEX_BRIDGE_URL:-http://localhost:8888}

# Test 1: APEX Bridge Health
echo "1️⃣  Testing APEX Bridge Health..."
if curl -s -f "$APEX_BRIDGE_URL/health" > /dev/null 2>&1; then
    echo "   ✅ APEX Bridge is running"
    HEALTH_RESPONSE=$(curl -s "$APEX_BRIDGE_URL/health")
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ❌ APEX Bridge is not running"
    echo "   💡 Start it with: ./scripts/start-bridge.sh"
fi

echo ""

# Test 2: APEX Bridge Status
echo "2️⃣  Testing APEX Bridge Status..."
if curl -s -f "$APEX_BRIDGE_URL/api/status" > /dev/null 2>&1; then
    echo "   ✅ APEX Bridge status endpoint accessible"
    STATUS_RESPONSE=$(curl -s "$APEX_BRIDGE_URL/api/status")
    echo "   Response: $STATUS_RESPONSE"
else
    echo "   ❌ APEX Bridge status endpoint not accessible"
fi

echo ""

# Test 3: MCP Server Build
echo "3️⃣  Testing MCP Server Build..."
if [ -d "$REPO_DIR/dist" ] && [ -f "$REPO_DIR/dist/index.js" ]; then
    echo "   ✅ MCP Server is built"
else
    echo "   ❌ MCP Server is not built"
    echo "   💡 Build it with: npm run build"
fi

echo ""

# Test 4: Node.js Dependencies
echo "4️⃣  Testing Node.js Dependencies..."
if [ -d "$REPO_DIR/node_modules" ]; then
    echo "   ✅ Node.js dependencies installed"
else
    echo "   ❌ Node.js dependencies not installed"
    echo "   💡 Install with: npm install"
fi

echo ""

# Test 5: Python Bridge Dependencies
echo "5️⃣  Testing Python Bridge Dependencies..."
BRIDGE_DIR="$REPO_DIR/bridge"
if [ -d "$BRIDGE_DIR/venv" ]; then
    echo "   ✅ Python virtual environment exists"
    source "$BRIDGE_DIR/venv/bin/activate"
    if python3 -c "import flask" 2>/dev/null; then
        echo "   ✅ Python dependencies installed"
    else
        echo "   ❌ Python dependencies not installed"
        echo "   💡 Install with: cd bridge && pip install -r requirements.txt"
    fi
    deactivate
else
    echo "   ❌ Python virtual environment not found"
    echo "   💡 Create with: cd bridge && python3 -m venv venv"
fi

echo ""

# Test 6: ilminate-agent Connection
echo "6️⃣  Testing ilminate-agent Connection..."
ILMINATE_AGENT_PATH="$REPO_DIR/../ilminate-agent"
if [ -d "$ILMINATE_AGENT_PATH" ]; then
    echo "   ✅ ilminate-agent directory found"
    if [ -f "$ILMINATE_AGENT_PATH/plugins/apex_detection_engine.py" ]; then
        echo "   ✅ APEX detection engine found"
    else
        echo "   ⚠️  APEX detection engine not found"
    fi
else
    echo "   ⚠️  ilminate-agent directory not found"
fi

echo ""
echo "✅ Connectivity tests complete!"
echo ""
echo "Summary:"
echo "- APEX Bridge: Check status above"
echo "- MCP Server: Ready to start with 'npm start'"
echo "- Integration: Configure .env file for service URLs"

