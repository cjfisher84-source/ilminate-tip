#!/bin/bash
# Setup GitHub SSH access on EC2 for private repository cloning

set -e

INSTANCE_IP="${EC2_INSTANCE_IP:-54.237.174.195}"
SSH_KEY="${EC2_SSH_KEY:-$HOME/.ssh/ilminate-mcp-key.pem}"
REMOTE_USER="${EC2_USER:-ec2-user}"
GITHUB_SSH_KEY="${GITHUB_SSH_KEY:-$HOME/.ssh/id_rsa}"

echo "🔑 Setting up GitHub SSH access on EC2"
echo ""

# Check if GitHub SSH key exists locally
if [ ! -f "$GITHUB_SSH_KEY" ]; then
    echo "❌ GitHub SSH key not found at: $GITHUB_SSH_KEY"
    echo ""
    echo "Options:"
    echo "1. Copy your existing SSH key:"
    echo "   export GITHUB_SSH_KEY=~/.ssh/id_rsa"
    echo "   ./setup-github-ssh.sh"
    echo ""
    echo "2. Generate a new SSH key:"
    echo "   ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "   # Then add to GitHub: https://github.com/settings/keys"
    echo ""
    echo "3. Use HTTPS instead (easier):"
    echo "   export ILMINATE_AGENT_REPO='https://github.com/cjfisher84-source/ilminate-agent.git'"
    echo "   ./deploy-agent-from-git.sh"
    exit 1
fi

echo "1️⃣  Copying SSH key to EC2..."
scp -i $SSH_KEY -o StrictHostKeyChecking=no \
  $GITHUB_SSH_KEY \
  $REMOTE_USER@$INSTANCE_IP:~/.ssh/id_rsa

echo "2️⃣  Setting up SSH config..."
ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$INSTANCE_IP << ENDSSH
set -e

# Create .ssh directory if needed
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Set key permissions
chmod 600 ~/.ssh/id_rsa

# Add GitHub to known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true

# Test GitHub connection
echo "Testing GitHub SSH connection..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "✅ GitHub SSH access configured!" || echo "⚠️  GitHub connection test completed"
ENDSSH

echo ""
echo "✅ GitHub SSH setup complete!"
echo ""
echo "Now you can deploy:"
echo "  export ILMINATE_AGENT_REPO='git@github.com:cjfisher84-source/ilminate-agent.git'"
echo "  ./deploy-agent-from-git.sh"
echo ""


