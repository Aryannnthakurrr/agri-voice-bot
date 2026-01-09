from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice
import os
from pathlib import Path

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