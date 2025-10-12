# Performance Baseline Report

**Generated**: 2025-10-12
**Benchmark Script**: `benchmark_quick.py`
**Model**: Spanish-F5 TTS (model_1250000.safetensors)
**Environment**: CPU-only (PyTorch 2.8.0+cpu)

---

## Executive Summary

This baseline establishes the current performance and quality metrics for Spanish-F5 TTS system. These metrics serve as the reference point for measuring improvements and detecting regressions during optimization work.

### Key Findings

✅ **Audio Quality**: Excellent (96.3/100, 73.2dB SNR)
⚠️ **Performance**: CPU-only latency is high (9-17s per sentence)
✅ **Prosody Detection**: Working correctly (100% question/exclamation detection)
⚠️ **Regional Processing**: Prosodic profile applied, but slang/phonetics not detected in test

---

## System Information

| Metric | Value |
|--------|-------|
| Device | CPU (no CUDA) |
| PyTorch Version | 2.8.0+cpu |
| Model Size | ~1.25M steps |
| Vocoder | Vocos (charactr/vocos-mel-24khz) |
| Model Load Time | 2.73s |

**Note**: This baseline was captured on CPU. GPU performance is expected to be significantly better (5-10x faster).

---

## Performance Metrics

### Latency Benchmarks (CPU)

| Text Type | Length (chars) | Latency (seconds) | Real-time Factor* |
|-----------|----------------|-------------------|-------------------|
| Very Short | 4 | 16.50s | ~5-6x slower |
| Short | 16 | 9.33s | ~3-4x slower |
| Medium | 44 | 11.11s | ~2-3x slower |

**Real-time Factor**: Estimated based on audio duration vs generation time.

### Observations

1. **Very short text has high overhead**: "Hola" (4 chars) takes 16.5s due to:
   - Reference audio transcription (~7-8s)
   - Model initialization overhead
   - Short text adjustments (fix_duration=12.0s)

2. **Medium text is more efficient**: 44-char sentence takes 11.11s, showing better amortization of fixed costs.

3. **CPU is bottleneck**: All tests run on CPU with warnings about CUDA unavailability. GPU would drastically improve these numbers.

---

## Quality Metrics

### Audio Quality Analysis

| Metric | Value | Level | Notes |
|--------|-------|-------|-------|
| **Overall Score** | 96.3/100 | Excellent | High-quality output |
| **SNR (dB)** | 73.2 | Excellent | Very clean audio |
| **Clipping Rate** | 0.0% | Perfect | No audio clipping |
| **Dynamic Range** | 105.7dB | Excellent | Good audio dynamics |
| **Spectral Flatness** | 0.195 | Good | Natural tonal quality |

**Interpretation**: The TTS system produces excellent audio quality with very high SNR and no clipping. The spectral flatness indicates natural-sounding speech with good tonal variation.

### Prosody Detection

| Test Type | Markers Detected | Status |
|-----------|------------------|--------|
| Question ("¿Cómo estás hoy?") | 1 | ✅ Pass |
| Exclamation ("¡Qué hermoso día!") | 1 | ✅ Pass |

**Status**: Prosody detection is working correctly for questions and exclamations.

### Regional Processing (Rioplatense)

| Metric | Value | Status |
|--------|-------|--------|
| Slang Terms Detected | 0 | ⚠️ Unexpected |
| Phonetic Transformations | 0 | ⚠️ Unexpected |
| Prosodic Profile Applied | Yes | ✅ Pass |

**Test Input**: "Che boludo, ¿vos querés tomar unos mates?"
**Expected**: Detection of "che", "boludo", "vos", "querés"

**Issue**: The slang/phonetic detection returned 0 hits despite clear regional markers in the test text. However, the prosodic profile was correctly applied. This suggests the benchmark script may need adjustment or the `process_spanish_text()` function may not be returning slang_terms in the expected format.

---

## Performance Bottlenecks Identified

### Primary Bottlenecks

1. **CPU Inference** (Critical)
   - All inference runs on CPU
   - Expected 5-10x speedup with CUDA
   - Priority: Deploy to GPU for realistic metrics

2. **Reference Audio Transcription** (High)
   - Whisper model download and transcription adds 7-8s overhead
   - Occurs on first inference or when ref_text is empty
   - Opportunity: Pre-transcribe reference audio or provide ref_text

3. **Model Compilation Overhead** (Medium)
   - torch.compile() adds initialization time
   - Benefits realized after warmup
   - Current: Enabled by default

### Secondary Bottlenecks

4. **Text Preprocessing** (Low-Medium)
   - Multiple passes over text (normalization, prosody, regional processing)
   - Opportunity: Single-pass processing

