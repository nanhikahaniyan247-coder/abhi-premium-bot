import telebot
import requests
import time
import random
import threading
from datetime import datetime

# ==============================================================================
#                               MAIN BOT CONFIG
# ==============================================================================

# REPLACE WITH YOUR ACTUAL TOKENS
BOT_TOKEN = "8323033899:AAFHoQO7ygDbXkHXsfIUl23XeTBkl57wSJk"
TRACKER_BOT_TOKEN = "8593315636:AAGJxp-zjtpRFmoKNkQtQ4jkdDe2urulZYI"
OWNER_CHAT_ID = 7381777230

# STICKERS
STICKER_START = "CAACAgUAAxkBAAEPqt9pA4hYynwVmdJMZBTB6TEiqoa0kwACCxIAAvpv6FflNJkimhkoPDYE"
STICKER_STOP  = "CAACAgUAAxkBAAEPquFpA4hbLeDOtbe5-UuqrSbdzAIY3wACahAAAmfo6VcDiISr18zVQzYE"
STICKER_WIN   = "CAACAgUAAxkBAAEPquNpA4jUOcz2chotdgABlMaa-IlbYuQAAt8QAAItsulXUgABc769I40wNgQ"

# API CONFIG
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://hgnice.biz"
}

# INIT BOTS
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
tracker_bot = telebot.TeleBot(TRACKER_BOT_TOKEN, parse_mode="HTML")

# STATE MANAGEMENT
active_sessions = {}
total_users = {}
active_users = set()

# ==============================================================================
#                          🔥 NEW AI PREDICTION LOGIC
# ==============================================================================

def big_small(num):
    """Returns BIG if digit >= 5, else SMALL."""
    try:
        val = int(str(num)[-1]) # Ensure we grab the last digit
        return "BIG" if val >= 5 else "SMALL"
    except:
        return "SMALL" # Fallback

def your_ai_prediction(last_results):
    """
    last_results: list of numbers (Last digit integers), ordered Oldest -> Newest
    """
    if len(last_results) < 5:
        return random.choice(["BIG", "SMALL"])

    # Ensure we use the last 5 results
    last5_nums = last_results[-5:]
    bs = [big_small(n) for n in last5_nums]

    # -------------------------------
    # 1️⃣ DRAGON TREND (3/4 same)
    # -------------------------------
    last4 = bs[-4:]
    big_count = last4.count("BIG")
    small_count = last4.count("SMALL")

    if big_count >= 3 or small_count >= 3:
        trend = "BIG" if big_count > small_count else "SMALL"
        # 20% random break
        if random.random() < 0.20:
            return "SMALL" if trend == "BIG" else "BIG"
        return trend

    # -------------------------------
    # 2️⃣ ALTERNATING TREND (BSB / SBS)
    # -------------------------------
    last3 = bs[-3:]
    if last3 == ["BIG", "SMALL", "BIG"] or last3 == ["SMALL", "BIG", "SMALL"]:
        next_alt = "SMALL" if last3[-1] == "BIG" else "BIG"
        # 15% random break
        if random.random() < 0.15:
            return last3[-1]
        return next_alt

    # -------------------------------
    # 3️⃣ NO TREND → WEIGHTED PROBABILITY
    # -------------------------------
    weights = [1, 2, 3, 4, 5]  # oldest → newest
    score = {"BIG": 0, "SMALL": 0}

    for val, w in zip(bs, weights):
        score[val] += w

    prediction = "BIG" if score["BIG"] > score["SMALL"] else "SMALL"

    # 30% randomness
    if random.random() < 0.30:
        prediction = "SMALL" if prediction == "BIG" else "BIG"

    return prediction

# ==============================================================================
#                               HELPER FUNCTIONS
# ==============================================================================

def notify_owner(msg):
    """Sends logs to the owner via Tracker Bot."""
    try:
        tracker_bot.send_message(OWNER_CHAT_ID, f"<b>[LOG]</b> {msg}")
    except:
        pass

def fetch_history_data():
    """Fetches the last 10 issues from API."""
    try:
        ts = int(time.time() * 1000)
        r = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json().get("data", {}).get("list", [])
            return data # Returns list of dicts
    except Exception as e:
        print(f"API Error: {e}")
    return []

def format_trend_visual(history_list):
    """Creates a visual string like 🔴🟢🔴🟢 for the message."""
    visuals = []
    # Take last 5, reverse to show Old -> New left to right
    subset = history_list[:5][::-1] 
    for item in subset:
        res = big_small(item['number'])
        if res == "BIG":
            visuals.append("🟡") # Yellow/Gold for Big
        else:
            visuals.append("🔵") # Blue for Small
    return "".join(visuals)

# ==============================================================================
#                               SESSION ENGINE
# ==============================================================================

