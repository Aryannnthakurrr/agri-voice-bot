# Kisan Voice Bot

The **Kisan Voice Bot** is a multilingual, AI-powered agricultural assistant designed to help Indian farmers. It processes voice queries in native languages and responds with expert agricultural advice in a natural, spoken format.

## Key Features

- **Multilingual Support**: Supports Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, Kannada, and Malayalam.
- **Voice-to-Voice Interaction**: Farmers speak naturally and receive voice responses.
- **Auto-Detection**: Automatically identifies the spoken language.
- **Casual Hinglish Mode**: For Hindi queries, the bot responds in "Casual Hinglish" (conversational Hindi/English mix) for a more relatable experience.
- **Hybrid Architecture**: Supports both local (offline-capable) and cloud-based (high-quality) pipelines.

## Architecture

The project implements two voice processing pipelines:

### 1. Hybrid Pipeline (V2) - *Recommended*
Uses state-of-the-art cloud models with a **two-Gemini architecture** for optimal quality.

| Stage | Technology | Role |
|-------|------------|------|
| **Input** | **OpenAI Whisper** (Local) | Transcribes audio and detects language. |
| **Intelligence 1** | **Google Gemini Flash** (Cloud) | Agricultural advisor - provides farming advice in user's language. |
| **Intelligence 2** | **Google Gemini Flash** (Cloud) | TTS optimizer - converts output to pronounceable romanized text. |
| **Output** | **Eleven Labs** (Cloud) | Converts text to ultra-realistic speech with Indian accent. |

### 2. Local Pipeline (V1) - *Legacy*
Runs entirely on-device (requires sufficient hardware).

| Stage | Technology | Role |
|-------|------------|------|
| **Input** | **OpenAI Whisper** | Transcribes audio. |
| **Intelligence** | **Qwen via Ollama** | Generates advice (local LLM). |
| **Output** | **Edge TTS** | Converts text to speech (using Microsoft Edge voices). |

## Setup & Configuration

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) (for V1 pipeline)
- ffmpeg (for audio processing)

### Environment Variables
Create a `.env` file in the root directory:

```env
# API Keys (Required for V2)
GOOGLE_API_KEY=your_google_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key

# Configuration
WHISPER_MODEL=medium
OLLAMA_MODEL=qwen2.5:7b
```

### Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR if using uv
uv sync
```

## API Documentation

The API runs on port `8000` by default.

### V2 Endpoints (Gemini + Eleven Labs)

#### `POST /api/v2/process-voice`
Main endpoint using the two-Gemini architecture.
- **Input**: `audio` file (wav, mp3, m4a).
- **Output**: Audio file (mp3) containing the answer.
- **Headers**: Returns metadata including:
  - `X-Transcription`: Original user query
  - `X-Raw-Response`: Agricultural advice from Gemini-1
  - `X-TTS-Text`: Optimized romanized text from Gemini-2
  - `X-Language`: Detected language code

#### `POST /api/v2/test-gemini`
Test Gemini Instance 1 (Agricultural Advisor) directly.
- **Input**: `query` (text), `language` (code).
- **Output**: JSON response with agricultural advice.

#### `POST /api/v2/test-elevenlabs`
Test the complete TTS optimization + speech pipeline.
- **Input**: `text` (text to convert).
- **Output**: Audio file (mp3).
- **Headers**: Returns `X-Original-Text` and `X-Optimized-Text`.

### V1 Endpoints (Local)

#### `POST /api/v1/process-voice`
Legacy local pipeline.
- **Input**: `audio` file, `language` code.
- **Output**: Audio file.

## Usage

1. **Start the Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access Swagger UI**:
   Open [http://localhost:8000/docs](http://localhost:8000/docs) to test endpoints interactively.

## License
[MIT License](LICENSE)
