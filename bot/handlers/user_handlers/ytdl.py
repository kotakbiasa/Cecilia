import os
from telegram import Update
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.ryzumi_api import get_ytmp3_media, get_ytmp4_media
from bot.modules.yt_search import search_youtube
from bot.modules.re_link import RE_LINK
from bot import logger
from bot.modules.ytdlp import youtube_download

async def _download_and_send_audio(message, youtube_link: str):
    """Helper function to download audio from a YouTube link and send it."""
    try:
        # --- Metode 1: Ryzumi API ---
        await message.edit_caption(caption="Mencoba mengunduh via API...")
        response_data = await get_ytmp3_media(youtube_link)
        audio_url = response_data.get("url") if response_data else None

        if isinstance(audio_url, str) and audio_url.startswith("http"):
            try:
                title = response_data.get("title", "Audio YouTube")
                thumbnail_url = response_data.get("thumbnail")
                thumbnail_content = None

                await message.edit_caption(caption="Mengunduh audio ke server...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url, timeout=300) as resp:
                        if not resp.ok:
                            raise ValueError(f"API download failed with status {resp.status}")
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
                return  # Sukses dengan API
            except Exception as api_e:
                logger.warning(f"Metode API gagal: {api_e}. Beralih ke yt-dlp.")

        logger.warning(f"API ytmp3 gagal atau mengembalikan URL tidak valid: {audio_url}. Beralih ke yt-dlp.")

        # --- Metode 2: yt-dlp Fallback ---
        await message.edit_caption(caption="API gagal, mencoba dengan metode unduh alternatif (yt-dlp)...")
        download_info = await youtube_download(url=youtube_link, is_video=False)

        if not download_info or not download_info.get('filepath'):
            await message.edit_caption(caption="Maaf, semua metode unduhan gagal. Video mungkin dilindungi atau tidak tersedia.")
            return

        filepath = download_info['filepath']
        title = download_info.get('title', 'Audio YouTube')
        performer = download_info.get('artist')
        duration = download_info.get('duration')
        thumbnail_path = download_info.get('thumbnail_path')
        
        thumbnail_content = None
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as f:
                thumbnail_content = f.read()

        caption = f"<b>{title}</b>\n\n<i>Diunduh dengan yt-dlp.</i>"

        await message.edit_caption(caption="Mengunggah audio ke Telegram...")
        with open(filepath, 'rb') as f:
            await message.reply_audio(
                audio=f, 
                title=title, 
                performer=performer, 
                caption=caption, 
                thumbnail=thumbnail_content, 
                duration=int(duration) if duration else None,
                write_timeout=600
            )
        await message.delete()
        
        # Cleanup
        try:
            os.remove(filepath)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except OSError as e:
            logger.error(f"Error membersihkan file yt-dlp: {e}")

    except Exception as e:
        logger.error(f"Gagal mengirim audio YouTube: {e}", exc_info=True)
        await message.edit_caption(caption="Gagal mengirim audio. Kemungkinan file terlalu besar atau terjadi error.")

async def _download_and_send_video(message, youtube_link: str, quality: str):
    """Helper function to download video from a YouTube link and send it."""
    try:
        # --- Metode 1: Ryzumi API ---
        await message.edit_caption(caption=f"Mencoba mengunduh video {quality}p via API...")
        response_data = await get_ytmp4_media(youtube_link, quality)
        video_url = response_data.get("url") if response_data else None

        if isinstance(video_url, str) and video_url.startswith("http"):
            try:
                title = response_data.get("title", "Video YouTube")
                await message.edit_caption(caption="Mengunduh video ke server...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url, timeout=600) as resp:
                        if not resp.ok:
                            raise ValueError(f"API download failed with status {resp.status}")
                        video_content = await resp.read()

                await message.edit_caption(caption="Mengunggah video ke Telegram...")
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
                await message.reply_video(video=video_content, caption=caption, write_timeout=600)
                await message.delete()
                return  # Sukses dengan API
            except Exception as api_e:
                logger.warning(f"Metode API untuk video gagal: {api_e}. Beralih ke yt-dlp.")

        logger.warning(f"API ytmp4 gagal atau mengembalikan URL tidak valid: {video_url}. Beralih ke yt-dlp.")

        # --- Metode 2: yt-dlp Fallback ---
        await message.edit_caption(caption="API gagal, mencoba dengan metode unduh alternatif (yt-dlp)...")
        download_info = await youtube_download(url=youtube_link, is_video=True, quality=quality)

        if not download_info or not download_info.get('filepath'):
            await message.edit_caption(caption="Maaf, semua metode unduhan gagal. Video mungkin dilindungi atau tidak tersedia.")
            return

        filepath = download_info['filepath']
        title = download_info.get('title', 'Video YouTube')
        duration = download_info.get('duration')
        width = download_info.get('width')
        height = download_info.get('height')
        thumbnail_path = download_info.get('thumbnail_path')
        
        thumbnail_content = None
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as f:
                thumbnail_content = f.read()

        caption = f"<b>{title}</b>\n\n<i>Diunduh dengan yt-dlp.</i>"

        await message.edit_caption(caption="Mengunggah video ke Telegram...")
        with open(filepath, 'rb') as f:
            await message.reply_video(
                video=f, 
                caption=caption, 
                duration=int(duration) if duration else None,
                width=width,
                height=height,
                thumbnail=thumbnail_content,
                write_timeout=600
            )
        await message.delete()
        
        # Cleanup
        try:
            os.remove(filepath)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except OSError as e:
            logger.error(f"Error membersihkan file yt-dlp: {e}")

    except Exception as e:
        logger.error(f"Gagal mengirim video YouTube: {e}", exc_info=True)
        await message.edit_caption(caption="Gagal mengirim video. Kemungkinan file terlalu besar atau terjadi error.")

async def func_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    query_or_link = " ".join(context.args)

    if not query_or_link:
        await message.reply_text(
            "Gunakan <code>/youtube [URL atau Judul]</code> untuk mencari atau mengunduh dari YouTube.\n"
            "Contoh: <code>/youtube Oasis - Stand By Me</code>",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Mencari...")

    # Try to find a YouTube link first
    links = RE_LINK.detectLinks(query_or_link)
    video_link = None
    for link in links:
        if "youtube.com" in link or "youtu.be" in link:
            video_link = link
            break

    if video_link:
        # A link was found, proceed with it
        results = await search_youtube(video_link, limit=1)
        if not results:
            await sent_message.edit_text("Gagal mendapatkan detail video dari link.")
            return
        video_title = results[0].get('title')
        thumbnail = results[0].get('thumbnail')
    else:
        # No link found, treat the whole thing as a search query
        results = await search_youtube(query_or_link, limit=1)
        if not results:
            await sent_message.edit_text(f"Tidak ada hasil yang ditemukan untuk '<code>{query_or_link}</code>'.")
            return
        video_link = results[0].get('link')
        video_title = results[0].get('title')
        thumbnail = results[0].get('thumbnail')

    context.user_data['youtube_link'] = video_link
    keyboard = [
        [
            InlineKeyboardButton("🎧 Audio", callback_data="youtube:format:audio"),
            InlineKeyboardButton("🎬 Video", callback_data="youtube:format:video"),
        ]
    ]
    await sent_message.delete()
    await message.reply_photo(
        photo=thumbnail,
        caption=f"Video ditemukan: <b>{video_title}</b>\n\nPilih format yang diinginkan:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def youtube_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data.split(':')
    action_type = callback_data[1]

    youtube_link = context.user_data.get('youtube_link')
    if not youtube_link:
        await query.edit_message_caption(caption="Sesi telah berakhir. Silakan mulai lagi dengan perintah /youtube.", reply_markup=None)
        return

    if action_type == "format":
        media_format = callback_data[2]
        if media_format == "audio":
            await query.edit_message_caption(caption="Memproses audio...", reply_markup=None)
            await _download_and_send_audio(query.message, youtube_link)
        elif media_format == "video":
            keyboard = [
                [
                    InlineKeyboardButton("480p", callback_data="youtube:quality:480"),
                    InlineKeyboardButton("720p", callback_data="youtube:quality:720"),
                ]
            ]
            await query.edit_message_caption(caption="Pilih kualitas video:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action_type == "quality":
        quality = callback_data[2]
        await query.edit_message_caption(caption=f"Memproses video {quality}p...", reply_markup=None)
        await _download_and_send_video(query.message, youtube_link, quality)
