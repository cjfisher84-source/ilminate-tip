#!/bin/bash
# Setup automatic updates for ilminate-agent from Git
# Creates a cron job to pull latest changes periodically

set -e

INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"
AGENT_REPO="${ILMINATE_AGENT_REPO}"
AGENT_BRANCH="${ILMINATE_AGENT_BRANCH:-main}"
UPDATE_INTERVAL="${UPDATE_INTERVAL:-0 2 * * *}"  # Daily at 2 AM

if [ -z "$AGENT_REPO" ]; then
    echo "❌ Error: ILMINATE_AGENT_REPO not set"
    echo ""
    echo "Usage:"
    echo "  export ILMINATE_AGENT_REPO='https://github.com/your-org/ilminate-agent.git'"
    echo "  ./setup-auto-update.sh"
    echo ""
    exit 1
fi

echo "🔧 Setting up automatic updates for ilminate-agent"
echo "Repository: $AGENT_REPO"
echo "Branch: $AGENT_BRANCH"
echo "Update schedule: $UPDATE_INTERVAL"
echo ""

# Create update script on EC2
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

cat > /home/$REMOTE_USER/update-ilminate-agent.sh << 'UPDATE_SCRIPT'
#!/bin/bash
# Auto-update script for ilminate-agent

set -e

AGENT_REPO="$AGENT_REPO"
AGENT_BRANCH="$AGENT_BRANCH"
REMOTE_DIR="/opt/ilminate-agent"

cd \$REMOTE_DIR

# Pull latest changes
git fetch origin
git checkout \$AGENT_BRANCH
git pull origin \$AGENT_BRANCH

# Install any new dependencies
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --user || pip3 install -r requirements.txt
fi

# Restart APEX Bridge
pm2 restart apex-bridge

echo "\$(date): Updated ilminate-agent from \$AGENT_REPO"
UPDATE_SCRIPT

chmod +x /home/$REMOTE_USER/update-ilminate-agent.sh

# Add to crontab
(crontab -l 2>/dev/null | grep -v "update-ilminate-agent.sh"; echo "$UPDATE_INTERVAL /home/$REMOTE_USER/update-ilminate-agent.sh >> /home/$REMOTE_USER/update-ilminate-agent.log 2>&1") | crontab -

echo "✅ Auto-update configured"
echo "Update script: /home/$REMOTE_USER/update-ilminate-agent.sh"
echo "Log file: /home/$REMOTE_USER/update-ilminate-agent.log"
ENDSSH

echo ""
echo "✅ Automatic updates configured!"
echo ""
echo "To update manually:"
echo "  ssh $REMOTE_USER@$INSTANCE_IP '/home/$REMOTE_USER/update-ilminate-agent.sh'"
echo ""


