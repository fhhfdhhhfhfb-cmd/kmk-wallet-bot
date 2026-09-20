import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "kmk_wallet.db")

MENU = [
    ["💼 কাজ", "💰 ব্যালেন্স"],
    ["💸 টাকা উত্তোলন", "👥 My Referrals"],
    ["🆘 সাপোর্ট", "🆕 আমি নতুন"],
]

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        pending REAL DEFAULT 0,
        total_income REAL DEFAULT 0,
        completed_tasks INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer INTEGER
    )""")
    con.commit()
    con.close()

def get_user(uid, username=None, referrer=None):
    con = db()
    row = con.execute(
        "SELECT * FROM users WHERE user_id=?", (uid,)
    ).fetchone()

    if not row:
        con.execute(
            "INSERT INTO users(user_id,username,referrer) VALUES(?,?,?)",
            (uid, username or "", referrer)
        )

        if referrer and referrer != uid:
            con.execute(
                "UPDATE users SET referrals=referrals+1 WHERE user_id=?",
                (referrer,)
            )

        con.commit()

    con.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer = None

    if context.args:
        try:
            referrer = int(context.args[0])
        except ValueError:
            pass

    get_user(user.id, user.username, referrer)

    kb = ReplyKeyboardMarkup(MENU, resize_keyboard=True)

    await update.message.reply_text(
        "👋 স্বাগতম KMK Wallet-এ!\n\n"
        "নিচের মেনু থেকে একটি অপশন নির্বাচন করুন।",
        reply_markup=kb
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    get_user(uid, update.effective_user.username)

    con = db()
    u = con.execute(
        "SELECT balance,pending,total_income,completed_tasks "
        "FROM users WHERE user_id=?",
        (uid,)
    ).fetchone()
    con.close()

    await update.message.reply_text(
        f"💰 <b>আপনার ব্যালেন্স</b>\n\n"
        f"💵 ব্যালেন্স: {u[0]:.2f} BDT\n"
        f"⏳ পেন্ডিং: {u[1]:.2f} BDT\n"
        f"💵 Total Income: {u[2]:.2f} BDT\n"
        f"✅ সম্পন্ন কাজ: {u[3]}টি\n"
        f"⏳ রিভিউতে: 0টি",
        parse_mode="HTML"
    )

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💼 <b>কাজ</b>\n\n"
        "এখানে অ্যাডমিন-যোগ করা কাজগুলো দেখানো হবে।\n"
        "বর্তমানে কোনো কাজ যোগ করা নেই।",
        parse_mode="HTML"
    )

async def referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    con = db()
    r = con.execute(
        "SELECT referrals FROM users WHERE user_id=?",
        (uid,)
    ).fetchone()
    con.close()

    count = r[0] if r else 0

    await update.message.reply_text(
        f"👥 <b>My Referrals</b>\n\n"
        f"আপনার রেফারেল: {count} জন\n\n"
        f"🔗 আপনার রেফারেল লিংক:\n"
        f"https://t.me/{context.bot.username}?start={uid}",
        parse_mode="HTML"
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 <b>টাকা উত্তোলন</b>\n\n"
        "উইথড্রল সিস্টেম চালু করতে অ্যাডমিনের "
        "পেমেন্ট পদ্ধতি ও ন্যূনতম উইথড্রল সীমা সেট করতে হবে।",
        parse_mode="HTML"
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 সাপোর্ট: আপনার সমস্যাটি লিখে পাঠান।"
    )

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆕 নতুন হলে /start চাপুন। "
        "তারপর কাজের তালিকা থেকে কাজ নির্বাচন করুন।"
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "💰 ব্যালেন্স":
        await balance(update, context)
    elif text == "💼 কাজ":
        await tasks(update, context)
    elif text == "💸 টাকা উত্তোলন":
        await withdraw(update, context)
    elif text == "👥 My Referrals":
        await referrals(update, context)
    elif text == "🆘 সাপোর্ট":
        await support(update, context)
    elif text == "🆕 আমি নতুন":
        await new_user(update, context)
    else:
        await update.message.reply_text(
            "অনুগ্রহ করে নিচের মেনু থেকে একটি অপশন নির্বাচন করুন।"
        )

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable সেট করা হয়নি।"
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("KMK Wallet bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
