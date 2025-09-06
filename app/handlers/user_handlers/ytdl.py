import os
from time import time

from pyrogram import filters
from pyrogram.types import Message

from app import bot, logger
from app.helpers.args_extractor import extract_cmd_args
from app.helpers.progress_updater import progress_updater
from app.modules.ytdlp import youtube_download

@bot.on_message(filters.command("ytdl", ["/", "!", "-", "."]))
async def func_ytdl(_, message: Message):
    url = extract_cmd_args(message.text, message.command)

    if not url or not url.startswith("http"):
        await message.reply_text(f"Download audio/song from youtube. E.g. `/{message.command[0]} url`")
        return
    
    sent_message = await message.reply_text("Downloading...")

    response = youtube_download(url)
    if not isinstance(response, dict):
        await sent_message.edit_text(f"Error: {response}")
        return
    
    file_name = f"{response['title']}.mp3"
    file_path = response["file_path"]

    try:
        startTime = time()
        text = (
            f"Uploading...\n"
            f"**File:** `{file_name}`"
        )
        await message.reply_audio(file_path, title=file_name, progress=progress_updater, progress_args=[message, text, startTime])
    except Exception as e:
        await sent_message.edit_text(str(e))
    
    try:
        os.remove(response["file_path"])
    except Exception as e:
        logger.error(e)
