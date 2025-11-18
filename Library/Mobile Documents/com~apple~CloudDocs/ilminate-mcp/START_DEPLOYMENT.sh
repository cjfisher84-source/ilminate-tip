#!/bin/bash
# Start Deployment Script
# Checks prerequisites and starts the deployment

echo "🚀 ilminate-mcp AWS Deployment"
echo "=============================="
echo ""

# Check AWS
echo "1️⃣  Checking AWS configuration..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run: aws configure"
    exit 1
fi
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
echo "✅ AWS Account: $ACCOUNT"
echo "✅ Region: $REGION"
echo ""

# Check Docker
echo "2️⃣  Checking Docker..."
if ! docker ps >/dev/null 2>&1; then
    echo "⚠️  Docker is not running"
    echo "   Starting Docker Desktop..."
    open -a Docker 2>/dev/null || echo "   Please start Docker Desktop manually"
    echo "   Waiting for Docker to start (30 seconds)..."
    sleep 30
    
    # Check again
    if ! docker ps >/dev/null 2>&1; then
        echo "❌ Docker still not running. Please start Docker Desktop and try again."
        exit 1
    fi
fi
echo "✅ Docker is running"
echo ""

# Check build
echo "3️⃣  Checking build..."
if [ ! -d "dist" ]; then
    echo "⚠️  dist/ directory not found. Building..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ Build failed. Fix errors and try again."
        exit 1
    fi
fi
echo "✅ Build ready"
echo ""

# Set region
export AWS_REGION=${AWS_REGION:-us-east-1}
export CLUSTER_NAME=ilminate-mcp

echo "4️⃣  Starting deployment setup..."
echo "   This will run: ./setup-ecs.sh"
echo "   Follow the prompts to complete deployment"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "🚀 Starting setup script..."
echo ""

./setup-ecs.sh

