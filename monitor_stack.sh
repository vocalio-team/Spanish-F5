#!/bin/bash

STACK_NAME="F5-TTS-SpotStack-v2"
REGION="us-east-1"

echo "Monitoring CloudFormation stack: $STACK_NAME"
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo "Error: Could not retrieve stack status"
        break
    fi
    
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] Stack Status: $STATUS"
    
    if [[ "$STATUS" == "CREATE_COMPLETE" ]]; then
        echo ""
        echo "🎉 Stack creation completed successfully!"
        echo ""
        echo "Getting outputs..."
        aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs' --output table
        break
    elif [[ "$STATUS" == "CREATE_FAILED" ]] || [[ "$STATUS" == "ROLLBACK_COMPLETE" ]] || [[ "$STATUS" == "ROLLBACK_FAILED" ]]; then
        echo ""
        echo "❌ Stack creation failed with status: $STATUS"
        echo ""
        echo "Recent events:"
        aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION --query 'StackEvents[0:5].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId,ResourceStatusReason]' --output table
        break
    fi
    
    sleep 30
done
