import telebot
import sqlite3
import os
import time

# ======================
# BOT TOKEN (Railway ENV)
# ======================
TOKEN = os.getenv("7274782030:AAGknhVGUF2G443fhgpIwU01li18WK__BhU")

if not TOKEN:
    raise Exception("BOT_TOKEN not found in environment variables")

bot = telebot.TeleBot(TOKEN)

# ======================
# DATABASE SETUP
# ======================
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    daily_earn INTEGER DEFAULT 0,
    referrer_id INTEGER
)
""")
conn.commit()

# ======================
# /start COMMAND
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    ref_id = None
    args = message.text.split()

    if len(args) > 1:
        try:
            ref_id = int(args[1])
        except:
            ref_id = None

    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)",
        (message.from_user.id, ref_id)
    )
    conn.commit()

    bot.reply_to(
        message,
        "👋 স্বাগতম!\n\n"
        "💰 Ads দেখে আয় করো\n"
        "📢 /ad লিখে কাজ শুরু করো\n"
        "💸 Referral দিয়ে +2 টাকা আয় করো"
    )

# ======================
# /ad COMMAND
# ======================
@bot.message_handler(commands=['ad'])
def ad(message):
    user_id = message.from_user.id

    cur.execute("SELECT daily_earn FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        bot.reply_to(message, "❌ আগে /start দাও")
        return

    daily = row[0]

    if daily >= 20:
        bot.reply_to(message, "⛔ আজকের earning limit শেষ হয়েছে")
        return

    ad_link = "https://shrinkme.io/example"
    reward = 1
    start_time = time.time()

    with open(f"{user_id}_time.txt", "w") as f:
        f.write(f"{start_time}:{reward}")

    bot.send_message(
        message.chat.id,
        f"🌐 এই link-এ 15 sec থাকো:\n{ad_link}\n\n"
        "শেষ হলে /done লিখো"
    )

# ======================
# /done COMMAND
# ======================
@bot.message_handler(commands=['done'])
def done(message):
    user_id = message.from_user.id

    try:
        with open(f"{user_id}_time.txt", "r") as f:
            start_time, reward = f.read().split(":")
            start_time = float(start_time)
            reward = int(reward)
    except:
        bot.reply_to(message, "❌ কোনো ad active নেই")
        return

    if time.time() - start_time < 15:
        bot.reply_to(message, "⏳ এখনো 15 sec হয়নি")
        return

    cur.execute(
        "UPDATE users SET balance = balance + ?, daily_earn = daily_earn + ? WHERE user_id=?",
        (reward, reward, user_id)
    )
    conn.commit()

    cur.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,))
    ref = cur.fetchone()[0]

    if ref:
        cur.execute(
            "UPDATE users SET balance = balance + 2 WHERE user_id=?",
            (ref,)
        )
        conn.commit()

    os.remove(f"{user_id}_time.txt")
    bot.reply_to(message, f"✅ Ad completed! +{reward} টাকা")

# ======================
# BOT START
# ======================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
