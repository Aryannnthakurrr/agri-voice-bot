import ollama
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

async def get_response(query: str, language: str = "hi") -> str:
    '''
    Get LLM response for farmer's query
    
    Args:
        query: Transcribed query from farmer
        language: Language code for response
    
    Returns:
        Response text in same language
    '''
    try:
        # Language-specific system prompts
        language_names = {
            "hi": "हिंदी (Hindi)",
            "ta": "தமிழ் (Tamil)",
            "te": "తెలుగు (Telugu)",
            "bn": "বাংলা (Bengali)",
            "mr": "मराठी (Marathi)",
            "gu": "ગુજરાતી (Gujarati)",
            "pa": "ਪੰਜਾਬੀ (Punjabi)",
            "kn": "ಕನ್ನಡ (Kannada)",
            "ml": "മലയാളം (Malayalam)",
        }
        
        lang_name = language_names.get(language, "the user's language")
        
        system_prompt = f'''You are an expert agricultural advisor for the Kisan Call Center in India.

Your role:
- Answer farmer queries about crops, diseases, fertilizers, weather, government schemes
- Provide practical, actionable advice suitable for Indian farming conditions
- Be concise and clear - farmers need quick, useful answers
- ALWAYS respond in {lang_name} language
- Keep responses under 100 words unless more detail is specifically requested

Important:
- If you don't know something, say so honestly
- Prioritize safety - never recommend harmful practices
- Consider the Indian agricultural context and seasons
'''

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query}
            ]
        )
        
        return response['message']['content']
        
    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")