from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_manga
from bot.handlers.query_handlers.message_builder import build_manga_info_message

async def func_manga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mencari informasi manga di Anilist."""
    message = update.effective_message
    query = " ".join(context.args)

    if not query:
        await message.reply_text("Gunakan <code>/manga [nama manga]</code>.")
        return

    sent_message = await message.reply_text("Mencari manga di Anilist...")

    try:
        manga_data = await search_manga(query)

        if not manga_data:
            await sent_message.edit_text(f"Maaf, manga dengan nama '<code>{query}</code>' tidak ditemukan.")
            return

        caption = await build_manga_info_message(manga_data)

        buttons = [[InlineKeyboardButton("Lihat di Anilist", url=manga_data['siteUrl'])]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Coba dapatkan URL gambar dari beberapa sumber, utamakan banner
        image_url = manga_data.get('bannerImage') or manga_data.get('coverImage', {}).get('extraLarge')
        final_caption = caption
        disable_preview = True

        if image_url:
            # Tambahkan zero-width space dengan link gambar untuk membuat pratinjau di atas teks
            final_caption = f"<a href='{image_url}'>&#8203;</a>{caption}"
            disable_preview = False

        # Edit pesan yang sudah ada untuk menampilkan hasil
        await sent_message.edit_text(
            text=final_caption,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview
        )

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian manga: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")