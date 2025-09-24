from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from html import escape
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_character
from bot.handlers.query_handlers.message_builder import build_character_info_message

async def func_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mencari karakter di Anilist."""
    message = update.effective_message
    query = " ".join(context.args)

    if not query:
        await message.reply_text("Gunakan <code>/character [nama karakter]</code>.")
        return

    sent_message = await message.reply_text("Mencari karakter...")

    try:
        char_data = await search_character(query)

        if not char_data:
            await sent_message.edit_text(f"Karakter '<code>{query}</code>' tidak ditemukan.")
            return

        caption = build_character_info_message(char_data)

        buttons = [[InlineKeyboardButton("Lihat di Anilist", url=char_data['siteUrl'])]]
        reply_markup = InlineKeyboardMarkup(buttons)

        image_url = char_data.get('image', {}).get('large')
        final_caption = caption
        disable_preview = True

        if image_url:
            final_caption = f"<a href='{image_url}'>&#8203;</a>{caption}"
            disable_preview = False

        await sent_message.edit_text(
            text=final_caption,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview
        )

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian karakter: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")