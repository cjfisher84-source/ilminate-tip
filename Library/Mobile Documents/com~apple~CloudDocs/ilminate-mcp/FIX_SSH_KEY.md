# Fix SSH Key Issue

## Problem
Instance launched with key pair `wazuh`, but SSH key file not found locally.

---

## Solution Options

### Option 1: Use Existing Key (If You Have It)

If you have the `wazuh.pem` file somewhere:

```bash
# Find it
find ~ -name "wazuh.pem" 2>/dev/null
find ~/Downloads -name "*.pem" 2>/dev/null

# Then deploy
export EC2_INSTANCE_IP="44.215.126.5"
export EC2_SSH_KEY="/path/to/wazuh.pem"
./deploy-to-ec2.sh
```

### Option 2: Create New Key Pair & Relaunch (Recommended)

**Step 1: Create new key pair**
```bash
# Create key pair
aws ec2 create-key-pair --key-name ilminate-mcp-key --query 'KeyMaterial' --output text > ~/.ssh/ilminate-mcp-key.pem
chmod 400 ~/.ssh/ilminate-mcp-key.pem

# Get key name
echo "Key created: ~/.ssh/ilminate-mcp-key.pem"
```

**Step 2: Terminate old instance**
```bash
aws ec2 terminate-instances --instance-ids i-0072a64945db7c13f
```

**Step 3: Launch new instance with new key**
```bash
cd "/Users/cfisher/Library/Mobile Documents/com~apple~CloudDocs/ilminate-mcp"

aws ec2 run-instances \
  --image-id ami-0cae6d6fe6048ca2c \
  --instance-type t3.medium \
  --key-name ilminate-mcp-key \
  --security-group-ids sg-080be80fca33b282e \
  --subnet-id subnet-07c149f7a889e8795 \
  --user-data file://ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ilminate-mcp}]'

# Wait and get IP
aws ec2 wait instance-running --instance-ids i-NEW_INSTANCE_ID
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids i-NEW_INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
```

**Step 4: Deploy**
```bash
export EC2_INSTANCE_IP=$INSTANCE_IP
export EC2_SSH_KEY=~/.ssh/ilminate-mcp-key.pem
./deploy-to-ec2.sh
```

### Option 3: Use AWS Systems Manager (If Configured)

If you have SSM access configured:

```bash
# Connect via SSM
aws ssm start-session --target i-0072a64945db7c13f

# Then manually deploy (see manual steps in DEPLOY_NOW.md)
```

---

## Quick Fix Script

I can create a script that:
1. Creates a new key pair
2. Terminates the old instance
3. Launches a new one
4. Deploys automatically

**Would you like me to create this script?**

---

## Current Status

- ✅ Instance running: `i-0072a64945db7c13f`
- ✅ IP: `44.215.126.5`
- ✅ Security group configured
- ❌ SSH key missing

**Choose an option above to proceed!**

