#!/bin/bash
# Test the new modular architecture

echo "Testing F5-TTS Modular Architecture"
echo "===================================="
echo ""

cd /app

python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

print("1. Testing Core Module...")
from f5_tts.core import get_config, AudioData, InferenceConfig
config = get_config()
print(f"   ✓ Config loaded: cross_fade={config.default_cross_fade_duration}s")

print("\n2. Testing Audio Module...")
from f5_tts.audio import get_crossfader, CrossfadeType, AudioProcessingPipeline
import numpy as np

crossfader = get_crossfader(CrossfadeType.EQUAL_POWER)
audio1 = np.ones(24000)
audio2 = np.zeros(24000)
result = crossfader.crossfade(audio1, audio2, 0.5, 24000)
print(f"   ✓ Equal-power crossfade: {len(result)} samples")

pipeline = AudioProcessingPipeline()
print(f"   ✓ Audio pipeline created")

print("\n3. Testing Text Module...")
from f5_tts.text import get_chunker, SentenceBasedChunker

chunker = get_chunker('sentence')
text = "Esta es una prueba. Otra oración. Y una más."
chunks = chunker.chunk(text, max_chars=100)
print(f"   ✓ Sentence chunker: {len(chunks)} chunks")

adaptive = get_chunker('adaptive', ref_audio_duration=6.0, ref_text_length=100)
max_chars = adaptive.calculate_max_chars()
print(f"   ✓ Adaptive chunker: max_chars={max_chars}")

print("\n4. Testing Edge Fading...")
from f5_tts.audio import apply_edge_fades
audio = np.ones(24000)
faded = apply_edge_fades(audio, fade_duration=0.005, sample_rate=24000)
print(f"   ✓ Edge fades applied: first={faded[0]:.3f}, last={faded[-1]:.3f}")

print("\n✅ All modules working correctly!")
print("==================================")

EOF
