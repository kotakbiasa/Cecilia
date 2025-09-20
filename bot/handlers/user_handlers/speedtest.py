import speedtest
from telegram import Update
from telegram.ext import ContextTypes

from bot import logger

def bytes_to_mbps(byte_value: float) -> float:
    """Mengonversi byte per detik menjadi megabit per detik."""
    return round(byte_value / 1_000_000, 2)

async def func_speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan speed test dan mengirimkan hasilnya."""
    message = update.effective_message
    sent_message = await message.reply_text("🚀 Menjalankan speed test, ini mungkin memakan waktu beberapa saat...")

    try:
        logger.info("Memulai speed test...")
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download(threads=None)
        s.upload(threads=None)
        results = s.results.dict()
        logger.info(f"Speed test selesai. Hasil: {results}")

        download_speed = bytes_to_mbps(results["download"])
        upload_speed = bytes_to_mbps(results["upload"])
        ping = round(results["ping"], 2)
        server_info = results["server"]

        result_text = (
            "<b>📊 Hasil Speed Test</b>\n\n"
            f"<b>Server:</b> {server_info['sponsor']} ({server_info['name']}, {server_info['country']})\n"
            f"<b>Ping:</b> {ping} ms\n"
            f"<b>⬇️ Download:</b> {download_speed} Mbps\n"
            f"<b>⬆️ Upload:</b> {upload_speed} Mbps\n"
        )

        await sent_message.edit_text(result_text)

    except Exception as e:
        logger.error(f"Gagal menjalankan speed test: {e}")
        await sent_message.edit_text(f"Gagal menjalankan speed test: {e}")