# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

whisper.cpp is a high-performance C/C++ implementation of OpenAI's Whisper automatic speech recognition (ASR) model. The implementation emphasizes portability, efficiency, and minimal dependencies, supporting multiple hardware acceleration backends.

## Build Commands

### Standard Build (CMake)
```bash
# Configure and build (Release mode)
cmake -B build
cmake --build build -j --config Release

# Built binaries are in: build/bin/
```

### Quick Start (Makefile)
```bash
# Download model and run on all samples
make base.en

# Just build
make build
```

### Build with Hardware Acceleration

**CUDA (NVIDIA GPUs):**
```bash
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
```

**Metal (Apple Silicon):**
Metal is automatically enabled on macOS with Apple Silicon.

**OpenVINO (Intel CPUs/GPUs):**
```bash
# First source OpenVINO environment
source /path/to/openvino/setupvars.sh

cmake -B build -DWHISPER_OPENVINO=1
cmake --build build -j --config Release
```

**Core ML (Apple Neural Engine):**
```bash
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```

**Vulkan (Cross-vendor GPU):**
```bash
cmake -B build -DGGML_VULKAN=1
cmake --build build -j --config Release
```

**OpenBLAS (CPU acceleration):**
```bash
cmake -B build -DGGML_BLAS=1
cmake --build build -j --config Release
```

### Build Options

FFmpeg support (Linux only, for additional audio formats):
```bash
cmake -B build -DWHISPER_FFMPEG=yes
cmake --build build -j --config Release
```

SDL2 support (for real-time audio input examples):
```bash
cmake -B build -DWHISPER_SDL2=ON
cmake --build build -j --config Release
```

## Testing

### Run Integration Tests
```bash
# From tests/ directory
cd tests
./run-tests.sh base.en

# With specific thread count
./run-tests.sh base.en 4
```

The test suite downloads audio samples, transcribes them, and compares output against reference transcripts using git diff for visual inspection.

### Build and Run Tests
```bash
# Tests are built by default in standalone mode
cmake -B build -DWHISPER_BUILD_TESTS=ON
cmake --build build -j --config Release
ctest --test-dir build
```

## Running Examples

