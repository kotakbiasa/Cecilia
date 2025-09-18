import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_manga

def clean_html(raw_html: str) -> str:
    """Menghapus tag HTML dari string."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

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

        title = manga_data['title']['romaji']
        if manga_data['title']['english']:
            title = f"{title} ({manga_data['title']['english']})"
        
        description = clean_html(manga_data.get('description', 'Tidak ada deskripsi.'))
        if len(description) > 400:
            description = description[:400] + "..."

        status = manga_data.get('status', 'N/A').replace('_', ' ').title()
        
        caption = (
            f"<b>{title}</b>\n\n"
            f"<b>Format:</b> {manga_data.get('format', 'N/A')}\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Chapter:</b> {manga_data.get('chapters', 'N/A')}\n"
            f"<b>Volume:</b> {manga_data.get('volumes', 'N/A')}\n"
            f"<b>Skor:</b> {manga_data.get('averageScore', 0) / 10 if manga_data.get('averageScore') else 'N/A'}/10\n"
            f"<b>Genre:</b> {', '.join(manga_data.get('genres', []))}\n\n"
            f"<blockquote expandable>{description}</blockquote>"
        )

        buttons = [[InlineKeyboardButton("Lihat di Anilist", url=manga_data['siteUrl'])]]
        reply_markup = InlineKeyboardMarkup(buttons)

        thumbnail_url = manga_data.get('bannerImage') or manga_data.get('coverImage', {}).get('extraLarge')

        await message.reply_photo(photo=thumbnail_url, caption=caption, reply_markup=reply_markup)
        await sent_message.delete()

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian manga: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")