from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import json
import logging
import requests  # <-- for sending data to Django
from auth_manage import register_user, login_user, logout_user, get_auth_header
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Bot token loaded: {bool(BOT_TOKEN)}")

# 🔑 Replace this with your actual JWT access token
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  
API_URL = "https://saarthi-backend-xv47.onrender.com/api/reports/"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ============================================================
# Gemini: Convert report text to JSON
# ============================================================
def format_report_with_gemini(user_text: str, lat: float = 0.0, lon: float = 0.0) -> dict | None:
    """Generate structured JSON using Gemini."""
    prompt = f"""
    You are a strict JSON generator for a Django backend model called AccessibilityReport.

    Convert the user’s message into valid JSON with these fields:
    {{
      "latitude": <float>,  
      "longitude": <float>, 
      "problem_type": <string>,  
      "disability_types": <list of strings>, 
      "severity": <string>,  
      "description": <string>, 
      "photo_url": <string or null>,  
      "status": <string>
    }}

    Rules:
    - Output only valid JSON, no markdown or text.
    - Use provided coordinates if available: latitude={lat}, longitude={lon}.
    - Default severity='Medium', photo_url=null, status='Active'.

    User report: "{user_text}"
    """

    try:
        response = gemini_model.generate_content(prompt)
        raw = response.text.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception as e:
        logging.error(f"Gemini JSON error: {e}")
        return None


# ============================================================
# Telegram Handlers
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "In your service, my lord 👑\n\n"
        "Use /sendlocation to share your current location first, "
        "then use /submitreport <description>."
    )



async def submitreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /submitreport <your report text>")
        return

    lat = context.user_data.get("latitude", 0.0)
    lon = context.user_data.get("longitude", 0.0)
    user_text = " ".join(context.args)

    await update.message.reply_text("Analyzing your report with Gemini... 🧠")

    report = format_report_with_gemini(user_text, lat, lon)
    if not report:
        await update.message.reply_text("⚠️ Gemini failed to process your report.")
        return

    # ✅ Get auth header for this Telegram user
    headers = get_auth_header(update.effective_user.id)
    if not headers:
        await update.message.reply_text("⚠️ You are not logged in. Please /login first.")
        return

    # ===============================================
    # 🛰️ Step 2: Send to Django Backend API
    # ===============================================
    try:
        resp = requests.post(API_URL, headers=headers, json=report, timeout=10)
        if resp.status_code in [200, 201]:
            await update.message.reply_text("✅ Report successfully submitted to the backend!")
        else:
            await update.message.reply_text(
                f"⚠️ Failed to send report (status {resp.status_code}):\n{resp.text[:200]}"
            )

    except Exception as e:
        logging.error(f"Backend POST error: {e}")
        await update.message.reply_text("❌ Error sending report to the backend.")

    # Optional debug output
    formatted = json.dumps(report, indent=2)
    await update.message.reply_text(
        f"📦 Sent JSON:\n```json\n{formatted}\n```", parse_mode="Markdown"
    )


async def sendlocation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to share their current GPS location."""
    keyboard = [[KeyboardButton("📍 Send my location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Please share your current location:", reply_markup=reply_markup)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the user's sent location."""
    user_location = update.message.location
    if user_location:
        context.user_data["latitude"] = user_location.latitude
        context.user_data["longitude"] = user_location.longitude
        await update.message.reply_text(f"📍 Location saved: ({user_location.latitude:.4f}, {user_location.longitude:.4f})")
    else:
        await update.message.reply_text("❌ Failed to get location, please try again.")

# async def submitreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not context.args:
#         await update.message.reply_text("Usage: /submitreport <your report text>")
#         return

#     lat = context.user_data.get("latitude", 0.0)
#     lon = context.user_data.get("longitude", 0.0)
#     user_text = " ".join(context.args)

#     await update.message.reply_text("Analyzing your report with Gemini... 🧠")

#     report = format_report_with_gemini(user_text, lat, lon)
#     if not report:
#         await update.message.reply_text("⚠️ Gemini failed to process your report.")
#         return

#     # ===============================================
#     # 🛰️ Step 2: Send to Django Backend API
#     # ===============================================
#     try:
#         headers = {
#             "Authorization": f"Bearer {ACCESS_TOKEN}",
#             "Content-Type": "application/json"
#         }
#         resp = requests.post(API_URL, headers=headers, json=report, timeout=10)
#         await update.message.reply_text("✅ Report successfully submitted to the backend!")
#         if resp.status_code in [200, 201]:
#             await update.message.reply_text("✅ Report successfully submitted to the backend!")
#         else:
#             await update.message.reply_text(
#                 f"⚠️ Failed to send report (status {resp.status_code}):\n{resp.text[:200]}"
#             )

