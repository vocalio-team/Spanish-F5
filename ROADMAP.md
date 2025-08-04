# F5-TTS AWS Deployment Roadmap

*Last Updated: August 4, 2025 - 00:54 UTC*

## 🎯 Current Status

### ✅ Completed Tasks
1. **Docker Image Built & Tagged**
   - F5-TTS API containerized with GPU support
   - Tagged as: `475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api:amd64`
   - Models (F5-TTS and E2-TTS) preload on container startup
   - Fixed device detection issues (GPU/CPU auto-detection)

2. **EFS Model Storage Setup**
   - EFS File System ID: `fs-00c1631283c0bd7e1`
   - F5-TTS and E2-TTS models uploaded to EFS (`/models/F5TTS_Base/`, `/models/E2TTS_Base/`)
   - Model files verified: `model_1200000.safetensors`, `vocab.txt`, `config.yaml`
   - Upload infrastructure stack deployed successfully

3. **CloudFormation Templates Created**
   - Production stack: `cloudformation.yaml` (Auto Scaling Group + ALB)
   - Debug stack: `cloudformation-simplified.yaml` (Single instance for testing)
   - EFS setup stack: `efs-setup.yaml` (Used for model upload)

4. **Debugging Tools Created**
   - `deploy_debug.sh` - Deploy simplified debug instance
   - `test_container_manual.sh` - Manual container testing on EC2
   - `monitor_deployment.sh` - Stack monitoring script

### ❌ Current Issues

1. **AWS CLI Connectivity Problems**
   - AWS commands returning empty outputs
   - Cannot verify current stack status or resource state
   - Credentials appear configured but not functioning

2. **Previous Deployment Failures**
   - Auto Scaling Group failures: "Received 1 FAILURE signal(s) out of 1"
   - Instances failing CloudFormation success signals
   - Container health check timeouts

3. **Root Cause Unknown**
   - EFS mounting issues?
   - Container startup problems with large models?
   - Resource constraints (16GB RAM might be insufficient)?
   - Security group / networking issues?

## 🛠️ Next Steps (Priority Order)

### Step 1: Restore AWS Connectivity
**Priority: HIGH**
```bash
# Test AWS connectivity
aws sts get-caller-identity
aws configure list
aws ec2 describe-regions --output table

# If needed, reconfigure credentials
aws configure
```

### Step 2: Verify EFS Status
**Priority: HIGH**
```bash
# Check if EFS still exists and has models
aws efs describe-file-systems --file-system-id fs-00c1631283c0bd7e1
aws efs describe-mount-targets --file-system-id fs-00c1631283c0bd7e1

# Check if upload instance still exists
aws cloudformation describe-stacks --stack-name f5-tts-models-upload
```

### Step 3: Deploy Debug Instance
**Priority: MEDIUM**
```bash
# Deploy single instance for debugging
./deploy_debug.sh

# Get instance IP and SSH in
aws cloudformation describe-stacks --stack-name f5-tts-debug --query 'Stacks[0].Outputs'
ssh -i ~/.ssh/f5-tts-debug-key.pem ubuntu@<INSTANCE_IP>
```

### Step 4: Manual Container Testing
**Priority: MEDIUM**
```bash
# On the debug instance, run comprehensive testing
sudo ./test_container_manual.sh

# Specific tests to run:
# - EFS mount and model file verification
# - Docker container startup with resource monitoring
# - API endpoint testing
# - Health check validation
```

### Step 5: Identify Root Cause
**Priority: HIGH**

Based on manual testing results, investigate:

#### A. Resource Constraints
- **Symptoms**: Container OOM killed, slow startup
- **Solution**: Upgrade to `g4dn.2xlarge` (32GB RAM)
- **Files to modify**: `cloudformation.yaml` line 7

#### B. EFS/Network Issues
- **Symptoms**: Mount failures, model files not accessible
- **Solution**: Fix security groups, verify mount targets
- **Check**: NFS port 2049 access, VPC routing

#### C. Container Health Check Issues
- **Symptoms**: Container runs but health endpoint fails
- **Solution**: Adjust health check timeouts, fix API startup
- **Files to modify**: `f5_tts_api.py`, container health check logic

