# Audio Quality Analysis Guide

## Overview

The Audio Quality Analyzer helps you assess reference audio quality before using it for TTS. Poor quality reference audio leads to poor TTS output, so it's important to use high-quality recordings.

## Quick Start

### Check a Single File

```bash
python examples/check_audio_quality.py path/to/audio.wav
```

### Check All Files in a Directory

```bash
python examples/check_audio_quality.py --check-dir path/to/audio/folder/
```

### Python API

```python
from f5_tts.audio import analyze_audio_quality, print_quality_report

# Analyze audio file
metrics = analyze_audio_quality("reference.wav")

# Print formatted report
print_quality_report(metrics)

# Check programmatically
if metrics.quality_level.value in ['excellent', 'good']:
    print("Audio quality is acceptable")
else:
    print(f"Issues: {', '.join(metrics.issues)}")
    print(f"Recommendations: {', '.join(metrics.recommendations)}")
```

## Quality Metrics Explained

### Overall Score (0-100)

- **90-100 (Excellent)**: Professional quality, ideal for TTS
- **70-89 (Good)**: Very acceptable, minor issues at most
- **50-69 (Fair)**: Usable but may have noticeable artifacts
- **30-49 (Poor)**: Significant issues, output quality will suffer
- **0-29 (Unacceptable)**: Not suitable for TTS, re-record recommended

### Signal-to-Noise Ratio (SNR)

Measures how loud the speech is compared to background noise.

- **35+ dB**: Excellent - studio quality
- **25-35 dB**: Good - clean recording
- **15-25 dB**: Fair - noticeable background noise
- **10-15 dB**: Poor - significant noise
- **< 10 dB**: Unacceptable - very noisy

**Common Issues:**
- Background noise (fans, traffic, hum)
- Room reverberation
- Electronic noise

**Solutions:**
- Record in a quiet environment
- Use acoustic treatment (foam, blankets)
- Use noise reduction software
- Record closer to microphone

### Clipping Rate

Percentage of audio samples that are clipped (distorted).

- **< 0.1%**: Excellent - no perceptible clipping
- **0.1-1%**: Fair - minor clipping
- **1-5%**: Poor - noticeable distortion
- **> 5%**: Unacceptable - severe distortion

**Common Causes:**
- Recording level too high
- Microphone overload
- Compression artifacts

**Solutions:**
- Reduce input gain
- Move further from microphone
- Use a limiter/compressor
- Check for peaks and reduce them

### Silence Ratio

Percentage of the audio that is silence.

- **< 30%**: Excellent - efficient recording
- **30-50%**: Fair - some silence
- **50-70%**: Poor - too much silence
- **> 70%**: Unacceptable - mostly empty

**Common Causes:**
- Long pauses before/after speech
- Recording started too early/late
- Very slow speech with long pauses

**Solutions:**
- Trim silence from beginning/end
- Use voice activity detection (VAD)
- Re-record with better timing

### Dynamic Range

Difference between loudest and quietest parts (in dB).

- **40+ dB**: Excellent - natural, expressive
- **30-40 dB**: Good - some variation
- **20-30 dB**: Fair - somewhat flat
- **15-20 dB**: Poor - very compressed
- **< 15 dB**: Unacceptable - no dynamics

**Common Causes:**
- Over-compression
- Aggressive limiting
- Recording level too low
- Poor microphone technique

**Solutions:**
- Reduce compression/limiting
- Increase recording level
- Use better microphone technique
- Avoid automatic gain control (AGC)

### Spectral Flatness

Measure of how "noisy" vs "tonal" the audio is. Speech should be more tonal (low flatness).

- **< 0.1**: Excellent - clear harmonic structure
- **0.1-0.3**: Good - typical speech
- **0.3-0.5**: Fair - less clear
- **> 0.5**: Poor - may not be speech

**Common Causes:**
- Excessive noise
- Poor recording quality
- Wrong file (music, silence, etc.)
- Heavily processed audio

**Solutions:**
- Ensure file contains clear speech
- Reduce background noise
- Use better recording equipment

## Real-World Examples

### Example 1: Studio Quality Recording

