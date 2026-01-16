"""
Kisan Voice Bot v2 - Cloud Processing Pipeline
Gemini STT + Gemini LLM + ElevenLabs TTS
"""
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice_v2, telegram
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Create directories
Path("temp").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

app = FastAPI(
    title="Kisan Voice Bot API",
    description="Multilingual agricultural voice assistant for Indian farmers (Cloud Processing)",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(voice_v2.router, prefix="/api/v2", tags=["voice"])
app.include_router(telegram.router, prefix="/api/webhook", tags=["telegram"])

logger.info("=" * 60)
logger.info("KISAN VOICE BOT v2.0 - Cloud Processing")
logger.info("Endpoints:")
logger.info("  - Voice API: /api/v2/process-voice")
logger.info("  - Telegram:  /api/webhook/telegram")
logger.info("  - Docs:      /docs")
logger.info("=" * 60)

@app.get("/")
async def root():
    return {
        "name": "Kisan Voice Bot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}