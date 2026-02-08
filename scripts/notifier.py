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

from zoneinfo import ZoneInfo

# ...

async def check_and_notify():
    logging.info("Checking for pending tasks...")
    
    # Define Target Timezone
    user_tz_str = os.getenv("USER_TIMEZONE", "America/Mexico_City")
    try:
        user_tz = ZoneInfo(user_tz_str)
    except Exception as e:
        logging.error(f"Timezone '{user_tz_str}' invalid: {e}. Defaulting to UTC.")
        user_tz = ZoneInfo("UTC")

    # Current Time in User's Timezone
    now = datetime.now(user_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    logging.info(f"🕒 Time Check: {now} (TZ: {user_tz_str})")

    # 1. Fetch active tasks
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
        hora_limite_str = task.get("hora_limite") # e.g. "16:00:00"
        ultimo_rec = task.get("ultimo_recordatorio") # ISO timestamp
        es_habito = task.get("es_habito")
        fecha_limite = task.get("fecha_limite") # ISO timestamp or YYYY-MM-DD
        dias_semana = task.get("dias_semana") # JSON list [0, 6]
        fecha_fin_habito = task.get("fecha_fin_habito") # YYYY-MM-DD

        # Skip if no specific time set
        if not hora_limite_str:
            continue

        # Check if already notified TODAY
        # ultimo_rec might be in UTC or ISO format with offset. 
        # Safest is to check string prefix YYYY-MM-DD if we assume it was stored in correct TZ,
        # BUT supabase stores timestamptz in UTC.
        # So we should parse it.
        already_notified_today = False
        if ultimo_rec:
            try:
                # Parse ultimo_recordatorio to datetime
                last_rec_dt = datetime.fromisoformat(ultimo_rec)
                # Convert to USER TZ to check the day
                if last_rec_dt.tzinfo is None:
                     # Assume UTC if naive, though supabase usually sends offset
                     last_rec_dt = last_rec_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                last_rec_local = last_rec_dt.astimezone(user_tz)
                if last_rec_local.strftime("%Y-%m-%d") == today_str:
                    already_notified_today = True
            except Exception as e:
                logging.warning(f"Error parsing ultimo_recordatorio '{ultimo_rec}': {e}")
                # Fallback to simple string check if parsing fails
                if today_str in ultimo_rec:
                    already_notified_today = True

        if already_notified_today:
            continue

        # Check Eligibility (Habit vs Deadline)
        should_notify = False
        
        # Scenario A: Habit
        if es_habito:
             if fecha_fin_habito and today_str > fecha_fin_habito:
                 should_notify = False # Expired
             elif dias_semana and isinstance(dias_semana, list) and len(dias_semana) > 0:
                 # Python weekday: Mon=0, Sun=6
                 current_weekday = now.weekday()
                 if current_weekday in dias_semana:
                     should_notify = True
                 else:
                     should_notify = False
             else:
                 should_notify = True # Daily
        
        # Scenario B: Specific Deadline Today
        elif fecha_limite:
            # fecha_limite is usually "YYYY-MM-DD" or ISO.
            deadline_str = fecha_limite.split("T")[0]
            if deadline_str == today_str:
                should_notify = True
        
        # CHECK TIME WINDOW
        if should_notify:
            try:
                # Construct Deadline Datetime for TODAY
                # hora_limite_str is "HH:MM:SS"
                h, m, s = map(int, hora_limite_str.split(":"))
                deadline_dt = now.replace(hour=h, minute=m, second=s, microsecond=0)
                
                # Difference: NOW - DEADLINE
                diff = now - deadline_dt
                diff_seconds = diff.total_seconds()
                
                # Logic:
                # 1. Too Early: diff < 0 -> Wait
                # 2. On Time: -60s <= diff <= 120min (7200s) -> Notify (Buffer of 60s early allowed?)
                #    Actually, user said "at that time". 
                #    Let's say strict: diff >= 0 and diff <= 7200
                # 3. Too Late: diff > 7200 -> Mark as "Missed/Done" silently to avoid spam.
                
                VALIDITY_WINDOW_SECONDS = 7200 # 2 Hours
                
                if 0 <= diff_seconds <= VALIDITY_WINDOW_SECONDS:
                    msg = f"⏰ **Recordatorio 2ndBrain**\n\nEs hora de: **{contenido}**\n({hora_limite_str})"
                    await send_telegram_message(msg)
                    
                    # Update DB
                    supabase.table("tareas").update({"ultimo_recordatorio": now.isoformat()}).eq("id", tid).execute()
                    
                elif diff_seconds > VALIDITY_WINDOW_SECONDS:
                    logging.info(f"Task {tid} ('{contenido}') is STALE (Deadline: {hora_limite_str}, Now: {now.strftime('%H:%M')}). Marking skipped.")
                    # Mark as notified so we don't check again today
                    supabase.table("tareas").update({"ultimo_recordatorio": now.isoformat()}).eq("id", tid).execute()
                    
                else:
                    # Too early, do nothing
                    pass

            except Exception as e:
                logging.error(f"Error checking time for task {tid}: {e}")

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
