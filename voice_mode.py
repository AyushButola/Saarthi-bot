import json, logging, requests
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from auth_manage import get_auth_header
from google.generativeai import GenerativeModel
import google.generativeai as genai
import os


# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = GenerativeModel("gemini-2.5-flash")

API_URL = "https://saarthi-backend-xv47.onrender.com/api/reports/"

# ===========================================================
# VOICE → REPORT FLOW
# ===========================================================

# def voice_to_text(file_path: str) -> str:
#     from pydub import AudioSegment
#     import speech_recognition as sr
#     sound = AudioSegment.from_file(file_path)
#     wav_path = file_path.replace(".ogg", ".wav")
#     sound.export(wav_path, format="wav")
#     r = sr.Recognizer()
#     with sr.AudioFile(wav_path) as src:
#         audio = r.record(src)
#     try:
#         return r.recognize_google(audio)
#     except Exception:
#         return ""

from config_utils import get_language

def voice_to_text(file_path: str) -> str:
    from pydub import AudioSegment
    import speech_recognition as sr

    lang = get_language()
    lang_map = {
        "english": "en-US",
        "hindi": "hi-IN",
        "hinglish": "en-IN"
    }
    lang_code = lang_map.get(lang, "en-US")

    sound = AudioSegment.from_file(file_path)
    wav_path = file_path.replace(".ogg", ".wav")
    sound.export(wav_path, format="wav")

    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as src:
        audio = r.record(src)

    try:
        text = r.recognize_google(audio, language=lang_code)
        return text
    except Exception:
        return ""




def gemini_generate_report(user_text: str) -> dict | None:
    """Let Gemini format the user’s voice text into a structured AccessibilityReport JSON"""
    prompt = f"""
    You are a JSON generator for an AccessibilityReport model.

    The user may speak in any language (Hindi, English, or mixed).
    Translate everything into clear English before generating the JSON.

    Generate only valid JSON in this exact format:
    {{
      "latitude": null,
      "longitude": null,
      "problem_type": "<brief type, like Broken Bridge, Slippery Path>",
      "disability_types": ["Wheelchair"] or ["Visual"] or ["hearing"] or ["other"],
      "severity": "<Low|Medium|High>",
      "description": "<detailed problem description>",
      "photo_url": null,
      "status": "Active"
    }}

    Only return JSON. User text: "{user_text}"
    """
    try:
        resp = gemini_model.generate_content(prompt)
        raw = resp.text.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception as e:
        logging.error(f"Gemini parse error: {e}")
        return None


async def handle_voice_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    """Main hook for ALL voice messages."""
    # 1️⃣ Convert voice → text
    voice_file = await update.message.voice.get_file()
    voice_path = "voice_input.ogg"
    await voice_file.download_to_drive(voice_path)
    text = voice_to_text(voice_path)

    if not text:
        await update.message.reply_text("⚠️ Couldn’t understand you. Try again.")
        return

    logging.info(f"🎙 User said: {text}")

    # 2️⃣ Let Gemini generate structured report
    report = gemini_generate_report(text)
    if not report:
        await update.message.reply_text("🤖 Gemini couldn’t format your report.")
        return

    # 3️⃣ Save report JSON temporarily in memory
    context.user_data["pending_report"] = report

    # 4️⃣ Ask for location using Telegram button
    keyboard = [[KeyboardButton("📍 Send my location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Got it! Please share your location to complete the report:",
        reply_markup=reply_markup
    )


async def handle_location2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called after the user shares location."""
    loc = update.message.location
    report = context.user_data.get("pending_report")
    if not report:
        await update.message.reply_text("⚠️ No active report found.")
        return

    # 1️⃣ Merge coordinates into the pending report
    report["latitude"] = loc.latitude
    report["longitude"] = loc.longitude

    # 2️⃣ Get auth header for this user
    headers = get_auth_header(update.effective_user.id)
    if not headers:
        await update.message.reply_text("⚠️ Please /login first.")
        return

    # 3️⃣ Send to backend
    try:
        resp = requests.post(API_URL, headers=headers, json=report, timeout=10)
        if resp.status_code in [200, 201]:
            await update.message.reply_text("✅ Report successfully submitted!")
        else:
            await update.message.reply_text(
                f"⚠️ Failed (status {resp.status_code}): {resp.text[:100]}"
            )
    except Exception as e:
        logging.error(f"Backend error: {e}")
        await update.message.reply_text("❌ Couldn’t send report.")

    # Optional debug output
    formatted = json.dumps(report, indent=2)
    await update.message.reply_text(f"📦 Sent JSON:\n```json\n{formatted}\n```", parse_mode="Markdown")

    # 4️⃣ Clear temp data
    context.user_data.pop("pending_report", None)
