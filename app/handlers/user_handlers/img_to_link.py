from time import time

from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers import BuildKeyboard
from app.modules.freeimagehost import upload_image

@bot.on_message(filters.command("imgtolink", ["/", "!", "-", "."]))
async def func_imgtolink(_, message: Message):
    re_msg = message.reply_to_message

    if re_msg:
        if re_msg.photo:
            photo = re_msg.photo.file_id
        elif re_msg.document and "image" in re_msg.document.mime_type:
            photo = re_msg.document.file_id
        else:
            photo = None

    if not re_msg or not photo:
        await message.reply_text("Reply a photo to get a public link for that photo!")
        return
    
    sent_message = await message.reply_text(f"💭 Generating...")
    photo_path = await re_msg.download(f"/downloads/imgtolink_{int(time())}.png")

    response = await upload_image(photo_path)
    if not response:
        await sent_message.edit_text("Timeout! Please try again or report the issue." if response is False else "Oops! Something went wrong!")
        return
    
    image_data = response["image"]

    img_url = image_data.get("url")
    img_width = image_data.get("width")
    img_height = image_data.get("height")
    img_size = image_data.get("size_formatted")
    img_mime = image_data["image"]["mime"]

    text = (
        "↓ <u>**Image Details**</u> ↓\n"
        f"**- URL:** <a href='{img_url}'>◊ See Image ◊</a>\n"
        f"**- Width:** `{img_width}px`\n"
        f"**- Height:** `{img_height}px`\n"
        f"**- Size:** `{img_size}`\n"
        f"**- Mime:** `{img_mime}`"
    )

    btn = BuildKeyboard.ubutton([{"View 👀": img_url}])
    await sent_message.edit_text(text, reply_markup=btn)
