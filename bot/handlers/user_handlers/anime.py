from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot import logger
from bot.modules.anilist import search_anime
from bot.handlers.query_handlers.message_builder import (
    build_anime_info_message_md
)

async def func_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mencari informasi anime di Anilist."""
    message = update.effective_message
    query = " ".join(context.args)

    if not query:
        await message.reply_text(
            "Format : /anime <nama anime>"
        )
        return

    sent_message = await message.reply_text("Mencari anime di Anilist...")

    try:
        anime_data = await search_anime(query)

        if not anime_data:
            await sent_message.edit_text("Anime tidak ditemukan.")
            return

        caption = await build_anime_info_message_md(anime_data)
        
        info_url = anime_data.get("siteUrl")
        trailer_url = None
        trailer_data = anime_data.get("trailer")
        if trailer_data and trailer_data.get("site") == "youtube":
            trailer_url = f"https://youtu.be/{trailer_data.get('id')}"

        buttons = []
        row = [InlineKeyboardButton("More Info", url=info_url)]
        if trailer_url:
            row.append(InlineKeyboardButton("Trailer 🎬", url=trailer_url))
        buttons.append(row)
        reply_markup = InlineKeyboardMarkup(buttons)

        # Gunakan img.anili.st sebagai sumber utama, dengan fallback ke banner/cover image
        primary_image_url = None
        if site_url := anime_data.get('siteUrl'):
            primary_image_url = site_url.replace("anilist.co/anime/", "img.anili.st/media/")
        fallback_image_url = anime_data.get('bannerImage') or anime_data.get('coverImage', {}).get('extraLarge')
        image_url = primary_image_url or fallback_image_url

        if image_url:
            # Kirim sebagai foto dengan caption untuk memastikan gambar di atas
            try:
                await message.reply_photo(photo=image_url, caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                await sent_message.delete()
            except Exception as e:
                logger.error(f"Gagal mengirim foto untuk anime, mencoba mengirim sebagai teks: {e}")
                # Fallback jika pengiriman foto gagal (misal, URL tidak valid)
                await sent_message.edit_text(text=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            # Jika tidak ada gambar, edit pesan yang ada
            await sent_message.edit_text(text=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian anime: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")