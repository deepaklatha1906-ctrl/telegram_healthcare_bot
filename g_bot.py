import os
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.request import HTTPXRequest
import asyncio

# ------------------ LOAD ENV ------------------

load_dotenv()

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2")
]

# Remove empty keys
API_KEYS = [key for key in API_KEYS if key]

# ------------------ START COMMAND ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your Smart Healthcare AI Bot 🤖🏥\n\n"
        "Ask me anything about health.\n"
        "Example:\n"
        "• I have fever and headache\n\n"
        "⚠️ This is not a medical diagnosis."
    )

# ------------------ AI RESPONSE WITH FAILOVER ------------------

def get_ai_response(user_text):
    for i, key in enumerate(API_KEYS):
        try:
            print(f"Trying API KEY {i+1}")

            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
You are a professional healthcare assistant.

Respond ONLY in this format:

🩺 Possible Issue:
<short explanation>

💡 What you can do:
• Point 1
• Point 2
• Point 3

⚠️ When to see a doctor:
<clear condition>

❗ Disclaimer:
This is not a medical diagnosis.

Keep it short, clear, and user-friendly.

User: {user_text}
""",
                config={
                    "temperature": 0.5,
                    "max_output_tokens": 200
                }
            )

            # Safe text extraction (new SDK)
            return response.candidates[0].content.parts[0].text.strip()

        except Exception as e:
            print(f"Key {i+1} failed:", e)
            continue

    return "⚠️ All AI services are busy. Please try again later."

# ------------------ HANDLE MESSAGE ------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.chat.send_action(action="typing")

    loop = asyncio.get_event_loop()

    try:
        reply = await asyncio.wait_for(
            loop.run_in_executor(None, get_ai_response, user_text),
            timeout=20
        )
    except asyncio.TimeoutError:
        reply = "⚠️ AI is taking too long. Please try again."

    await update.message.reply_text(reply)

# ------------------ MAIN ------------------

def main():
    # Increase timeout to avoid network issues
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Multi-Key Gemini Healthcare Bot Running...")
    app.run_polling()

# ------------------ RUN ------------------

if __name__ == "__main__":
    main()