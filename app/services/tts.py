import edge_tts
import asyncio
import os
from pathlib import Path
from datetime import datetime

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# Edge TTS voice mapping for Indian languages
# These are high-quality Microsoft neural voices
# NOTE: Punjabi (pa) is NOT supported by Edge TTS - we use Hindi as fallback
VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",      # Hindi female
    "ta": "ta-IN-PallaviNeural",    # Tamil female
    "te": "te-IN-ShrutiNeural",     # Telugu female
    "bn": "bn-IN-TanishaaNeural",   # Bengali female
    "mr": "mr-IN-AarohiNeural",     # Marathi female
    "gu": "gu-IN-DhwaniNeural",     # Gujarati female
    "kn": "kn-IN-SapnaNeural",      # Kannada female
    "ml": "ml-IN-SobhanaNeural",    # Malayalam female
    "en": "en-IN-NeerjaNeural",     # English India female
    "ur": "ur-IN-GulNeural",        # Urdu female
    # Punjabi fallback - Edge TTS doesn't support Punjabi, use Hindi
    "pa": "hi-IN-SwaraNeural",      # Fallback to Hindi (similar understanding)
}

# Alternative male voices
MALE_VOICE_MAP = {
    "hi": "hi-IN-MadhurNeural",
    "ta": "ta-IN-ValluvarNeural",
    "te": "te-IN-MohanNeural",
    "bn": "bn-IN-BashkarNeural",
    "mr": "mr-IN-ManoharNeural",
    "gu": "gu-IN-NiranjanNeural",
    "kn": "kn-IN-GaganNeural",
    "ml": "ml-IN-MidhunNeural",
    "en": "en-IN-PrabhatNeural",
    "ur": "ur-IN-SalmanNeural",
    "pa": "hi-IN-MadhurNeural",     # Fallback to Hindi male
}

print("Edge TTS initialized - supports Indian languages (Punjabi uses Hindi voice)")

async def text_to_speech(text: str, language: str = "hi", use_male_voice: bool = False) -> str:
    '''
    Convert text to speech audio using Microsoft Edge TTS
    
    Args:
        text: Text to speak
        language: Language code (hi, ta, te, bn, mr, gu, kn, ml, en, ur)
                  Note: Punjabi (pa) uses Hindi voice as fallback
        use_male_voice: Use male voice instead of female
    
    Returns:
        Path to generated audio file
    '''
    # Handle empty/None language - default to Hindi
    if not language or language.strip() == "":
        language = "hi"
        print("Warning: Empty language provided, defaulting to Hindi")
    
    # Get appropriate voice
    voice_map = MALE_VOICE_MAP if use_male_voice else VOICE_MAP
    voice = voice_map.get(language)
    
    # Fallback to Hindi if language not found
    if not voice:
        voice = VOICE_MAP.get("hi")
        print(f"Warning: No voice for '{language}', falling back to Hindi")
    
    if language == "pa":
        print("Note: Punjabi not supported by Edge TTS, using Hindi voice")
    
    # Generate unique output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = TEMP_DIR / f"output_{timestamp}.mp3"
    
    # Generate speech using Edge TTS
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        
        # Verify file was created and has content
        if output_path.exists() and output_path.stat().st_size > 0:
            return str(output_path)
        else:
            raise Exception("Generated audio file is empty")
            
    except Exception as e:
        raise Exception(f"TTS error: {str(e)}")