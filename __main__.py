import logging

from telegram import Update, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from yt_dlp import YoutubeDL, FFmpegPostProcessor
from os import getenv, remove
import urllib3

__import__("dotenv").load_dotenv()

OWNER_USER_ID = int(getenv("OWNER_USER_ID") or 0)

ALLOWED_USER_IDS = [int(userid or 0) for userid in getenv("ALLOWED_USER_IDS").split(",")] + [OWNER_USER_ID]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
# fh = logging.FileHandler("bot_logs.log")
# fh.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
# logger.addHandler(fh)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Welcome to the bot!\nYou can start downloading videos by simply sending the link(s)")

async def not_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"You're not allowed to use this bot.\nYour user id: {update.effective_user.id}")

async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for url in update.effective_message.parse_entities([MessageEntity.URL, MessageEntity.TEXT_LINK]).values():
        await show_download_options(url, update.effective_chat.id, context)

async def show_download_options(url: str, chat_id: int, context: ContextTypes.DEFAULT_TYPE):

    with YoutubeDL() as ydl:
        video_info = ydl.extract_info(url, download=False)

    params = {
        "thumbnail": video_info['thumbnail'],
        "duration": video_info['duration'],
        "url": url,
        "audio": False
    }

    keyboard = [
        [
            InlineKeyboardButton("Video, highest quality", callback_data=params | {
                "ytdl_options": {
                    "merge_output_format": "mp4",
                }
            })
        ],
        [
            InlineKeyboardButton("Video, lowest filesize", callback_data=params | {
                "ytdl_options": {
                    "merge_output_format": "mp4",
                    "format_sort": ["+size","+br","+res","+fps"]
                }
            })
        ],
        [
            InlineKeyboardButton("Audio", callback_data=params | {
                "ytdl_options": {
                    "format": "bestaudio",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3"
                        }
                    ]
                },
                "audio": True
            })
        ]
    ]

    

    if "thumbnail" in video_info:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=video_info['thumbnail'],
            caption=video_info.get('title'),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            caption=video_info.get('title') or "Video",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )



async def try_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = update.callback_query.data

    await update.effective_message.delete()
    msg = await update.effective_chat.send_message(
        "Downloading content..."
    )

    data["ytdl_options"]["outtmpl"] = "temp"
    with YoutubeDL(data["ytdl_options"]) as ydl:
        download_result = ydl.extract_info(data["url"])
        filename = "temp." + ("mp3" if data["audio"] else download_result["ext"])
    
    await msg.delete()

    if data["audio"]:
        msg = await update.effective_chat.send_message(
            "Sending audio file..."
        )
        await update.effective_chat.send_audio(
            audio=filename,
            performer = download_result.get("uploader"),
            title = download_result.get("title"),
            thumbnail = urllib3.request("GET", download_result.get("thumbnail")).data
        )
        await msg.delete()
    else:
        msg = await update.effective_chat.send_message(
            "Sending video file..."
        )
        await update.effective_chat.send_video(
            video=filename,
            supports_streaming=True
        )
        await msg.delete()
        
    remove(filename)


def main():
    application = Application.builder().token(getenv("TOKEN")).arbitrary_callback_data(True).build()

    application.add_handler(MessageHandler(~filters.User(ALLOWED_USER_IDS), not_allowed))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Entity(MessageEntity.URL) | filters.Entity(MessageEntity.TEXT_LINK), handle_links))
    application.add_handler(CallbackQueryHandler(try_download))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()