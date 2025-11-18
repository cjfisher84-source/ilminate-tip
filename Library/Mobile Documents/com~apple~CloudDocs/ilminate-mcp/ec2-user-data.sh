#!/bin/bash
# EC2 User Data Script
# Runs on instance startup to install dependencies

# Update system
yum update -y

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Install Python 3 and pip
yum install -y python3 python3-pip git

# Install PM2 for process management
npm install -g pm2

# Create application directory
mkdir -p /opt/ilminate-mcp
chown ec2-user:ec2-user /opt/ilminate-mcp

# Log completion
echo "User data script completed at $(date)" >> /var/log/user-data.log

