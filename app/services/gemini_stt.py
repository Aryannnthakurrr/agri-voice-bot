"""
Gemini-based Speech-to-Text Service
Uses Gemini's multimodal capabilities to transcribe audio.
"""
from google import genai
from google.genai import types
import os
import sys
import time
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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

if not GOOGLE_API_KEY:
    log("[WARNING] GOOGLE_API_KEY not found - Gemini STT won't work")

# Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# Retry delays
RETRY_DELAYS = [5, 10, 15]

# Language code mapping
LANGUAGE_CODE_MAP = {
    "hindi": "hi", "tamil": "ta", "telugu": "te", "bengali": "bn",
    "marathi": "mr", "gujarati": "gu", "punjabi": "pa", "kannada": "kn",
    "malayalam": "ml", "urdu": "ur", "english": "en", "bhojpuri": "bh",
    "nepali": "ne", "odia": "or", "assamese": "as",
}


def _parse_language_code(lang_text: str) -> str:
    """Convert language name to code"""
    lang_lower = lang_text.lower().strip()
    for name, code in LANGUAGE_CODE_MAP.items():
        if name in lang_lower:
            return code
    return "hi"


async def transcribe_audio_gemini(audio_path: str) -> dict:
    """
    Transcribe audio using Gemini's multimodal capabilities.
    
    Args:
        audio_path: Path to audio file (ogg, mp3, wav, etc.)
    
    Returns:
        dict with "text" and "language"
    """
    start_time = time.time()
    last_error = None
    
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise Exception(f"Audio file not found: {audio_path}")
            
            # Determine MIME type
            suffix = audio_path.suffix.lower()
            mime_types = {
                ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
                ".wav": "audio/wav", ".m4a": "audio/mp4", ".webm": "audio/webm",
            }
            mime_type = mime_types.get(suffix, "audio/ogg")
            
            # Read audio data
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            
            audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime_type)
            
            system_instruction = """You are an expert audio transcriber for Indian languages.

Your task:
1. Listen to the audio carefully
2. Transcribe EXACTLY what is spoken
3. Detect the language AND dialect

Output format:
LANGUAGE: [language name]
TEXT: [transcribed text]

Rules:
- Transcribe in the ORIGINAL script
- Do NOT translate to English
- For Hindi/Hinglish, keep English words as-is
- IMPORTANT: Distinguish between Hindi, Urdu, and Punjabi carefully:
  * Hindi: Uses Devanagari script, common in North India
  * Urdu: Uses Arabic/Persian-style vocabulary, more formal
  * Punjabi: Distinct Punjabi vocabulary and accent
- Preserve the exact dialect spoken (e.g., Bhojpuri vs Hindi, Haryanvi vs Hindi)"""

            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=[audio_part, "Transcribe this audio."],
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            
            result_text = response.text.strip()
            
            # Parse response
            language_code = "hi"
            transcription = result_text
            
            if "LANGUAGE:" in result_text and "TEXT:" in result_text:
                for line in result_text.split("\n"):
                    if line.startswith("LANGUAGE:"):
                        language_code = _parse_language_code(line.replace("LANGUAGE:", ""))
                    elif line.startswith("TEXT:"):
                        transcription = line.replace("TEXT:", "").strip()
            
            elapsed = time.time() - start_time
            log(f"           Gemini STT: Transcribed in {elapsed:.1f}s (lang: {language_code})")
            
            return {"text": transcription, "language": language_code}
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            if "429" in str(e) or "quota" in error_str:
                error_type = "API_LIMIT"
            elif "503" in str(e) or "overloaded" in error_str:
                error_type = "OVERLOADED"
            else:
                error_type = "ERROR"
            
            if attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                log(f"           Gemini STT: Attempt {attempt + 1} failed ({error_type}), retry in {delay}s...")
                await asyncio.sleep(delay)
            else:
                log(f"           Gemini STT: All attempts failed ({error_type})")
    
    elapsed = time.time() - start_time
    error_msg = str(last_error)
    
    if "429" in error_msg or "quota" in error_msg.lower():
        raise Exception(f"Gemini API limit exceeded. Try again later. ({elapsed:.1f}s)")
    elif "503" in error_msg or "overload" in error_msg.lower():
        raise Exception(f"Gemini is overloaded. Please try again. ({elapsed:.1f}s)")
    else:
        raise Exception(f"Transcription failed: {error_msg} ({elapsed:.1f}s)")
