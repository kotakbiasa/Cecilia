import asyncio
import aiohttp
import tempfile
import os
import re
import time
from html import escape

import instaloader
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

# Impor objek config dan logger dari modul bot utama.
from bot import config, logger
from bot.modules.ryzumi_api import get_igdl_media

# --- Instaloader setup ---
# Custom RateController to avoid blocking and be less aggressive.
class SimpleRateController(instaloader.RateController):
    def __init__(self, context, sleep_time=2):
        super().__init__(context)
        self.sleep_time = sleep_time

    def sleep(self, secs):
        # Avoid blocking the event loop — Instaloader runs in a thread
        time.sleep(secs)

    def query_waittime(self, query_type, current_time, untracked_queries=False):
        return self.sleep_time

    def handle_429(self, query_type):
        self.sleep(self.query_waittime(query_type, time.time()))

    def count_per_sliding_window(self, query_type):
        return 1

# Global instance with the custom rate controller.
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern="",
    max_connection_attempts=3,
    request_timeout=30,
    rate_controller=lambda ctx: SimpleRateController(ctx, 2), # Using the custom controller
    quiet=True,
)

# --- Penanganan Sesi ---
SESSION_FILE = ".instagram_session"

try:
    # Dapatkan kredensial dari objek config.
    IG_USERNAME = getattr(config, 'ig_username', None)
    IG_PASSWORD = getattr(config, 'ig_password', None)

    if not IG_USERNAME:
        logger.info("Instagram: Tidak ada username, berjalan dalam mode publik.")
    else:
        session_loaded = False
        if os.path.exists(SESSION_FILE):
            try:
                logger.info(f"Instagram: Mencoba memuat sesi untuk '{IG_USERNAME}' dari file...")
                L.load_session_from_file(IG_USERNAME, SESSION_FILE)
                logger.info("Instagram: Sesi berhasil dimuat.")
                session_loaded = True
            except Exception as e:
                logger.warning(f"Instagram: Gagal memuat sesi dari file (mungkin korup atau kedaluwarsa): {e}")

        if not session_loaded:
            if IG_PASSWORD:
                logger.info(f"Instagram: Mencoba login baru sebagai {IG_USERNAME}...")
                L.login(IG_USERNAME, IG_PASSWORD)
                L.save_session_to_file(SESSION_FILE)
                logger.info("Instagram: Login berhasil dan sesi disimpan.")
            else:
                logger.info("Instagram: Tidak dapat memuat sesi dan tidak ada password. Berjalan dalam mode publik.")
except Exception as e:
    logger.error(f"Instagram: Gagal memuat sesi atau login: {e}. Berjalan dalam mode publik.")

def _extract_shortcode(url: str) -> str | None:
    """Extracts shortcode from Instagram URL."""
    for pattern in (
        r"(?:https?://)?(?:www\.)?instagram\.com/p/([^/?#]+)",
        r"(?:https?://)?(?:www\.)?instagram\.com/reel/([^/?#]+)",
        r"(?:https?://)?(?:www\.)?instagram\.com/tv/([^/?#]+)",
        r"(?:https?://)?(?:www\.)?instagram\.com/stories/[^/]+/([^/?#]+)",
    ):
        if m := re.search(pattern, url):
            return m.group(1)
    return None

