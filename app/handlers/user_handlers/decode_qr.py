from time import time

from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.modules.qr import QR

@bot.on_message(filters.command("decqr", ["/", "!", "-", "."]))
async def func_decqr(_, message: Message):
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message

    if not re_msg or not (re_msg.photo or re_msg.document):
        await message.reply_text(f"Reply a QR code image using /{message.command[0]} to decode it!")
        return
    
    if re_msg.document and not "image" in re_msg.document.mime_type:
        await message.reply_text("Replied message isn't an image!")
        return
    
    image = re_msg.photo or re_msg.document
    if isinstance(image, tuple): image = image[-1]
    
    if re_msg.photo:
        sent_message = await message.reply_photo(image.file_id, caption="Please wait...")
    else:
        sent_message = await message.reply_document(image.file_id, caption="Please wait...")
    
    # Reading Image file in memory
    image_data = await re_msg.download(f"/downloads/qrimage_{int(time())}.png", True)

    start_time = time()
    response = QR.decode_qr(image_data)
    response_time = f"{((time() - start_time) * 1000):.2f}ms"

    if response:
        text = (
            f"**Decoded Data:** `{response.data.decode()}`\n"
            f"**Type:** `{response.type}`\n"
            f"**R.time:** `{response_time}`\n"
            f"**Req by:** {user.mention} | `{user.id}`"
        )
    else:
        text = "Oops! Something went wrong!"

    await sent_message.edit_caption(text)
