#!/bin/bash

# Deployment script for F5-TTS API
# This script builds Docker image, pushes to ECR, and updates CloudFormation stack

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api"
STACK_NAME="f5-tts-spot-stack"
DEPLOYMENT_TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo "🚀 Starting F5-TTS API deployment..."
echo "   Timestamp: $DEPLOYMENT_TIMESTAMP"
echo "   ECR Repository: $ECR_REPOSITORY"
echo "   Stack: $STACK_NAME"

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.api --target production -t f5-tts-api:latest .

# Step 2: Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag f5-tts-api:latest $ECR_REPOSITORY:latest
docker tag f5-tts-api:latest $ECR_REPOSITORY:amd64

# Step 3: Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Step 4: Push to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_REPOSITORY:latest
docker push $ECR_REPOSITORY:amd64

# Step 5: Update CloudFormation stack
echo "☁️  Updating CloudFormation stack..."
aws cloudformation update-stack \
  --stack-name $STACK_NAME \
  --template-body file://cloudformation.yaml \
  --parameters \
    ParameterKey=ECRImageURI,ParameterValue=$ECR_REPOSITORY:amd64 \
    ParameterKey=DeploymentTimestamp,ParameterValue=$DEPLOYMENT_TIMESTAMP \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

echo "⏳ Waiting for stack update to complete..."
aws cloudformation wait stack-update-complete \
  --stack-name $STACK_NAME \
  --region $AWS_REGION

# Step 6: Get stack outputs
echo "📋 Stack update completed! Getting outputs..."
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs' \
  --output table

echo "✅ Deployment completed successfully!"
echo "🌐 API URL: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' --output text)"