async def func_instagramdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    url = " ".join(context.args)

    if not url or "instagram.com" not in url:
        await message.reply_text(
            "Gunakan <code>/ig [URL]</code> untuk mengunduh media dari Instagram.\n"
            "Contoh: <code>/ig https://www.instagram.com/p/C1234567890/</code>",
            disable_web_page_preview=True,
        )
        return

    sent_message = await message.reply_text("Sedang memproses...")

    # Use a temporary directory that will be cleaned up automatically
    with tempfile.TemporaryDirectory() as tmpdir:
        media_files = []
        media_types = []
        caption = ""

        try:
            # --- PRIMARY METHOD: Instaloader ---
            await sent_message.edit_text("Mencoba metode unduh primer (Instaloader)...")
            shortcode = _extract_shortcode(url)
            if not shortcode:
                raise ValueError("Format URL Instagram tidak valid.")

            # Run synchronous instaloader code in a separate thread to avoid blocking asyncio
            def do_download():
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=tmpdir)
                return post.caption or ""

            post_caption = await asyncio.to_thread(do_download)

            # Collect downloaded files, sorted to maintain order
            files_in_dir = sorted(os.listdir(tmpdir))
            for f in files_in_dir:
                if f.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png')):
                    path = os.path.join(tmpdir, f)
                    media_files.append(path)
                    media_types.append('video' if path.lower().endswith('.mp4') else 'image')

            if not media_files:
                raise ValueError("Instaloader tidak menemukan file media.")

            # Build caption from Instaloader
            caption_parts = []
            if post_caption:
                caption_parts.append(f"<blockquote expandable>{escape(post_caption)}</blockquote>")
            caption_parts.append(f"<b>Source:</b> <a href='{url}'>Instagram</a>")
            caption = "\n\n".join(caption_parts)

        except Exception as e:
            # --- FALLBACK METHOD: Ryzumi API ---
            logger.warning(f"Instaloader gagal: {e}. Beralih ke metode sekunder (API).")
            await sent_message.edit_text("Metode primer gagal, mencoba dengan API...")

            # Clear any partial files from the failed Instaloader attempt
            media_files.clear()
            media_types.clear()

            response_data = await get_igdl_media(url)

            if not response_data or not response_data.get("status") or not isinstance(response_data.get("data"), list) or not response_data["data"]:
                await sent_message.edit_text("Maaf, gagal mengunduh media dari URL tersebut. Pastikan URL valid dan postingan bersifat publik.")
                return

            media_items = response_data["data"]

            # Build caption from API response
            caption_text = (response_data.get("caption") or media_items[0].get("caption") or "").strip()
            caption_parts = []
            if caption_text:
                caption_parts.append(f"<blockquote expandable>{escape(caption_text)}</blockquote>")
            caption_parts.append(f"<b>Source:</b> <a href='{url}'>Instagram</a>")
            caption = "\n\n".join(caption_parts)

            await sent_message.edit_text(f"Mengunduh {len(media_items)} media via API...")

            async with aiohttp.ClientSession() as session:
                for i, item in enumerate(media_items):
                    file_url = item.get("url")
                    if not file_url: continue

                    file_type = item.get("type", "").lower()
                    ext = 'mp4' if file_type == 'video' else 'jpg'
                    filepath = os.path.join(tmpdir, f"media_{i}.{ext}")

                    try:
                        async with session.get(file_url, timeout=300) as resp:
                            if resp.status == 200:
                                with open(filepath, "wb") as f:
                                    f.write(await resp.read())
                                media_files.append(filepath)
                                media_types.append(file_type)
                            else:
                                logger.warning(f"Gagal mengunduh {file_url}: HTTP {resp.status}")
                    except Exception as dl_e:
                        logger.error(f"Error saat mengunduh {file_url} dari API: {dl_e}")

        # --- SENDING LOGIC (common for both methods) ---
        if not media_files:
            await sent_message.edit_text("Gagal mengunduh media apa pun dari post tersebut.")
            return

        try:
            await sent_message.edit_text("Mengirim media ke Telegram...")

            if len(media_files) == 1:
                path = media_files[0]
                # Use `with open` to ensure file is closed after sending
                with open(path, 'rb') as f:
                    if media_types[0] == 'video':
                        await message.reply_video(video=f, caption=caption, write_timeout=600)
                    else:
                        await message.reply_photo(photo=f, caption=caption, write_timeout=600)
            else:
                media_group = []
                opened_files = []
                # Use try...finally to ensure all files in the album are closed
                try:
                    for i, path in enumerate(media_files):
                        f = open(path, 'rb')
                        opened_files.append(f)
                        if media_types[i] == 'video':
                            media_group.append(InputMediaVideo(f))
                        else:
                            media_group.append(InputMediaPhoto(f))

                    if media_group:
                        media_group[0].caption = caption

                    # Send in chunks of 10
                    for i in range(0, len(media_group), 10):
                        chunk = media_group[i:i+10]
                        await message.reply_media_group(media=chunk, write_timeout=600)
                finally:
                    for f in opened_files:
                        f.close()

            await sent_message.delete()
        except Exception as send_e:
            logger.error(f"Gagal mengirim media Instagram: {send_e}")
            await sent_message.edit_text("Gagal mengirim media. Kemungkinan file terlalu besar atau terjadi error.")