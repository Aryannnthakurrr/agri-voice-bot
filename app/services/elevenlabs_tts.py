import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from pathlib import Path
from datetime import datetime

load_dotenv()

ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
TEMP_DIR = Path("temp")

if not ELEVEN_LABS_API_KEY:
    print("Warning: ELEVEN_LABS_API_KEY not found in .env")

client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

async def text_to_speech_elevenlabs(text: str) -> str:
    '''
    Convert text to speech using Eleven Labs
    
    Args:
        text: Text to convert
    
    Returns:
        Path to audio file
    '''
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = TEMP_DIR / f"eleven_{timestamp}.mp3"
        
        # Voice Mapping Strategy
        # The user can define specific voice IDs in .env for Indian languages
        # e.g., ELEVEN_LABS_INDIAN_VOICE_ID=...
        # If not provided, we default to "Rachel" (JBFqnCBsd6RMkjVDRZzb) which is a stable default.
        # To get a natural Indian accent, the user should add a specific Indian voice from ElevenLabs Library
        # and set its ID in the .env file.
        
        default_voice_id = "JBFqnCBsd6RMkjVDRZzb" # Rachel
        indian_voice_id = os.getenv("ELEVEN_LABS_INDIAN_VOICE_ID", default_voice_id)
        
        # Simple logic: If we had language passed in, we could select based on that.
        # For now, we assume the pipeline wants the "Indian" voice for all queries since this is an Indian farmer bot.
        selected_voice_id = indian_voice_id
        
        # Audio generation
        # Using a multilingual model with the selected voice
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=selected_voice_id, 
            model_id="eleven_multilingual_v2"
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)
                
        return str(output_path)

    except Exception as e:
        print(f"ElevenLabs Error: {e}")
        raise Exception(f"ElevenLabs Error: {str(e)}")
