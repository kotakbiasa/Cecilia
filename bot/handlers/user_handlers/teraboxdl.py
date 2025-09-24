import asyncio
import math
from html import escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.terabox import get_download_link

def format_size(size_bytes):
    """Formats size in bytes to a human-readable string."""
    if not size_bytes or size_bytes == 0:
        return "0B"
    try:
        size_bytes = int(size_bytes)
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
    except (ValueError, TypeError):
        return "N/A"

async def func_teraboxdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles Terabox download requests."""
    message = update.effective_message
    url = " ".join(context.args)

    if not url:
        await message.reply_text("Gunakan <code>/teraboxdl [URL Terabox]</code> untuk mengunduh.")
        return

    sent_message = await message.reply_text("🔍 Menganalisis tautan Terabox...")

    try:
        # Fungsi get_download_link sekarang menangani semua logika
        result = await asyncio.to_thread(get_download_link, url)

        if result.get('status') != 'success':
            error_msg = result.get("message", "Terjadi kesalahan yang tidak diketahui.")
            await sent_message.edit_text(f"❌ Gagal: {escape(error_msg)}")
            return

        file_name = result.get("file_name", "N/A")
        file_size = format_size(result.get("size"))
        download_link = result.get("download_link")

        buttons = [[InlineKeyboardButton("📥 Unduh File", url=download_link)]]
        reply_markup = InlineKeyboardMarkup(buttons)

        caption = (f"✅ Link unduhan siap!\n\n"
                   f"<b>Nama:</b> <code>{escape(file_name)}</code>\n"
                   f"<b>Ukuran:</b> <code>{file_size}</code>")

        await sent_message.edit_text(caption, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Gagal memproses TeraboxDL: {e}", exc_info=True)
        await sent_message.edit_text(f"Terjadi error yang tidak terduga: {escape(str(e))}")