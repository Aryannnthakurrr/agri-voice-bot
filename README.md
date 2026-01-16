# Kisan Voice Bot v2

A multilingual voice-based agricultural assistant for Indian farmers using cloud AI processing.

## Overview

This voice bot helps Indian farmers get agricultural advice in their native language. Send a voice message and get a spoken response - no typing required.

**Architecture: Cloud Processing Pipeline**

```
Voice Input → Gemini STT → Gemini LLM → ElevenLabs TTS → Voice Output
     ↓            ↓            ↓              ↓
   Audio     Transcription  Response      Audio File
```

All processing happens in the cloud - no GPU required!

## Features

- **Speech-to-Text**: Google Gemini 2.5 Flash (multimodal)
- **LLM**: Google Gemini 2.5 Flash (agricultural advisor)
- **Text-to-Speech**: ElevenLabs (multilingual v2)
- **Telegram Bot**: Voice message support
- **Retry Logic**: Automatic retries with exponential backoff
- **Detailed Logging**: Per-step timing and log files

## Languages Supported

Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, Kannada, Malayalam, Bhojpuri, Maithili, and more.

## Requirements

- Python 3.11
- Google AI API key (free tier available)
- ElevenLabs API key (free tier available)
- Telegram Bot Token (optional, for Telegram integration)

**No GPU required!** Pure cloud processing.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aryannnthakurrr/agri-voice-bot.git
   cd agri-voice-bot
   git checkout v2
   ```

2. **Install dependencies**
   ```bash
   pip install uv
   uv sync
   ```

3. **Create environment file**
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   GOOGLE_API_KEY=your_google_ai_api_key
   ELEVEN_LABS_API_KEY=your_elevenlabs_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ELEVEN_LABS_INDIAN_VOICE_ID=optional_custom_voice_id
   ```

## Getting API Keys

### Google AI API Key (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create a new API key

### ElevenLabs API Key (Free Tier)
1. Go to [ElevenLabs](https://elevenlabs.io/)
2. Sign up and go to Profile Settings
3. Copy your API key

### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token

## Running the Server

```bash
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: http://localhost:8000/docs

## API Endpoints

### Voice Processing

**POST** `/api/v2/process-voice`

Upload audio and get a spoken response.

| Parameter | Type | Description |
|-----------|------|-------------|
| audio | File | Audio file (mp3, wav, ogg, m4a) |

**Response**: Audio file (MP3)

### Telegram Webhook

**POST** `/api/webhook/telegram`

Webhook endpoint for Telegram bot. Set your webhook URL to:
```
https://your-domain.com/api/webhook/telegram
```

### Test Endpoints

| Endpoint | Description |
|----------|-------------|
| POST `/api/v2/test-gemini` | Test Gemini LLM |
| POST `/api/v2/test-gemini-stt` | Test Gemini STT |
| POST `/api/v2/test-elevenlabs` | Test ElevenLabs TTS |

## Project Structure

```
kisan-voice-bot/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── routers/
│   │   ├── voice_v2.py            # Voice API endpoints
│   │   └── telegram.py            # Telegram webhook
│   └── services/
│       ├── gemini_stt.py          # Gemini speech-to-text
│       ├── gemini_llm.py          # Gemini agricultural advisor
│       └── elevenlabs_tts.py      # ElevenLabs text-to-speech
├── logs/                          # Daily log files
├── pyproject.toml                 # Dependencies
└── README.md
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GOOGLE_API_KEY | Yes | Google AI Studio API key |
| ELEVEN_LABS_API_KEY | Yes | ElevenLabs API key |
| TELEGRAM_BOT_TOKEN | No | Telegram bot token |
| ELEVEN_LABS_INDIAN_VOICE_ID | No | Custom voice ID |

## Logging

Logs are saved to `logs/bot_YYYYMMDD.log` with detailed timing:

```
[2026-01-16 16:30:45] ======================================================================
[2026-01-16 16:30:45] NEW VOICE MESSAGE from User (chat: 123456)
[2026-01-16 16:30:46] TRANSCRIPTION (2.1s)
[2026-01-16 16:30:46]   Language: hi
[2026-01-16 16:30:46]   Text: mera gehun mein kida lag gaya
[2026-01-16 16:30:48] GEMINI RESPONSE (1.8s)
[2026-01-16 16:30:48]   Gehun mein kida ke liye neem oil spray karein...
[2026-01-16 16:30:52] COMPLETED in 7.2s total
```

## Error Handling

The bot includes automatic retry logic:
- 3 retries with 5s, 10s, 15s delays
- Clear error messages for API limits and overload

## License

MIT License

## Author

Aryan Thakur ([@Aryannnthakurrr](https://github.com/Aryannnthakurrr))
