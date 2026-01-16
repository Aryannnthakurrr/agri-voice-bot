from fastapi import APIRouter, Request, BackgroundTasks
import requests
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.services.gemini_stt import transcribe_audio_gemini
from app.services.gemini_llm import get_gemini_response, make_pronounceable_for_tts
from app.services.elevenlabs_tts import text_to_speech_elevenlabs

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

processed_updates = set()

# Logs directory
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)


def log(message: str):
    """Print to terminal (stderr for visibility) AND save to log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    
    # Print to STDERR (more reliable in uvicorn)
    print(formatted, file=sys.stderr, flush=True)
    sys.stderr.flush()
    
    # Also save to file
    log_file = os.path.join(LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")


@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except Exception as e:
        log(f"[ERROR] Failed to parse request: {e}")
        return {"status": "error"}
    
    log(f"Telegram update: id={data.get('update_id')}")

    if "message" not in data:
        return {"status": "ignored"}

    update_id = data.get("update_id")
    if update_id in processed_updates:
        log(f"[WARN] Duplicate: {update_id}")
        return {"status": "duplicate"}
    processed_updates.add(update_id)

    background_tasks.add_task(process_update_async, data)
    return {"status": "ok"}


async def process_update_async(data):
    """Process voice messages using Gemini for everything"""
    chat_id = None
    total_start = time.time()
    
    try:
        chat_id = data["message"]["chat"]["id"]
        user_info = data["message"].get("from", {})
        user_name = user_info.get("first_name", "Unknown")

        # Text Message
        if "text" in data["message"]:
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": "Please send a voice message. I will reply in voice."
            })
            log(f"Text from {user_name} - sent prompt")
            return

        # Voice Message
        if "voice" in data["message"]:
            file_id = data["message"]["voice"]["file_id"]
            
            log("=" * 70)
            log(f"NEW VOICE MESSAGE from {user_name} (chat: {chat_id})")
            log("=" * 70)

            # Get file from Telegram
            file_info = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()

            if not file_info.get("ok"):
                log(f"[ERROR] Telegram getFile failed")
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Audio file process nahi ho paayi. Dubara bhejein."
                })
                return

            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            # ========== STEP 1: DOWNLOAD ==========
            step1_start = time.time()
            os.makedirs("temp", exist_ok=True)
            local_audio = "temp/telegram_input.ogg"
            log(f"[STEP 1/5] Downloading audio...")
            with open(local_audio, "wb") as f:
                f.write(requests.get(file_url).content)
            step1_time = time.time() - step1_start
            log(f"           Done in {step1_time:.1f}s")

            # ========== STEP 2: GEMINI STT ==========
            step2_start = time.time()
            log(f"[STEP 2/5] Transcribing with Gemini STT...")
            result = await transcribe_audio_gemini(local_audio)
            user_text = result["text"]
            detected_lang = result.get("language", "hi")
            step2_time = time.time() - step2_start
            
            log("-" * 70)
            log(f"TRANSCRIPTION ({step2_time:.1f}s)")
            log(f"  Language: {detected_lang}")
            log(f"  Text: {user_text}")
            log("-" * 70)

            # ========== STEP 3: GEMINI RESPONSE ==========
            step3_start = time.time()
            log(f"[STEP 3/5] Getting Gemini response...")
            try:
                raw_response = await get_gemini_response(user_text, detected_lang)
            except Exception as e:
                error_msg = str(e)
                log(f"[ERROR] Gemini failed: {error_msg}")
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"Sorry, {error_msg}"
                })
                return
            step3_time = time.time() - step3_start
            
            log("-" * 70)
            log(f"GEMINI RESPONSE ({step3_time:.1f}s)")
            log(f"  {raw_response}")
            log("-" * 70)

            # ========== STEP 4: TTS PREPARATION ==========
            step4_start = time.time()
            log(f"[STEP 4/5] Preparing text for TTS...")
            tts_ready_text = await make_pronounceable_for_tts(raw_response, detected_lang)
            step4_time = time.time() - step4_start
            
            was_romanized = (tts_ready_text != raw_response)
            
            log("-" * 70)
            log(f"TTS PREP ({step4_time:.1f}s)")
            log(f"  Romanized: {'YES' if was_romanized else 'NO'}")
            log(f"  Text: {tts_ready_text}")
            log("-" * 70)

            # ========== STEP 5: AUDIO GENERATION ==========
            step5_start = time.time()
            log(f"[STEP 5/5] Generating audio with ElevenLabs...")
            output_audio = await text_to_speech_elevenlabs(tts_ready_text)
            step5_time = time.time() - step5_start
            log(f"           Done in {step5_time:.1f}s")

            # Send voice back
            log(f"Sending voice to Telegram...")
            send_start = time.time()
            with open(output_audio, "rb") as audio:
                response = requests.post(
                    f"{BASE_URL}/sendVoice",
                    data={"chat_id": chat_id},
                    files={"voice": audio}
                )
            send_time = time.time() - send_start
            
            total_time = time.time() - total_start
            
            if response.status_code == 200:
                log(f"[SUCCESS] Voice sent to {user_name}")
            else:
                log(f"[ERROR] Send failed: {response.status_code}")
            
            log("=" * 70)
            log(f"COMPLETED in {total_time:.1f}s total")
            log(f"  Step 1 (Download):      {step1_time:.1f}s")
            log(f"  Step 2 (Gemini STT):    {step2_time:.1f}s")
            log(f"  Step 3 (Gemini LLM):    {step3_time:.1f}s")
            log(f"  Step 4 (TTS Prep):      {step4_time:.1f}s")
            log(f"  Step 5 (ElevenLabs):    {step5_time:.1f}s")
            log(f"  Send to Telegram:       {send_time:.1f}s")
            log("=" * 70)

    except Exception as e:
        import traceback
        log(f"[ERROR] {e}")
        log(traceback.format_exc())
        try:
            if chat_id:
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"Sorry, error: {str(e)}"
                })
        except:
            pass
