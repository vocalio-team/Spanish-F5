#!/bin/bash

# Script to upload F5-TTS models to EFS
# Usage: ./upload_models_to_efs.sh <EFS_FILE_SYSTEM_ID>

set -e

EFS_ID="$1"
REGION="us-east-1"
MOUNT_POINT="/tmp/efs_mount"

if [ -z "$EFS_ID" ]; then
    echo "Usage: $0 <EFS_FILE_SYSTEM_ID>"
    echo "Example: $0 fs-0abcd1234efgh5678"
    exit 1
fi

echo "🚀 Uploading F5-TTS models to EFS: $EFS_ID"
echo "⏰ Started at: $(date)"

# Check if models directory exists
if [ ! -d "models" ]; then
    echo "❌ ERROR: models directory not found. Make sure you're running this from the Spanish-F5 directory."
    exit 1
fi

# Install required packages
echo "📦 Installing required packages..."
sudo apt update -y || echo "WARNING: apt update failed"
sudo apt install -y nfs-common || echo "WARNING: nfs-common install failed"

# Create mount point
echo "📁 Creating mount point..."
sudo mkdir -p "$MOUNT_POINT"

# Mount EFS
echo "🔗 Mounting EFS file system..."
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,intr,timeo=600,retrans=2 \
    "${EFS_ID}.efs.${REGION}.amazonaws.com:/" "$MOUNT_POINT"

# Create models directory structure in EFS
echo "📂 Creating directory structure..."
sudo mkdir -p "$MOUNT_POINT/models"
sudo mkdir -p "$MOUNT_POINT/models/F5TTS_Base"
sudo mkdir -p "$MOUNT_POINT/models/E2TTS_Base"

# Copy F5TTS models
if [ -d "models/F5TTS_Base" ]; then
    echo "📋 Copying F5TTS_Base models..."
    sudo cp -r models/F5TTS_Base/* "$MOUNT_POINT/models/F5TTS_Base/"
    echo "✅ F5TTS_Base models copied successfully"
else
    echo "⚠️  WARNING: models/F5TTS_Base directory not found"
fi

# Copy E2TTS models
if [ -d "models/E2TTS_Base" ]; then
    echo "📋 Copying E2TTS_Base models..."
    sudo cp -r models/E2TTS_Base/* "$MOUNT_POINT/models/E2TTS_Base/"
    echo "✅ E2TTS_Base models copied successfully"
else
    echo "⚠️  WARNING: models/E2TTS_Base directory not found"
fi

# Set permissions
echo "🔐 Setting permissions..."
sudo chmod -R 755 "$MOUNT_POINT/models"

# Show what was uploaded
echo "📊 EFS contents:"
sudo find "$MOUNT_POINT/models" -type f -exec ls -lh {} \; | head -20

# Calculate total size
echo "💾 Total size of uploaded models:"
sudo du -sh "$MOUNT_POINT/models"

# Unmount
echo "🔌 Unmounting EFS..."
sudo umount "$MOUNT_POINT"
sudo rmdir "$MOUNT_POINT"

echo "🎉 Models uploaded successfully to EFS: $EFS_ID"
echo "✅ Completed at: $(date)"
