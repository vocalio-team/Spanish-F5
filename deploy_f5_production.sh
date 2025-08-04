#!/bin/bash

STACK_NAME="f5-tts-production"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "🚀 Deploying F5-TTS Production Stack with EFS Integration"
echo "Stack Name: $STACK_NAME"
echo "Timestamp: $TIMESTAMP"
echo "EFS ID: fs-00c1631283c0bd7e1 (preloaded with models)"
echo ""

echo "📋 Validating CloudFormation template..."
aws cloudformation validate-template --template-body file://cloudformation.yaml || {
    echo "❌ Template validation failed!"
    exit 1
}

echo "✅ Template validated successfully!"
echo ""

echo "🏗️  Creating CloudFormation stack..."
aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://cloudformation.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters \
        ParameterKey=DeploymentTimestamp,ParameterValue="$TIMESTAMP" \
        ParameterKey=ExistingEFSId,ParameterValue=fs-00c1631283c0bd7e1 || {
    echo "❌ Stack creation failed!"
    exit 1
}

echo "✅ Stack creation initiated!"
echo ""
echo "🔍 You can monitor the deployment with:"
echo "./monitor_deployment.sh"
echo ""
echo "📊 Or check in AWS Console:"
echo "https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks"
