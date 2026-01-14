from fastapi import APIRouter, Request, BackgroundTasks
import requests
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.stt import transcribe_audio
from app.services.gemini_llm import get_gemini_response, make_pronounceable_for_tts
from app.services.elevenlabs_tts import text_to_speech_elevenlabs

router = APIRouter()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

processed_updates = set()   #duplicate guard

@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    # Safely parse JSON with error handling
    try:
        body = await request.body()
        data = await request.json()
    except Exception as e:
        print(f"❌ Failed to parse request body: {e}")
        print(f"   Raw body (first 200 bytes): {body[:200] if 'body' in dir() else 'N/A'}")
        return {"status": "error", "message": "Invalid JSON payload"}
    
    print("Incoming Telegram Update:", data)

    #Ignore non-message updates
    if "message" not in data:
        return {"status": "ignored"}

    update_id = data.get("update_id")
    if update_id in processed_updates:
        print("⚠ Duplicate update ignored:", update_id)
        return {"status": "duplicate"}
    processed_updates.add(update_id)

    # Immediately acknowledge Telegram
    # FastAPI's BackgroundTasks natively supports async functions
    background_tasks.add_task(process_update_async, data)
    return {"status": "ok"}   # <-- THIS STOPS RE-SENDING


# ================= BACKGROUND WORK =================

async def process_update_async(data):
    """Async version of process_update to properly handle async services"""
    try:
        chat_id = data["message"]["chat"]["id"]

        # 📝 Text Message
        if "text" in data["message"]:
            reply = "🎙 Please send a voice message. I will reply in voice."
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": reply
            })
            return

        # Voice Message
        if "voice" in data["message"]:
            file_id = data["message"]["voice"]["file_id"]
            
            print(f"📥 Processing voice message from chat {chat_id}, file_id: {file_id}")

            #Get file path
            file_info = requests.get(
                f"{BASE_URL}/getFile?file_id={file_id}"
            ).json()

            if not file_info.get("ok"):
                print("❌ Telegram getFile Error:", file_info)
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Audio file process nahi ho paayi. Please dubara bhejein."
                })
                return

            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            #Download audio
            os.makedirs("temp", exist_ok=True)
            local_audio = "temp/telegram_input.ogg"
            print(f"⬇️ Downloading audio from {file_url}")
            with open(local_audio, "wb") as f:
                f.write(requests.get(file_url).content)
            print(f"✅ Audio saved to {local_audio}")

            # Speech to Text (Whisper)
            print("🎤 Transcribing audio...")
            result = await transcribe_audio(local_audio)
            user_text = result["text"]
            lang = result.get("language", "hi")
            print(f"✅ Transcription: '{user_text}' (lang: {lang})")

            # GEMINI INSTANCE 1 - Agricultural Advisor
            print("🤖 Getting Gemini response...")
            raw_response = await get_gemini_response(user_text, lang)
            print(f"✅ Gemini response: '{raw_response[:100]}...'")

            # GEMINI INSTANCE 2 - TTS Optimizer (v2 pipeline)
            print("📝 Optimizing for TTS...")
            tts_ready_text = await make_pronounceable_for_tts(raw_response, lang)
            print(f"✅ TTS-ready text: '{tts_ready_text[:100]}...'")

            # Text to Speech (Eleven Labs)
            print("🔊 Generating speech...")
            output_audio = await text_to_speech_elevenlabs(tts_ready_text)
            print(f"✅ Audio generated: {output_audio}")

            # 6️⃣ Send voice back
            print("📤 Sending voice response to Telegram...")
            with open(output_audio, "rb") as audio:
                response = requests.post(
                    f"{BASE_URL}/sendVoice",
                    data={"chat_id": chat_id},
                    files={"voice": audio}
                )
                print(f"✅ Voice sent! Response: {response.status_code}")

    except Exception as e:
        import traceback
        print("❌ Error in background task:", e)
        traceback.print_exc()
        # Try to notify user about the error
        try:
            requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"❌ Sorry, there was an error processing your message: {str(e)}"
            })
        except:
            pass
