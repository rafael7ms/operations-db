#!/bin/bash
set -e

# opsdb Serverless Destroy Script

STACK_NAME="opsdb-api-dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}WARNING: This will destroy the opsdb stack and all its resources!${NC}"
echo -e "${YELLOW}Stack to destroy: $STACK_NAME${NC}"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Deployment cancelled.${NC}"
    exit 0
fi

# Delete CloudFormation stack
echo -e "${YELLOW}Deleting CloudFormation stack...${NC}"
aws cloudformation delete-stack \
    --stack-name "$STACK_NAME" \
    --region us-east-1

# Wait for stack deletion
echo -e "${YELLOW}Waiting for stack deletion...${NC}"
aws cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Stack deleted successfully!${NC}"
else
    echo -e "${RED}Failed to delete stack!${NC}"
    exit 1
fi
