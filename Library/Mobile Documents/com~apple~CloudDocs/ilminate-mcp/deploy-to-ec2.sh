#!/bin/bash
# Deploy ilminate-mcp to EC2 (No Docker Required)

set -e

# Configuration
INSTANCE_IP="${EC2_INSTANCE_IP}"
SSH_KEY="${EC2_SSH_KEY:-~/.ssh/id_rsa}"
REMOTE_USER="${EC2_USER:-ec2-user}"
REMOTE_DIR="/opt/ilminate-mcp"

# Check if instance IP provided
if [ -z "$INSTANCE_IP" ]; then
    echo "❌ Error: EC2_INSTANCE_IP not set"
    echo ""
    echo "Usage:"
    echo "  export EC2_INSTANCE_IP=your-instance-ip"
    echo "  export EC2_SSH_KEY=~/.ssh/your-key.pem  # Optional"
    echo "  ./deploy-to-ec2.sh"
    echo ""
    exit 1
fi

echo "🚀 Deploying ilminate-mcp to EC2"
echo "Instance: $INSTANCE_IP"
echo "Remote: $REMOTE_USER@$INSTANCE_IP:$REMOTE_DIR"
echo ""

# Step 1: Build
echo "1️⃣  Building application..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi
echo "✅ Build complete"
echo ""

# Step 2: Ensure directory exists
echo "2️⃣  Ensuring directory exists on EC2..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP "sudo mkdir -p $REMOTE_DIR && sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR"

# Step 3: Copy files
echo "3️⃣  Copying files to EC2..."
rsync -avz \
  --exclude node_modules \
  --exclude .git \
  --exclude '*.log' \
  --exclude .env \
  --include 'dist/**' \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  ./ $REMOTE_USER@$INSTANCE_IP:$REMOTE_DIR/

echo "✅ Files copied"
echo ""

# Step 4: Setup on EC2
echo "4️⃣  Setting up on EC2..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

echo "Creating directory and setting permissions..."
sudo mkdir -p $REMOTE_DIR
sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR

echo "Installing Node.js dependencies..."
cd $REMOTE_DIR
npm install --production

echo "Installing Python dependencies..."
cd bridge
pip3 install -r requirements.txt --user || pip3 install -r requirements.txt

echo "Creating logs directory..."
mkdir -p $REMOTE_DIR/logs

echo "Checking PM2..."
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    sudo npm install -g pm2 || npm install -g pm2 --prefix ~/.local
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Starting services with PM2..."
cd $REMOTE_DIR
export PATH="$HOME/.local/bin:$PATH"
which pm2 || export PATH="/usr/local/bin:$PATH"

pm2 delete apex-bridge mcp-server 2>/dev/null || true
pm2 start ecosystem.config.cjs || (sudo npm install -g pm2 && pm2 start ecosystem.config.cjs)
pm2 save

echo "Setting up PM2 startup..."
pm2 startup systemd -u $REMOTE_USER --hp /home/$REMOTE_USER 2>&1 | grep -v "PM2" | sudo bash || true

echo "✅ Setup complete on EC2"
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Next steps:"
echo "1. Test health endpoint:"
echo "   curl http://$INSTANCE_IP:8888/health"
echo ""
echo "2. View logs:"
echo "   ssh $REMOTE_USER@$INSTANCE_IP 'pm2 logs'"
echo ""
echo "3. Check status:"
echo "   ssh $REMOTE_USER@$INSTANCE_IP 'pm2 status'"
echo ""

