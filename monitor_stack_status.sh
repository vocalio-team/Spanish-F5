#!/bin/zsh

# Monitor CloudFormation stack status
STACK_NAME="f5-tts-spot-stack"
REGION="us-east-1"

echo "🔍 Monitoring CloudFormation stack: $STACK_NAME"
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
  STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
  
  if [[ $? -ne 0 ]]; then
    echo "❌ Stack not found or error occurred"
    break
  fi
  
  TIMESTAMP=$(date '+%H:%M:%S')
  echo "[$TIMESTAMP] Stack Status: $STATUS"
  
  if [[ "$STATUS" == "ROLLBACK_COMPLETE" ]]; then
    echo "✅ Rollback completed - ready to delete and recreate stack"
    break
  elif [[ "$STATUS" == "CREATE_COMPLETE" ]]; then
    echo "🎉 Stack creation completed successfully!"
    break
  elif [[ "$STATUS" == "CREATE_FAILED" ]] || [[ "$STATUS" == "ROLLBACK_FAILED" ]]; then
    echo "❌ Stack operation failed with status: $STATUS"
    break
  fi
  
  sleep 30
done
