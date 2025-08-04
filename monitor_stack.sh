#!/bin/bash

STACK_NAME="f5-tts-spot-stack"
REGION="us-east-1"

echo "🔍 Monitoring CloudFormation stack: $STACK_NAME"
echo "=================================="

while true; do
    # Get current stack status
    STATUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$STATUS" ]; then
        echo "❌ Stack not found or error occurred"
        break
    fi
    
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] Stack Status: $STATUS"
    
    # Check if stack creation is complete
    case "$STATUS" in
        "CREATE_COMPLETE")
            echo "✅ Stack creation completed successfully!"
            # Get Load Balancer DNS
            ALB_DNS=$(aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --region "$REGION" \
                --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
                --output text)
            echo "🌐 Load Balancer DNS: $ALB_DNS"
            break
            ;;
        "CREATE_FAILED"|"ROLLBACK_COMPLETE"|"ROLLBACK_FAILED")
            echo "❌ Stack creation failed with status: $STATUS"
            echo "📋 Recent events:"
            aws cloudformation describe-stack-events \
                --stack-name "$STACK_NAME" \
                --region "$REGION" \
                --query 'StackEvents[0:3].[Timestamp,ResourceStatus,ResourceType,ResourceStatusReason]' \
                --output table
            break
            ;;
        "ROLLBACK_IN_PROGRESS")
            echo "⚠️  Stack is rolling back due to failure"
            ;;
        "CREATE_IN_PROGRESS")
            echo "⏳ Stack creation in progress..."
            ;;
    esac
    
    # Wait before next check
    sleep 30
done

echo "🔚 Monitoring completed"
