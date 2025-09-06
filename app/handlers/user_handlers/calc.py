from pyrogram import filters
from pyrogram.types import Message
from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.utils import UTILITY

@bot.on_message(filters.command("decode", ["/", "!", "-", "."]))
async def func_calc(_, message: Message):
    re_msg = message.reply_to_message
    text = extract_cmd_args(message.text, message.command) or (re_msg.text or re_msg.caption if re_msg else None)

    if not text:
        await message.reply_text(f"Use `/{message.command[0]} math`\nor reply the math with `/{message.command[0]}` command.\nE.g. `/{message.command[0]} (980 - 80) + 100 / 4 * 4 - 20`")
        return
    
    res, output = UTILITY.calculator(text)
    await message.reply_text(f"Calculation: `{output}`" if res else f"Error: {output.msg}")
