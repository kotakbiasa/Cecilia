import os
from telegram import Update
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.ryzumi_api import get_ytmp3_media, get_ytmp4_media
from bot.modules.yt_search import search_youtube
from bot import logger
from bot.modules.ytdlp import youtube_download

async def _download_and_send_audio(message, youtube_link: str):
    """Helper function to download audio from a YouTube link and send it."""
    try:
        response_data = await get_ytmp3_media(youtube_link)
        if not (response_data and response_data.get("url")):
            error_detail = response_data.get("message", "Pastikan URL valid.") if response_data else "Gagal mendapatkan respons dari API."
            await message.edit_caption(caption=f"Maaf, gagal memproses permintaan audio. {error_detail}")
            return

        audio_url = response_data["url"]
        title = response_data.get("title", "Audio YouTube")
        thumbnail_url = response_data.get("thumbnail")
        thumbnail_content = None

        await message.edit_caption(caption="Mengunduh audio ke server...")
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url, timeout=300) as resp:
                if not resp.ok:
                    await message.edit_caption(caption=f"Gagal mengunduh audio. Coba manual: {audio_url}")
                    return
                audio_content = await resp.read()

            if thumbnail_url:
                async with session.get(thumbnail_url) as thumb_resp:
                    if thumb_resp.ok:
                        thumbnail_content = await thumb_resp.read()

        await message.edit_caption(caption="Mengunggah audio ke Telegram...")
        performer = response_data.get("author", "Unknown")
        views = response_data.get("views", 0)
        author_url = response_data.get("authorUrl")
        video_url = response_data.get("videoUrl", youtube_link)
        artist_line = f"<a href='{author_url}'>{performer}</a>" if author_url else performer
        caption = (
            f"<b>{title}</b>\n\n"
            f"<b>Artis:</b> {artist_line}\n"
            f"<b>Dilihat:</b> {views:,}\n\n"
            f"<b>Source:</b> <a href='{video_url}'>YouTube</a>"
        )
        await message.reply_audio(audio=audio_content, title=title, performer=performer, caption=caption, thumbnail=thumbnail_content, write_timeout=600)
        await message.delete()
    except Exception as e:
        logger.error(f"Gagal mengirim audio YouTube: {e}")
        await message.edit_caption(caption="Gagal mengirim audio. Kemungkinan file terlalu besar atau terjadi error.")

async def _download_and_send_video(message, youtube_link: str, quality: str):
    """Helper function to download video from a YouTube link and send it."""
    try:
        response_data = await get_ytmp4_media(youtube_link, quality)
        if not (response_data and response_data.get("url")):
            error_detail = response_data.get("message", "Kualitas tidak tersedia.") if response_data else "Gagal mendapatkan respons dari API."
            await message.edit_caption(caption=f"Maaf, gagal memproses permintaan video. {error_detail}")
            return

        video_url = response_data["url"]
        title = response_data.get("title", "Video YouTube")
        await message.edit_caption(caption="Mengirim video ke Telegram...")
        performer = response_data.get("author", "Unknown")
        views = response_data.get("views", 0)
        author_url = response_data.get("authorUrl")
        video_url_page = response_data.get("videoUrl", youtube_link)
        artist_line = f"<a href='{author_url}'>{performer}</a>" if author_url else performer
        caption = (
            f"<b>{title}</b>\n\n"
            f"<b>Artis:</b> {artist_line}\n"
            f"<b>Dilihat:</b> {views:,}\n\n"
            f"<b>Source:</b> <a href='{video_url_page}'>YouTube</a>"
        )
        await message.reply_video(video=video_url, caption=caption, write_timeout=600)
        await message.delete()
    except Exception as e:
        logger.error(f"Gagal mengirim video YouTube: {e}")
        await message.edit_caption(caption="Gagal mengirim video. Kemungkinan file terlalu besar atau terjadi error.")

async def func_ytdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    query_or_link = " ".join(context.args)

    if not query_or_link:
        await message.reply_text(
            "Gunakan <code>/ytdl [URL atau Judul]</code> untuk mencari atau mengunduh dari YouTube.\n"
            "Contoh: <code>/ytdl Oasis - Stand By Me</code>",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Mencari...")
    if "youtube.com" in query_or_link or "youtu.be" in query_or_link:
        video_link = query_or_link
        results = await search_youtube(video_link, limit=1)
        if not results:
            await sent_message.edit_text("Gagal mendapatkan detail video dari link.")
            return
        video_title = results[0].get('title')
        thumbnail = results[0].get('thumbnail')
    else:
        results = await search_youtube(query_or_link, limit=1)
        if not results:
            await sent_message.edit_text(f"Tidak ada hasil yang ditemukan untuk '<code>{query_or_link}</code>'.")
            return
        video_link = results[0].get('link')
        video_title = results[0].get('title')
        thumbnail = results[0].get('thumbnail')

    context.user_data['ytdl_link'] = video_link
    keyboard = [
        [
            InlineKeyboardButton("🎧 Audio", callback_data="ytdl:format:audio"),
            InlineKeyboardButton("🎬 Video", callback_data="ytdl:format:video"),
        ]
    ]
    await sent_message.delete()
    await message.reply_photo(
        photo=thumbnail,
        caption=f"Video ditemukan: <b>{video_title}</b>\n\nPilih format yang diinginkan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ytdl_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data.split(':')
    action_type = callback_data[1]

    youtube_link = context.user_data.get('ytdl_link')
    if not youtube_link:
        await query.edit_message_caption(caption="Sesi telah berakhir. Silakan mulai lagi dengan perintah /ytdl.", reply_markup=None)
        return

    if action_type == "format":
        media_format = callback_data[2]
        if media_format == "audio":
            await query.edit_message_caption(caption="Memproses audio...", reply_markup=None)
            await _download_and_send_audio(query.message, youtube_link)
        elif media_format == "video":
            keyboard = [
                [
                    InlineKeyboardButton("480p", callback_data="ytdl:quality:480"),
                    InlineKeyboardButton("720p", callback_data="ytdl:quality:720"),
                ]
            ]
            await query.edit_message_caption(caption="Pilih kualitas video:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action_type == "quality":
        quality = callback_data[2]
        await query.edit_message_caption(caption=f"Memproses video {quality}p...", reply_markup=None)
        await _download_and_send_video(query.message, youtube_link, quality)
