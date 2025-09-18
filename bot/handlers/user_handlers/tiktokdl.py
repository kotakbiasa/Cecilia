import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.ryzumi_api import get_ttdl_media

async def func_tiktokdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    url = " ".join(context.args)

    if not url or "tiktok.com" not in url:
        await message.reply_text(
            "Gunakan <code>/tt [URL]</code> untuk mengunduh video dari TikTok.\n"
            "Contoh: <code>/tt https://www.tiktok.com/@user/video/123456</code>",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Sedang memproses...")
    response_data = await get_ttdl_media(url)

    if not response_data or not response_data.get("success") or not response_data.get("data", {}).get("data"):
        await sent_message.edit_text("Maaf, gagal mengunduh video dari URL tersebut. Pastikan URL valid dan video bersifat publik.")
        return

    media_data = response_data["data"]["data"]
    video_url = media_data.get("play")  # No watermark
    title = media_data.get("title")
    uploader = media_data.get("author", {}).get("unique_id")

    if not video_url:
        await sent_message.edit_text("Tidak ditemukan link unduhan video yang valid.")
        return

    caption_parts = []
    if title:
        caption_parts.append(f"<b>{title}</b>")
    if uploader:
        caption_parts.append(f"<b>Uploader:</b> @{uploader}")
    caption_parts.append(f"<b>Source:</b> <a href='{url}'>TikTok</a>")

    caption_text = "\n\n".join(caption_parts)
    caption = f"<blockquote>{caption_text}</blockquote>"

    try:
        await sent_message.edit_text("Mengunduh video ke server...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(video_url, timeout=600) as resp:
                if not resp.ok:
                    await sent_message.edit_text("Gagal mengunduh video dari sumber. Coba lagi nanti.")
                    return
                video_content = await resp.read()

        await sent_message.edit_text("Mengirim video ke Telegram...")
        await message.reply_video(video=video_content, caption=caption, write_timeout=600)
        await sent_message.delete()
    except Exception as e:
        logger.error(f"Gagal mengirim video TikTok: {e}")
        await sent_message.edit_text("Gagal mengirim video. Kemungkinan file terlalu besar atau terjadi error.")