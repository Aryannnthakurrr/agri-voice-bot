import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env")

# Configure Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# Model Candidate List
# Gemini 2.5 Flash is preferred for better performance
MODEL_CANDIDATES = [
    "gemini-2.5-flash", 
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash-exp",
    "models/gemini-1.5-flash",
    "models/gemini-2.5-flash",
]

# Language mapping
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "kn": "Kannada",
    "ml": "Malayalam",
}


async def get_gemini_response(query: str, language_code: str = "hi") -> str:
    '''
    GEMINI INSTANCE 1: Agricultural Advisor
    
    This instance focuses ONLY on providing agricultural advice.
    It does NOT worry about romanization or TTS optimization.
    
    Args:
        query: User query about farming
        language_code: Detected language code
    
    Returns:
        Response text in the user's language (may be in native script)
    '''
    try:
        lang_name = LANGUAGE_NAMES.get(language_code, "the user's language")
        
        # Simple, focused prompt - just agricultural advice
        # Let Gemini respond naturally in the target language
        if language_code == "hi":
            style_note = "Use a casual, conversational tone (Hinglish is fine)."
        else:
            style_note = f"Use a natural, conversational tone in {lang_name}."
        
        system_prompt = f'''You are an expert agricultural advisor for Indian farmers.

Your role:
- Answer queries about farming, crops, diseases, pest control, irrigation, weather, etc.
- Be helpful, practical, and concise
- {style_note}
- Keep answers short (2-3 sentences) for voice output
- Respond in {lang_name}
'''
        
        # Try models in order until one works
        last_error = None
        for model_name in MODEL_CANDIDATES:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                response = await model.generate_content_async(query)
                return response.text.strip()
            except Exception as e:
                last_error = e
                continue
        
        # If all models fail
        print("Error: All model candidates failed for agricultural advisor.")
        raise last_error
        
    except Exception as e:
        print(f"Gemini Agricultural Advisor Error: {e}")
        raise Exception(f"Gemini Error: {str(e)}")


async def make_pronounceable_for_tts(text: str, language_code: str = "hi") -> str:
    '''
    GEMINI INSTANCE 2: TTS Optimizer
    
    This instance's ONLY job is to convert text into a form that sounds good
    when spoken by ElevenLabs TTS. It converts native scripts to romanized/
    phonetic pronunciation.
    
    Args:
        text: Text from the agricultural advisor (may be in native script)
        language_code: Language code
    
    Returns:
        Pronounceable romanized text optimized for TTS
    '''
    try:
        # Check if text is already romanized (mostly ASCII)
        if len(text) > 0:
            ascii_count = sum(1 for c in text if c.isascii())
            ascii_ratio = ascii_count / len(text)
            
            # If already >90% ASCII, it's likely already romanized
            if ascii_ratio > 0.9:
                print(f"Text already romanized ({ascii_ratio:.1%} ASCII), skipping optimization")
                return text
        
        lang_name = LANGUAGE_NAMES.get(language_code, language_code)
        
        # This prompt is specifically designed to make text pronounceable
        system_prompt = f'''You are a pronunciation specialist for text-to-speech systems.

Your ONLY job: Convert {lang_name} text into romanized script (Latin/English letters) that sounds natural when read aloud by a TTS engine.

Rules:
- Do NOT translate to English meaning
- your role is to transform the text in such a manner that its easy for eleven labs to pronounce it in native indian sounding languages
- Make it sound natural for an Indian accent
- Example: "नमस्ते किसान भाई" → "Namaste kisaan bhai"
- Example: "தமிழ்" → "Tamil"
-Be careful when distinguishing between hindi and urdu when in doubt go with hindi

Output ONLY the romanized text, nothing else.'''

        prompt = f"Convert this to pronounceable romanized text:\n\n{text}"
        
        # Try models in order
        last_error = None
        for model_name in MODEL_CANDIDATES:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                response = await model.generate_content_async(prompt)
                result = response.text.strip()
                
                # Validate: Result should be mostly ASCII
                if len(result) > 0:
                    ascii_count = sum(1 for c in result if c.isascii())
                    ascii_ratio = ascii_count / len(result)
                    
                    # If >80% ASCII, accept it
                    if ascii_ratio > 0.8:
                        print(f"TTS Optimization successful: {ascii_ratio:.1%} ASCII")
                        return result
                    else:
                        print(f"TTS Optimization produced non-ASCII text ({ascii_ratio:.1%}), trying next model...")
                        continue
                
            except Exception as e:
                print(f"TTS Optimization error with {model_name}: {e}")
                last_error = e
                continue
        
        # If all models fail, return original
        print("Warning: TTS optimization failed with all models. Using original text.")
        return text
        
    except Exception as e:
        print(f"TTS Optimizer Error: {e}")
        # On error, return original text so pipeline doesn't break
        return text
