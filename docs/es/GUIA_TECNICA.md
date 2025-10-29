# Guía Técnica Detallada - Spanish-F5 TTS

**Versión**: 1.0
**Fecha**: 2025-10-29
**Audiencia**: Desarrolladores e ingenieros de ML

---

## 📋 Tabla de Contenidos

- [Componentes Internos](#-componentes-internos)
- [Motor de Procesamiento Regional](#-motor-de-procesamiento-regional)
- [Pipeline de Inferencia](#-pipeline-de-inferencia)
- [Arquitectura de Modelos](#-arquitectura-de-modelos)
- [Procesamiento de Audio](#-procesamiento-de-audio)
- [Sistema de Prosodia](#-sistema-de-prosodia)
- [Optimizaciones CUDA](#-optimizaciones-cuda)
- [API REST Modular](#-api-rest-modular)
- [Testing y Quality Assurance](#-testing-y-quality-assurance)

---

## 🔧 Componentes Internos

### Estructura de Directorios

```
src/f5_tts/
├── core/                      # Núcleo del sistema
│   ├── config.py             # GlobalConfig (singleton)
│   ├── types.py              # AudioData, InferenceConfig, protocolos
│   └── __init__.py
│
├── audio/                     # Procesamiento de audio
│   ├── crossfading.py        # Algoritmos de crossfading
│   ├── processors.py         # Pipeline de audio
│   └── __init__.py
│
├── text/                      # Procesamiento de texto
│   ├── chunker.py            # Estrategias de chunking
│   ├── spanish_regional.py   # Procesador regional ⭐
│   ├── discourse_prosody.py  # Prosodia a nivel de discurso ⭐
│   └── __init__.py
│
├── model/                     # Definiciones de modelos
│   ├── backbones/            # Arquitecturas DiT, MMDiT, UNetT
│   │   ├── dit.py
│   │   ├── mmdit.py
│   │   └── unett.py
│   ├── cfm.py                # Conditional Flow Matching
│   ├── dataset.py            # Manejo de datasets
│   ├── trainer.py            # Lógica de entrenamiento
│   └── utils.py              # Utilidades de modelo
│
├── infer/                     # Lógica de inferencia
│   ├── utils_infer.py        # Utilidades principales ⭐
│   ├── infer_cli.py          # Interfaz CLI
│   └── infer_gradio.py       # Interfaz Gradio
│
├── train/                     # Entrenamiento y finetuning
│   ├── train.py
│   ├── finetune_cli.py
│   └── datasets/             # Scripts de preparación de datos
│
├── rest_api/                  # REST API (REFACTORIZADO) ⭐
│   ├── app.py                # Factory de app FastAPI
│   ├── config.py             # Configuración de API
│   ├── state.py              # Gestión de estado global
│   ├── models.py             # Modelos Pydantic
│   ├── enhancements.py       # Procesamiento de mejoras
│   ├── tts_processor.py      # Lógica de generación TTS
│   └── routes/               # Manejadores de endpoints
│       ├── tts.py
│       ├── upload.py
│       ├── tasks.py
│       └── analysis.py
│
├── api.py                     # Clase F5TTS Python API
└── socket_server.py           # Servidor streaming (legacy)
```

---

## 🌎 Motor de Procesamiento Regional

### Visión General

El procesador regional es el **componente diferenciador** de Spanish-F5, proporcionando soporte auténtico para variantes regionales del español latinoamericano.

**Archivo**: `src/f5_tts/text/spanish_regional.py` (828 líneas)

### Arquitectura

```python
┌──────────────────────────────────────────────────────────┐
│         SpanishRegionalProcessor (Main Class)            │
├──────────────────────────────────────────────────────────┤
│  + process_text(text, region, apply_phonetics) → Result │
│  + detect_region(text) → RegionalVariant                │
│  + normalize_text(text) → str                            │
└────────┬─────────────────────────────────────────────────┘
         │
         │ Utiliza
         │
    ┌────▼─────────────────┐  ┌─────────────────────┐
    │  RegionalSlang       │  │ RegionalPhonetics   │
    │  • Diccionarios      │  │ • Transformaciones  │
    │  • Puntuación        │  │   fonéticas         │
    │  • Auto-detección    │  │ • Sheísmo/yeísmo    │
    └──────────────────────┘  └─────────────────────┘

    ┌──────────────────────┐  ┌─────────────────────┐
    │  RegionalProsody     │  │ RegionalProsodicProfile│
    │  • Marcadores        │  │ • Pace multipliers  │
    │  • Patrones          │  │ • F0 ranges         │
    │  • Detección         │  │ • Stress patterns   │
    └──────────────────────┘  └─────────────────────┘
```

### Componentes Principales

#### 1. RegionalSlang

Gestiona jerga y expresiones idiomáticas por región.

```python
class RegionalSlang:
    """Diccionarios de jerga y expresiones por región."""

    RIOPLATENSE = {
        # Interjecciones
        "che", "boludo", "pelotudo", "flaco",

        # Verbos voseo
        "querés", "tenés", "sabés", "vení", "andá",

        # Sustantivos
        "colectivo", "bondi", "mate", "pilcha",

        # Expresiones
        "ni en pedo", "al pedo", "una bocha"
    }

    COLOMBIAN = {
        "parcero", "parce", "chimba", "bacano",
        "vaina", "berraco", "malparido",
        # Coletilla característica
        "¿sí?", "¿cierto?"
    }

    MEXICAN = {
        "órale", "güey", "buey", "ahorita",
        "chido", "padre", "neta",
        # Diminutivos -ito/-ita muy frecuentes
    }

    # ... otras regiones

    @staticmethod
    def detect_region(text: str) -> Tuple[str, int]:
        """
        Detecta región basado en marcadores de jerga.

        Returns:
            (region_name, confidence_score)
        """
        scores = defaultdict(int)

        text_lower = text.lower()

        # Puntuar por cada marcador encontrado
        for region_name, markers in [
            ("rioplatense", RegionalSlang.RIOPLATENSE),
            ("colombian", RegionalSlang.COLOMBIAN),
            ("mexican", RegionalSlang.MEXICAN),
            # ...
        ]:
            for marker in markers:
                if marker in text_lower:
                    scores[region_name] += 1

        # Retornar región con mayor puntaje
        if scores:
            best_region = max(scores.items(), key=lambda x: x[1])
            return best_region
        else:
            return ("neutral", 0)
```

**Uso:**
```python
text = "Che boludo, ¿vos querés tomar unos mates?"
region, score = RegionalSlang.detect_region(text)
# region = "rioplatense", score = 4
```

#### 2. RegionalPhonetics

Aplica transformaciones fonéticas características de cada región.

```python
class RegionalPhonetics:
    """Transformaciones fonéticas por región."""

    @staticmethod
    def apply_rioplatense(text: str) -> str:
        """
        Aplica transformaciones rioplatenses:
        - Sheísmo: ll/y → sh
        - Aspiración de /s/ final: -s → -h
        - Voseo: Mantener acentuación en voseo
        """
        # Sheísmo: ll/y → sh (representado con 'sh')
        text = re.sub(r'\bll', 'sh', text)
        text = re.sub(r'\by', 'sh', text, flags=re.IGNORECASE)

        # Aspiración de s al final de sílaba
        # "estás" → "ehtáh"
        text = re.sub(r's\b', 'h', text)
        text = re.sub(r's([^aeiouáéíóú])', r'h\1', text)

        return text

    @staticmethod
    def apply_chilean(text: str) -> str:
        """
        Transformaciones chilenas:
        - Aspiración/elisión de /s/
        - Reducción de /d/ intervocálica
        - Entonación característica
        """
        # Elisión de d intervocálica
        # "todo" → "too", "nada" → "naa"
        text = re.sub(r'([aeiou])d([ao])\b', r'\1\2', text)

        # Aspiración de s
        text = re.sub(r's\b', '', text)  # Más fuerte que rioplatense

        return text

    # ... otras regiones
```

**Ejemplo de aplicación:**
```python
original = "¿Vos sabés dónde está el colectivo?"
transformed = RegionalPhonetics.apply_rioplatense(original)
# "¿Voh habéh dónde ehtá el colectivo?"
# Nota: Representación fonética, no ortográfica
```

#### 3. RegionalProsody

Detecta y marca patrones prosódicos característicos.

```python
class RegionalProsody:
    """Análisis y marcadores de prosodia regional."""

    @staticmethod
    def analyze_rioplatense(text: str) -> List[str]:
        """
        Características prosódicas rioplatenses:
        - Entonación ascendente en preguntas
        - Doble acentuación
        - Ritmo más lento
        - Cualidad quejumbrosa
        """
        markers = []

        # Detectar preguntas (entonación ascendente muy marcada)
        if '¿' in text:
            markers.append("QUESTION_RISE_STRONG")

        # Detectar exclamaciones (cualidad quejumbrosa)
        if '¡' in text:
            markers.append("EXCLAMATION_PLAINTIVE")

        # Palabras con voseo (doble acentuación)
        voseo_words = ["querés", "sabés", "tenés", "sos", "vos"]
        for word in voseo_words:
            if word in text.lower():
                markers.append("VOSEO_STRESS")

        return markers

    @staticmethod
    def analyze_mexican(text: str) -> List[str]:
        """
        Características prosódicas mexicanas:
        - Contornos melódicos distintivos
        - Entonación expresiva
        - Diminutivos frecuentes
        """
        markers = []

        # Detectar diminutivos
        if re.search(r'\w+it[oa]s?\b', text):
            markers.append("DIMINUTIVE_AFFECTIVE")

        # Exclamaciones mexicanas (entonación muy expresiva)
        if any(word in text.lower() for word in ["órale", "híjole", "ándale"]):
            markers.append("EXCLAMATION_EXPRESSIVE")

        return markers
```

#### 4. RegionalProsodicProfile

**Perfiles prosódicos basados en investigación académica** (NUEVO ⭐)

```python
@dataclass
class RegionalProsodicProfile:
    """Perfil prosódico completo validado empíricamente."""

    name: str
    pace_multiplier: float      # Multiplicador de velocidad
    f0_range_hz: Tuple[float, float]  # Rango de F0 (min, max)
    stress_pattern: str         # Patrón de acentuación
    intonation_style: str       # Estilo de entonación
    rhythm_type: str            # Tipo de ritmo
    voice_quality: str          # Cualidad de voz

# Perfiles empíricos basados en investigación
RIOPLATENSE_PROFILE = RegionalProsodicProfile(
    name="rioplatense",
    pace_multiplier=0.75,        # LENTO (Cuello & Oro Ozán 2024)
    f0_range_hz=(75, 340),       # Femenino: 75-340Hz
    stress_pattern="double_accentuation",  # Doble acentuación
    intonation_style="circumflex",  # Circunfleja
    rhythm_type="stress_timed",
    voice_quality="plaintive"    # Cualidad quejumbrosa
)

COLOMBIAN_PROFILE = RegionalProsodicProfile(
    name="colombian",
    pace_multiplier=1.0,         # MEDIO
    f0_range_hz=(80, 280),
    stress_pattern="clear",
    intonation_style="neutral",
    rhythm_type="syllable_timed",
    voice_quality="clear"
)

MEXICAN_PROFILE = RegionalProsodicProfile(
    name="mexican",
    pace_multiplier=1.0,         # MEDIO
    f0_range_hz=(85, 320),
    stress_pattern="melodic",
    intonation_style="expressive",
    rhythm_type="mixed",
    voice_quality="warm"
)
```

**Referencias Académicas:**
- **Cuello & Oro Ozán (2024)**: "Análisis de la prosodia del español rioplatense a través del corpus T.E.P.HA"
- **Guglielmone et al. (2014)**: "La prosodia del español rioplatense en el marco de la teoría de la optimalidad"

### Flujo de Procesamiento Completo

```python
def process_spanish_text(
    text: str,
    region: str = "auto",
    apply_phonetics: bool = True
) -> ProcessingResult:
    """
    Pipeline completo de procesamiento regional.

    Steps:
    1. Normalizar texto básico
    2. Detectar/aplicar jerga regional
    3. Aplicar transformaciones fonéticas (opcional)
    4. Agregar marcadores prosódicos
    5. Aplicar perfil prosódico empírico
    6. Retornar resultado estructurado
    """
    processor = SpanishRegionalProcessor()

    # 1. Normalización básica
    normalized = processor.normalize_text(text)

    # 2. Detección de región (si auto)
    if region == "auto":
        detected_region, confidence = processor.detect_region(text)
    else:
        detected_region = region

    # 3. Aplicar transformaciones fonéticas
    if apply_phonetics:
        phonetic = processor.apply_phonetics(normalized, detected_region)
    else:
        phonetic = normalized

    # 4. Agregar marcadores prosódicos
    prosody_markers = processor.analyze_prosody(text, detected_region)

    # 5. Obtener perfil prosódico empírico
    prosodic_profile = processor.get_prosodic_profile(detected_region)

    # 6. Retornar resultado completo
    return ProcessingResult(
        original_text=text,
        normalized_text=normalized,
        phonetic_text=phonetic,
        detected_region=detected_region,
        slang_markers=processor.get_slang_markers(text, detected_region),
        prosody_markers=prosody_markers,
        prosodic_profile=prosodic_profile
    )
```

**Ejemplo de uso completo:**
```python
from f5_tts.text import process_spanish_text

result = process_spanish_text(
    "Che boludo, ¿vos querés tomar unos mates?",
    region="auto",  # Detectará "rioplatense"
    apply_phonetics=True
)

print(f"Región detectada: {result.detected_region}")
# "rioplatense"

print(f"Marcadores de jerga: {result.slang_markers}")
# ["che", "boludo", "vos", "querés"]

print(f"Perfil prosódico: pace={result.prosodic_profile.pace_multiplier}x")
# pace=0.75x (lento, empíricamente validado)

print(f"Rango F0: {result.prosodic_profile.f0_range_hz} Hz")
# (75, 340) Hz para voz femenina
```

---

## 🎯 Pipeline de Inferencia

### Visión General del Flujo

```
Input Text
    │
    ▼
┌─────────────────────┐
│ Text Preprocessing  │ ← Regional processing
│ - Normalize         │
│ - Phonetics         │
│ - Prosody markers   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Text Encoding       │
│ - Tokenization      │
│ - Embedding         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Reference Audio     │
│ - Load ref audio    │
│ - Extract mel-spec  │
│ - Encode features   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ DiT/UNetT Model     │ ← GPU Inference
│ - Flow matching     │
│ - NFE steps (8-64)  │
│ - Generate mel-spec │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Vocoder (Vocos)     │
│ - Mel → Waveform    │
│ - 24kHz output      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Post-Processing     │
│ - Normalize         │
│ - Crossfade         │
│ - Quality check     │
└──────┬──────────────┘
       │
       ▼
   Output WAV
```

### Código de Inferencia

**Archivo**: `src/f5_tts/infer/utils_infer.py`

```python
def infer_batch(
    model,
    vocoder,
    ref_audio,
    ref_text,
    gen_text_batches,
    cfg_strength=2.0,
    nfe_step=32,
    speed=1.0,
    sway_sampling_coef=-1.0,
    device="cuda"
):
    """
    Inferencia por lotes con DiT/UNetT.

    Args:
        model: Modelo DiT o UNetT
        vocoder: Vocos vocoder
        ref_audio: Audio de referencia (tensor)
        ref_text: Texto de referencia
        gen_text_batches: Lista de textos a generar
        cfg_strength: Classifier-free guidance (1.5-3.0)
        nfe_step: Número de pasos de integración (8-64)
        speed: Multiplicador de velocidad
        sway_sampling_coef: Coeficiente de sway sampling
        device: cuda/cpu

    Returns:
        generated_waves: Lista de waveforms generados
    """
    # 1. Preparar audio de referencia
    ref_audio = ref_audio.to(device)

    # 2. Extraer mel-espectrograma de referencia
    with torch.no_grad():
        ref_mel = vocoder.extract_mel(ref_audio)

    # 3. Tokenizar textos
    ref_text_tokens = tokenize(ref_text)
    gen_text_tokens = [tokenize(text) for text in gen_text_batches]

    # 4. Generar mel-espectrogramas con modelo DiT
    with torch.no_grad():
        generated_mels = model.sample(
            cond=ref_mel,
            text=gen_text_tokens,
            duration=None,  # Auto-detect
            steps=nfe_step,
            cfg_strength=cfg_strength,
            sway_sampling_coef=sway_sampling_coef
        )

    # 5. Vocoder: mel → waveform
    generated_waves = []
    for mel in generated_mels:
        with torch.no_grad():
            wave = vocoder.decode(mel)

        # Aplicar speed
        if speed != 1.0:
            wave = resample_audio(wave, speed)

        generated_waves.append(wave)

    return generated_waves
```

### Parámetros de Calidad

| Parámetro | Rango | Default | Efecto |
|-----------|-------|---------|--------|
| `nfe_step` | 8-64 | 32 | Pasos de integración (↑ = mejor calidad, ↓ = más rápido) |
| `cfg_strength` | 1.0-5.0 | 2.0 | Guidance strength (↑ = más fiel a condición) |
| `speed` | 0.5-2.0 | 1.0 | Velocidad de habla |
| `sway_sampling_coef` | -1 a 1 | -1 | Coeficiente de sway (-1 = auto) |

**Recomendaciones:**
- **Calidad alta**: nfe=32-64, cfg=2.0-2.5
- **Balanceado**: nfe=16-24, cfg=2.0
- **Rápido**: nfe=8-12, cfg=1.8-2.0

---

## 🏗️ Arquitectura de Modelos

### DiT (Diffusion Transformer)

**Archivo**: `src/f5_tts/model/backbones/dit.py`

```python
class DiT(nn.Module):
    """
    Diffusion Transformer para F5-TTS.

    Arquitectura:
    - Transformer encoder-decoder
    - Posicional embeddings rotatorios
    - Multi-head attention con flash attention
    - Feed-forward con SwiGLU activation
    """

    def __init__(
        self,
        dim=1024,
        depth=24,
        heads=16,
        ff_mult=4,
        text_dim=512,
        conv_layers=4
    ):
        super().__init__()

        # Text encoder
        self.text_embed = nn.Embedding(vocab_size, text_dim)

        # Time embedding (difusión)
        self.time_embed = TimestepEmbedding(dim)

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerBlock(
                dim=dim,
                heads=heads,
                ff_mult=ff_mult
            )
            for _ in range(depth)
        ])

        # Output projection
        self.to_pred = nn.Linear(dim, mel_dim)

    def forward(self, x, cond, text, time):
        """
        Args:
            x: Noisy mel-spectrogram [B, T, mel_dim]
            cond: Conditioning mel [B, T_ref, mel_dim]
            text: Text tokens [B, T_text]
            time: Diffusion timestep [B]

        Returns:
            pred: Predicted noise [B, T, mel_dim]
        """
        # Embed text
        text_emb = self.text_embed(text)  # [B, T_text, text_dim]

        # Time embedding
        t_emb = self.time_embed(time)  # [B, dim]

        # Concatenate conditioning
        x = torch.cat([cond, x], dim=1)  # [B, T_ref+T, mel_dim]

        # Add time embedding
        x = x + t_emb[:, None, :]

        # Transformer layers con cross-attention a texto
        for layer in self.layers:
            x = layer(x, context=text_emb)

        # Output
        pred = self.to_pred(x[:, cond.size(1):, :])  # Solo parte generada

        return pred
```

### Conditional Flow Matching (CFM)

**Archivo**: `src/f5_tts/model/cfm.py`

Flow matching es una alternativa a difusión estándar que ofrece:
- Convergencia más rápida
- Mejor calidad de audio
- Menor número de pasos de inferencia

```python
class ConditionalFlowMatching:
    """
    Conditional Flow Matching para generación de mel-espectrogramas.

    Usa ODE (Ordinary Differential Equation) solver para muestreo.
    """

    def __init__(self, model, sigma_min=1e-4):
        self.model = model
        self.sigma_min = sigma_min

    def sample(
        self,
        cond,
        text,
        steps=32,
        cfg_strength=2.0,
        method="euler"
    ):
        """
        Muestreo con flow matching.

        Args:
            cond: Conditioning (ref mel-spec)
            text: Text tokens
            steps: Integration steps (NFE)
            cfg_strength: Classifier-free guidance
            method: ODE solver (euler, heun, rk4)

        Returns:
            mel: Generated mel-spectrogram
        """
        # 1. Inicializar con ruido
        B, T = text.shape[0], self.estimate_duration(text)
        z = torch.randn(B, T, self.mel_dim).to(cond.device)

        # 2. Timestepping
        dt = 1.0 / steps
        t_schedule = torch.linspace(0, 1, steps+1)

        # 3. Integrar ODE
        for i in range(steps):
            t = t_schedule[i]

            # Predecir velocidad
            with torch.no_grad():
                v_pred = self.model(z, cond, text, t)

                # Classifier-free guidance
                if cfg_strength != 1.0:
                    v_uncond = self.model(z, cond, None, t)
                    v_pred = v_uncond + cfg_strength * (v_pred - v_uncond)

            # Euler step
            z = z + v_pred * dt

        return z
```

### Vocoder (Vocos)

**Vocos** es un vocoder basado en convoluciones que convierte mel-espectrogramas a waveforms.

**Características:**
- Arquitectura ligera (~5M parámetros)
- Inferencia rápida (GPU: ~10ms para 5s audio)
- Alta calidad (comparable a HiFi-GAN)

```python
class Vocos:
    """Wrapper para vocoder Vocos."""

    def __init__(self, checkpoint_path, device="cuda"):
        self.model = load_vocos_model(checkpoint_path)
        self.model.to(device)
        self.model.eval()

    def decode(self, mel):
        """
        Mel-spectrogram → Waveform

        Args:
            mel: [B, mel_bins, T] o [mel_bins, T]

        Returns:
            wave: [B, samples] o [samples]
        """
        with torch.no_grad():
            wave = self.model.decode(mel)
        return wave

    def extract_mel(self, audio, sr=24000):
        """
        Waveform → Mel-spectrogram

        Args:
            audio: [samples] o [B, samples]
            sr: Sample rate

        Returns:
            mel: [mel_bins, T] o [B, mel_bins, T]
        """
        with torch.no_grad():
            mel = self.model.extract_mel(audio, sr)
        return mel
```

---

## 🎵 Procesamiento de Audio

### Crossfading

**Archivo**: `src/f5_tts/audio/crossfading.py`

Tres algoritmos implementados:

#### 1. Equal Power Crossfading (Estándar Industria)

```python
class EqualPowerCrossfader:
    """
    Crossfading con ley de potencia igual.

    Previene caídas de amplitud durante transiciones.
    Usa curvas de fade sqrt para mantener potencia constante.
    """

    def crossfade(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        duration: float = 0.5,
        sample_rate: int = 24000
    ) -> np.ndarray:
        """
        Aplica equal-power crossfade.

        Args:
            audio1: Primer segmento de audio
            audio2: Segundo segmento de audio
            duration: Duración del fade (segundos)
            sample_rate: Sample rate

        Returns:
            Concatenated audio con crossfade suave
        """
        fade_samples = int(duration * sample_rate)

        # Curvas de fade (sqrt para equal power)
        fade_out = np.sqrt(np.linspace(1, 0, fade_samples))
        fade_in = np.sqrt(np.linspace(0, 1, fade_samples))

        # Aplicar fades
        audio1_end = audio1[-fade_samples:]
        audio2_start = audio2[:fade_samples]

        crossfaded = audio1_end * fade_out + audio2_start * fade_in

        # Concatenar
        result = np.concatenate([
            audio1[:-fade_samples],
            crossfaded,
            audio2[fade_samples:]
        ])

        return result
```

#### 2. Raised Cosine Crossfading

```python
class RaisedCosineCrossfader:
    """
    Crossfading con ventana raised cosine (Hann).
    Transiciones aún más suaves que equal power.
    """

    def crossfade(self, audio1, audio2, duration=0.5, sample_rate=24000):
        fade_samples = int(duration * sample_rate)

        # Ventana Hann
        fade_out = np.cos(np.linspace(0, np.pi/2, fade_samples)) ** 2
        fade_in = np.sin(np.linspace(0, np.pi/2, fade_samples)) ** 2

        # ... resto igual que equal power
```

#### 3. Linear Crossfading

```python
class LinearCrossfader:
    """Crossfading lineal simple (menos smooth)."""

    def crossfade(self, audio1, audio2, duration=0.5, sample_rate=24000):
        fade_samples = int(duration * sample_rate)

        fade_out = np.linspace(1, 0, fade_samples)
        fade_in = np.linspace(0, 1, fade_samples)

        # ... resto igual
```

**Recomendación**: Usar **EqualPowerCrossfader** para mejor calidad.

### Audio Processing Pipeline

```python
from f5_tts.audio import (
    remove_dc_offset,
    normalize_rms,
    resample_audio,
    prevent_clipping,
    AudioProcessingPipeline
)

# Pipeline completo
pipeline = AudioProcessingPipeline([
    remove_dc_offset,      # 1. Remover DC offset
    normalize_rms,         # 2. Normalizar RMS
    resample_audio,        # 3. Resamplear a 24kHz
    prevent_clipping       # 4. Prevenir clipping
])

# Aplicar pipeline
processed = pipeline.process(raw_audio, target_sr=24000, target_rms=0.1)
```

### Audio Quality Analyzer

```python
from f5_tts.audio import AudioQualityAnalyzer

analyzer = AudioQualityAnalyzer()
quality = analyzer.analyze("output.wav")

print(f"Overall Quality: {quality.overall_level}")  # EXCELLENT/GOOD/FAIR/POOR
print(f"SNR: {quality.snr_db:.1f} dB")
print(f"Clipping Rate: {quality.clipping_rate:.2%}")
print(f"Dynamic Range: {quality.dynamic_range_db:.1f} dB")
print(f"Issues: {quality.detected_issues}")
```

---

## 📊 Sistema de Prosodia

### Prosodia a Nivel de Discurso

**Archivo**: `src/f5_tts/text/discourse_prosody.py`

Basado en **Guglielmone et al. (2014)**, implementa:

- **Unidades de declinación**: Secciones temáticas con reset de F0
- **Tonos nucleares**: Descendente (↘), suspensivo (→), ascendente (↗)
- **Frases entonacionales**: Unidades prosódicas completas

```python
from f5_tts.text.discourse_prosody import analyze_discourse_prosody

result = analyze_discourse_prosody(
    "Hola amigo. ¿Cómo estás? Estoy muy bien, gracias.",
    voice_type="female"
)

# result.phrases:
# [
#   IntonationalPhrase(text="Hola amigo", nuclear_tone="descending"),
#   IntonationalPhrase(text="¿Cómo estás?", nuclear_tone="ascending"),
#   IntonationalPhrase(text="Estoy muy bien, gracias", nuclear_tone="descending")
# ]

# result.declination_units:
# [
#   DeclinationUnit(
#     phrases=[...],
#     f0_start=200,
#     f0_end=120
#   )
# ]
```

---

## ⚡ Optimizaciones CUDA

### torch.compile

```python
import torch

# Habilitar compilación de modelo
model = torch.compile(
    model,
    mode="reduce-overhead",  # o "max-autotune"
    backend="inductor"
)

# Beneficios:
# - 20-40% reducción de latencia
# - Kernels fusionados
# - Menos overhead de Python
```

### cuDNN Benchmark

```python
import torch

# Auto-tuning de kernels cuDNN
torch.backends.cudnn.benchmark = True

# Beneficios:
# - Selecciona kernels óptimos por tamaño de input
# - 5-10% ganancia de velocidad
```

### TF32 (Tensor Float 32)

```python
# GPUs Ampere+ (A100, RTX 3090, etc.)
torch.set_float32_matmul_precision("high")  # Habilita TF32

# Beneficios:
# - 8x más rápido que FP32
# - Misma precisión para deep learning
```

### Variables de Entorno

```bash
# Configurar optimizaciones
export ENABLE_TORCH_COMPILE=true
export ENABLE_CUDNN_BENCHMARK=true
export TORCH_MATMUL_PRECISION=high

# Ejecutar API
python f5_tts_api.py
```

---

## 🌐 API REST Modular

### Refactorización

La API fue refactorizada de un monolito de **1000+ líneas** a una arquitectura modular:

```
f5_tts_api.py (48 líneas) → Entry point
    │
    └─→ src/f5_tts/rest_api/
        ├── app.py (180 líneas) - Factory de app
        ├── state.py (120 líneas) - Estado global
        ├── models.py (200 líneas) - Modelos Pydantic
        ├── enhancements.py (150 líneas) - Mejoras de texto
        ├── tts_processor.py (180 líneas) - Lógica TTS
        └── routes/ - Endpoints organizados
            ├── tts.py (140 líneas)
            ├── upload.py (90 líneas)
            ├── tasks.py (70 líneas)
            └── analysis.py (60 líneas)
```

**Beneficios:**
- ✅ Modularidad y testabilidad
- ✅ Separación de responsabilidades
- ✅ Reutilización de código
- ✅ 100% compatibilidad hacia atrás

Ver [docs/API_REFACTORING.md](../API_REFACTORING.md) para detalles completos.

---

## 🧪 Testing y Quality Assurance

### Cobertura de Tests

**287 tests** con **60% cobertura de código**

#### Test Suites

1. **Regional Spanish** (`test_spanish_regional.py`)
   - 40 tests
   - Transformaciones fonéticas por región
   - Detección automática de variantes
   - Normalización de jerga

2. **Prosody Improvements** (`test_prosody_improvements.py`)
   - 31 tests ⭐
   - Perfiles prosódicos empíricos
   - Prosodia a nivel de discurso
   - Prevención de regresiones

3. **Audio Processing** (`test_audio_processors.py`, `test_audio.py`)
   - 50 tests
   - Algoritmos de crossfading
   - Normalización de audio
   - Análisis de calidad

4. **API Integration** (`test_api_integration.py`)
   - 31 tests
   - Endpoints REST
   - Gestión de estado
   - Procesamiento de mejoras

### Ejecutar Tests

```bash
# Suite completa
pytest tests/ -v

# Con cobertura
pytest --cov=src/f5_tts --cov-report=html tests/

# Suite específica
pytest tests/test_prosody_improvements.py -v

# Test específico
pytest tests/test_spanish_regional.py::test_rioplatense_phonetics -v
```

### Análisis de Cobertura

```bash
python analyze_coverage.py

# Genera:
# - htmlcov/ - Reporte HTML interactivo
# - Resumen por módulo
# - Líneas no cubiertas
```

---

## 📚 Referencias

### Papers Académicos

- **F5-TTS**: [arXiv:2410.06885](https://arxiv.org/abs/2410.06885)
- **E2-TTS**: [arXiv:2406.18009](https://arxiv.org/abs/2406.18009)
- **Cuello & Oro Ozán (2024)**: Prosodia T.E.P.HA rioplatense
- **Guglielmone et al. (2014)**: Prosodia del español rioplatense

### Documentación Relacionada

- **[README.es.md](../../README.es.md)** - Documentación principal
- **[ARQUITECTURA_ECOSISTEMA.md](ARQUITECTURA_ECOSISTEMA.md)** - Integración Vocalio
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** - Arquitectura interna (inglés)
- **[../PROSODY_ANALYSIS_ACADEMIC_PAPERS.md](../PROSODY_ANALYSIS_ACADEMIC_PAPERS.md)** - Análisis académico

---

<div align="center">

**Documentación Técnica - Spanish-F5 TTS**

**Parte del Ecosistema Vocalio**

</div>
