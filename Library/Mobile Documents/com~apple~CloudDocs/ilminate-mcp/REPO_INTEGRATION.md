# Repository Integration - No Copy/Paste Needed!

**Connect all ilminate repos directly - no manual copying**

---

## 🎯 The Problem

Currently, you have to manually copy ilminate-agent files to EC2. This is tedious and error-prone.

## ✅ The Solution

**Use Git!** All repos can communicate directly via Git repositories.

---

## 🚀 Option 1: Deploy from Git (Recommended)

### Setup Once

```bash
# Set your repository URL
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"
export ILMINATE_AGENT_BRANCH="main"  # Optional, defaults to main
export EC2_INSTANCE_IP="54.237.174.195"

# Deploy (clones directly from Git)
./deploy-agent-from-git.sh
```

**That's it!** The script will:
1. Clone ilminate-agent from Git to EC2
2. Install dependencies
3. Restart APEX Bridge
4. Verify it works

### Update Later

Just run the script again - it will pull the latest changes:

```bash
./deploy-agent-from-git.sh
```

Or set up automatic updates (see below).

---

## 🔄 Option 2: Automatic Updates

Set up a cron job to automatically pull latest changes:

```bash
# Set repository
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"

# Setup auto-update (daily at 2 AM)
./setup-auto-update.sh
```

**Manual update anytime:**
```bash
ssh ec2-user@54.237.174.195 '/home/ec2-user/update-ilminate-agent.sh'
```

---

## 🔗 Option 3: Connect Multiple Repos

### Setup All Repos

```bash
# ilminate-agent
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"
./deploy-agent-from-git.sh

# ilminate-portal (if needed)
export PORTAL_REPO="https://github.com/your-org/ilminate-portal.git"
# Create similar script for portal

# ilminate-siem (if needed)
export SIEM_REPO="https://github.com/your-org/ilminate-siem.git"
# Create similar script for siem
```

---

## 🔐 Private Repositories

### HTTPS with Credentials

```bash
# Use personal access token
export ILMINATE_AGENT_REPO="https://TOKEN@github.com/your-org/ilminate-agent.git"
./deploy-agent-from-git.sh
```

### SSH (Recommended for Private)

```bash
# 1. Add SSH key to EC2
scp -i ~/.ssh/ilminate-mcp-key.pem ~/.ssh/id_rsa ec2-user@54.237.174.195:~/.ssh/

# 2. Use SSH URL
export ILMINATE_AGENT_REPO="git@github.com:your-org/ilminate-agent.git"
./deploy-agent-from-git.sh
```

---

## 📋 Workflow Examples

### Development Workflow

```bash
# 1. Make changes in ilminate-agent repo
cd /path/to/ilminate-agent
# ... make changes ...
git add .
git commit -m "Update detection logic"
git push origin main

# 2. Deploy to EC2 (pulls latest)
cd /path/to/ilminate-mcp
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"
./deploy-agent-from-git.sh

# 3. Test
curl http://54.237.174.195:8888/health
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy ilminate-agent
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to EC2
        run: |
          export ILMINATE_AGENT_REPO="https://github.com/${{ github.repository }}.git"
          ./deploy-agent-from-git.sh
```

---

## 🔧 Advanced: Multi-Repo Setup

### Setup Script for All Repos

Create `setup-all-repos.sh`:

```bash
#!/bin/bash
# Setup all ilminate repos from Git

export EC2_INSTANCE_IP="54.237.174.195"

# ilminate-agent
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"
./deploy-agent-from-git.sh

# ilminate-mcp (if updating)
# Already deployed, but can update:
ssh ec2-user@$EC2_INSTANCE_IP 'cd /opt/ilminate-mcp && git pull'

# Other repos...
```

---

## ✅ Benefits

1. ✅ **No Manual Copying** - Git handles everything
2. ✅ **Version Control** - Track what's deployed
3. ✅ **Easy Updates** - Just pull latest changes
4. ✅ **Rollback** - Easy to revert to previous version
5. ✅ **Automation** - Can set up CI/CD
6. ✅ **Multiple Environments** - Deploy different branches

---

## 📊 Comparison

| Method | Manual Copy | Git Clone |
|--------|-------------|-----------|
| Setup | Copy files | Set repo URL |
| Update | Copy again | Run script (pulls latest) |
| Version Control | None | Full Git history |
| Rollback | Manual | `git checkout <tag>` |
| Automation | Hard | Easy (CI/CD) |

---

## 🚀 Quick Start

```bash
# 1. Set repository URL
export ILMINATE_AGENT_REPO="https://github.com/your-org/ilminate-agent.git"

# 2. Deploy
./deploy-agent-from-git.sh

# 3. Done! No copying needed.
```

**To update later:**
```bash
# Just run again - pulls latest
./deploy-agent-from-git.sh
```

---

## 🔍 Troubleshooting

### "Git clone failed"

**For private repos:** Use SSH or add credentials:
```bash
# SSH
export ILMINATE_AGENT_REPO="git@github.com:your-org/ilminate-agent.git"

# HTTPS with token
export ILMINATE_AGENT_REPO="https://TOKEN@github.com/your-org/ilminate-agent.git"
```

### "Permission denied"

Ensure Git is installed on EC2:
```bash
ssh ec2-user@54.237.174.195 'sudo yum install -y git'
```

### "Branch not found"

Specify correct branch:
```bash
export ILMINATE_AGENT_BRANCH="develop"  # or "main", "master", etc.
```

---

## 📚 Summary

**Instead of copying files:**
- ❌ `rsync` or `scp` files manually
- ❌ Update dependencies manually
- ❌ Restart services manually

**Use Git integration:**
- ✅ Set repository URL once
- ✅ Run deployment script
- ✅ Automatic updates available
- ✅ Version control built-in

**No more copy/paste!** 🎉

