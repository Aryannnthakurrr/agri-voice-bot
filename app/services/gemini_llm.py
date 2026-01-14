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

# Language mapping - expanded for dialects
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
    "ur": "Urdu",
    "bh": "Bhojpuri",
    "mai": "Maithili",
    "raj": "Rajasthani",
    "ne": "Nepali",
    "or": "Odia",
    "as": "Assamese",
    "ks": "Kashmiri",
    "sd": "Sindhi",
}

# Languages that use Devanagari or similar scripts that ElevenLabs handles well
# These do NOT need romanization - send directly to TTS
DEVANAGARI_SCRIPT_LANGS = {
    "hi",    # Hindi
    "mr",    # Marathi
    "ne",    # Nepali
    "bh",    # Bhojpuri
    "mai",   # Maithili
    "raj",   # Rajasthani
    "ks",    # Kashmiri
    "sd",    # Sindhi (Devanagari variant)
}

# Languages that need romanization for TTS (non-Latin, non-Devanagari scripts)
NEEDS_ROMANIZATION_LANGS = {
    "ta",    # Tamil - Tamil script
    "te",    # Telugu - Telugu script
    "kn",    # Kannada - Kannada script
    "ml",    # Malayalam - Malayalam script
    "bn",    # Bengali - Bengali script
    "gu",    # Gujarati - Gujarati script
    "pa",    # Punjabi - Gurmukhi script
    "or",    # Odia - Odia script
    "as",    # Assamese - Assamese script
}


def _is_devanagari_script(text: str) -> bool:
    """
    Check if text contains Devanagari script characters.
    Devanagari Unicode range: U+0900 to U+097F
    """
    if not text:
        return False
    
    devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    # Consider it Devanagari if >30% of non-space characters are Devanagari
    non_space = sum(1 for c in text if not c.isspace())
    if non_space == 0:
        return False
    
    return (devanagari_count / non_space) > 0.3


def _is_already_romanized(text: str) -> bool:
    """Check if text is already in Latin/ASCII script."""
    if not text:
        return True
    
    ascii_count = sum(1 for c in text if c.isascii())
    return (ascii_count / len(text)) > 0.9


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
        
        # Dialect-aware style guidance
        if language_code == "hi":
            style_note = "Use a casual, conversational tone. Hinglish (Hindi+English mix) is perfectly fine and often preferred."
        elif language_code in DEVANAGARI_SCRIPT_LANGS:
            style_note = f"Respond naturally in {lang_name}. Pay attention to the specific dialect - Bhojpuri, Maithili, etc. have distinct vocabulary and expressions."
        else:
            style_note = f"Use a natural, conversational tone in {lang_name}."
        
        system_prompt = f'''You are an expert agricultural advisor for Indian farmers.

CRITICAL LANGUAGE RULES:
- Detect and respond in the EXACT dialect/language the farmer speaks
- Many Indian languages share similarities but are DISTINCT: Hindi ≠ Bhojpuri ≠ Maithili ≠ Marathi
- Listen for dialect markers and vocabulary differences
- When in doubt between Hindi/Urdu, lean towards Hindi vocabulary
- {style_note}

Your role:
- Answer queries about farming, crops, diseases, pest control, irrigation, weather, government schemes, etc.
- Be helpful, practical, and concise
- Keep answers short (2-3 sentences max) - this is for voice output
- Respond in {lang_name} using the appropriate script
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
    
    Converts text to a form optimized for ElevenLabs TTS.
    
    KEY LOGIC:
    - Devanagari scripts (Hindi, Bhojpuri, Maithili, Marathi): SKIP romanization
      → ElevenLabs handles these well natively
    - Dravidian/other scripts (Tamil, Telugu, Bengali, etc.): ROMANIZE
      → These need Latin transliteration for good TTS output
    
    Args:
        text: Text from the agricultural advisor (may be in native script)
        language_code: Language code
    
    Returns:
        Text optimized for TTS (romanized if needed, or original if Devanagari)
    '''
    try:
        # CASE 1: Already romanized (mostly ASCII) - return as-is
        if _is_already_romanized(text):
            print(f"✅ Text already romanized, sending directly to TTS")
            return text
        
        # CASE 2: Devanagari script (Hindi, Bhojpuri, Maithili, etc.)
        # ElevenLabs handles these well - NO romanization needed
        if language_code in DEVANAGARI_SCRIPT_LANGS or _is_devanagari_script(text):
            print(f"✅ Devanagari script detected ({language_code}), skipping romanization - ElevenLabs handles natively")
            return text
        
        # CASE 3: Other scripts (Tamil, Telugu, Bengali, etc.)
        # These NEED romanization for good TTS output
        print(f"🔄 Non-Devanagari script ({language_code}), romanizing for TTS...")
        
        lang_name = LANGUAGE_NAMES.get(language_code, language_code)
        
        system_prompt = f'''You are a pronunciation specialist for Indian language text-to-speech.

Your ONLY job: Convert {lang_name} text (in native script) into romanized pronunciation that sounds natural when spoken.

Rules:
- Do NOT translate to English - keep the SAME meaning
- Write phonetically in Latin/English letters
- Make it sound natural for an Indian accent
- Preserve the rhythm and flow of the original

Examples:
- Tamil: "வணக்கம்" → "Vanakkam"
- Telugu: "నమస్కారం" → "Namaskaram"  
- Bengali: "নমস্কার" → "Nomoshkar"
- Kannada: "ನಮಸ್ಕಾರ" → "Namaskara"

Output ONLY the romanized text, nothing else.'''

        prompt = f"Romanize this {lang_name} text for pronunciation:\n\n{text}"
        
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
                    
                    if ascii_ratio > 0.8:
                        print(f"✅ Romanization successful: {ascii_ratio:.1%} ASCII")
                        return result
                    else:
                        print(f"⚠️ Romanization still has non-ASCII ({ascii_ratio:.1%}), trying next model...")
                        continue
                
            except Exception as e:
                print(f"Romanization error with {model_name}: {e}")
                last_error = e
                continue
        
        # If all models fail, return original
        print("⚠️ Romanization failed with all models. Using original text.")
        return text
        
    except Exception as e:
        print(f"TTS Optimizer Error: {e}")
        # On error, return original text so pipeline doesn't break
        return text