### Basic Transcription
```bash
# Download a model first
./models/download-ggml-model.sh base.en

# Transcribe an audio file (16-bit WAV, 16kHz, mono)
./build/bin/whisper-cli -f samples/jfk.wav -m models/ggml-base.en.bin

# Convert audio to correct format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

### Real-time Stream Example
```bash
# Requires SDL2
./build/bin/whisper-stream -m models/ggml-base.en.bin -t 8 --step 500 --length 5000
```

### Server Example
```bash
./build/bin/whisper-server -m models/ggml-base.en.bin
```

## Architecture Overview

### Core Components

**whisper.cpp/whisper.h** (`src/whisper.cpp`, `include/whisper.h`):
- Main implementation of the Whisper model (9000+ lines)
- Contains the complete inference engine
- C-style API for language bindings
- Thread-safe when contexts are not shared

**ggml** (`ggml/`):
- Submodule containing the machine learning tensor library
- Provides low-level operations (matrix multiplication, attention, etc.)
- Supports multiple hardware backends (CPU, CUDA, Metal, Vulkan, etc.)
- whisper.cpp builds on top of ggml primitives

**whisper-arch.h** (`src/whisper-arch.h`):
- Defines tensor naming conventions mapping to Whisper architecture
- Enumerates encoder, decoder, and cross-attention tensor types
- Used for model loading and conversion

### Model Architecture

Whisper uses an encoder-decoder transformer architecture:
- **Encoder**: Processes audio spectrograms (mel-frequency features)
- **Decoder**: Generates text tokens autoregressively
- **Cross-attention**: Links encoder outputs to decoder

The encoder can be offloaded to specialized hardware:
- Core ML (Apple Neural Engine)
- OpenVINO (Intel devices)
- Standard backends (CUDA, Metal, etc.)

### Hardware Acceleration Strategy

1. **Encoder acceleration**: Primary target for hardware offload since it's the most computationally intensive part
2. **Decoder runs on CPU/GPU**: Less intensive, runs after encoder
3. **Mixed precision**: Uses F16/F32 for better performance
4. **Quantization support**: Q5_0 and other quantized formats reduce memory and improve speed

### Examples Structure

Located in `examples/`, each with its own subdirectory:
- **cli**: Main command-line transcription tool (formerly "main")
- **stream**: Real-time audio transcription
- **server**: HTTP server with OpenAI-compatible API
- **bench**: Performance benchmarking tool
- **command**: Voice command recognition
- **talk-llama**: Integration with LLaMA for conversational AI
- **quantize**: Model quantization utility

Common code shared across examples:
- `examples/common.cpp/h`: General utilities (arg parsing, file I/O)
- `examples/common-whisper.cpp/h`: Whisper-specific utilities
- `examples/common-sdl.cpp/h`: SDL2 audio capture utilities
- `examples/grammar-parser.cpp/h`: Grammar parsing for constrained generation

### Language Bindings

Located in `bindings/`:
- **go**: Go bindings
- **java**: Java bindings
- **javascript**: Node.js/JavaScript bindings
- **ruby**: Ruby bindings

Each binding wraps the C API from `include/whisper.h`.

### Model Format

Models use custom `ggml` format (not PyTorch):
- Single-file format containing weights, vocabulary, and mel filters
- Download pre-converted models: `./models/download-ggml-model.sh [model-name]`
- Or convert manually: `models/convert-pt-to-ggml.py`
- Available models: tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo
- Models ending in `.en` are English-only
- Models ending in `-q5_0` are quantized
- Models ending in `-tdrz` support speaker diarization

### Core ML Integration

When Core ML is enabled:
1. Generate Core ML model: `./models/generate-coreml-model.sh base.en`
2. This creates `models/ggml-base.en-encoder.mlmodelc` directory
3. At runtime, encoder automatically uses Core ML if available
4. First run compiles to device-specific format (slow), subsequent runs are fast

### OpenVINO Integration

When OpenVINO is enabled:
1. Convert model: `python models/convert-whisper-to-openvino.py --model base.en`
2. This creates `ggml-base.en-encoder-openvino.xml/.bin` files
3. Source OpenVINO environment before building
4. First run compiles to device-specific blob (cached for future runs)

## Development Notes

### Audio Input Requirements

Whisper expects:
- **Sample rate**: 16kHz (WHISPER_SAMPLE_RATE = 16000)
- **Format**: 32-bit floating point PCM in range [-1.0, 1.0]
- **Channels**: Mono (single channel)

Most examples handle conversion internally, but whisper-cli requires pre-converted WAV files.

### Code Organization

- Core library code in `src/`
- Public API in `include/whisper.h`
- Examples in `examples/` (self-contained with their own mains)
- Tests in `tests/`
- Model utilities in `models/`
- Hardware-specific code in `src/coreml/` and `src/openvino/`

### CMake Configuration

Important CMake options (see CMakeLists.txt line 66+):
- `WHISPER_BUILD_EXAMPLES`: Build example programs (default: ON in standalone)
- `WHISPER_BUILD_TESTS`: Build test suite (default: ON in standalone)
- `WHISPER_BUILD_SERVER`: Build server example (default: ON in standalone)
- `WHISPER_COREML`: Enable Core ML support
- `WHISPER_OPENVINO`: Enable OpenVINO support
- `WHISPER_SDL2`: Enable SDL2 for audio input
- `WHISPER_FFMPEG`: Enable FFmpeg for additional audio formats (Linux only)
- `GGML_CUDA`: Enable CUDA support (replaces deprecated WHISPER_CUDA)
- `GGML_METAL`: Enable Metal support (automatic on macOS)
- `GGML_VULKAN`: Enable Vulkan support
- `GGML_BLAS`: Enable BLAS/OpenBLAS support

### Model Loading Flow

1. Load model file (whisper_init_from_file or whisper_init_from_buffer)
2. Parse ggml format: magic number, hparams, mel filters, vocabulary, tensors
3. Initialize hardware backend if available (Core ML, OpenVINO)
4. Create inference state
5. Ready for transcription via whisper_full()

### Transcription Flow

1. Convert audio to mel spectrogram (using mel filters from model)
2. Run encoder on mel spectrogram (potentially on specialized hardware)
3. Run decoder autoregressively to generate tokens
4. Convert tokens to text using vocabulary
5. Apply timestamp alignment if requested
6. Return segments with text and timestamps

### Voice Activity Detection (VAD)

VAD preprocessing filters silence before transcription:
- Download VAD model: `./models/download-vad-model.sh silero-v6.2.0`
- Use with `--vad` and `-vm path/to/vad-model.bin`
- Significantly speeds up processing by skipping silence
- Configurable thresholds and parameters (see README section on VAD)

### Debugging

- Use `--debug-mode` flag in examples for verbose output
- Print internal state with `--print-special` and `--print-colors`
- Enable sanitizers: `-DWHISPER_SANITIZE_ADDRESS=ON`, `-DWHISPER_SANITIZE_THREAD=ON`
- Check system info in output to verify hardware acceleration is active

## Common Patterns

### Adding a New Example

1. Create directory in `examples/your-example/`
2. Add `your-example.cpp` with main()
3. Create `CMakeLists.txt` linking to whisper library
4. Add to `examples/CMakeLists.txt`
5. Use common utilities from `examples/common.h` for arg parsing

### Adding Hardware Backend Support

Most backend support goes through ggml. For encoder offloading (Core ML, OpenVINO):
1. Conversion script in `models/` to generate backend-specific model
2. Runtime code in `src/coreml/` or `src/openvino/`
3. CMake option to enable/disable
4. Initialization in `whisper_init_state()` checks for backend availability
5. Encoder execution routes through backend if available, falls back to ggml otherwise

### Working with Models

Model files are portable but backend-specific accelerator models are not:
- ggml models work everywhere
- Core ML models are macOS/iOS specific
- OpenVINO models are device-specific after first compilation
- Always include both base ggml model and accelerator model for full functionality

## Current Project: Enhanced whisper-stream

### Goal

Adapt `examples/stream/stream.cpp` to support an enhanced real-time transcription use case with initial voice activation check, continual silence detection, and UDP network output.

### Key Requirements

#### 1. Initial Voice Activation Check
- Start with VAD model only for configurable duration (default: 10 seconds)
- Check audio on capture device in 2-second increments
- If NO audio is detected during initial period, exit before loading whisper model
- This saves resources when no speech is present
- Uses existing `vad_simple()` functionality from `examples/stream/stream.cpp:283`

#### 2. Continual Silence Detection
- Already partially implemented at `examples/stream/stream.cpp:249-252`
- Current code: exits after 3 minutes (180 seconds) of continual silence
- Needs better integration with existing code structure
- Should match existing coding style and patterns
- Make silence timeout configurable via command-line parameter

#### 3. UDP Network Output
- Send current transcription segment as UDP packets
- Use SRT format (see `examples/cli/cli.cpp:489-506` for reference)
- Each packet should contain:
  - Segment number/ID
  - Start time (t0)
  - End time (t1)
  - Transcription text
  - Current timestamp (for network unreliability handling)
- Target host/port should be configurable
- Copy `output_srt()` formatting logic into stream.cpp to minimize dependencies

#### 4. Console Output Enhancement
- Current behavior: same segment is repeated step/length times as it's refined
- Each inference step updates the current segment (same t0/t1, changing text)
- Need to identify segments consistently across updates (by t0/t1 or other means)
- Consider experiments with console output before implementing UDP transfer

#### 5. Implementation Constraints
- **Do NOT modify existing code** - only add new functionality
- This makes it easier to incorporate upstream changes from remote repo
- All new features should be toggleable via command-line parameters
- All features should be OFF by default (opt-in)
- Follow existing code style and patterns

### Configuration Parameters to Add

New command-line options needed:
- `--vad-startup-ms N`: Duration of initial VAD check before loading whisper model (default: 10000ms, 0 = disabled)
- `--silence-timeout-ms N`: Duration of continual silence before exit (default: 180000ms, 0 = disabled)
- `--udp-host HOST`: Target host for UDP output (default: none)
- `--udp-port PORT`: Target port for UDP output (default: none)
- `--udp-enable`: Enable UDP output (default: false)

### Technical Notes

#### SRT Format Reference
From `examples/cli/cli.cpp:489-506`:
```cpp
static void output_srt(struct whisper_context * ctx, std::ofstream & fout,
                       const whisper_params & params, std::vector<std::vector<float>> pcmf32s) {
    const int n_segments = whisper_full_n_segments(ctx);
    for (int i = 0; i < n_segments; ++i) {
        const char * text = whisper_full_get_segment_text(ctx, i);
        const int64_t t0 = whisper_full_get_segment_t0(ctx, i);
        const int64_t t1 = whisper_full_get_segment_t1(ctx, i);

        fout << i + 1 + params.offset_n << "\n";
        fout << to_timestamp(t0, true) << " --> " << to_timestamp(t1, true) << "\n";
        fout << text << "\n\n";
    }
}
```

The `to_timestamp()` function is in `examples/common-whisper.cpp:138-151`:
```cpp
std::string to_timestamp(int64_t t, bool comma) {
    int64_t msec = t * 10;
    int64_t hr = msec / (1000 * 60 * 60);
    msec = msec - hr * (1000 * 60 * 60);
    int64_t min = msec / (1000 * 60);
    msec = msec - min * (1000 * 60);
    int64_t sec = msec / 1000;
    msec = msec - sec * 1000;

    char buf[32];
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d%s%03d",
             (int) hr, (int) min, (int) sec, comma ? "," : ".", (int) msec);
    return std::string(buf);
}
```

#### Current Stream Implementation Details

**VAD usage** (`examples/stream/stream.cpp:137`):
```cpp
const bool use_vad = n_samples_step <= 0; // sliding window mode uses VAD
```

**Current silence detection** (`examples/stream/stream.cpp:249-252`):
```cpp
if (silence_count * params.step_ms >= 1000 * 60 * 3) {
    printf("silent for %d steps. bye!\n", silence_count);
    is_running = false;
}
```

**VAD check logic** (`examples/stream/stream.cpp:283-287`):
```cpp
if (::vad_simple(pcmf32_new, WHISPER_SAMPLE_RATE, 1000, params.vad_thold, params.freq_thold, false)) {
    silence_count++;
} else {
    silence_count = 0;
}
```

**Typical usage pattern**:
```bash
# User typically runs with 2s step and 10s length
./build/bin/whisper-stream -m models/ggml-base.en.bin --step 2000 --length 10000
```

#### Segment Update Behavior

In stream mode (non-VAD), the same segment is refined across multiple inference steps:
- Same t0 and t1 values across multiple steps
- Text content may change as more context is available
- Console currently shows segment repeatedly
- UDP receiver needs to handle segment updates (same t0/t1 = update existing)
- Target device displays last N segments (e.g., 2) and updates based on timestamp

### Implementation Strategy

1. First, add new command-line parameters to `whisper_params` struct
2. Implement initial VAD check before whisper model loading
3. Better integrate existing silence detection code
4. Add UDP socket functionality (platform-specific: POSIX vs Windows)
5. Implement SRT formatting for UDP packets
6. Test console output behavior across multiple steps
7. Implement segment tracking and update logic for UDP transmission
