from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.re_link import RE_LINK
from bot.modules.ryzumi_api import get_negro_image

async def func_penghitaman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    re_msg = message.reply_to_message
    args = context.args
    image_url = None
    filter_name = None

    if re_msg and re_msg.photo:
        # Get the largest photo from the replied message
        photo = re_msg.photo[-1]
        file = await photo.get_file()
        image_url = file.file_path  # This is the URL to the file on Telegram's servers
        if args:
            filter_name = args[0]
    elif args:
        # When no reply, args can be [url], [filter] [url], or [url] [filter]
        arg_string = " ".join(args)
        links = RE_LINK.detectLinks(arg_string)
        if links:
            image_url = links[0]
            # The rest of the string is the filter
            filter_text = arg_string.replace(image_url, "").strip()
            if filter_text:
                filter_name = filter_text.split()[0]  # Take the first word

    if not image_url:
        await message.reply_text(
            "Gunakan <code>/hitamkan [filter] [URL gambar]</code> atau balas sebuah gambar waifu dengan perintah <code>/hitamkan [filter]</code>.\n\n"
            "<b>Filter yang tersedia:</b> <code>coklat</code>, <code>hitam</code>, <code>nerd</code>, "
            "<code>piggy</code>, <code>carbon</code>, <code>botak</code>.",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Sedang menghitamkan waifu...")

    try:
        image_bytes = await get_negro_image(image_url, filter_name)

        if not image_bytes:
            await sent_message.edit_text("Maaf, gagal memproses gambar. API mungkin sedang down atau URL tidak valid.")
            return

        caption = f"Ini waifu yang telah dihitamkan dengan filter '{filter_name}'." if filter_name else "Ini gambar yang telah dihitamkan."
        await message.reply_photo(photo=image_bytes, caption=caption)
        await sent_message.delete()
    except Exception as e:
        logger.error(f"Gagal dalam proses penghitaman: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")