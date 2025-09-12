from pyrogram import filters
from pyrogram.types import Message
from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.base64 import BASE64

@bot.on_message(filters.command("decode", ["/", "!", "-", "."]))
async def func_decode(_, message: Message):
    re_msg = message.reply_to_message
    text = extract_cmd_args(message.text, message.command) or (re_msg.text or re_msg.caption if re_msg else None)

    if not text:
        await message.reply_text(f"Use `/{message.command[0]} base64code`\nor reply the base64code with `/{message.command[0]}`command.")
        return
    
    decodedText = BASE64.decode(text)
    await message.reply_text(f"`{decodedText}`" if decodedText else "Invalid base64!")
