from google import genai
from google.genai import types
import os
import sys
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Logging setup
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def log(message: str):
    """Print to terminal AND save to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted, flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    log_file = os.path.join(LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

if not GOOGLE_API_KEY:
    log("[WARNING] GOOGLE_API_KEY not found in .env")

# Create Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# Retry delays in seconds
RETRY_DELAYS = [5, 10, 15]

# Language mapping
LANGUAGE_NAMES = {
    "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "bn": "Bengali",
    "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi", "kn": "Kannada",
    "ml": "Malayalam", "ur": "Urdu", "bh": "Bhojpuri", "mai": "Maithili",
    "raj": "Rajasthani", "ne": "Nepali", "or": "Odia", "as": "Assamese",
    "ks": "Kashmiri", "sd": "Sindhi",
}

DEVANAGARI_SCRIPT_LANGS = {"hi", "mr", "ne", "bh", "mai", "raj", "ks", "sd"}
NEEDS_ROMANIZATION_LANGS = {"ta", "te", "kn", "ml", "bn", "gu", "pa", "or", "as"}


def _is_devanagari_script(text: str) -> bool:
    if not text:
        return False
    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    non_space = sum(1 for c in text if not c.isspace())
    return (devanagari_count / non_space) > 0.3 if non_space else False


def _is_already_romanized(text: str) -> bool:
    if not text:
        return True
    ascii_count = sum(1 for c in text if c.isascii())
    return (ascii_count / len(text)) > 0.9


def _parse_gemini_error(error: Exception) -> str:
    """Parse Gemini error to give user-friendly message"""
    error_str = str(error).lower()
    
    if "429" in str(error) or "resource_exhausted" in error_str or "quota" in error_str:
        return "API_LIMIT_EXCEEDED"
    elif "overloaded" in error_str or "503" in str(error) or "unavailable" in error_str:
        return "MODEL_OVERLOADED"
    elif "invalid" in error_str or "api_key" in error_str:
        return "INVALID_API_KEY"
    elif "timeout" in error_str:
        return "TIMEOUT"
    else:
        return "UNKNOWN_ERROR"


async def _call_gemini_with_retry(contents: str, system_instruction: str, purpose: str) -> str:
    """
    Call Gemini API with retry logic.
    Retries 3 times with delays of 5s, 10s, 15s.
    
    Args:
        contents: The user prompt
        system_instruction: System prompt for Gemini
        purpose: What this call is for (for logging)
    
    Returns:
        Response text
    
    Raises:
        Exception with clear error message if all retries fail
    """
    last_error = None
    last_error_type = None
    
    for attempt in range(len(RETRY_DELAYS) + 1):  # 4 attempts total (initial + 3 retries)
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            
            if response.text and response.text.strip():
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            last_error = e
            last_error_type = _parse_gemini_error(e)
            
            if attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                log(f"           [{purpose}] Attempt {attempt + 1} failed: {last_error_type}")
                log(f"           [{purpose}] Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                # All retries exhausted
                log(f"           [{purpose}] All {len(RETRY_DELAYS) + 1} attempts failed")
    
    # Generate clear error message
    if last_error_type == "API_LIMIT_EXCEEDED":
        error_msg = "Gemini API limit exceeded. Your daily quota may be exhausted. Try again later or upgrade your plan."
    elif last_error_type == "MODEL_OVERLOADED":
        error_msg = "Gemini model is currently overloaded. Please try again in a few minutes."
    elif last_error_type == "INVALID_API_KEY":
        error_msg = "Invalid Gemini API key. Please check your GOOGLE_API_KEY in .env file."
    elif last_error_type == "TIMEOUT":
        error_msg = "Gemini request timed out. Please try again."
    else:
        error_msg = f"Gemini error: {str(last_error)}"
    
    raise Exception(error_msg)


async def get_gemini_response(query: str, language_code: str = "hi") -> str:
    """
    GEMINI 1: Agricultural Advisor
    Get farming advice in the user's language.
    Returns tuple: (response_text, time_taken_seconds)
    """
    start_time = time.time()
    
    try:
        lang_name = LANGUAGE_NAMES.get(language_code, "the user's language")
        
        if language_code == "hi":
            style_note = "Use casual Hinglish."
        elif language_code in DEVANAGARI_SCRIPT_LANGS:
            style_note = f"Respond naturally in {lang_name}."
        else:
            style_note = f"Use natural {lang_name}."
        
        system_prompt = f'''You are an agricultural advisor for Indian farmers.
Respond in {lang_name}. {style_note}
Keep answers SHORT (2-3 sentences) for voice output.'''
        
        result = await _call_gemini_with_retry(
            contents=query,
            system_instruction=system_prompt,
            purpose="Agricultural Advisor"
        )
        
        elapsed = time.time() - start_time
        log(f"           Gemini response received in {elapsed:.1f}s")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"           [ERROR] Gemini failed after {elapsed:.1f}s: {e}")
        raise


async def make_pronounceable_for_tts(text: str, language_code: str = "hi") -> str:
    """
    GEMINI 2: TTS Optimizer
    Romanize non-Devanagari scripts for TTS.
    """
    start_time = time.time()
    
    try:
        # Already ASCII?
        if _is_already_romanized(text):
            log(f"           TTS: Already ASCII, no change needed (0.0s)")
            return text
        
        # Devanagari? ElevenLabs handles it
        if language_code in DEVANAGARI_SCRIPT_LANGS or _is_devanagari_script(text):
            log(f"           TTS: Devanagari ({language_code}), ElevenLabs handles it (0.0s)")
            return text
        
        # Other scripts need romanization
        log(f"           TTS: Romanizing {language_code} for TTS...")
        
        lang_name = LANGUAGE_NAMES.get(language_code, language_code)
        
        system_prompt = f'''Convert {lang_name} to romanized pronunciation.
Do NOT translate. Write phonetically in English letters.
Output ONLY the romanized text.'''

        result = await _call_gemini_with_retry(
            contents=f"Romanize: {text}",
            system_instruction=system_prompt,
            purpose="TTS Romanizer"
        )
        
        elapsed = time.time() - start_time
        
        if len(result) > 0:
            ascii_ratio = sum(1 for c in result if c.isascii()) / len(result)
            if ascii_ratio > 0.8:
                log(f"           TTS: Romanization done ({ascii_ratio:.0%} ASCII) in {elapsed:.1f}s")
                return result
        
        log(f"           TTS: Romanization failed, using original ({elapsed:.1f}s)")
        return text
        
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"           [ERROR] TTS Romanizer failed after {elapsed:.1f}s: {e}")
        # Return original text on error - don't break the pipeline
        return text
