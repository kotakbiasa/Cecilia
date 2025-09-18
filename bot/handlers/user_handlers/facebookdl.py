import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.re_link import RE_LINK
from bot.modules.ryzumi_api import get_fbdl_media

async def func_facebookdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    arg_string = " ".join(context.args)
    links = RE_LINK.detectLinks(arg_string)
    url = links[0] if links else None

    if not url or ("facebook.com" not in url and "fb.watch" not in url):
        await message.reply_text(
            "Gunakan <code>/fb [URL]</code> untuk mengunduh video dari Facebook.\n"
            "Contoh: <code>/fb https://www.facebook.com/watch/?v=123456</code>",
            disable_web_page_preview=True
        )
        return

    sent_message = await message.reply_text("Sedang memproses...")
    response_data = await get_fbdl_media(url)

    if not response_data or not response_data.get("status") or not isinstance(response_data.get("data"), list) or not response_data["data"]:
        await sent_message.edit_text("Maaf, gagal mengunduh video dari URL tersebut. Pastikan URL valid dan video bersifat publik.")
        return

    # Find the best quality video URL that doesn't need rendering
    video_url = None
    for media in response_data["data"]:
        if media.get("type") == "video" and not media.get("shouldRender") and media.get("url"):
            video_url = media.get("url")
            break  # Found a good one, let's use it.

    if not video_url:
        await sent_message.edit_text("Tidak ditemukan link unduhan video yang valid.")
        return

    # Coba dapatkan caption dari respons API
    post_caption = response_data.get("title") or response_data.get("description")

    caption_parts = []
    if post_caption:
        caption_parts.append(f"<blockquote>{post_caption.strip()}</blockquote>")
    caption_parts.append(f"<b>Source:</b> <a href='{url}'>Facebook</a>")
    caption = "\n\n".join(caption_parts)

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
        logger.error(f"Gagal mengirim video Facebook: {e}")
        await sent_message.edit_text("Gagal mengirim video. Kemungkinan file terlalu besar atau terjadi error.")