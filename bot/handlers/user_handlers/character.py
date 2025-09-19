import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from html import escape
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_character

def clean_html(raw_html: str) -> str:
    """Menghapus tag HTML dari string."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

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

        title = char_data['name']['full']
        if char_data['name']['native']:
            title = f"{title} ({char_data['name']['native']})"
        
        description = clean_html(char_data.get('description', 'Tidak ada deskripsi.'))
        if len(description) > 400:
            description = description[:400] + "..."

        caption_parts = [f"<b>{title}</b>"]

        if description and description != 'Tidak ada deskripsi.':
            caption_parts.append(f"\n\n<blockquote expandable>{description}</blockquote>")

        # Add media information from the response
        media_nodes = char_data.get('media', {}).get('nodes', [])
        if media_nodes:
            media_list = []
            # Limit to 5 to avoid a very long message
            for media in media_nodes[:5]:
                # Prefer userPreferred, fallback to romaji
                media_title = media.get('title', {}).get('userPreferred') or media.get('title', {}).get('romaji')
                if media_title:
                    media_list.append(f"• <code>{escape(media_title)}</code>")
            
            if media_list:
                caption_parts.append("\n\n<b>Muncul di:</b>\n" + "\n".join(media_list))

        caption = "".join(caption_parts)

        buttons = [[InlineKeyboardButton("Lihat di Anilist", url=char_data['siteUrl'])]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_photo(photo=char_data['image']['large'], caption=caption, reply_markup=reply_markup)
        await sent_message.delete()

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian karakter: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")