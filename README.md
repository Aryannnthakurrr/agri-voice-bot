# Kisan Voice Bot v1

A multilingual voice-based agricultural assistant for Indian farmers using local AI processing.

## Overview

This voice bot helps Indian farmers get agricultural advice in their native language. It processes voice queries and responds with voice answers - no typing required.

**Architecture: Local Processing Pipeline**

```
Voice Input → Whisper STT → Qwen LLM → Edge TTS → Voice Output
     ↓              ↓            ↓           ↓
   Audio      Transcription   Response   Audio File
```

## Features

- **Speech-to-Text**: OpenAI Whisper (runs locally on GPU)
- **LLM**: Qwen 2.5 7B via Ollama (runs locally)
- **Text-to-Speech**: Microsoft Edge TTS (free, cloud-based)
- **Languages Supported**: Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, Kannada, Malayalam

## Requirements

- Python 3.11
- NVIDIA GPU with CUDA (recommended for Whisper)
- [Ollama](https://ollama.ai/) installed and running
- 8GB+ VRAM for Whisper medium model

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aryannnthakurrr/agri-voice-bot.git
   cd agri-voice-bot
   git checkout v1
   ```

2. **Install dependencies**
   ```bash
   pip install uv
   uv sync
   ```

3. **Install Ollama and download model**
   ```bash
   # Install Ollama from https://ollama.ai/
   ollama pull qwen2.5:7b
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   WHISPER_MODEL=medium
   OLLAMA_MODEL=qwen2.5:7b
   ```

## Running the Server

```bash
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: http://localhost:8000/docs

## API Endpoints

### Main Endpoint

**POST** `/api/v1/process-voice`

Process a voice query and get a voice response.

| Parameter | Type | Description |
|-----------|------|-------------|
| audio | File | Audio file (mp3, wav, ogg, m4a) |
| language | String | Language code (hi, ta, te, bn, mr, gu, pa, kn, ml) |

**Response**: Audio file (MP3) with headers containing transcription and response text.

### Test Endpoints

| Endpoint | Description |
|----------|-------------|
| POST `/api/v1/transcribe-only` | Test Whisper transcription |
| POST `/api/v1/llm-only` | Test LLM response |
| POST `/api/v1/text-to-speech` | Test Edge TTS |

## Project Structure

```
kisan-voice-bot/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   └── voice.py         # Voice processing endpoints
│   └── services/
│       ├── stt.py           # Whisper speech-to-text
│       ├── llm.py           # Qwen/Ollama LLM
│       └── tts.py           # Edge TTS
├── pyproject.toml           # Dependencies
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| WHISPER_MODEL | medium | Whisper model size (tiny, base, small, medium, large) |
| OLLAMA_MODEL | qwen2.5:7b | Ollama model name |

## Language Support

| Code | Language | TTS Voice |
|------|----------|-----------|
| hi | Hindi | hi-IN-SwaraNeural |
| ta | Tamil | ta-IN-PallaviNeural |
| te | Telugu | te-IN-ShrutiNeural |
| bn | Bengali | bn-IN-TanishaaNeural |
| mr | Marathi | mr-IN-AarohiNeural |
| gu | Gujarati | gu-IN-DhwaniNeural |
| pa | Punjabi | hi-IN-SwaraNeural (fallback) |
| kn | Kannada | kn-IN-SapnaNeural |
| ml | Malayalam | ml-IN-SobhanaNeural |

Note: Punjabi uses Hindi voice as Edge TTS does not support Punjabi.

## License

MIT License