#     except Exception as e:
#         logging.error(f"Backend POST error: {e}")
#         await update.message.reply_text("❌ Error sending report to the backend.")

#     # Optionally show JSON for debugging
#     formatted = json.dumps(report, indent=2)
#     await update.message.reply_text(f"📦 Sent JSON:\n```json\n{formatted}\n```", parse_mode="Markdown")


#     # /register <email> <username> <password>
# async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if len(context.args) < 3:
#         await update.message.reply_text("Usage: /register <email> <username> <password>")
#         return
#     email, username, password = context.args[0], context.args[1], context.args[2]
#     ok, msg = register_user(email, username, password)
#     await update.message.reply_text(msg)

# /login <email> <password>
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /login <username> <password>")
        return
    username, password = context.args[0], context.args[1]
    ok, msg = login_user(update.effective_user.id, username, password)
    await update.message.reply_text(msg)


# /logout
async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if logout_user(update.effective_user.id):
        await update.message.reply_text("👋 Logged out successfully.")
    else:
        await update.message.reply_text("⚠️ You are not logged in.")








from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

(FIRST_NAME, LAST_NAME, EMAIL, PASSWORD, CONFIRM_PASSWORD,
 USER_TYPE, WHEELCHAIR, TACTILE, AUDIO) = range(9)


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Let's create your Saarthi account!\nWhat's your *first name*?",
        parse_mode="Markdown"
    )
    return FIRST_NAME

async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Great! Now your *last name*?", parse_mode="Markdown")
    return LAST_NAME

async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Enter your *email* address:")
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Set a *password* (min 6 chars):", parse_mode="Markdown")
    return PASSWORD


async def confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirm = update.message.text
    if confirm != context.user_data["password"]:
        await update.message.reply_text("⚠️ Passwords don't match. Please enter your password again:")
        return PASSWORD
    context.user_data["password_confirm"] = confirm
    keyboard = [["user", "volunteer"]]
    await update.message.reply_text(
        "Choose your *user type*:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return USER_TYPE

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["password"] = update.message.text
    await update.message.reply_text("Please confirm your password:")
    return CONFIRM_PASSWORD

async def user_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_type"] = update.message.text
    keyboard = [["Yes", "No"]]
    await update.message.reply_text("Do you need *wheelchair access*?", parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return WHEELCHAIR

async def wheelchair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["needs_wheelchair_access"] = update.message.text.lower() == "yes"
    keyboard = [["Yes", "No"]]
    await update.message.reply_text("Do you need *tactile paths*?", parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return TACTILE

async def tactile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["needs_tactile_paths"] = update.message.text.lower() == "yes"
    keyboard = [["Yes", "No"]]
    await update.message.reply_text("Do you need *audio guidance*?", parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return AUDIO

async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["needs_audio_guidance"] = update.message.text.lower() == "yes"
    await update.message.reply_text("📝 Submitting your registration...", reply_markup=ReplyKeyboardRemove())

    data = {
        "username": context.user_data["email"].split("@")[0],
        "email": context.user_data["email"],
        "password": context.user_data["password"],
        "password_confirm": context.user_data["password_confirm"],
        "first_name": context.user_data["first_name"],
        "last_name": context.user_data["last_name"],
        "user_type": context.user_data["user_type"],
        "needs_wheelchair_access": context.user_data["needs_wheelchair_access"],
        "needs_tactile_paths": context.user_data["needs_tactile_paths"],
        "needs_audio_guidance": context.user_data["needs_audio_guidance"],
        "phone_number": "",
        "disability_type": "none"
    }

    ok, msg = register_user(**data)

    if ok:
        username = data["username"]
        await update.message.reply_text(
            f"🎉 Registration successful!\nYou can now /login with username: *{username}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(msg)

    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registration canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

registration_conversation = ConversationHandler(
    entry_points=[CommandHandler("register", start_registration)],
    states={
        FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name)],
        LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name)],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        CONFIRM_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_password)],
        USER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_type)],
        WHEELCHAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, wheelchair)],
        TACTILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactile)],
        AUDIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, audio)],
    },
    fallbacks=[CommandHandler("cancel", cancel_registration)]
)





# ============================================================
# MAIN
# ============================================================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(registration_conversation)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("sendlocation", sendlocation))
app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(CommandHandler("submitreport", submitreport))
app.add_handler(CommandHandler("login", login))
app.add_handler(CommandHandler("logout", logout))


print("🤖 Bot running...")
app.run_polling()
