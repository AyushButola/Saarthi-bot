from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import google.generativeai as genai
# FIX: Explicitly import Schema, Type, and GenerateContentConfig directly from the types submodule
from google.generativeai.types import Schema, Type, GenerateContentConfig 
import json
import os
import logging

# ===============================
# CONFIG
# ===============================
# NOTE: Using 'gemini-2.5-flash' for faster, cheaper API calls for structured tasks.
# I also highly recommend moving this key to an environment variable or a secrets manager!
BOT_TOKEN = "7894237738:AAGsb-qWOuuowSN7QfTfNGrNK9ToZSdjuyg"
GEMINI_API_KEY = "AIzaSyAMYZo3AQSKwCjLiVXXW18srO0o1upKBt4" 

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Using the flash model for faster, cost-effective structured output generation
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    logging.info(f"Gemini client initialized with model: {GEMINI_MODEL_NAME}")
except Exception as e:
    logging.error(f"Error initializing Gemini: {e}")
    # Exit or handle inability to run bot without API access
    raise

# Define the expected JSON structure (Schema) for the report
REPORT_SCHEMA = Schema(
    type=Type.OBJECT,
    properties={
        "latitude": Schema(type=Type.NUMBER, description="Geographic latitude (e.g., 34.0522)"),
        "longitude": Schema(type=Type.NUMBER, description="Geographic longitude (e.g., -118.2437)"),
        "problem_type": Schema(type=Type.STRING, description="The main category of the issue (e.g., 'Ramp Obstruction', 'Broken Elevator', 'Missing Signage')"),
        "disability_types": Schema(type=Type.ARRAY, items=Schema(type=Type.STRING), description="List of affected disability types (e.g., ['wheelchair', 'visual', 'hearing'])"),
        "severity": Schema(type=Type.STRING, description="Severity level: 'High', 'Medium', or 'Low'"),
        "description": Schema(type=Type.STRING, description="A trimmed description of the problem (max 200 chars)"),
        "photo_url": Schema(type=Type.STRING, description="A placeholder URL or null if none provided"),
        "status": Schema(type=Type.STRING, description="Initial status, always 'Reported'")
    },
    required=["latitude", "longitude", "problem_type", "severity", "description", "status"]
)

# ===============================
# COMMAND HANDLERS
# ===============================

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user."""
    await update.message.reply_text("In your service, my lord 👑. Use /submitreport <issue description> to log an accessibility issue.")

# Format report text using Gemini (uses Structured Output)
def format_report_with_gemini(user_text: str) -> dict | None:
    """Uses Gemini to parse free-form text into a structured JSON report."""
    
    # System Instruction to guide the model's behavior and constraints
    system_instruction = (
        "You are an expert accessibility report generator. "
        "Your sole purpose is to convert user-provided text describing an accessibility issue "
        "into a strict JSON object that follows the provided schema. "
        "Strictly adhere to the following rules: "
        "1. Output ONLY the JSON object. "
        "2. If coordinates are missing, use a safe default like (0.0, 0.0). "
        "3. Use a photo_url of 'null' if the user doesn't mention a photo. "
        "4. Set the status always to 'Reported'. "
        "5. Keep the final 'description' field under 200 characters."
    )
    
    prompt = f"Analyze the following report and fill the schema fields: \n\nReport: '{user_text}'"
    
    try:
        response = gemini_model.generate_content(
            contents=prompt,
            config=GenerateContentConfig( 
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=REPORT_SCHEMA
            )
        )
        
        # The response.text is guaranteed to be a JSON string if successful
        raw_json_string = response.text.strip()
        
        # We should parse the JSON. If the model had an issue, it might not be valid JSON,
        # but the Structured Output feature drastically reduces this risk.
        return json.loads(raw_json_string)

    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}. Raw output: {raw_json_string}")
        return None
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        return None

# /submitreport command
async def submitreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's report submission and calls Gemini for processing."""
    if not context.args:
        await update.message.reply_text("Usage: /submitreport <your report text>")
        return

    user_text = " ".join(context.args)
    await update.message.reply_text("Analyzing your report with Gemini... 🧠")

    data = format_report_with_gemini(user_text)

    if data:
        # Use a more user-friendly way to display the result than just dumping the raw JSON
        report_display = (
            f"**Report Processed!**\n\n"
            f"**Issue Type:** {data.get('problem_type', 'N/A')}\n"
            f"**Severity:** {data.get('severity', 'N/A')}\n"
            f"**Location:** ({data.get('latitude', 0.0):.4f}, {data.get('longitude', 0.0):.4f})\n"
            f"**Affected:** {', '.join(data.get('disability_types', ['General']))}\n"
            f"**Description:** _{data.get('description', 'No description provided')}_\n\n"
            f"**Raw JSON Output:**"
        )
        
        pretty_json = json.dumps(data, indent=2)
        
        # Sending two messages: one with the friendly display, one with the raw JSON
        await update.message.reply_text(report_display, parse_mode="Markdown")
        await update.message.reply_text(f"```json\n{pretty_json}\n```", parse_mode="Markdown")
        
    else:
        await update.message.reply_text("⚠️ Failed to process your report with Gemini. Check the console logs for details.")


# ===============================
# MAIN
# ===============================

if __name__ == '__main__':
    # Initialize the Application Builder
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("submitreport", submitreport))

    logging.info("Bot is running... Starting long polling.")
    app.run_polling(poll_interval=1.0)

# # normal user messages (no slash)
# async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_text = update.message.text
#     # send to your NLP or API
#     response = f"Analyzing: {user_text}"
#     await update.message.reply_text(response)

# # /review command example
# async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not context.args:
#         await update.message.reply_text("Usage: /review <place name>")
#         return
#     place_name = " ".join(context.args)
#     # here you can call your backend API
#     await update.message.reply_text(f"Fetching reviews for {place_name} ...")


