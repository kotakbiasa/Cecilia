import os
from telegram import Update
import re
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.ryzumi_api import get_ytmp3_media, get_ytmp4_media
from bot.modules.yt_search import search_youtube
from bot.modules.re_link import RE_LINK
from bot import logger
from bot.modules.ytdlp import youtube_download
 
async def _process_download(message, youtube_link: str, is_video: bool, quality: str = None):
    """
    A unified helper function to download and send YouTube media.
    It tries the API first and falls back to yt-dlp.
    """
    media_type = "video" if is_video else "audio"
    quality_text = f" {quality}p" if is_video and quality else ""
 
    try:
        # --- Method 1: Ryzumi API ---
        await message.edit_caption(caption=f"Mencoba mengunduh {media_type}{quality_text} via API...")
        
        if is_video:
            response_data = await get_ytmp4_media(youtube_link, quality)
        else:
            response_data = await get_ytmp3_media(youtube_link)
            
        media_url = response_data.get("url") if response_data else None
 
        if isinstance(media_url, str) and media_url.startswith("http"):
            try:
                title = response_data.get("title", f"YouTube {media_type.capitalize()}")
                thumbnail_url = response_data.get("thumbnail")
                thumbnail_content = None
 
                await message.edit_caption(caption=f"Mengunduh {media_type} ke server...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(media_url, timeout=600) as resp:
                        if not resp.ok:
                            raise ValueError(f"API download failed with status {resp.status}")
                        media_content = await resp.read()
 
                    if thumbnail_url:
                        async with session.get(thumbnail_url) as thumb_resp:
                            if thumb_resp.ok:
                                thumbnail_content = await thumb_resp.read()
 
                await message.edit_caption(caption=f"Mengunggah {media_type} ke Telegram...")
                performer = response_data.get("author", "Unknown")
                views = response_data.get("views", 0)
                author_url = response_data.get("authorUrl")
                video_url = response_data.get("videoUrl", youtube_link)
                artist_line = f"<a href='{author_url}'>{performer}</a>" if author_url else performer
                caption = (
                    f"<b>{title}</b>\n"
                    f"<b>Artis:</b> {artist_line}\n"
                    f"<b>Dilihat:</b> {views:,}\n\n"
                    f"<b>Source:</b> <a href='{video_url}'>YouTube</a>"
                )
 
                if is_video:
                    await message.reply_video(video=media_content, caption=caption, write_timeout=600)
                else:
                    await message.reply_audio(audio=media_content, title=title, performer=performer, caption=caption, thumbnail=thumbnail_content, write_timeout=600)
                
                await message.delete()
                return  # Success with API
            except Exception as api_e:
                logger.warning(f"Metode API untuk {media_type} gagal: {api_e}. Beralih ke yt-dlp.")
 
        logger.warning(f"API {media_type} gagal atau mengembalikan URL tidak valid: {media_url}. Beralih ke yt-dlp.")
 
        # --- Method 2: yt-dlp Fallback ---
        await message.edit_caption(caption="API gagal, mencoba dengan metode unduh alternatif (yt-dlp)...")
        download_info = await youtube_download(url=youtube_link, is_video=is_video, quality=quality)
 
        if not download_info or not download_info.get('filepath'):
            await message.edit_caption(caption="Maaf, semua metode unduhan gagal. Video mungkin dilindungi atau tidak tersedia.")
            return
 
        filepath = download_info['filepath']
        title = download_info.get('title', f'YouTube {media_type.capitalize()}')
        performer = download_info.get('artist')
        duration = download_info.get('duration')
        thumbnail_path = download_info.get('thumbnail_path')
 
        thumbnail_content = None
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as f:
                thumbnail_content = f.read()
 
        caption = f"<b>{title}</b>\n\n<i>Diunduh dengan yt-dlp.</i>"
 
        await message.edit_caption(caption=f"Mengunggah {media_type} ke Telegram...")
        with open(filepath, 'rb') as f:
            if is_video:
                await message.reply_video(
                    video=f, caption=caption, duration=int(duration) if duration else None,
                    width=download_info.get('width'), height=download_info.get('height'),
                    thumbnail=thumbnail_content, write_timeout=600
                )
            else:
                await message.reply_audio(
                    audio=f, title=title, performer=performer, caption=caption,
                    thumbnail=thumbnail_content, duration=int(duration) if duration else None,
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
        logger.error(f"Gagal mengirim {media_type} YouTube: {e}", exc_info=True)
        await message.edit_caption(caption=f"Gagal mengirim {media_type}. Kemungkinan file terlalu besar atau terjadi error.")

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
    video_id = None
    for link in links:
        # Regex to capture video ID from various YouTube URL formats
        match = re.search(r"(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([a-zA-Z0-9_-]{11})", link)
        if match:
            video_id = match.group(1)
            break
    
    if video_id:
        video_link = f"https://www.youtube.com/watch?v={video_id}"
    else:
        video_link = None
 
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
        video_id = re.search(r"v=([a-zA-Z0-9_-]{11})", results[0].get('link')).group(1)
        video_title = results[0].get('title')
        thumbnail = results[0].get('thumbnail')
 
    # Embed video_id in callback_data instead of using user_data
    keyboard = [
        [
            InlineKeyboardButton("🎧 Audio", callback_data=f"youtube:format:audio:{video_id}"),
            InlineKeyboardButton("🎬 Video", callback_data=f"youtube:format:video:{video_id}"),
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

    try:
        _, action_type, media_format_or_quality, video_id = query.data.split(':')
    except ValueError:
        await query.edit_message_caption(caption="Error: Callback data tidak valid.", reply_markup=None)
        return
 
    youtube_link = f"https://www.youtube.com/watch?v={video_id}"

    if action_type == "format":
        media_format = media_format_or_quality
        if media_format == "audio":
            await query.edit_message_caption(caption="Memproses audio...", reply_markup=None)
            await _process_download(query.message, youtube_link, is_video=False)
        elif media_format == "video":
            keyboard = [
                [
                    InlineKeyboardButton("480p", callback_data=f"youtube:quality:480:{video_id}"),
                    InlineKeyboardButton("720p", callback_data=f"youtube:quality:720:{video_id}"),
                ]
            ]
            await query.edit_message_caption(caption="Pilih kualitas video:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif action_type == "quality":
        quality = media_format_or_quality
        await query.edit_message_caption(caption=f"Memproses video {quality}p...", reply_markup=None)
        await _process_download(query.message, youtube_link, is_video=True, quality=quality)