def run_session(chat_id):
    last_processed_period = -1
    last_prediction = None
    
    bot.send_sticker(chat_id, STICKER_START)
    bot.send_message(chat_id, "💎 <b>CONNECTED TO SERVER... CALCULATING NEXT RESULT</b> 💎")

    while active_sessions.get(chat_id, False):
        history = fetch_history_data()
        
        if not history:
            time.sleep(2)
            continue

        # API usually returns [Newest, ..., Oldest]
        latest_issue = history[0]
        current_period = int(latest_issue["issueNumber"])
        current_result_num = int(latest_issue["number"])
        current_result_bs = big_small(current_result_num)

        # 1. CHECK WIN FOR PREVIOUS PERIOD
        if last_processed_period == current_period:
            # We already processed this, check if we need to predict next
            pass 
        else:
            # New result has arrived
            if last_prediction and last_processed_period != -1:
                # Check if previous prediction was correct
                # Note: Logic here assumes we predicted for 'current_period' in the previous loop
                if last_prediction == current_result_bs:
                    try:
                        bot.send_sticker(chat_id, STICKER_WIN)
                        bot.send_message(chat_id, f"✅ <b>WINNER WINNER!</b>\nRESULT: <b>{current_result_bs}</b>")
                    except: pass
            
            # 2. PREPARE NEXT PREDICTION
            next_period = current_period + 1
            
            # Prepare data for Algorithm (Need Oldest -> Newest list of numbers)
            # Take last 10 items, reverse them
            data_subset = history[:10][::-1]
            num_list = [int(item['number']) for item in data_subset]
            
            # --- CALL YOUR AI ALGORITHM ---
            prediction = your_ai_prediction(num_list)
            
            # Visual Trend
            trend_viz = format_trend_visual(history)

            msg = (
                "💎 <b>ABHI PREMIUM SIGNAL</b> 💎\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>TREND</b> : {trend_viz}\n"
                f"🆔 <b>PERIOD</b> : <code>{str(next_period)[-6:]}</code>\n"
                f"🎰 <b>PREDICTION</b> : <b>{prediction}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ <b>PLAY SAFELY & USE 3X LEVEL</b>\n"
                "👨‍💻 <b>DEV</b> : @AM_OWNER"
            )

            try:
                bot.send_message(chat_id, msg)
            except Exception as e:
                print(f"Send Error: {e}")
                active_sessions[chat_id] = False
                break

            last_processed_period = current_period
            last_prediction = prediction

            # Wait loop to avoid spamming API
            # Wait until near the end of the period or just simple sleep
            for _ in range(15):
                if not active_sessions.get(chat_id): break
                time.sleep(1)

# ==============================================================================
#                          MAIN BOT COMMANDS (Small Letters)
# ==============================================================================

@bot.message_handler(commands=['start', 'help'])
def start_cmd(m):
    bot.reply_to(
        m,
        "⚡ <b>WELCOME TO ABHI PREMIUM SYSTEM</b> ⚡\n\n"
        "🟢 <b>COMMANDS AVAILABLE:</b>\n"
        "▶️ /run  : <b>START PREDICTIONS</b>\n"
        "⏹️ /stop : <b>STOP PREDICTIONS</b>\n\n"
        "💎 <b>ALGORITHM VERSION: 2.0 (AI)</b>\n"
        "👨‍💻 <b>DEV : @AM_OWNER</b>"
    )

@bot.message_handler(commands=['run'])
def run_cmd(m):
    cid = m.chat.id
    u = m.from_user
    
    if active_sessions.get(cid):
        bot.reply_to(m, "⚠️ <b>SESSION ALREADY ACTIVE!</b>")
        return

    active_sessions[cid] = True
    total_users[u.id] = u.username or "NO_USERNAME"
    active_users.add(u.id)

    notify_owner(f"🚀 <b>USER STARTED</b> : @{u.username or 'NO_USERNAME'} ({u.id})")
    threading.Thread(target=run_session, args=(cid,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop_cmd(m):
    cid = m.chat.id
    uid = m.from_user.id

    if not active_sessions.get(cid):
        bot.reply_to(m, "⚠️ <b>NO ACTIVE SESSION.</b>")
        return

    active_sessions[cid] = False
    active_users.discard(uid)

    bot.send_sticker(cid, STICKER_STOP)
    bot.send_message(cid, "🛑 <b>SESSION STOPPED SUCCESSFULLY.</b>")
    notify_owner(f"🛑 <b>USER STOPPED</b> : {uid}")

# ==============================================================================
#                        TRACKER BOT COMMANDS (Admin Panel)
# ==============================================================================

def owner_only(m): return m.chat.id == OWNER_CHAT_ID

@tracker_bot.message_handler(commands=['start', 'help'])
def tracker_start(m):
    if owner_only(m):
        tracker_bot.reply_to(
            m,
            "📊 <b>ABHI ADMIN PANEL</b>\n"
            "━━━━━━━━━━━━━━━━━\n"
            "/status - View Stats\n"
            "/users - All Users\n"
            "/active - Online Users\n"
            "/offline - Offline Users\n"
            "━━━━━━━━━━━━━━━━━\n"
            "👨‍💻 <b>DEV : @AM_OWNER</b>"
        )

@tracker_bot.message_handler(commands=['status'])
def tracker_status(m):
    if owner_only(m):
        tracker_bot.reply_to(
            m,
            f"📈 <b>SYSTEM STATUS</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>TOTAL USERS :</b> {len(total_users)}\n"
            f"🟢 <b>ACTIVE NOW  :</b> {len(active_users)}\n"
            f"🔴 <b>OFFLINE     :</b> {len(total_users)-len(active_users)}"
        )

@tracker_bot.message_handler(commands=['users'])
def tracker_users(m):
    if owner_only(m):
        msg = "\n".join([f"ID: {k} | @{v}" for k, v in total_users.items()])
        tracker_bot.reply_to(m, f"<b>ALL USERS:</b>\n{msg}" if msg else "NO DATA")

@tracker_bot.message_handler(commands=['active'])
def tracker_active(m):
    if owner_only(m):
        msg = "\n".join([f"@{total_users[i]}" for i in active_users])
        tracker_bot.reply_to(m, f"<b>🟢 ACTIVE USERS:</b>\n{msg}" if msg else "NONE")

# ==============================================================================
#                               SYSTEM BOOT
# ==============================================================================

print("--- BOTS STARTING ---")

def start_bots():
    threading.Thread(
        target=tracker_bot.infinity_polling,
        kwargs={"skip_pending": True},
        daemon=True
    ).start()

    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    start_bots()
