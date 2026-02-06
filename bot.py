import telebot
import sqlite3
import os
import time

TOKEN = os.getenv("7274782030:AAGknhVGUF2G443fhgpIwU01li18WK__BhU")  # Railway / environment variable use করো

bot = telebot.TeleBot(TOKEN)

# Database connection
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    daily_earn INTEGER DEFAULT 0,
    referrer_id INTEGER
)
""")
conn.commit()

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    ref_id = None
    # Referral logic (if /start 123)
    args = message.text.split()
    if len(args) > 1:
        try:
            ref_id = int(args[1])
        except:
            ref_id = None

    cur.execute("INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)", (message.from_user.id, ref_id))
    conn.commit()

    bot.reply_to(
        message,
        "👋 স্বাগতম!\n\n"
        "💰 Ads দেখে আয় করো\n"
        "📢 /ad লিখে কাজ শুরু করো\n"
        "💸 Referral দিয়ে +2 টাকা আয় করো"
    )

# /ad command (example shortlink)
@bot.message_handler(commands=['ad'])
def ad(message):
    user_id = message.from_user.id

    # Check daily earning limit
    cur.execute("SELECT daily_earn FROM users WHERE user_id=?", (user_id,))
    daily = cur.fetchone()[0]

    if daily >= 20:  # Daily limit, তুমি চাইলে 30/50 রাখো
        bot.reply_to(message, "⛔ আজকের earning limit শেষ হয়েছে, কাল আবার চেষ্টা করো।")
        return

    # Send ad link
    ad_link = "https://shrinkme.io/example"
    reward = 1  # 1 টাকা per shortlink
    start_time = time.time()

    with open(f"{user_id}_time.txt", "w") as f:
        f.write(f"{start_time}:{reward}")

    bot.send_message(
        message.chat.id,
        f"🌐 এই link-এ 15 sec থাকো:\n{ad_link}\n\n"
        "শেষ হলে /done লিখো"
    )

# /done command
@bot.message_handler(commands=['done'])
def done(message):
    user_id = message.from_user.id

    try:
        with open(f"{user_id}_time.txt", "r") as f:
            data = f.read().split(":")
            start_time = float(data[0])
            reward = int(data[1])
    except:
        bot.reply_to(message, "❌ কোনো ad active নেই")
        return

    if time.time() - start_time >= 15:
        # Update balance and daily_earn
        cur.execute("UPDATE users SET balance = balance + ?, daily_earn = daily_earn + ? WHERE user_id=?",
                    (reward, reward, user_id))
        conn.commit()

        # Referral reward (once)
        cur.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,))
        ref_id = cur.fetchone()[0]
        if ref_id:
            cur.execute("UPDATE users SET balance = balance + 2 WHERE user_id=? AND daily_earn < 20", (ref_id,))
            conn.commit()

        bot.reply_to(message, f"✅ Ad completed! +{reward} টাকা")
    else:
        bot.reply_to(message, "⏳ এখনো 15 sec হয়নি")

bot.infinity_polling()
