#!/bin/bash

# Pre-deployment checks for F5-TTS API
# Run this script before deploying to catch issues early

set -e

echo "🔍 F5-TTS API Pre-Deployment Checks"
echo "===================================="

# Check if AWS CLI is configured
echo "✅ Checking AWS CLI configuration..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI is not configured or credentials are invalid"
    exit 1
fi
echo "   AWS credentials are valid"

# Check if ECR repository exists
echo "✅ Checking ECR repository..."
ECR_REPOSITORY="475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api"
if ! aws ecr describe-repositories --repository-names f5-tts-api --region us-east-1 >/dev/null 2>&1; then
    echo "❌ ECR repository 'f5-tts-api' does not exist"
    echo "   Create it with: aws ecr create-repository --repository-name f5-tts-api --region us-east-1"
    exit 1
fi
echo "   ECR repository exists"

# Check if Docker is running
echo "✅ Checking Docker..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi
echo "   Docker is running"

# Check if required files exist
echo "✅ Checking required files..."
REQUIRED_FILES=("Dockerfile" "f5_tts_api.py" "cloudformation.yaml" "ref_audio/default.wav")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "   All required files present"

# Check CloudFormation stack status
echo "✅ Checking CloudFormation stack..."
STACK_NAME="f5-tts-spot-stack"
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region us-east-1 --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS")

if [ "$STACK_STATUS" = "NOT_EXISTS" ]; then
    echo "   Stack does not exist - will be created"
elif [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
    echo "   Stack exists and is in ready state: $STACK_STATUS"
elif [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "⚠️  Stack is in ROLLBACK_COMPLETE state - you may need to delete and recreate"
    echo "   Delete with: aws cloudformation delete-stack --stack-name $STACK_NAME --region us-east-1"
else
    echo "⚠️  Stack is in state: $STACK_STATUS"
fi

# Validate CloudFormation template
echo "✅ Validating CloudFormation template..."
if ! aws cloudformation validate-template --template-body file://cloudformation.yaml --region us-east-1 >/dev/null; then
    echo "❌ CloudFormation template validation failed"
    exit 1
fi
echo "   CloudFormation template is valid"

# Check if key pair exists
echo "✅ Checking EC2 key pair..."
KEY_NAME="f5-tts-debug-key"
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region us-east-1 >/dev/null 2>&1; then
    echo "⚠️  EC2 key pair '$KEY_NAME' does not exist"
    echo "   Create it with: aws ec2 create-key-pair --key-name $KEY_NAME --region us-east-1"
    echo "   Or update the CloudFormation template with an existing key pair name"
else
    echo "   EC2 key pair exists"
fi

echo ""
echo "🎉 Pre-deployment checks completed!"
echo "   Ready to deploy with: ./deploy.sh"