```
============================================================
AUDIO QUALITY REPORT
============================================================

🟢 Overall Quality: EXCELLENT
   Score: 92.0/100

Detailed Metrics:
  • SNR: 56.8 dB
  • Clipping: 0.00%
  • Silence: 31.1%
  • Dynamic Range: 64.1 dB
  • Spectral Flatness: 0.224

============================================================
```

**Analysis:** Professional recording with excellent SNR, no clipping, good dynamic range. Perfect for TTS reference audio.

### Example 2: Home Recording with Issues

```
============================================================
AUDIO QUALITY REPORT
============================================================

🟡 Overall Quality: FAIR
   Score: 58.2/100

Detailed Metrics:
  • SNR: 18.3 dB
  • Clipping: 0.12%
  • Silence: 45.2%
  • Dynamic Range: 28.5 dB
  • Spectral Flatness: 0.385

⚠️  Issues Detected:
  • Low SNR (18.3 dB) - noticeable background noise
  • High silence ratio (45.2%)

💡 Recommendations:
  • Reduce background noise if possible
  • Consider trimming some silence
============================================================
```

**Analysis:** Usable but not ideal. Background noise and excess silence. Would benefit from noise reduction and trimming.

### Example 3: Poor Quality - Needs Re-recording

```
============================================================
AUDIO QUALITY REPORT
============================================================

🔴 Overall Quality: UNACCEPTABLE
   Score: 28.9/100

Detailed Metrics:
  • SNR: 8.5 dB
  • Clipping: 5.23%
  • Silence: 15.2%
  • Dynamic Range: 12.3 dB
  • Spectral Flatness: 0.612

⚠️  Issues Detected:
  • Very low SNR (8.5 dB) - noisy audio
  • Severe clipping (5.2%) - distorted audio
  • Very low dynamic range (12.3 dB)
  • High spectral flatness - may not be clear speech

💡 Recommendations:
  • ⚠️ Audio quality is too low for good TTS results
  • Record in a quieter environment or use noise reduction
  • Reduce recording volume to prevent clipping
  • Audio may be over-compressed or too quiet
  • Ensure audio contains clear, natural speech
  • Consider re-recording with better equipment or conditions
============================================================
```

**Analysis:** Not suitable for TTS. Multiple severe issues including very low SNR, significant clipping, and poor dynamic range. Re-recording strongly recommended.

## Best Practices for Recording

### Equipment

**Minimum:**
- Decent USB microphone (Blue Yeti, Audio-Technica ATR2020USB+)
- Quiet room
- Pop filter

**Recommended:**
- XLR condenser microphone
- Audio interface (Focusrite Scarlett, PreSonus AudioBox)
- Acoustic treatment
- Shock mount and pop filter

**Professional:**
- Large diaphragm condenser mic
- Professional interface
- Treated recording booth
- Professional monitoring

### Recording Environment

**Do:**
- ✅ Record in a quiet room
- ✅ Use soft furnishings to absorb reflections
- ✅ Turn off fans, AC, appliances
- ✅ Record during quiet times of day
- ✅ Close windows and doors
- ✅ Use acoustic treatment if available

**Don't:**
- ❌ Record near windows (traffic noise)
- ❌ Record in empty rooms (echo)
- ❌ Record near computers (fan noise)
- ❌ Record during peak hours
- ❌ Use automatic gain control (AGC)

### Recording Technique

**Optimal Settings:**
- Sample rate: 24 kHz or 48 kHz
- Bit depth: 24-bit
- Format: WAV or FLAC (lossless)
- Gain: Set so peaks are around -12 to -6 dB
- Distance: 6-12 inches from microphone

**During Recording:**
- Maintain consistent distance
- Speak naturally and clearly
- Avoid sudden movements
- Monitor levels to avoid clipping
- Take your time, pause between sentences
- Re-record mistakes immediately

**Post-Recording:**
- Trim silence from beginning/end
- Light noise reduction if needed (but be careful not to overdo it)
- Normalize to -3 dB peak
- Export as WAV or FLAC

## Troubleshooting Common Issues

### "Low SNR - noisy audio"

