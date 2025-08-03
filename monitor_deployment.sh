#!/bin/bash

STACK_NAME="f5-tts-models-upload"
REGION="us-east-1"

echo "🚀 Monitoring CloudFormation deployment for $STACK_NAME..."
echo "⏰ Started at: $(date)"
echo ""

# Function to get stack status
get_stack_status() {
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --output json 2>/dev/null | jq -r '.Stacks[0].StackStatus'
}

# Function to get recent events
get_recent_events() {
    aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION --max-items 5 --output json 2>/dev/null | jq -r '.StackEvents[] | "\(.Timestamp) \(.LogicalResourceId) \(.ResourceStatus) \(.ResourceStatusReason // "")"'
}

# Function to get instances
get_instances() {
    aws ec2 describe-instances --region $REGION --filters "Name=tag:aws:cloudformation:stack-name,Values=$STACK_NAME" --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,PublicIpAddress]' --output table 2>/dev/null
}

# Function to get load balancer
get_alb() {
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --output json 2>/dev/null | jq -r '.Stacks[0].Outputs[]? | select(.OutputKey=="LoadBalancerURL") | .OutputValue'
}

# Monitor loop
while true; do
    STATUS=$(get_stack_status)
    
    echo "📊 Current Status: $STATUS"
    echo ""
    
    case $STATUS in
        "CREATE_COMPLETE")
            echo "🎉 SUCCESS! Stack created successfully!"
            echo ""
            echo "🌐 Load Balancer URL:"
            get_alb
            echo ""
            echo "🖥️  Instances:"
            get_instances
            echo ""
            echo "✅ Deployment completed at: $(date)"
            exit 0
            ;;
        "CREATE_FAILED"|"ROLLBACK_IN_PROGRESS"|"ROLLBACK_COMPLETE")
            echo "❌ FAILED! Stack creation failed with status: $STATUS"
            echo ""
            echo "📋 Recent events:"
            get_recent_events
            exit 1
            ;;
        "CREATE_IN_PROGRESS")
            echo "⏳ Stack creation in progress..."
            echo ""
            echo "📋 Recent events:"
            get_recent_events
            echo ""
            echo "🖥️  Current instances:"
            get_instances
            echo ""
            echo "---"
            ;;
        *)
            echo "ℹ️  Unknown status: $STATUS"
            ;;
    esac
    
    echo "⏰ Next check in 60 seconds... ($(date))"
    echo ""
    sleep 60
done
