#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

STACK_NAME="gpu-spot-stack"
REGION="us-east-1"
CLUSTER_NAME="dev-vocalio-chatterbox"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GPU SPOT Deployment${NC}"
echo -e "${GREEN}Instance: g4dn.xlarge SPOT${NC}"
echo -e "${GREEN}Cost: ~\$0.15-0.25/hour (~\$110-180/month)${NC}"
echo -e "${GREEN}Savings: 60-70% vs On-Demand!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Deploy stack
echo -e "${YELLOW}Step 1: Deploying CloudFormation stack with SPOT instances...${NC}"
aws cloudformation deploy \
  --template-file ecs-gpu-spot.yaml \
  --stack-name $STACK_NAME \
  --region $REGION \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ClusterName=$CLUSTER_NAME

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Stack deployed successfully${NC}"
else
  echo -e "${RED}✗ Stack deployment failed${NC}"
  exit 1
fi

# Get outputs
echo ""
echo -e "${YELLOW}Step 2: Getting stack outputs...${NC}"
CAPACITY_PROVIDER=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs[?OutputKey=='CapacityProviderName'].OutputValue" \
  --output text)

ALB_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs[?OutputKey=='ALBURL'].OutputValue" \
  --output text)

TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs[?OutputKey=='TargetGroupArn'].OutputValue" \
  --output text)

SECURITY_GROUP_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query "Stacks[0].Outputs[?OutputKey=='SecurityGroupId'].OutputValue" \
  --output text)

echo -e "${GREEN}✓ Capacity Provider: $CAPACITY_PROVIDER${NC}"
echo -e "${GREEN}✓ ALB URL: $ALB_URL${NC}"

# Attach capacity provider
echo ""
echo -e "${YELLOW}Step 3: Attaching capacity provider to cluster...${NC}"
aws ecs put-cluster-capacity-providers \
  --cluster $CLUSTER_NAME \
  --capacity-providers $CAPACITY_PROVIDER FARGATE \
  --default-capacity-provider-strategy \
    capacityProvider=$CAPACITY_PROVIDER,weight=1,base=0 \
  --region $REGION 2>/dev/null || echo -e "${YELLOW}Capacity provider may already be attached${NC}"

# Wait for instance
echo ""
echo -e "${YELLOW}Step 4: Waiting for SPOT instance to register...${NC}"
for i in {1..20}; do
  INSTANCE_COUNT=$(aws ecs describe-clusters \
    --clusters $CLUSTER_NAME \
    --region $REGION \
    --query "clusters[0].registeredContainerInstancesCount" \
    --output text)

  if [ "$INSTANCE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ $INSTANCE_COUNT instance(s) registered${NC}"
    break
  fi

  echo -e "Waiting... ($i/20)"
  sleep 15
done

# Create service
echo ""
echo -e "${YELLOW}Step 5: Creating F5-TTS ECS service...${NC}"

SUBNET_IDS="subnet-cbc5a6e0,subnet-1f507768"

aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name f5-tts-spot-service \
  --task-definition dev-f5-tts:1 \
  --desired-count 1 \
  --capacity-provider-strategy capacityProvider=$CAPACITY_PROVIDER,weight=1,base=0 \
  --load-balancers targetGroupArn=$TARGET_GROUP_ARN,containerName=dev-f5-tts,containerPort=8000 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
  --health-check-grace-period-seconds 300 \
  --region $REGION 2>/dev/null || echo -e "${YELLOW}Service may already exist${NC}"

echo -e "${GREEN}✓ Service created/updated${NC}"

# Wait for service
echo ""
echo -e "${YELLOW}Step 6: Waiting for service to stabilize...${NC}"
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services f5-tts-spot-service \
  --region $REGION

# Test
echo ""
echo -e "${YELLOW}Step 7: Testing endpoint...${NC}"
sleep 30

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $ALB_URL/health || echo "000")

if [ "$HTTP_CODE" -eq 200 ]; then
  echo -e "${GREEN}✓ API is live! (HTTP $HTTP_CODE)${NC}"
else
  echo -e "${YELLOW}⚠ API not ready yet (HTTP $HTTP_CODE)${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SPOT Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "F5-TTS API: ${GREEN}$ALB_URL${NC}"
echo -e "Instance Type: ${GREEN}g4dn.xlarge SPOT${NC}"
echo -e "Cost: ${GREEN}~\$0.15-0.25/hour (~\$110-180/month)${NC}"
echo -e "Savings: ${GREEN}60-70% vs On-Demand!${NC}"
echo ""
