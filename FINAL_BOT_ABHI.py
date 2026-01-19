import telebot
import requests
import time
import random
import threading

# ==============================================================================
#                               CONFIG & SETUP
# ==============================================================================

# 🔹 TOMAR BOT TOKEN EKHANE DAO
BOT_TOKEN = "8323033899:AAFHoQO7ygDbXkHXsfIUl23XeTBkl57wSJk"

# 🔹 TOMAR STICKER ID
STICKER_START = "CAACAgUAAxkBAAEPqt9pA4hYynwVmdJMZBTB6TEiqoa0kwACCxIAAvpv6FflNJkimhkoPDYE"
STICKER_STOP  = "CAACAgUAAxkBAAEPquFpA4hbLeDOtbe5-UuqrSbdzAIY3wACahAAAmfo6VcDiISr18zVQzYE"
STICKER_WIN   = "CAACAgUAAxkBAAEPquNpA4jUOcz2chotdgABlMaa-IlbYuQAAt8QAAItsulXUgABc769I40wNgQ"

# 🔹 API CONFIG
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Referer": "https://hgnice.biz"
}

# 🔹 GLOBAL OBJECTS
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
active_sessions = {} 

# ==============================================================================
#                               CORE LOGIC
# ==============================================================================

def get_random_prediction():
    return random.choice(["BIG", "SMALL"])

def fetch_latest_issue():
    try:
        ts = int(time.time() * 1000)
        response = requests.get(API_URL.format(ts), headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
    except:
        pass
    return []

def get_result_from_number(number):
    try:
        return "BIG" if int(str(number)[-1]) >= 5 else "SMALL"
    except:
        return "UNKNOWN"

# ==============================================================================
#                               UI TEMPLATES (UPDATED)
# ==============================================================================

def ui_welcome():
    return (
        "⚡ <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐀𝐁𝐇𝐈 𝐕𝐈𝐏 𝐒𝐘𝐒𝐓𝐄𝐌</b> ⚡\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🔰 <b>𝐀𝐂𝐂𝐄𝐒𝐒 𝐆𝐑𝐀𝐍𝐓𝐄𝐃</b>\n"
        "👤 <b>𝐔𝐒𝐄𝐑:</b> 𝐏𝐑𝐄𝐌𝐈𝐔𝐌\n\n"
        "🕹️ <b>𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒:</b>\n"
        "▶️ <code>/run</code>  : 𝐒𝐓𝐀𝐑𝐓 𝐇𝐀𝐂𝐊\n"
        "⏹️ <code>/stop</code> : 𝐒𝐓𝐎𝐏 𝐇𝐀𝐂𝐊\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👨‍💻 <b>𝐃𝐄𝐕:</b> @ABHI_SCRIPT"
    )

def ui_session_start():
    # Waiting msg removed, Dev added
    return (
        "🚀 <b>𝐒𝐘𝐒𝐓𝐄𝐌 𝐀𝐂𝐓𝐈𝐕𝐀𝐓𝐄𝐃</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🎮 <b>𝐆𝐀𝐌𝐄   :</b> 𝐖𝐈𝐍𝐆𝐎 𝟑𝟎𝐒\n"
        "📡 <b>𝐒𝐄𝐑𝐕𝐄𝐑 :</b> 𝐂𝐎𝐍𝐍𝐄𝐂𝐓𝐄𝐃\n"
        "🤖 <b>𝐀𝐈 𝐌𝐎𝐃𝐄:</b> 𝐇𝐈𝐆𝐇 𝐀𝐂𝐂𝐔𝐑𝐀𝐂𝐘\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👨‍💻 <b>𝐃𝐄𝐕    :</b> @ABHI_SCRIPT"
    )

def ui_prediction(period, prediction):
    # Amount removed, Emojis removed
    return (
        "💎 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐒𝐈𝐆𝐍𝐀𝐋</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🆔 <b>𝐏𝐄𝐑𝐈𝐎𝐃 :</b> <code>{period}</code>\n"
        f"🎰 <b>𝐏𝐈𝐂𝐊   :</b> <b>{prediction}</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🔥 <b>𝐃𝐄𝐕    :</b> @ABHI_SCRIPT"
    )

def ui_session_stop():
    return (
        "🛑 <b>𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐓𝐄𝐑𝐌𝐈𝐍𝐀𝐓𝐄𝐃</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🔋 <b>𝐒𝐘𝐒𝐓𝐄𝐌 𝐎𝐅𝐅𝐋𝐈𝐍𝐄</b>\n"
        "👋 <b>𝐒𝐄𝐄 𝐘𝐎𝐔 𝐍𝐄𝐗𝐓 𝐓𝐈𝐌𝐄</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

# ==============================================================================
#                               SESSION ENGINE
# ==============================================================================

def run_session(chat_id):
    last_period = None
    last_pred = None
    
    # 1. Send Start
    try:
        bot.send_sticker(chat_id, STICKER_START)
        time.sleep(1)
        bot.send_message(chat_id, ui_session_start())
    except:
        active_sessions[chat_id] = False
        return

    # 2. Main Loop
    while active_sessions.get(chat_id, False):
        
        history = fetch_latest_issue()
        if not history:
            time.sleep(2)
            continue

        latest = history[0]
        curr_period = str(latest["issueNumber"])
        curr_result = get_result_from_number(latest["number"])

        # Check Win/Loss
        if last_period == curr_period:
            if last_pred == curr_result:
                try:
                    bot.send_sticker(chat_id, STICKER_WIN)
                except: pass
            last_period = None

        # Predict Next
        next_period_int = int(curr_period) + 1
        next_period = str(next_period_int)
        next_period_short = next_period[-6:]

        if last_period != next_period:
            pred = get_random_prediction()
            
            try:
                bot.send_message(chat_id, ui_prediction(next_period_short, pred))
            except:
                active_sessions[chat_id] = False
                break

            last_period = next_period
            last_pred = pred
            
            # Smart Wait (Instant Stop support)
            for _ in range(20):
                if not active_sessions.get(chat_id, False):
                    break 
                time.sleep(1)
        else:
            time.sleep(1)

# ==============================================================================
#                               COMMAND HANDLERS
# ==============================================================================

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    bot.reply_to(message, ui_welcome())

@bot.message_handler(commands=['run', 'play'])
def handle_run(message):
    chat_id = message.chat.id
    if active_sessions.get(chat_id, False):
        bot.reply_to(message, "⚠️ <b>SYSTEM IS ALREADY RUNNING!</b>")
        return

    active_sessions[chat_id] = True
    t = threading.Thread(target=run_session, args=(chat_id,))
    t.daemon = True
    t.start()

@bot.message_handler(commands=['stop', 'end'])
def handle_stop(message):
    chat_id = message.chat.id
    if not active_sessions.get(chat_id, False):
        bot.reply_to(message, "⚠️ <b>NO ACTIVE SESSION FOUND!</b>")
        return
    
    active_sessions[chat_id] = False
    try:
        bot.send_sticker(chat_id, STICKER_STOP)
        bot.send_message(chat_id, ui_session_stop())
    except: pass

# ==============================================================================
#                               BOOT
# ==============================================================================
print("⚡ ABHI ULTIMATE BOT IS ONLINE...")
bot.infinity_polling()
