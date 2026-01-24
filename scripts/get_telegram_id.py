import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def get_chat_id():
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    bot = Bot(token=TOKEN)
    print(f"🤖 Connecting to Bot...")
    
    try:
        updates = await bot.get_updates()
        if not updates:
            print("⚠️ No updates found. Please send a message 'Hola' to your bot first!")
            print(f"Bot Link: https://t.me/{ (await bot.get_me()).username }")
        else:
            last_update = updates[-1]
            chat_id = last_update.message.chat.id
            username = last_update.message.chat.username
            print(f"\n✅ SUCCESS! Found Chat ID.")
            print(f"👤 User: {username}")
            print(f"🆔 CHAT_ID: {chat_id}")
            print(f"\nPlease add this line to your .env file:\nTELEGRAM_CHAT_ID={chat_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_chat_id())
