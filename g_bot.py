import os
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai
import asyncio

# ---------------- LOAD ENV ----------------

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2")
]
API_KEYS = [k for k in API_KEYS if k]

# ---------------- FLASK APP ----------------

app = Flask(__name__)

# ---------------- TELEGRAM APP ----------------

telegram_app = Application.builder().token(TOKEN).build()

# ---------------- GEMINI FUNCTION ----------------

def get_ai_response(user_text):
    for i, key in enumerate(API_KEYS):
        try:
            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
You are a healthcare assistant.

Respond in:

🩺 Issue:
💡 Advice:
⚠️ Doctor visit condition:
❗ Disclaimer:

User: {user_text}
""",
                config={"temperature": 0.5, "max_output_tokens": 200}
            )

            return response.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            print(f"API key {i+1} failed:", e)

    return "⚠️ AI unavailable"

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Healthcare Bot Active!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.chat.send_action("typing")

    reply = await asyncio.to_thread(get_ai_response, user_text)

    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ---------------- WEBHOOK ROUTE (FIXED) ----------------

@app.post(f"/{TOKEN}")
def webhook():
    data = request.get_json(force=True)

    update = Update.de_json(data, telegram_app.bot)

    # SAFE execution (important fix)
    asyncio.run(telegram_app.process_update(update))

    return "OK"

# ---------------- HOME ROUTE ----------------

@app.get("/")
def home():
    return "Bot is running!"

# ---------------- STARTUP + WEBHOOK SETUP ----------------

if __name__ == "__main__":
    async def setup():
        await telegram_app.initialize()

        # IMPORTANT: must match route
        await telegram_app.bot.set_webhook(
            url=f"https://telegram-healthcare-bot.onrender.com/{TOKEN}"
        )

    asyncio.run(setup())

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
