import speedtest
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def bytes_to_mbps(byte_value: float) -> float:
    """Mengonversi byte per detik menjadi megabit per detik."""
    return round(byte_value / 1_000_000, 2)

async def create_speedtest_image(results: dict) -> BytesIO:
    """Membuat gambar dari hasil speed test."""
    download_speed = bytes_to_mbps(results["download"])
    upload_speed = bytes_to_mbps(results["upload"])
    ping = round(results["ping"], 2)
    server_info = results["server"]
    client_info = results["client"]

    # Image dimensions and colors
    width, height = 800, 450
    bg_color = (240, 235, 250)      # Light Lavender
    text_color = (40, 30, 60)          # Dark Purple
    highlight_color = (255, 105, 180)  # Hot Pink
    label_color = (120, 110, 140)      # Muted Purple/Gray
    
    # Create image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        # Common fonts on Linux systems
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        main_font = ImageFont.truetype("DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 18)
        label_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except IOError:
        logger.warning("Font 'DejaVuSans' tidak ditemukan, menggunakan font default dari Pillow.")
        title_font = ImageFont.load_default(size=36)
        main_font = ImageFont.load_default(size=24)
        small_font = ImageFont.load_default(size=18)
        label_font = ImageFont.load_default(size=18)

    # --- Drawing content on the image ---
    draw.text((width/2, 40), "Speed Test Result", font=title_font, fill=highlight_color, anchor="mt")

    # Metrics (Ping, Download, Upload) - Top part
    y_metrics = 120

    draw.text((width / 3, y_metrics), "Download", font=main_font, fill=text_color, anchor="mt")
    draw.text((width / 3, y_metrics + 40), f"{download_speed}", font=title_font, fill=text_color, anchor="mt")
    draw.text((width / 3, y_metrics + 80), "Mbps", font=main_font, fill=text_color, anchor="mt")

    draw.text((width * 2 / 3, y_metrics), "Upload", font=main_font, fill=text_color, anchor="mt")
    draw.text((width * 2 / 3, y_metrics + 40), f"{upload_speed}", font=title_font, fill=text_color, anchor="mt")
    draw.text((width * 2 / 3, y_metrics + 80), "Mbps", font=main_font, fill=text_color, anchor="mt")

    # Divider line
    draw.line([(50, 250), (width - 50, 250)], fill=label_color, width=1)

    # Client and Server Info - Bottom part
    y_info = 280
    row_height = 60
 
    # Row 1: ISP and Server Host
    draw.text((50, y_info), "ISP", font=label_font, fill=label_color)
    draw.text((50, y_info + 25), client_info['isp'], font=small_font, fill=text_color)
    draw.text((width/2, y_info), "Server Host", font=label_font, fill=label_color)
    draw.text((width/2, y_info + 25), server_info['sponsor'], font=small_font, fill=text_color)
    
    # Row 2: Client Location and Server Location
    y_row2 = y_info + row_height
    draw.text((50, y_row2), "Client Location", font=label_font, fill=label_color)
    draw.text((50, y_row2 + 25), client_info['country'], font=small_font, fill=text_color)
    server_location_text = f"{server_info['name']}, {server_info['country']} ({server_info['cc']})"
    draw.text((width/2, y_row2), "Server Location", font=label_font, fill=label_color)
    draw.text((width/2, y_row2 + 25), server_location_text, font=small_font, fill=text_color)

    # Save image to a memory buffer
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

async def func_speedtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menjalankan speed test dan mengirimkan hasilnya dalam bentuk gambar."""
    message = update.effective_message
    sent_message = await message.reply_text("🚀 Menjalankan speed test, ini mungkin memakan waktu beberapa saat...")

    try:
        logger.info("Memulai speed test...")
        
        # Run synchronous speedtest code in a separate thread to avoid blocking
        def do_speedtest():
            s = speedtest.Speedtest(secure=True)
            s.get_best_server()
            s.download(threads=None)
            s.upload(threads=None)
            return s.results.dict()

        results = await asyncio.get_running_loop().run_in_executor(None, do_speedtest)
        logger.info(f"Speed test selesai. Hasil: {results}")

        await sent_message.edit_text("🎨 Membuat gambar hasil...")
        image_buffer = await create_speedtest_image(results)

        download_speed = bytes_to_mbps(results["download"])
        upload_speed = bytes_to_mbps(results["upload"])
        ping = round(results["ping"], 2)
        server_info = results["server"]
        client_info = results["client"]

        caption = (
            "<b>📊 Hasil Speed Test</b>\n\n"
            f"<b>Ping:</b> {ping} ms\n\n"
            f"<b>ISP:</b> <code>{client_info['isp']}</code>\n"
            f"<b>Lokasi Klien:</b> <code>{client_info['country']}</code>\n\n"
            f"<b>Host Server:</b> <code>{server_info['sponsor']}</code>\n"
            f"<b>Lokasi Server:</b> <code>{server_info['name']}, {server_info['country']} ({server_info['cc']})</code>"
        )
        await message.reply_photo(photo=image_buffer, caption=caption)
        await sent_message.delete()

    except Exception as e:
        logger.error(f"Gagal menjalankan speed test: {e}")
        await sent_message.edit_text(f"Gagal menjalankan speed test: {e}")