from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot import logger
from bot.modules.re_link import RE_LINK
from bot.modules.tracemoe import get_anime_source

async def func_whatanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finds the anime source from an image."""
    message = update.effective_message
    re_msg = message.reply_to_message
    args = context.args
    image_url = None

    # Check for replied photo or sticker
    if re_msg:
        if re_msg.photo:
            photo = re_msg.photo[-1]
            file = await photo.get_file()
            image_url = file.file_path
        elif re_msg.sticker and not re_msg.sticker.is_animated and not re_msg.sticker.is_video:
            file = await re_msg.sticker.get_file()
            image_url = file.file_path

    # Check for URL in args if no reply
    elif args:
        arg_string = " ".join(args)
        links = RE_LINK.detectLinks(arg_string)
        if links:
            image_url = links[0]

    if not image_url:
        await message.reply_text(
            "Gunakan <code>/whatanime [URL gambar]</code> atau balas sebuah gambar/stiker dengan perintah ini.",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Mencari sumber anime, mohon tunggu...")

    try:
        response_data = await get_anime_source(image_url)

        if not response_data or not response_data.get("result"):
            await sent_message.edit_text("Maaf, tidak dapat menemukan sumber anime atau terjadi kesalahan pada API.")
            return

        # Get the first and most similar result
        anime_data = response_data["result"][0]

        # Prepare Anilist button if ID is available
        anilist_id = anime_data.get('anilist')
        reply_markup = None
        if anilist_id:
            anilist_url = f"https://anilist.co/anime/{anilist_id}"
            buttons = [[InlineKeyboardButton("Cari di Anilist", url=anilist_url)]]
            reply_markup = InlineKeyboardMarkup(buttons)

        # Format timestamps from seconds to MM:SS
        from_time = anime_data.get('from', 0)
        to_time = anime_data.get('to', 0)
        from_str = f"{int(from_time // 60):02d}:{int(from_time % 60):02d}"
        to_str = f"{int(to_time // 60):02d}:{int(to_time % 60):02d}"

        caption = (
            f"<b>Anime Ditemukan!</b>\n\n"
            f"<b>Judul:</b> <code>{anime_data.get('filename', 'N/A')}</code>\n"
            f"<b>Episode:</b> {anime_data.get('episode', 'N/A')}\n"
            f"<b>Waktu Adegan:</b> <code>{from_str} - {to_str}</code>\n"
            f"<b>Tingkat kemiripan:</b> {anime_data.get('similarity', 0) * 100:.2f}%"
        )

        if preview_video_url := anime_data.get("video"):
            await message.reply_video(video=preview_video_url, caption=caption, reply_markup=reply_markup)
            await sent_message.delete()
        else:
            # Fallback to image if video URL is not available
            if preview_image_url := anime_data.get("image"):
                await message.reply_photo(photo=preview_image_url, caption=caption, reply_markup=reply_markup)
                await sent_message.delete()
            else:
                await sent_message.edit_text(caption, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Gagal dalam proses whatanime: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")