#### D. CloudFormation Signal Issues
- **Symptoms**: Stack creation timeouts, signal failures
- **Solution**: Increase timeout periods, fix cfn-signal calls
- **Files to modify**: `cloudformation.yaml` lines 254-256, 221-223

### Step 6: Fix and Redeploy
**Priority: MEDIUM**

Based on root cause findings, apply fixes and redeploy:

```bash
# Clean up debug resources
aws cloudformation delete-stack --stack-name f5-tts-debug

# Apply fixes to production template
# Redeploy with fixed configuration
./deploy_f5_production.sh

# Monitor deployment
./monitor_deployment.sh
```

## 📁 Key Files Reference

### Configuration Files
- `cloudformation.yaml` - Production Auto Scaling Group deployment
- `cloudformation-simplified.yaml` - Debug single instance deployment
- `f5_tts_api.py` - FastAPI application with model loading
- `Dockerfile` - Container build configuration

### Deployment Scripts
- `deploy_f5_production.sh` - Deploy production stack
- `deploy_debug.sh` - Deploy debug instance
- `test_container_manual.sh` - Manual container testing
- `monitor_deployment.sh` - Deployment monitoring

### Model Information
- **EFS ID**: `fs-00c1631283c0bd7e1`
- **Models Path**: `/mnt/efs/models/`
- **F5-TTS**: `/mnt/efs/models/F5TTS_Base/model_1200000.safetensors`
- **E2-TTS**: `/mnt/efs/models/E2TTS_Base/model_1200000.safetensors`

### AWS Resources (if still exist)
- **ECR Repository**: `475302692635.dkr.ecr.us-east-1.amazonaws.com/f5-tts-api`
- **VPC**: `vpc-d29f88b7`
- **Subnets**: `subnet-cbc5a6e0` (us-east-1b), `subnet-1f507768` (us-east-1c)
- **Key Pair**: `f5-tts-debug-key`

## 🔍 Debugging Commands

### Quick Status Check
```bash
# AWS connectivity
aws sts get-caller-identity

# Stack status
aws cloudformation list-stacks --query 'StackSummaries[?contains(StackName, `f5-tts`)]' --output table

# Running instances
aws ec2 describe-instances --filters "Name=tag-key,Values=aws:cloudformation:stack-name" --query 'Reservations[].Instances[?State.Name==`running`].[InstanceId,PublicIpAddress,Tags[?Key==`aws:cloudformation:stack-name`].Value[0]]' --output table

# EFS status
aws efs describe-file-systems --file-system-id fs-00c1631283c0bd7e1
```

### Container Debugging (on EC2)
```bash
# Check container status
docker ps -a
docker logs f5-tts-api

# Test API manually
curl http://localhost:8000/health
curl http://localhost:8000/models

# Check resources
docker stats f5-tts-api
nvidia-smi
df -h /mnt/efs
```

## 📊 Success Criteria

### Minimal Success (Debug Phase)
- [ ] AWS CLI connectivity restored
- [ ] Debug instance deploys successfully
- [ ] EFS mounts with models accessible
- [ ] Container starts without errors
- [ ] Health endpoint returns 200 OK

### Full Success (Production)
- [ ] Auto Scaling Group creates instances successfully
- [ ] Load balancer health checks pass
- [ ] CloudFormation signals success
- [ ] API accessible via ALB DNS
- [ ] TTS generation works end-to-end

## ⚠️ Known Issues & Workarounds

1. **Large Model Memory Usage**
   - F5-TTS models use ~8GB+ RAM
   - May need g4dn.2xlarge (32GB) instead of g4dn.xlarge (16GB)

2. **EFS Mount Timing**
   - EFS mount can be slow on first access
   - Add retry logic and longer timeouts

3. **Container Startup Time**
   - Model loading takes 2-5 minutes
   - Health check grace period should be 10+ minutes

4. **CloudFormation Resource Conflicts**
   - Use versioned resource names (v8, v9, etc.)
   - Clean up failed stacks before redeploying

---

**Resume Point**: Start with Step 1 (AWS connectivity) and work through systematically. The debug instance approach should quickly reveal the root cause of deployment failures.
