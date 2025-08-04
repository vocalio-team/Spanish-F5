#!/bin/bash

STACK_NAME="f5-tts-debug"

echo "🔍 Deploying F5-TTS Debug Stack"
echo "Stack Name: $STACK_NAME"
echo ""

# Clean up any existing debug stack first
echo "🧹 Cleaning up existing debug stack..."
aws cloudformation delete-stack --stack-name "$STACK_NAME" 2>/dev/null
echo "Waiting for cleanup to complete..."
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" 2>/dev/null

echo "📋 Validating CloudFormation template..."
aws cloudformation validate-template --template-body file://cloudformation-simplified.yaml || {
    echo "❌ Template validation failed!"
    exit 1
}

echo "✅ Template validated successfully!"
echo ""

echo "🏗️  Creating debug CloudFormation stack..."
aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://cloudformation-simplified.yaml \
    --capabilities CAPABILITY_NAMED_IAM || {
    echo "❌ Stack creation failed!"
    exit 1
}

echo "✅ Debug stack creation initiated!"
echo ""
echo "🔍 Monitoring stack creation..."

# Wait for stack creation to complete
aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" && {
    echo "✅ Stack created successfully!"
    echo ""
    echo "📊 Stack outputs:"
    aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table
    echo ""
    echo "🔍 Get instance details with:"
    echo "aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs'"
} || {
    echo "❌ Stack creation failed!"
    echo ""
    echo "📊 Checking stack events for errors:"
    aws cloudformation describe-stack-events --stack-name "$STACK_NAME" --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' --output table
    exit 1
}
