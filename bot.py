from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp
import os
import uuid

BOT_TOKEN = '7677692942:AAELv-HwgUh37NAHN6bGAJUWxUXHwz4Ny10'
LINK_QUALITY = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a YouTube link to download.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Please send a valid YouTube link.")
        return

    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])

        keyboard = []
        buttons_added = set()
        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("filesize") and f["format_note"] not in buttons_added:
                buttons_added.add(f["format_note"])
                keyboard.append([InlineKeyboardButton(f["format_note"], callback_data=f"{url}|{f['format_id']}")])

        LINK_QUALITY[update.effective_chat.id] = url
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose the quality:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    url = data[0]
    format_id = data[1]
    filename = f"video_{uuid.uuid4()}.mp4"

    ydl_opts = {
        'format': format_id,
        'outtmpl': filename,
    }

    try:
        await query.edit_message_text("Downloading...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, 'rb') as f:
            await query.message.reply_video(f)

        os.remove(filename)

    except Exception as e:
        await query.message.reply_text(f"Failed: {str(e)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button_click))

app.run_polling()
