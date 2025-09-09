from time import time

from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.qr import QR

@bot.on_message(filters.command("genqr", ["/", "!", "-", "."]))
async def func_genqr(_, message: Message):
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message
    data = extract_cmd_args(message.txt, message.command) or (re_msg.text or re_msg.caption if re_msg else None)

    if not data:
        await message.reply_text(f"Use `/{message.command[0]} url/data/text` to generate a QR code.\nor reply the 'url/data/text' with `/{message.command[0]}` command.\nE.g. `/{message.command[0]} https://google.com`")
        return

    start_time = time()
    response = QR.generate_qr(data)
    response_time = f"{((time() - start_time) * 1000):.2f}ms"

    if not response:
        await message.reply_text("Oops! Something went wrong!")
        return
    
    caption = (
        f"**Data:** `{data}`\n"
        f"**R.time:** `{response_time}`\n"
        f"**Req by:** {user.mention} | `{user.id}`"
    )

    await message.reply_photo(response, caption=caption)
