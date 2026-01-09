from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
import os
from datetime import datetime
from urllib.parse import quote

from app.services.stt import transcribe_audio
from app.services.llm import get_response
from app.services.tts import text_to_speech

router = APIRouter()

TEMP_DIR = Path("temp")

@router.post("/process-voice")
async def process_voice(
    audio: UploadFile = File(..., description="Audio file from farmer"),
    language: str = Form("hi", description="Language code (hi, ta, te, bn, mr, gu)")
):
    '''
    Process farmer's voice query and return audio response
    
    - **audio**: Audio file (mp3, wav, m4a, ogg)
    - **language**: Language code (hi=Hindi, ta=Tamil, te=Telugu, bn=Bengali, mr=Marathi, gu=Gujarati)
    '''
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = TEMP_DIR / f"input_{timestamp}_{audio.filename}"
        
        # Save uploaded audio
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Step 1: Speech to Text (Whisper)
        print(f"[1/3] Transcribing audio in language: {language}")
        transcription = await transcribe_audio(str(input_path), language)
        print(f"Transcription: {transcription}")
        
        # Step 2: Get LLM response (Qwen)
        print(f"[2/3] Getting LLM response")
        response_text = await get_response(transcription, language)
        print(f"Response: {response_text}")
        
        # Step 3: Text to Speech
        print(f"[3/3] Converting to speech")
        output_audio_path = await text_to_speech(response_text, language)
        
        # Cleanup input file
        input_path.unlink()
        
        # Return audio file with metadata in headers (URL-encoded for Unicode support)
        return FileResponse(
            output_audio_path,
            media_type="audio/mpeg",
            headers={
                "X-Transcription": quote(transcription[:200], safe=''),
                "X-Response-Text": quote(response_text[:200], safe=''),
                "X-Language": language
            },
            filename=f"response_{timestamp}.mp3"
        )
        
    except Exception as e:
        # Cleanup on error
        if input_path.exists():
            input_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-only")
async def transcribe_only(
    audio: UploadFile = File(...),
    language: str = Form("hi")
):
    '''Test endpoint: Only transcribe audio to text'''
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = TEMP_DIR / f"test_{timestamp}_{audio.filename}"
        
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        transcription = await transcribe_audio(str(input_path), language)
        
        input_path.unlink()
        
        return JSONResponse({
            "transcription": transcription,
            "language": language
        })
        
    except Exception as e:
        if input_path.exists():
            input_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-to-speech")
async def text_to_speech_endpoint(
    text: str = Form(..., description="Text to convert to speech"),
    language: str = Form("hi")
):
    '''Test endpoint: Convert text to speech'''
    try:
        output_path = await text_to_speech(text, language)
        
        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="tts_output.mp3"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm-only")
async def llm_only(
    query: str = Form(..., description="Text query"),
    language: str = Form("hi")
):
    '''Test endpoint: Get LLM response without audio'''
    try:
        response = await get_response(query, language)
        
        return JSONResponse({
            "query": query,
            "response": response,
            "language": language
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))