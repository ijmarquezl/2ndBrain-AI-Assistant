import os
import asyncio
import logging
from datetime import datetime, date
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Bot

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN, CHAT_ID]):
    logging.error("Missing environment variables. Check .env")
    exit(1)

# Init Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_message(text: str):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        logging.info(f"Message sent: {text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

async def check_and_notify():
    logging.info("Checking for pending tasks...")
    
    # Current Time info
    now = datetime.now()
    current_time_str = now.strftime("%H:%M:%S")
    today_str = now.strftime("%Y-%m-%d")

    # 1. Fetch Tasks that have a DEADLINE (Date) = Today OR are HABITS (Daily)
    # AND have a specified TIME LIMIT (hora_limite)
    # AND haven't been notified today.
    
    # Note: Supabase/PostgREST filtering on 'time' columns can be tricky with simple clients.
    # We'll fetch active tasks and filter in Python for robustness.
    
    try:
        # Get pending tasks or habits
        response = supabase.table("tareas").select("*").in_("estado", ["pendiente", "aprobado"]).execute()
        tasks = response.data
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return

    for task in tasks:
        tid = task.get("id")
        contenido = task.get("contenido")
        hora_limite = task.get("hora_limite") # e.g. "16:00:00"
        ultimo_rec = task.get("ultimo_recordatorio") # ISO timestamp
        es_habito = task.get("es_habito")
        fecha_limite = task.get("fecha_limite") # ISO timestamp

        # Skip if no specific time set
        if not hora_limite:
            continue

        # Check if already notified TODAY
        already_notified_today = False
        if ultimo_rec:
            # Check if ultimo_rec date part is same as today
            last_notif_date = ultimo_rec.split("T")[0]
            if last_notif_date == today_str:
                already_notified_today = True
        
        if already_notified_today:
            continue

        # Check Eligibility
        should_notify = False
        
        # Scenario A: Habit (runs every day if 'daily' or implicitly if habit=true)
        if es_habito:
             should_notify = True
        
        # Scenario B: Specific Deadline Today
        elif fecha_limite:
            deadline_date = fecha_limite.split("T")[0]
            if deadline_date == today_str:
                should_notify = True
        
        # CHECK TIME
        # Only notify if NOW >= Limit Time
        if should_notify:
            # Simple string comparison works for ISO times "HH:MM:SS"
            # If now "16:05" >= limit "16:00" -> Notify
            # We add a buffer? User said "At that time". 
            # If script runs every 10 mins, sending at 16:05 for 16:00 is fine.
            if current_time_str >= hora_limite:
                msg = f"⏰ **Recordatorio 2ndBrain**\n\nEs hora de: **{contenido}**\n({hora_limite})"
                await send_telegram_message(msg)
                
                # Update DB to avoid spam
                supabase.table("tareas").update({"ultimo_recordatorio": now.isoformat()}).eq("id", tid).execute()

async def main_loop():
    logging.info("🚀 Notifier Service Started (Looping every 60s)")
    while True:
        await check_and_notify()
        await asyncio.sleep(60)

if __name__ == "__main__":
    mode = os.getenv("NOTIFIER_MODE", "loop")
    
    if mode == "one_off":
        logging.info("🚀 Notifier running in ONE-OFF mode (Cron)")
        asyncio.run(check_and_notify())
    else:
        try:
            asyncio.run(main_loop())
        except KeyboardInterrupt:
            logging.info("Notifier Stopped")