5. **Audio Postprocessing** (Low)
   - Crossfading and audio cleanup
   - Already optimized, but could vectorize further

---

## Quality Improvement Opportunities

### Prosody Enhancements

1. **Stress detection**: Could add more sophisticated stress pattern detection
2. **Discourse-level prosody**: Apply declination units for multi-sentence texts
3. **Emotion modeling**: Add sentiment-aware prosodic adjustments

### Regional Accuracy

1. **Debug slang detection**: Investigate why test returned 0 slang terms
2. **Strengthen phonetic transforms**: Ensure sheísmo, yeísmo applied audibly
3. **Add more regional profiles**: Currently have 3-4, could expand to 10+

### Audio Quality

1. **Vocoder upgrade**: Consider BigVGAN or HiFi-GAN++ for even higher quality
2. **Noise reduction**: Post-processing cleanup (already very clean at 73.2dB)
3. **Crossfading refinement**: Already using equal-power, minimal improvement needed

---

## Regression Test Thresholds

Use these thresholds to detect regressions during optimization:

| Metric | Baseline | Acceptable Range | Regression Alert |
|--------|----------|------------------|------------------|
| **Audio Quality Score** | 96.3 | > 94.0 | < 94.0 |
| **SNR (dB)** | 73.2 | > 70.0 | < 70.0 |
| **Clipping Rate** | 0.0% | < 0.1% | > 0.1% |
| **Prosody Detection** | 100% | > 95% | < 95% |
| **Latency (medium text)** | 11.11s | < 12.0s (CPU) | > 12.0s (CPU) |

**Note**: Latency thresholds will be re-evaluated once GPU baseline is established.

---

## Next Steps (Phase 2: Low-Risk Optimizations)

Based on this baseline, the recommended optimization priorities are:

### Immediate Actions

1. **Establish GPU Baseline** (Critical)
   - Deploy to CUDA-enabled environment
   - Re-run benchmark with GPU
   - Update this document with GPU metrics

2. **Debug Regional Processing** (High)
   - Investigate why slang_detected=0 in baseline
   - Verify `process_spanish_text()` return format
   - Update test or fix detection logic

### Priority 1 Optimizations (Low-Risk)

3. **Text Processing Optimization**
   - Single-pass text analysis
   - Expected: 20-30% reduction in preprocessing time
   - Risk: Low (pure refactoring)

4. **Reference Audio Pre-transcription**
   - Pre-transcribe default ref_audio/short.wav
   - Store transcription in metadata or config
   - Expected: 7-8s reduction in first-inference overhead

5. **Adaptive NFE Tuning**
   - Test NFE steps: 12, 14, 16, 18, 20
   - Find optimal quality-speed tradeoff
   - Current: 16 steps (good balance)

### Priority 2 Optimizations (Medium-Risk)

6. **Model Quantization** (after GPU baseline)
   - Test FP16 and INT8 quantization
   - Expected: 30-50% speedup, 50% memory reduction
   - Risk: Potential quality degradation (test thoroughly)

7. **Batch Processing**
   - Implement batched inference for multi-sentence
   - Expected: 2-3x throughput improvement

---

## Benchmark Reproducibility

### Running the Baseline Benchmark

```bash
# Quick baseline (used for this report)
python benchmark_quick.py --output baseline_quick.json

# Full performance benchmark (comprehensive, CPU may timeout)
python benchmark_performance.py --output performance_baseline.json

# Full quality benchmark (comprehensive)
python benchmark_quality.py --output quality_baseline.json
```

### System Requirements

- Python 3.10+
- PyTorch 2.8.0+ (CPU or CUDA)
- Spanish-F5 TTS model (models/Spanish/model_1250000.safetensors)
- Reference audio (ref_audio/short.wav)

### Expected Runtime

- Quick baseline: ~1-2 minutes (CPU), ~30s (GPU)
- Full performance: ~10-15 minutes (CPU), ~2-3 minutes (GPU)
- Full quality: ~15-20 minutes (CPU), ~3-5 minutes (GPU)

---

## Changelog

- **2025-10-12**: Initial baseline established (CPU-only)
  - Audio quality: 96.3/100 (73.2dB SNR)
  - Latency: 9-17s per sentence (CPU)
  - Prosody detection: 100% accurate
  - Regional processing: Needs investigation

---

## Appendix: Raw Benchmark Data

Complete benchmark results are available in:
- [baseline_quick.json](./baseline_quick.json) - Quick baseline data
- [performance_baseline.json](./performance_baseline.json) - Full performance data (if available)
- [quality_baseline.json](./quality_baseline.json) - Full quality data (if available)

**Benchmark Script Version**: benchmark_quick.py (v1.0)
**Analysis Date**: 2025-10-12
**Analyst**: Claude Code (Automated)
