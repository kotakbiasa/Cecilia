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

        caption = build_manga_info_message(manga_data)

        buttons = [[InlineKeyboardButton("Lihat di Anilist", url=manga_data['siteUrl'])]]
        reply_markup = InlineKeyboardMarkup(buttons)

        thumbnail_url = manga_data.get('bannerImage') or manga_data.get('coverImage', {}).get('extraLarge')

        await message.reply_photo(photo=thumbnail_url, caption=caption, reply_markup=reply_markup)
        await sent_message.delete()

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian manga: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")