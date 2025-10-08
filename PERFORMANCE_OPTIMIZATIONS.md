# Performance Optimizations for F5-TTS Spanish Model

## Overview
This document describes the performance optimizations implemented to improve GPU utilization and inference speed for the Spanish F5-TTS model.

## Implemented Optimizations

### 1. Mixed Precision Inference (FP16/BF16)
**Location:** `src/f5_tts/infer/utils_infer.py:139-152`

- Automatically selects optimal dtype based on GPU compute capability:
  - **Ampere+ GPUs (8.0+):** Uses `bfloat16` for better numerical stability
  - **Older GPUs (6.0+):** Uses `float16` for 2x memory bandwidth
  - **CPU/Legacy:** Falls back to `float32`

**Expected Speedup:** 2-3x faster inference, 50% less VRAM usage

**Trade-off:** Minimal quality impact (typically imperceptible)

### 2. Torch Compile (Kernel Fusion)
**Location:** `src/f5_tts/api.py:76-88`

- Uses PyTorch 2.0+ `torch.compile()` with `reduce-overhead` mode
- Fuses operations into optimized CUDA kernels
- Reduces kernel launch overhead

**Expected Speedup:** 10-30% additional performance improvement

**Control:** Set `ENABLE_TORCH_COMPILE=false` to disable

### 3. Automatic Mixed Precision (AMP)
**Location:** `src/f5_tts/infer/utils_infer.py:429-430`

- Wraps inference with `torch.amp.autocast()`
- Automatically casts operations to optimal precision
- Works in conjunction with FP16/BF16 models

**Expected Speedup:** Better GPU utilization, reduced memory transfers

### 4. CUDA Optimizations
**Location:** `f5_tts_api.py:108-121`

Applied optimizations:
- **cuDNN Benchmark Mode:** Selects fastest convolution algorithms
- **TF32 on Ampere+:** Faster matmul operations (19-bit precision)
- **High Precision Matmul:** Configurable via `TORCH_MATMUL_PRECISION`

**Expected Speedup:** 5-15% improvement on compatible hardware

### 5. Reduced CPU-GPU Transfers
**Location:** `src/f5_tts/infer/utils_infer.py:450-451`

- Keeps tensors on GPU longer during inference
- Only transfers final results to CPU
- Reduces PCIe bandwidth bottleneck

**Expected Speedup:** 5-10% improvement, especially for longer audio

## Environment Variables

Configure optimizations via environment variables:

```bash
# Enable/disable torch.compile (default: true)
ENABLE_TORCH_COMPILE=true

# Enable cuDNN benchmark mode (default: true)
ENABLE_CUDNN_BENCHMARK=true

# Matmul precision: "high" or "highest" (default: high)
TORCH_MATMUL_PRECISION=high
```

## Expected Performance Improvements

### Before Optimizations
- GPU Utilization: ~30%
- Inference Speed: Baseline

### After Optimizations
- GPU Utilization: 70-90% (expected)
- Inference Speed: 2.5-4x faster (combined effect)
- VRAM Usage: ~50% reduction

## Benchmarking

To benchmark performance improvements:

```bash
# Test inference with short text
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "gen_text": "Hola, esta es una prueba de rendimiento.",
    "ref_text": "",
    "nfe_step": 16
  }'
```

Monitor GPU usage with:
```bash
watch -n 0.5 nvidia-smi
```

## Troubleshooting

### Model compilation takes a long time on first run
- Expected behavior - torch.compile caches compiled kernels
- Subsequent runs will be much faster
- Warmup inference runs during startup to pre-compile

### Out of memory errors
- Reduce `nfe_step` (default: 16, try 12-14)
- Disable torch.compile: `ENABLE_TORCH_COMPILE=false`
- Consider using `torch.float16` instead of `bfloat16` for less VRAM

### Lower quality audio
- Increase `nfe_step` back to 32 for higher quality
- Use `cfg_strength=2.0` (default) for better conditioning

## API Changes

### New Request Parameter
- `use_fp16` (bool, default: true): Enable mixed precision inference

Example:
```json
{
  "gen_text": "Text to generate",
  "ref_text": "",
  "nfe_step": 16,
  "use_fp16": true
}
```

## Compatibility

- **PyTorch Version:** 2.0+ (for torch.compile)
- **CUDA Version:** 11.6+ (recommended 12.0+)
- **GPU Compute Capability:** 6.0+ (Pascal or newer)
  - Optimal: 8.0+ (Ampere: A100, RTX 30/40 series)

## References

- PyTorch Mixed Precision: https://pytorch.org/docs/stable/amp.html
- Torch Compile: https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html
- CUDA Optimization Guide: https://pytorch.org/docs/stable/notes/cuda.html
