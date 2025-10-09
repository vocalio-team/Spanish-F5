# Audio Compression for Low-Bandwidth Environments

## Overview

The F5-TTS API now supports **audio compression** to dramatically reduce bandwidth usage. This is essential for deployment in areas with poor network coverage where bandwidth comes at a premium.

### Bandwidth Savings

| Format | Bitrate | Size/Second | Bandwidth Saved | Use Case |
|--------|---------|-------------|-----------------|----------|
| **OPUS** (default) | 32 kbps | ~4 KB/s | **92%** ✨ | Poor coverage, mobile data |
| **MP3** | 64 kbps | ~8 KB/s | **83%** | Good compatibility |
| **WAV** | 384 kbps | ~48 KB/s | 0% (baseline) | High bandwidth available |

**Example**: A 10-second audio response:
- WAV: ~480 KB
- OPUS: **~40 KB** (12x smaller!)
- Savings: **440 KB per request**

## Quick Start

### Default Compression (OPUS)

The API now returns **OPUS-compressed audio by default** (32kbps):

```python
import requests

response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": ""
    # output_format defaults to "opus"
})

# Save compressed audio
with open("output.ogg", "wb") as f:
    f.write(response.content)
```

### Choosing Format

Specify format explicitly:

```python
# OPUS (best for low bandwidth)
response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "opus"  # 32kbps, ~4KB/s
})

# MP3 (good compatibility)
response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "mp3"  # 64kbps, ~8KB/s
})

# WAV (uncompressed, maximum quality)
response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "wav"  # ~48KB/s
})
```

### Custom Bitrate

Override default bitrate for fine-tuned control:

```python
# Ultra-low bandwidth (16kbps) - acceptable for voice
response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "opus",
    "output_bitrate": "16k"  # Half the default, ~2KB/s
})

# Higher quality (64kbps)
response = requests.post("http://localhost:8000/tts", json={
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "opus",
    "output_bitrate": "64k"  # Better quality, ~8KB/s
})
```

## Supported Formats

### OPUS (Recommended for Low Bandwidth)

**Default: 32 kbps | MIME: `audio/ogg; codecs=opus`**

- ✅ **Best quality-to-size ratio** for voice
- ✅ **Variable bitrate** automatically adjusts quality
- ✅ **Lowest latency** - optimized for real-time
- ✅ **Excellent voice clarity** even at low bitrates
- 📦 **File extension**: `.ogg`

**When to use**: Poor network coverage, mobile data constraints, real-time streaming

### MP3

**Default: 64 kbps | MIME: `audio/mpeg`**

- ✅ **Universal compatibility** - plays everywhere
- ✅ **Good voice quality** at 64kbps
- ✅ **Predictable file sizes**
- 📦 **File extension**: `.mp3`

**When to use**: Need broad compatibility, moderate bandwidth savings

### WAV

**Uncompressed | MIME: `audio/wav`**

- ✅ **Maximum quality** - no compression artifacts
- ❌ **High bandwidth** - 12x larger than OPUS
- 📦 **File extension**: `.wav`

**When to use**: High bandwidth available, archival, further processing

## API Endpoints

### GET /tts/formats

List available compression formats and recommendations:

```bash
curl http://localhost:8000/tts/formats
```

Response:
```json
{
  "formats": {
    "opus": {
      "mime_type": "audio/ogg; codecs=opus",
      "description": "OPUS codec in OGG container (best for voice, lowest bandwidth)"
    },
    "mp3": {
      "mime_type": "audio/mpeg",
      "description": "MP3 format (good compatibility)"
    },
    "wav": {
      "mime_type": "audio/wav",
      "description": "Uncompressed WAV (highest bandwidth)"
    }
  },
  "default": "opus",
  "recommendation": "Use 'opus' for lowest bandwidth (best for poor network coverage)",
  "bandwidth_comparison": {
    "opus_32k": "~4 KB/s (32kbps) - Excellent voice quality, minimal bandwidth",
    "mp3_64k": "~8 KB/s (64kbps) - Good voice quality, moderate bandwidth",
    "wav": "~48 KB/s - Uncompressed, maximum bandwidth"
  }
}
```

