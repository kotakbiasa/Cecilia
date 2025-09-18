import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from bot.modules.ryzumi_api import get_pinterest_media
from bot import logger

async def func_pinterestdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    pinterest_link = " ".join(context.args)

    if not pinterest_link or "pinterest.com" not in pinterest_link:
        await message.reply_text(
            "Gunakan <code>/pinterestdl [URL]</code> untuk mengunduh media dari"
            " Pinterest.\n"
            "Contoh: <code>/pinterestdl https://id.pinterest.com/pin/25614291625233634/</code>",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Mengunduh...")
    data = await get_pinterest_media(pinterest_link)
    if data and data.get("success") and isinstance(data.get("media"), list) and data["media"]:
        media_list = data["media"]
        # Ambil URL dari media pertama dalam daftar
        media_url = media_list[0].get("url")

        if not media_url:
            await sent_message.edit_text("Maaf, API tidak mengembalikan URL media.")
            return
        try:
            await sent_message.edit_text("Mengunduh media ke server...")
            async with aiohttp.ClientSession() as session:
                async with session.get(media_url, timeout=300) as resp:
                    if not resp.ok:
                        await sent_message.edit_text(f"Gagal mengunduh media dari sumber. Coba unduh manual: {media_url}")
                        return
                    media_content = await resp.read()

            await sent_message.edit_text("Mengunggah media...")
            caption = "Ini media Anda!"
            file_ext = media_url.split('.')[-1].lower().split('?')[0]

            if file_ext in ("jpg", "jpeg", "png"):
                await message.reply_photo(photo=media_content, caption=caption, write_timeout=300)
            elif file_ext in ("mp4", "gif"):
                await message.reply_video(video=media_content, caption=caption, write_timeout=300)
            else:
                await message.reply_document(document=media_content, caption=caption, write_timeout=300)
            await sent_message.delete()
        except Exception as e:
            logger.error(f"Gagal mengirim media Pinterest: {e}")
            await sent_message.edit_text(
                f"Gagal mengirim media. Kemungkinan file terlalu besar atau terjadi error. Coba unduh manual: {media_url}"
            )
    else:
        error_detail = (
            data.get("result")
            if data and isinstance(data.get("result"), str)
            else "Pastikan URL valid."
        )
        await sent_message.edit_text(
            f"Maaf, gagal mengunduh media. {error_detail}"
        )
