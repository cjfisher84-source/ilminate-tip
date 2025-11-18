#!/bin/bash
# Fix SSH key issue and deploy automatically

set -e

echo "🔧 Fixing SSH key and deploying..."
echo ""

# Step 1: Create new key pair
echo "1️⃣  Creating new key pair..."
KEY_NAME="ilminate-mcp-key"
KEY_FILE="$HOME/.ssh/ilminate-mcp-key.pem"

# Check if key already exists
if [ -f "$KEY_FILE" ]; then
    echo "✅ Key already exists: $KEY_FILE"
else
    aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > "$KEY_FILE"
    chmod 400 "$KEY_FILE"
    echo "✅ Key created: $KEY_FILE"
fi

# Step 2: Terminate old instance
echo ""
echo "2️⃣  Terminating old instance..."
OLD_INSTANCE_ID="i-0072a64945db7c13f"
aws ec2 terminate-instances --instance-ids $OLD_INSTANCE_ID > /dev/null
echo "⏳ Waiting for instance to terminate..."
aws ec2 wait instance-terminated --instance-ids $OLD_INSTANCE_ID
echo "✅ Old instance terminated"

# Step 3: Launch new instance
echo ""
echo "3️⃣  Launching new instance with new key..."
SG_ID="sg-080be80fca33b282e"
SUBNET_ID="subnet-07c149f7a889e8795"
AMI_ID="ami-0cae6d6fe6048ca2c"

INSTANCE_OUTPUT=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.medium \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --user-data file://ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ilminate-mcp}]' \
  --query 'Instances[0].[InstanceId,State.Name]' \
  --output text)

NEW_INSTANCE_ID=$(echo $INSTANCE_OUTPUT | awk '{print $1}')
echo "✅ Instance launched: $NEW_INSTANCE_ID"

# Step 4: Wait for running
echo ""
echo "4️⃣  Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $NEW_INSTANCE_ID
sleep 5

INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $NEW_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Instance running at: $INSTANCE_IP"

# Step 5: Wait for user-data script
echo ""
echo "5️⃣  Waiting for user-data script to complete..."
sleep 30
echo "✅ Ready to deploy"

# Step 6: Deploy
echo ""
echo "6️⃣  Deploying application..."
export EC2_INSTANCE_IP=$INSTANCE_IP
export EC2_SSH_KEY=$KEY_FILE
export EC2_USER="ec2-user"

./deploy-to-ec2.sh

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Instance IP: $INSTANCE_IP"
echo "SSH Key: $KEY_FILE"
echo ""
echo "Test: curl http://$INSTANCE_IP:8888/health"
echo ""