### POST /tts (with compression)

Generate compressed TTS audio:

```bash
# OPUS compression
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "opus"
  }' \
  --output output.ogg

# MP3 compression
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "mp3",
    "output_bitrate": "96k"
  }' \
  --output output.mp3
```

### POST /tts/stream (with compression)

Stream compressed audio:

```bash
curl -X POST http://localhost:8000/tts/stream \
  -H "Content-Type": application/json" \
  -d '{
    "gen_text": "Hola, ¿cómo estás?",
    "ref_text": "",
    "output_format": "opus"
  }' \
  --output stream.ogg
```

## Performance Characteristics

### Compression Speed

Compression adds **minimal latency** (~50-100ms for 10s audio):

| Format | Compression Time (10s audio) |
|--------|------------------------------|
| OPUS | ~80ms |
| MP3 | ~60ms |
| WAV | 0ms (no compression) |

### Quality vs. Bitrate (OPUS)

| Bitrate | Quality | Use Case |
|---------|---------|----------|
| 16 kbps | Acceptable | Ultra-low bandwidth |
| **32 kbps** | **Excellent** (default) | **Low bandwidth** ✨ |
| 48 kbps | Very Good | Balanced |
| 64 kbps | Excellent | High quality preference |

### File Size Examples

10-second Spanish TTS output:

| Format | Bitrate | File Size | vs WAV |
|--------|---------|-----------|--------|
| OPUS | 16k | ~20 KB | -96% |
| **OPUS** | **32k** | **~40 KB** | **-92%** ✨ |
| OPUS | 64k | ~80 KB | -83% |
| MP3 | 64k | ~80 KB | -83% |
| MP3 | 128k | ~160 KB | -67% |
| WAV | N/A | ~480 KB | baseline |

## Integration Examples

### Python Client

```python
import requests
from pathlib import Path

def generate_tts(text: str, output_format: str = "opus", bitrate: str = None) -> bytes:
    """Generate TTS with compression."""
    response = requests.post(
        "http://localhost:8000/tts",
        json={
            "gen_text": text,
            "ref_text": "",
            "output_format": output_format,
            "output_bitrate": bitrate
        }
    )
    response.raise_for_status()
    return response.content

# Generate compressed audio
audio_data = generate_tts("Hola, ¿cómo estás?", output_format="opus")
Path("output.ogg").write_bytes(audio_data)

# Ultra-low bandwidth
audio_data = generate_tts(
    "Mensaje importante para áreas remotas",
    output_format="opus",
    bitrate="16k"
)
Path("low_bandwidth.ogg").write_bytes(audio_data)
```

### JavaScript/TypeScript

```typescript
async function generateTTS(text: string, format: string = 'opus'): Promise<Blob> {
  const response = await fetch('http://localhost:8000/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      gen_text: text,
      ref_text: '',
      output_format: format
    })
  });

  if (!response.ok) {
    throw new Error(`TTS failed: ${response.statusText}`);
  }

  return await response.blob();
}

// Use in web app
const audioBlob = await generateTTS('Hola, ¿cómo estás?', 'opus');
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
await audio.play();
```

### Mobile App (React Native)

```javascript
import RNFS from 'react-native-fs';
import Sound from 'react-native-sound';

async function generateAndPlayTTS(text) {
  // Request compressed audio (saves mobile data)
  const response = await fetch('http://api.example.com:8000/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      gen_text: text,
      ref_text: '',
      output_format: 'opus',  // Minimal data usage
      output_bitrate: '16k'   // Even lower for 3G/2G
    })
  });

  const audioData = await response.blob();
  const path = `${RNFS.DocumentDirectoryPath}/tts_${Date.now()}.ogg`;

  // Save and play
  await RNFS.writeFile(path, audioData, 'base64');
  const sound = new Sound(path, '', (error) => {
    if (!error) sound.play();
  });
}
```

## Bandwidth Calculator

Estimate bandwidth requirements:

