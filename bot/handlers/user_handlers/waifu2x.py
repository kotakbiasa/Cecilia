from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.re_link import RE_LINK
from bot.modules.ryzumi_api import get_waifu2x_image

async def func_waifu2x(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upscales an image using the Waifu2x API."""
    message = update.effective_message
    re_msg = message.reply_to_message
    args = context.args
    image_url = None

    # Case 1: The command is a reply to a message with a photo.
    if re_msg and re_msg.photo:
        photo = re_msg.photo[-1]  # Get the highest resolution photo
        file = await photo.get_file()
        image_url = file.file_path  # This is the temporary URL from Telegram's servers

    # Case 2: An image URL is provided in the command arguments.
    elif args:
        arg_string = " ".join(args)
        links = RE_LINK.detectLinks(arg_string)
        if links:
            image_url = links[0]

    # If no image URL is found, send a help message.
    if not image_url:
        await message.reply_text(
            "Gunakan <code>/waifu2x [URL gambar]</code> atau balas sebuah gambar dengan perintah <code>/waifu2x</code> untuk meningkatkan resolusi gambar.",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text(
        "Sedang meningkatkan resolusi gambar, proses ini mungkin memakan waktu beberapa menit. Mohon tunggu..."
    )

    try:
        image_bytes = await get_waifu2x_image(image_url)

        if not image_bytes:
            await sent_message.edit_text("Maaf, gagal memproses gambar. Pastikan URL valid dan API dapat diakses.")
            return

        caption = "Ini gambar yang telah ditingkatkan resolusinya."
        await message.reply_document(document=image_bytes, caption=caption, filename="waifu2x_upscaled.png")
        await sent_message.delete()
    except Exception as e:
        logger.error(f"Gagal dalam proses Waifu2x: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")