from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import os

from app.services.gemini_stt import transcribe_audio_gemini
from app.services.gemini_llm import get_gemini_response, make_pronounceable_for_tts
from app.services.elevenlabs_tts import text_to_speech_elevenlabs

router = APIRouter()

TEMP_DIR = Path("temp")
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def log(message: str):
    """Print to terminal AND save to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted, file=sys.stderr, flush=True)
    sys.stderr.flush()
    log_file = os.path.join(LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")


@router.post("/process-voice")
async def process_voice_v2(
    audio: UploadFile = File(..., description="Audio file from farmer")
):
    '''
    V2 Pipeline - Uses Gemini for EVERYTHING:
    - Gemini STT: Audio transcription (replaces Whisper)
    - Gemini Instance 1: Agricultural advice
    - Gemini Instance 2: TTS optimization (romanization)
    - ElevenLabs: Text-to-speech
    '''
    input_path = None
    total_start = time.time()
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = TEMP_DIR / f"v2_input_{timestamp}_{audio.filename}"
        
        # Save uploaded audio
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        log("=" * 70)
        log(f"V2 VOICE PROCESSING - {audio.filename}")
        log("=" * 70)
        
        # Step 1: Gemini STT (replaces Whisper)
        step1_start = time.time()
        log(f"[STEP 1/4] Transcribing with Gemini STT...")
        transcription_result = await transcribe_audio_gemini(str(input_path))
        transcription = transcription_result["text"]
        detected_language = transcription_result.get("language", "hi")
        step1_time = time.time() - step1_start
        
        log("-" * 70)
        log(f"TRANSCRIPTION ({step1_time:.1f}s)")
        log(f"  Language: {detected_language}")
        log(f"  Text: {transcription}")
        log("-" * 70)
        
        # Step 2: Gemini Agricultural Advisor
        step2_start = time.time()
        log(f"[STEP 2/4] Getting Gemini response...")
        raw_response = await get_gemini_response(transcription, detected_language)
        step2_time = time.time() - step2_start
        
        log("-" * 70)
        log(f"GEMINI RESPONSE ({step2_time:.1f}s)")
        log(f"  {raw_response}")
        log("-" * 70)
        
        # Step 3: Gemini TTS Optimizer
        step3_start = time.time()
        log(f"[STEP 3/4] Optimizing for TTS...")
        tts_ready_text = await make_pronounceable_for_tts(raw_response, detected_language)
        step3_time = time.time() - step3_start
        
        was_romanized = (tts_ready_text != raw_response)
        log("-" * 70)
        log(f"TTS PREP ({step3_time:.1f}s)")
        log(f"  Romanized: {'YES' if was_romanized else 'NO'}")
        log(f"  Text: {tts_ready_text}")
        log("-" * 70)
        
        # Step 4: ElevenLabs TTS
        step4_start = time.time()
        log(f"[STEP 4/4] Generating speech with ElevenLabs...")
        output_audio_path = await text_to_speech_elevenlabs(tts_ready_text)
        step4_time = time.time() - step4_start
        log(f"           Done in {step4_time:.1f}s")
        
        # Cleanup input file
        input_path.unlink()
        
        total_time = time.time() - total_start
        
        log("=" * 70)
        log(f"V2 COMPLETED in {total_time:.1f}s")
        log(f"  Step 1 (Gemini STT):    {step1_time:.1f}s")
        log(f"  Step 2 (Gemini LLM):    {step2_time:.1f}s")
        log(f"  Step 3 (TTS Prep):      {step3_time:.1f}s")
        log(f"  Step 4 (ElevenLabs):    {step4_time:.1f}s")
        log("=" * 70)
        
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
        if input_path and input_path.exists():
            input_path.unlink()
        log(f"[ERROR] V2 pipeline: {e}")
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
        log(f"[Test] Optimizing text for TTS: {text}")
        tts_ready_text = await make_pronounceable_for_tts(text)
        log(f"[Test] Optimized result: {tts_ready_text}")
        
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


@router.post("/test-gemini-stt")
async def test_gemini_stt(
    audio: UploadFile = File(..., description="Audio file to transcribe")
):
    '''Test endpoint for Gemini STT only'''
    input_path = None
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = TEMP_DIR / f"stt_test_{timestamp}_{audio.filename}"
        
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        start = time.time()
        result = await transcribe_audio_gemini(str(input_path))
        elapsed = time.time() - start
        
        input_path.unlink()
        
        return JSONResponse({
            "text": result["text"],
            "language": result["language"],
            "time_seconds": round(elapsed, 2)
        })
        
    except Exception as e:
        if input_path and input_path.exists():
            input_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))
