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

        caption = build_anime_info_message_md(anime_data)
        
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

        image = anime_data.get("bannerImage") or anime_data.get("coverImage", {}).get("extraLarge")

        if image:
            try:
                await message.reply_photo(
                    photo=image,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup,
                )
                await sent_message.delete()
            except Exception:
                # Fallback jika reply_photo gagal (misal, karena gambar terlalu besar atau format tidak didukung)
                caption += f" [⁠]({image})" # Tambahkan link gambar tersembunyi
                await sent_message.edit_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        else:
            await sent_message.edit_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian anime: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")