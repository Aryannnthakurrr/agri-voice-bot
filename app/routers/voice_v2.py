from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from app.services.stt import transcribe_audio
from app.services.gemini_llm import get_gemini_response, make_pronounceable_for_tts
from app.services.elevenlabs_tts import text_to_speech_elevenlabs

router = APIRouter()

TEMP_DIR = Path("temp")

@router.post("/process-voice")
async def process_voice_v2(
    audio: UploadFile = File(..., description="Audio file from farmer")
):
    '''
    Process farmer's voice query using TWO-GEMINI architecture:
    - Gemini Instance 1: Agricultural advice
    - Gemini Instance 2: TTS optimization (romanization)
    '''
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = TEMP_DIR / f"v2_input_{timestamp}_{audio.filename}"
        
        # Save uploaded audio
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Step 1: Speech to Text (Whisper) - Auto-detect language
        print(f"[STT] Transcribing with Whisper...")
        transcription_result = await transcribe_audio(str(input_path))
        transcription = transcription_result["text"]
        detected_language = transcription_result.get("language", "hi")
        print(f"[STT] Complete: '{transcription[:50]}...' (Lang: {detected_language})")
        
        # Step 2: GEMINI INSTANCE 1 - Agricultural Advisor
        print(f"[Gemini-1] Getting agricultural advice...")
        raw_response = await get_gemini_response(transcription, detected_language)
        print(f"[Gemini-1] Response: '{raw_response[:50]}...'")
        
        # Step 3: GEMINI INSTANCE 2 - TTS Optimizer
        print(f"[Gemini-2] Optimizing for pronunciation...")
        tts_ready_text = await make_pronounceable_for_tts(raw_response, detected_language)
        print(f"[Gemini-2] Optimized: '{tts_ready_text[:50]}...'")
        
        # Step 4: Text to Speech (Eleven Labs)
        print(f"[TTS] Generating speech with Eleven Labs...")
        output_audio_path = await text_to_speech_elevenlabs(tts_ready_text)
        print(f"[TTS] Audio generated successfully")
        
        # Cleanup input file
        input_path.unlink()
        
        # Return audio file with metadata
        return FileResponse(
            output_audio_path,
            media_type="audio/mpeg",
            headers={
                "X-Transcription": quote(transcription[:200], safe=''),
                "X-Raw-Response": quote(raw_response[:200], safe=''),
                "X-TTS-Text": quote(tts_ready_text[:200], safe=''),
                "X-Language": detected_language
            },
            filename=f"v2_response_{timestamp}.mp3"
        )
        
    except Exception as e:
        # Cleanup on error
        if input_path.exists():
            input_path.unlink()
        print(f"Error in v2 pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-gemini")
async def test_gemini(
    query: str = Form(...),
    language: str = Form("hi")
):
    '''Test endpoint for Gemini response'''
    try:
        response = await get_gemini_response(query, language)
        return JSONResponse({
            "query": query,
            "response": response,
            "language": language
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-elevenlabs")
async def test_elevenlabs(
    text: str = Form(...)
):
    '''Test endpoint for Eleven Labs TTS with pronunciation optimization'''
    try:
        # Use Gemini Instance 2 to optimize for TTS
        print(f"[Gemini-2] Optimizing text for TTS: {text}")
        tts_ready_text = await make_pronounceable_for_tts(text)
        print(f"[Gemini-2] Optimized result: {tts_ready_text}")
        
        output_path = await text_to_speech_elevenlabs(tts_ready_text)
        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            headers={
                "X-Original-Text": quote(text[:200], safe=''),
                "X-Optimized-Text": quote(tts_ready_text[:200], safe='')
            },
            filename="test_elevenlabs.mp3"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
