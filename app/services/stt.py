import whisper
import torch
import os
from dotenv import load_dotenv

load_dotenv()

# Load Whisper model once at startup
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "medium")
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Whisper model: {WHISPER_MODEL_NAME} on {device}")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME, device=device)
print("Whisper model loaded successfully")

async def transcribe_audio(audio_path: str, language: str = None) -> str:
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
        
        result = whisper_model.transcribe(
            audio_path,
            language=whisper_lang,
            fp16=torch.cuda.is_available()
        )
        
        return result["text"].strip()
        
    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")