# 🌾 Kisan Voice Bot

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A multilingual voice-based agricultural assistant for Indian farmers. Send a voice message, get spoken advice - no typing required!

## 🚀 Quick Start

```bash
# 1. Clone and enter directory
git clone https://github.com/Aryannnthakurrr/agri-voice-bot.git
cd agri-voice-bot

# 2. Install dependencies
pip install uv
uv sync

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys (see below)

# 4. Run the server
uv run uvicorn app.main:app --reload --port 8000

# 5. Open API docs
# http://localhost:8000/docs
```

## ⚙️ Architecture

```
Voice Input → Gemini STT → Gemini LLM → ElevenLabs TTS → Voice Output
     ↓            ↓            ↓              ↓
   Audio     Transcription  Response      Audio File
```

**No GPU required** - 100% cloud processing!

## 🔑 API Keys

| Service | Get Key | Free Tier |
|---------|---------|-----------|
| **Google AI** | [aistudio.google.com](https://aistudio.google.com/) | ✅ Yes |
| **ElevenLabs** | [elevenlabs.io](https://elevenlabs.io/) | ✅ Yes |
| **Telegram** | [@BotFather](https://t.me/botfather) | ✅ Yes |

## 📡 API Endpoints

### Voice Processing

**POST** `/api/v2/process-voice`

Process a voice message and get a spoken response.

```bash
curl -X POST http://localhost:8000/api/v2/process-voice \
  -F "audio=@voice_message.ogg" \
  --output response.mp3
```

**Response Headers:**
- `X-Transcription`: What the user said
- `X-Raw-Response`: AI response text
- `X-Language`: Detected language code

### Telegram Bot

**POST** `/api/webhook/telegram`

Set up your Telegram bot webhook:

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-domain.com/api/webhook/telegram"
```

### Test Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v2/test-gemini` | Test LLM with text |
| `POST /api/v2/test-gemini-stt` | Test speech-to-text |
| `POST /api/v2/test-elevenlabs` | Test text-to-speech |

## 🌍 Supported Languages

Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, Kannada, Malayalam, Bhojpuri, Maithili, Urdu, and more.

## 📁 Project Structure

```
kisan-voice-bot/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   ├── voice_v2.py      # Voice API endpoints
│   │   └── telegram.py      # Telegram webhook
│   └── services/
│       ├── gemini_stt.py    # Speech-to-text
│       ├── gemini_llm.py    # Agricultural advisor
│       └── elevenlabs_tts.py # Text-to-speech
├── logs/                     # Daily log files
└── pyproject.toml           # Dependencies
```

## 🔧 Environment Variables

```env
# Required
GOOGLE_API_KEY=your_google_ai_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key

# Optional
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ELEVEN_LABS_INDIAN_VOICE_ID=custom_voice_id
```

## 📊 Logging

Logs are saved to `logs/bot_YYYYMMDD.log`:

```
[2026-01-25 15:30:45] NEW VOICE MESSAGE from User
[2026-01-25 15:30:47] TRANSCRIPTION (2.1s) - Language: hi
[2026-01-25 15:30:49] GEMINI RESPONSE (1.8s)
[2026-01-25 15:30:52] COMPLETED in 7.2s total
```

## ☁️ Deploy to Render (Free)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml`
5. Add environment variables in dashboard
6. Deploy!

**Set Telegram webhook after deploy:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-app.onrender.com/api/webhook/telegram"
```

**Monitor Logs:** Render dashboard → Logs tab (real-time streaming)

## 🔄 Error Handling

- Automatic retry: 3 attempts with 5s, 10s, 15s delays
- Clear error messages for API limits and overload
- Graceful fallback when romanization fails

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 👤 Author

**Aryan Thakur** - [@Aryannnthakurrr](https://github.com/Aryannnthakurrr)
