from pyrogram import filters
from pyrogram.types import Message
from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.base64 import BASE64

@bot.on_message(filters.command("encode", ["/", "!", "-", "."]))
async def func_encode(_, message: Message):
    re_msg = message.reply_to_message
    text = extract_cmd_args(message.text, message.command) or (re_msg.text or re_msg.caption if re_msg else None)

    if not text:
        await message.reply_text(f"Use `/{message.command[0]} text`\nor reply any text with `/{message.command[0]}`command.")
        return
    
    encodedText = BASE64.encode(text)
    await message.reply_text(f"`{encodedText}`" if encodedText else "Invalid text!")
