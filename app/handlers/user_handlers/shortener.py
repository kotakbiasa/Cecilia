from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.shrinkme import shortener_url

@bot.on_message(filters.command("shorturl", ["/", "!", "-", "."]))
async def func_shorturl(_, message: Message):
    re_msg = message.reply_to_message
    url = (re_msg.text or re_msg.caption) if re_msg else extract_cmd_args(message.text, message.command)

    if not url:
        await message.reply_text(f"Use `/{message.command[0]} url`\nor reply the url with `/{message.command[0]}` command.\nE.g. `/{message.command[0]} https://google.com`")
        return
    
    shortedURL = await shortener_url(url) or "Oops! Something went wrong!"
    await message.reply_text(shortedURL)
