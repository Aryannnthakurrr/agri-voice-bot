import edge_tts
import asyncio
import os

TEMP_DIR = "temp"

async def test_voice(text, voice, lang):
    try:
        output_path = f"{TEMP_DIR}/test_{lang}.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        size = os.path.getsize(output_path)
        print(f"✅ {lang}: {voice} - {size} bytes")
        return True
    except Exception as e:
        print(f"❌ {lang}: {voice} - {str(e)}")
        return False

async def main():
    tests = [
        ("नमस्ते किसान भाई", "hi-IN-SwaraNeural", "hi"),
        ("வணக்கம் விவசாயி", "ta-IN-PallaviNeural", "ta"),
        ("నమస్తే రైతు", "te-IN-ShrutiNeural", "te"),
        ("নমস্কার কৃষক", "bn-IN-TanishaaNeural", "bn"),
        ("નમસ્તે ખેડૂત", "gu-IN-DhwaniNeural", "gu"),
        ("नमस्कार शेतकरी", "mr-IN-AarohiNeural", "mr"),
        ("ನಮಸ್ತೆ ರೈತ", "kn-IN-SapnaNeural", "kn"),
        ("നമസ്കാരം കർഷകൻ", "ml-IN-SobhanaNeural", "ml"),
        ("Hello farmer", "en-IN-NeerjaNeural", "en"),
    ]
    
    print("Testing Edge TTS voices...\n")
    for text, voice, lang in tests:
        await test_voice(text, voice, lang)

asyncio.run(main())