```python
from f5_tts.rest_api.audio_compression import audio_compressor

# Estimate 30-second audio in different formats
duration = 30.0

opus_size = audio_compressor.estimate_size(duration, "opus")
mp3_size = audio_compressor.estimate_size(duration, "mp3")
wav_size = audio_compressor.estimate_size(duration, "wav")

print(f"30s audio sizes:")
print(f"OPUS 32k: {opus_size / 1024:.1f} KB")  # ~120 KB
print(f"MP3 64k: {mp3_size / 1024:.1f} KB")     # ~240 KB
print(f"WAV: {wav_size / 1024:.1f} KB")         # ~1440 KB
```

## Best Practices

### 1. Choose Format Based on Network

```python
def get_optimal_format(network_type: str) -> dict:
    """Select format based on network conditions."""
    formats = {
        '2g': {'format': 'opus', 'bitrate': '16k'},  # Ultra-low
        '3g': {'format': 'opus', 'bitrate': '24k'},  # Low
        '4g': {'format': 'opus', 'bitrate': '32k'},  # Default
        '5g': {'format': 'mp3', 'bitrate': '64k'},   # Balanced
        'wifi': {'format': 'mp3', 'bitrate': '128k'} # High quality
    }
    return formats.get(network_type, formats['4g'])

# Use in app
network = detect_network_type()  # Your network detection
config = get_optimal_format(network)
audio = generate_tts(text, **config)
```

### 2. Progressive Enhancement

```python
# Try high quality first, fallback to compressed
try:
    audio = generate_tts(text, output_format='mp3', bitrate='128k')
except Exception:
    # Network issue, use minimal bandwidth
    audio = generate_tts(text, output_format='opus', bitrate='16k')
```

### 3. Caching

```python
import hashlib
from pathlib import Path

def get_cached_tts(text: str, format: str = 'opus') -> bytes:
    """Cache compressed audio to avoid re-generation."""
    cache_key = hashlib.md5(f"{text}:{format}".encode()).hexdigest()
    cache_path = Path(f"cache/{cache_key}.{format_ext[format]}")

    if cache_path.exists():
        return cache_path.read_bytes()

    # Generate and cache
    audio = generate_tts(text, output_format=format)
    cache_path.parent.mkdir(exist_ok=True)
    cache_path.write_bytes(audio)
    return audio
```

## Deployment Considerations

### CDN Integration

Serve compressed audio through CDN:

```python
# Generate and upload to CDN
audio = generate_tts(text, output_format='opus')
cdn_url = upload_to_cdn(audio, f"{text_hash}.ogg")

# Client downloads from CDN (cached, compressed)
return {"audio_url": cdn_url, "format": "opus"}
```

### Load Balancing

Compression is CPU-light (~50ms), safe for high concurrency:

```yaml
# docker-compose.yml
services:
  tts-api:
    image: spanish-f5-tts
    deploy:
      replicas: 4
    environment:
      - DEFAULT_OUTPUT_FORMAT=opus  # Set default
```

## Troubleshooting

### Audio Not Playing

**Problem**: OPUS/OGG not playing in browser

**Solution**: Check browser support or use MP3 fallback:

```javascript
const audio = new Audio();
if (audio.canPlayType('audio/ogg; codecs=opus')) {
  generateTTS(text, 'opus');
} else {
  generateTTS(text, 'mp3');  // Fallback
}
```

### Quality Issues

**Problem**: Audio quality degraded

**Solution**: Increase bitrate:

```python
# From 32k to 48k for better quality
audio = generate_tts(text, output_format='opus', output_bitrate='48k')
```

### Large File Sizes

**Problem**: Files still too large

**Solution**: Use lower bitrate:

```python
# Ultra-low bandwidth (acceptable for voice)
audio = generate_tts(text, output_format='opus', output_bitrate='16k')
```

## Summary

- **Default**: OPUS @ 32kbps (**92% bandwidth savings**)
- **Ultra-low**: OPUS @ 16kbps (**96% savings**)
- **Compatibility**: MP3 @ 64kbps (**83% savings**)
- **Maximum quality**: WAV (no compression)

**Recommendation**: Use **OPUS with 32kbps** (default) for optimal balance of quality and bandwidth efficiency in low-coverage areas.
