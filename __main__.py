import logging

from telegram import Update, MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, InvalidCallbackData
from pyrogram import Client as MPTProtoClient

from yt_dlp import YoutubeDL, DownloadError
from os import getenv, remove
import urllib3
from io import BytesIO

__import__("dotenv").load_dotenv()

OWNER_USER_ID = int(getenv("OWNER_USER_ID") or 0)

ALLOWED_USER_IDS = [int(userid or 0) for userid in getenv("ALLOWED_USER_IDS").split(",")] + [OWNER_USER_ID]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
# fh = logging.FileHandler("bot_logs.log")
# fh.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
# logger.addHandler(fh)

TOKEN = getenv("TOKEN")

API_ID, API_HASH = getenv("API_ID"), getenv("API_HASH")

mtprotoclient = None
if API_ID and API_HASH:
    mtprotoclient = MPTProtoClient("bot", API_ID, API_HASH, bot_token=TOKEN, no_updates=True)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Welcome to the bot!\nYou can start downloading videos by simply sending the link(s)")

async def not_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"You're not allowed to use this bot.\nYour user id: {update.effective_user.id}")

async def handle_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for url in update.effective_message.parse_entities([MessageEntity.URL, MessageEntity.TEXT_LINK]).values():
        await show_download_options(url, update.effective_chat.id, context)



async def show_download_options(url: str, chat_id: int, context: ContextTypes.DEFAULT_TYPE):

    try:
        with YoutubeDL() as ydl:
            video_info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        if "Unsupported URL" in e.msg:
            await context.bot.send_message(chat_id, "Unsupported URL")
            return
        await context.bot.send_message(chat_id, e)
        if (chat_id != OWNER_USER_ID):
            await context.bot.send_message(OWNER_USER_ID, f"User {chat_id} just had the following exception:\n\n{e}")
        logger.error(e)
        return
    except Exception as e:
        await context.bot.send_message(chat_id, e)
        if (chat_id != OWNER_USER_ID):
            await context.bot.send_message(OWNER_USER_ID, f"User {chat_id} just had the following exception:\n\n{e}")
        logger.error(e)
        return
    
    params = {
        "thumbnail": video_info.get('thumbnail'),
        "duration": video_info.get('duration'),
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

    try:
        data["ytdl_options"]["outtmpl"] = "temp"
        with YoutubeDL(data["ytdl_options"]) as ydl:
            download_result = ydl.extract_info(data["url"])
        
        filename = "temp." + ("mp3" if data["audio"] else download_result["ext"])

        await msg.delete()

        thumb = download_result.get("thumbnail")

        if data["audio"]:
            msg = await update.effective_chat.send_message(
                "Sending audio file..."
            )
            await update.effective_chat.send_audio(
                audio=filename,
                performer = download_result.get("uploader"),
                title = download_result.get("title"),
                thumbnail = urllib3.request("GET", thumb).data if thumb else None
            )
            await msg.delete()
        else:
            msg = await update.effective_chat.send_message(
                "Sending video file..."
            )
            if mtprotoclient:
                await mtprotoclient.send_video(
                    chat_id=update.effective_chat.id,
                    video=filename,
                    duration=data.get("duration"),
                    thumb= BytesIO(urllib3.request("GET", thumb).data) if thumb else None,
                    width=download_result.get("width"),
                    height=download_result.get("height"),
                    supports_streaming=True
                )
            else:
                await update.effective_chat.send_video(
                    video=filename,
                    supports_streaming=True
                )
            await msg.delete()
    except Exception as e:
        await update.effective_chat.send_message(f"Something unexpected happened:\n\n{e}")
        if (update.effective_chat != OWNER_USER_ID):
            await context.bot.send_message(OWNER_USER_ID, f"User {update.effective_chat.id} just had the following exception:\n\n{e}")
        logger.error(e)
        return
    remove(filename)

async def invalid_callbackquery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(text='Button is no longer valid', show_alert=True)

async def post_init(application: Application):
    await mtprotoclient.start()


def main():
    application = Application.builder().token(TOKEN).arbitrary_callback_data(True).post_init(post_init).build()

    application.add_handler(MessageHandler(~filters.User(ALLOWED_USER_IDS), not_allowed))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Entity(MessageEntity.URL) | filters.Entity(MessageEntity.TEXT_LINK), handle_links))
    application.add_handler(CallbackQueryHandler(try_download, dict))
    application.add_handler(CallbackQueryHandler(invalid_callbackquery, InvalidCallbackData))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()