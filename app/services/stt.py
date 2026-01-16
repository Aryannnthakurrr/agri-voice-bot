import whisper
import torch
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Load Whisper model once at startup
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "medium")
device = "cuda" if torch.cuda.is_available() else "cpu"

logger.info(f"Loading Whisper model: {WHISPER_MODEL_NAME} on {device}")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME, device=device)
logger.info("Whisper model loaded successfully")

async def transcribe_audio(audio_path: str, language: str = None) -> dict:
    '''
    Transcribe audio file to text using Whisper
    
    Args:
        audio_path: Path to audio file
        language: Language code (hi, ta, te, etc.) or None for auto-detect
    
    Returns:
        Transcribed text
    '''
    try:
        # Map language codes to Whisper format
        language_map = {
            "hi": "hi",  # Hindi
            "ta": "ta",  # Tamil
            "te": "te",  # Telugu
            "bn": "bn",  # Bengali
            "mr": "mr",  # Marathi
            "gu": "gu",  # Gujarati
            "pa": "pa",  # Punjabi
            "kn": "kn",  # Kannada
            "ml": "ml",  # Malayalam
        }
        
        whisper_lang = language_map.get(language, language) if language else None
        
        logger.debug(f"Transcribing: {audio_path}, lang_hint={whisper_lang}")
        
        result = whisper_model.transcribe(
            audio_path,
            language=whisper_lang,
            fp16=torch.cuda.is_available()
        )
        
        transcription = result["text"].strip()
        detected_lang = result["language"]
        
        logger.debug(f"Transcription complete: lang={detected_lang}, len={len(transcription)}")
        
        return {
            "text": transcription,
            "language": detected_lang
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise Exception(f"Transcription error: {str(e)}")