**Causes:**
- Background noise
- Electronic noise
- Room acoustics

**Solutions:**
1. Re-record in quieter environment
2. Apply noise reduction (RX, Audacity, etc.)
3. Use noise gate
4. Move closer to mic
5. Use directional microphone

### "Clipping detected"

**Causes:**
- Input gain too high
- Speaking too loudly/close
- Peaks not controlled

**Solutions:**
1. Reduce input gain
2. Increase distance from mic
3. Speak more consistently
4. Use pop filter
5. Apply gentle limiting before recording

### "High silence ratio"

**Causes:**
- Pauses before/after speech
- Slow speech with long pauses
- Recording gaps

**Solutions:**
1. Trim beginning and end
2. Use VAD to remove long pauses
3. Re-record more efficiently
4. Split into shorter segments

### "Low dynamic range"

**Causes:**
- Over-compression
- Aggressive limiting
- Too quiet recording

**Solutions:**
1. Reduce compression
2. Remove limiting
3. Increase recording level
4. Re-record with better gain staging

## Integration with TTS Workflow

### Pre-inference Check

```python
from f5_tts.api import F5TTS
from f5_tts.audio import analyze_audio_quality, QualityLevel

# Check reference audio quality
metrics = analyze_audio_quality("reference.wav")

if metrics.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]:
    print("⚠️ Warning: Reference audio quality is poor")
    print(f"Issues: {', '.join(metrics.issues)}")
    print("TTS output may be degraded. Consider using better quality reference audio.")

    # Optionally abort
    # raise ValueError("Reference audio quality too low")

# Proceed with TTS
tts = F5TTS()
wav, sr, _ = tts.infer(
    ref_file="reference.wav",
    ref_text="",
    gen_text="Hello world",
)
```

### Batch Processing

```python
from pathlib import Path
from f5_tts.audio import analyze_audio_quality, QualityLevel

def filter_quality_audio(audio_dir, min_score=70):
    """Filter audio files by quality score."""
    good_files = []
    poor_files = []

    for audio_file in Path(audio_dir).glob("*.wav"):
        metrics = analyze_audio_quality(str(audio_file))

        if metrics.overall_score >= min_score:
            good_files.append(str(audio_file))
        else:
            poor_files.append((str(audio_file), metrics.overall_score))

    return good_files, poor_files

# Usage
good, poor = filter_quality_audio("reference_audio/", min_score=70)

print(f"✅ {len(good)} files passed quality check")
print(f"❌ {len(poor)} files failed quality check")

if poor:
    print("\nFiles needing attention:")
    for file, score in poor:
        print(f"  • {Path(file).name}: {score:.1f}/100")
```

## API Reference

### `analyze_audio_quality(audio_path: str) -> QualityMetrics`

Analyze audio quality from file.

**Parameters:**
- `audio_path`: Path to audio file

**Returns:**
- `QualityMetrics` object with scores and recommendations

### `AudioQualityAnalyzer`

Main analyzer class.

```python
analyzer = AudioQualityAnalyzer(sample_rate=24000)
metrics = analyzer.analyze(audio_tensor, sample_rate)
```

### `QualityMetrics`

Results from analysis:

- `overall_score`: 0-100
- `quality_level`: QualityLevel enum
- `snr_db`: Signal-to-noise ratio
- `clipping_rate`: 0-1 (percentage of clipped samples)
- `silence_ratio`: 0-1 (percentage of silence)
- `dynamic_range_db`: Dynamic range in dB
- `spectral_flatness`: 0-1 (measure of tonality)
- `issues`: List of detected problems
- `recommendations`: List of suggested improvements

### `print_quality_report(metrics: QualityMetrics)`

Print formatted quality report to console.

## Conclusion

Audio quality analysis is a crucial first step in TTS workflows. By ensuring your reference audio meets quality standards, you'll get significantly better TTS output. Use the analyzer to:

1. **Pre-screen** reference audio before TTS
2. **Batch process** large audio collections
3. **Quality control** for recording sessions
4. **Troubleshoot** poor TTS output

Remember: **Garbage in, garbage out.** High-quality reference audio is essential for high-quality TTS results!
