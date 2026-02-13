#!/bin/bash
set -e

# opsdb Serverless Deployment Script

# Configuration
STACK_NAME="opsdb-api-dev"
TEMPLATE_FILE="template.yaml"
PARAMS_FILE="dev.params.json"
S3_BUCKET="opsdb-sam-deployments-$(date +%Y%m%d)-$RANDOM"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting opsdb deployment...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}SAM CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS credentials are not configured. Please run 'aws configure'.${NC}"
    exit 1
fi

# Parse parameters
while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" =~ ^# ]] && continue
    export "$key=$value"
done < "$PARAMS_FILE"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Stack Name: $STACK_NAME"
echo "  Environment: $EnvironmentName"
echo "  VPC ID: $VpcId"
echo "  Subnets: $SubnetIds"
echo "  Security Group: $SecurityGroupId"

# Create S3 bucket for deployment artifacts
echo -e "${YELLOW}Creating S3 bucket for deployment artifacts...${NC}"
aws s3 mb "s3://$S3_BUCKET" --region us-east-1 2>/dev/null || true

# Build the SAM application
echo -e "${YELLOW}Building SAM application...${NC}"
sam build \
    --template-file "$TEMPLATE_FILE" \
    --use-container

# Validate the template
echo -e "${YELLOW}Validating SAM template...${NC}"
sam validate --template-file template.yaml

# Package and deploy
echo -e "${YELLOW}Deploying to AWS...${NC}"
sam deploy \
    --template-file template.yaml \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        EnvironmentName="$EnvironmentName" \
        VpcId="$VpcId" \
        SubnetIds="$SubnetIds" \
        SecurityGroupId="$SecurityGroupId" \
        DatabaseName="$DatabaseName" \
        MasterUsername="$MasterUsername" \
        SecretKey="$SecretKey" \
        MasterUserPassword="$MasterUserPassword" \
    --s3-bucket "$S3_BUCKET" \
    --region us-east-1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment complete!${NC}"
    echo ""
    echo -e "${YELLOW}Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs' \
        --output table
else
    echo -e "${RED}Deployment failed!${NC}"
    exit 1
fi
