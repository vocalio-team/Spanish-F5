#!/bin/bash
set -e

# Download models from S3 if not already present
MODEL_DIR="/app/models/Spanish"
S3_BUCKET="vocalio-chatterbox-models-1758401711"
S3_PREFIX="Spanish/"

if [ ! -f "$MODEL_DIR/model_1250000.safetensors" ]; then
    echo "Downloading F5-TTS models from S3..."
    mkdir -p "$MODEL_DIR"

    # Use Python + boto3 to download (lighter than AWS CLI)
    python3 << 'PYTHON_SCRIPT'
import boto3
import os

s3 = boto3.client('s3')
bucket = 'vocalio-chatterbox-models-1758401711'
prefix = 'Spanish/'
local_dir = '/app/models/Spanish'

# List and download all files
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
    for obj in page.get('Contents', []):
        key = obj['Key']
        local_path = os.path.join(local_dir, os.path.basename(key))
        print(f"Downloading {key}...")
        s3.download_file(bucket, key, local_path)

print("✓ Models downloaded successfully")
PYTHON_SCRIPT

    ls -lh "$MODEL_DIR"
else
    echo "✓ Models already present, skipping download"
fi

# Download Vocos model from S3 if not already present
VOCOS_DIR="/app/.cache/huggingface/hub/models--charactr--vocos-mel-24khz/snapshots/0feb3fdd929bcd6649e0e7c5a688cf7dd012ef21"
if [ ! -f "$VOCOS_DIR/pytorch_model.bin" ]; then
    echo "Downloading Vocos model from S3..."
    mkdir -p "$VOCOS_DIR"

    # Use Python + boto3 to download Vocos
    python3 << 'PYTHON_SCRIPT'
import boto3
import os

s3 = boto3.client('s3')
bucket = 'vocalio-chatterbox-models-1758401711'
prefix = 'vocos-mel-24khz/'
local_dir = '/app/.cache/huggingface/hub/models--charactr--vocos-mel-24khz/snapshots/0feb3fdd929bcd6649e0e7c5a688cf7dd012ef21'

files = ['pytorch_model.bin', 'config.yaml', 'README.md']
for file in files:
    key = prefix + file
    local_path = os.path.join(local_dir, file)
    print(f"Downloading {key}...")
    s3.download_file(bucket, key, local_path)

print("✓ Vocos model downloaded successfully")
PYTHON_SCRIPT

    ls -lh "$VOCOS_DIR"
else
    echo "✓ Vocos model already present, skipping download"
fi

# Execute the main command
exec "$@"
