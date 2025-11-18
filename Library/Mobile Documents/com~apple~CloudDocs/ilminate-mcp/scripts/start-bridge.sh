#!/bin/bash
# Start APEX Bridge Service
# This script starts the Python Flask bridge that connects MCP server to ilminate-agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE_DIR="$REPO_DIR/bridge"

echo "🌉 Starting APEX Bridge Service..."
echo ""

# Check if bridge directory exists
if [ ! -d "$BRIDGE_DIR" ]; then
    echo "❌ Bridge directory not found: $BRIDGE_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$BRIDGE_DIR/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    cd "$BRIDGE_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
cd "$BRIDGE_DIR"
source venv/bin/activate

# Check if ilminate-agent is accessible
ILMINATE_AGENT_PATH="$REPO_DIR/../ilminate-agent"
if [ ! -d "$ILMINATE_AGENT_PATH" ]; then
    echo "⚠️  Warning: ilminate-agent not found at $ILMINATE_AGENT_PATH"
    echo "   APEX Bridge may not work correctly"
fi

# Set port from environment or use default
BRIDGE_PORT=${APEX_BRIDGE_PORT:-8888}
export APEX_BRIDGE_PORT=$BRIDGE_PORT

echo "📍 Bridge will run on port: $BRIDGE_PORT"
echo "📍 ilminate-agent path: $ILMINATE_AGENT_PATH"
echo ""
echo "Starting APEX Bridge..."
echo "Press Ctrl+C to stop"
echo ""

# Start the bridge
cd "$BRIDGE_DIR"
python3 apex_bridge.py
