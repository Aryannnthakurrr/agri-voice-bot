import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from pathlib import Path

load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
TEMP_DIR = Path("temp")
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def log(message: str):
    """Print to terminal AND save to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted, file=sys.stderr, flush=True)
    sys.stderr.flush()
    log_file = os.path.join(LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

if not ELEVEN_LABS_API_KEY:
    log("[WARNING] ELEVEN_LABS_API_KEY not found in .env")

client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

async def text_to_speech_elevenlabs(text: str) -> str:
    """Convert text to speech using ElevenLabs"""
    start_time = time.time()
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = TEMP_DIR / f"eleven_{timestamp}.mp3"
        
        default_voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Rachel
        indian_voice_id = os.getenv("ELEVEN_LABS_INDIAN_VOICE_ID", default_voice_id)
        
        log(f"           ElevenLabs: Generating ({len(text)} chars)...")
        
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=indian_voice_id, 
            model_id="eleven_multilingual_v2"
        )
        
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)
        
        elapsed = time.time() - start_time
        file_size = output_path.stat().st_size
        log(f"           ElevenLabs: Done ({file_size} bytes, {elapsed:.1f}s)")
                
        return str(output_path)

    except Exception as e:
        elapsed = time.time() - start_time
        log(f"[ERROR] ElevenLabs ({elapsed:.1f}s): {e}")
        raise Exception(f"ElevenLabs Error: {str(e)}")
