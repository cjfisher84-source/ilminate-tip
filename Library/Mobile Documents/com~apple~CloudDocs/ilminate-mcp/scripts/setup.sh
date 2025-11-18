#!/bin/bash
# ilminate MCP Server Setup Script
# Sets up the MCP server and APEX Bridge service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Setting up ilminate MCP Server..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✅ Node.js: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install npm"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo "✅ npm: $NPM_VERSION"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ Python: $PYTHON_VERSION"

# Check ilminate-agent
if [ ! -d "$REPO_DIR/../ilminate-agent" ]; then
    echo "⚠️  Warning: ilminate-agent not found at ../ilminate-agent"
    echo "   APEX Bridge may not work correctly"
else
    echo "✅ ilminate-agent found"
fi

echo ""
echo "📦 Installing dependencies..."

# Install Node.js dependencies
cd "$REPO_DIR"
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies already installed"
fi

# Install Python dependencies for bridge
cd "$REPO_DIR/bridge"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Python dependencies installed"

# Build TypeScript
echo ""
echo "🔨 Building TypeScript..."
cd "$REPO_DIR"
npm run build
echo "✅ Build complete"

# Create .env if it doesn't exist
if [ ! -f "$REPO_DIR/.env" ]; then
    echo ""
    echo "📝 Creating .env file from .env.example..."
    if [ -f "$REPO_DIR/.env.example" ]; then
        cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
        echo "✅ .env file created"
        echo "⚠️  Please review and update .env with your configuration"
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > "$REPO_DIR/.env" << EOF
# ilminate MCP Server Configuration
APEX_BRIDGE_URL=http://localhost:8888
LOG_LEVEL=info
API_KEY_REQUIRED=false
EOF
        echo "✅ Basic .env file created"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file if needed"
echo "2. Start APEX Bridge: ./scripts/start-bridge.sh"
echo "3. Start MCP Server: npm start"
echo "4. Test connectivity: ./scripts/test-connectivity.sh"

