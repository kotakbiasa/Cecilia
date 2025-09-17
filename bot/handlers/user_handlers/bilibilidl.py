from telegram import Update
from telegram.ext import ContextTypes
from bot.modules.ryuzumi_api import bilibili_downloader

async def func_bilibili(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_message = update.effective_message
    url = " ".join(context.args)

    if not url:
        await effective_message.reply_text(
            "Silakan berikan URL video Bilibili.\n"
            "Contoh: <code>/bili https://www.bilibili.tv/id/video/4796777523845120</code>"
        )
        return

    sent_message = await effective_message.reply_text("Mengunduh video Bilibili, harap tunggu...")

    video_data = await bilibili_downloader(url)

    if not video_data:
        await sent_message.edit_text("Gagal mengunduh video. URL mungkin tidak valid atau terjadi kesalahan pada API.")
        return

    title = video_data.get('title', 'N/A')
    video_list = video_data.get('mediaList', {}).get('videoList', [])

    if not video_list:
        await sent_message.edit_text("Tidak ada media video yang ditemukan dalam respons API.")
        return

    video_url = video_list[0].get('url')

    caption = f"<b>{title}</b>"

    try:
        await sent_message.delete()
        await effective_message.reply_video(video=video_url, caption=caption)
    except Exception as e:
        await effective_message.reply_text(f"Gagal mengirim video: {e}\n\nAnda dapat mengunduhnya dari link ini: {video_url}")
