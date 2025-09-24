import asyncio
import math
from html import escape

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.terabox import get_info, get_download_link, extract_shorturl

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
        shorturl = extract_shorturl(url)
        if not shorturl:
            await sent_message.edit_text("URL Terabox tidak valid. Pastikan URL Anda benar.")
            return

        await sent_message.edit_text(f"ℹ️ Mendapatkan informasi file untuk <code>{shorturl}</code>...")
        
        info = await asyncio.to_thread(get_info, shorturl)

        if not info or not info.get("ok"):
            error_msg = info.get("message", "Gagal mendapatkan informasi dari API.") if info else "API tidak merespons."
            await sent_message.edit_text(f"❌ Gagal: {escape(error_msg)}")
            return

        if not info.get("list"):
            await sent_message.edit_text("❌ Tidak ada file yang ditemukan di tautan ini.")
            return

        # For simplicity, we'll process the first file in the list.
        file_data = info["list"][0]
        file_name = file_data.get("server_filename", "N/A")
        file_size = format_size(file_data.get("size"))

        await sent_message.edit_text(
            f"✅ File ditemukan!\n\n"
            f"<b>Nama:</b> <code>{escape(file_name)}</code>\n"
            f"<b>Ukuran:</b> <code>{file_size}</code>\n\n"
            f"🔗 Mendapatkan link unduhan..."
        )

        params = {
            'shareid': int(info['shareid']),
            'uk': int(info['uk']),
            'sign': str(info['sign']),
            'timestamp': int(info['timestamp']),
            'fs_id': int(file_data['fs_id'])
        }

        download_info = await asyncio.to_thread(get_download_link, params, shorturl=shorturl)

        if not download_info or not download_info.get("ok") or not download_info.get("downloadLink"):
            error_msg = download_info.get("message", "Gagal mendapatkan link unduhan.") if download_info else "API tidak merespons."
            await sent_message.edit_text(f"❌ Gagal: {escape(error_msg)}")
            return

        download_link = download_info["downloadLink"]
        buttons = [[InlineKeyboardButton("📥 Unduh File", url=download_link)]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await sent_message.edit_text(f"✅ Link unduhan siap!\n\n<b>Nama:</b> <code>{escape(file_name)}</code>", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Gagal memproses TeraboxDL: {e}", exc_info=True)
        await sent_message.edit_text(f"Terjadi error yang tidak terduga: {escape(str(e))}")