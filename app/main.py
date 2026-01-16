# Configure logging FIRST, before any other imports
import logging
import sys

# Set up logging to print to stdout/terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override any existing configuration
)

# Now import everything else
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice, voice_v2, telegram
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Create temp directory
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Kisan Voice Bot API",
    description="Multilingual agricultural assistance bot for Indian farmers",
    version="1.0.0"
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
app.include_router(voice.router, prefix="/api/v1", tags=["voice"])
app.include_router(voice_v2.router, prefix="/api/v2", tags=["voice-v2"])
app.include_router(telegram.router, prefix="/api/webhook", tags=["telegram"])

logger.info("=" * 60)
logger.info("KISAN VOICE BOT API STARTED")
logger.info("Endpoints:")
logger.info("  - Telegram webhook: /api/webhook/telegram")
logger.info("  - Voice API v1: /api/v1/process-voice")
logger.info("  - Voice API v2: /api/v2/process-voice")
logger.info("  - Docs: /docs")
logger.info("=" * 60)

@app.get("/")
async def root():
    return {
        "message": "Kisan Voice Bot API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}