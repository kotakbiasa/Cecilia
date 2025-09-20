import aiohttp
from time import time
from telegram import Update
from telegram.ext import ContextTypes

async def func_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    effective_message = update.effective_message
    url = " ".join(context.args)

    if not url:
        await effective_message.reply_text("Gunakan <code>/ping [url]</code>\nContoh: <code>/ping https://google.com</code>")
        return
    
    if url[0:4] != "http":
        url = f"http://{url}"

    sent_message = await effective_message.reply_text(f"Melakukan ping ke {url}\nMohon tunggu...")
    start_time = time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_time = int((time() - start_time) * 1000) # converting to ms
                if response_time > 1000:
                    response_time = f"{(response_time / 1000):.2f}s"
                else:
                    response_time = f"{response_time}ms"
                
                status_codes = {
                    200: "✅ Online (OK)",
                    201: "✅ Dibuat",
                    202: "✅ Diterima",
                    204: "⚠️ Tanpa Konten",
                    301: "➡️ Dipindahkan Permanen",
                    302: "➡️ Ditemukan (Redirect)",
                    400: "❌ Permintaan Buruk",
                    401: "🔒 Tidak Diizinkan",
                    403: "🚫 Dilarang",
                    404: "❌ Tidak Ditemukan",
                    408: "⏳ Waktu Permintaan Habis",
                    500: "🔥 Kesalahan Server Internal",
                    502: "⚠️ Gateway Buruk",
                    503: "⚠️ Layanan Tidak Tersedia"
                }

                status = status_codes.get(response.status, "⚠️ Status Tidak Diketahui")
                text = (
                    f"<b>Situs:</b> {url}\n"
                    f"<b>Waktu Respons:</b> <code>{response_time}</code>\n"
                    f"<b>Kode Respons:</b> <code>{response.status}</code>\n"
                    f"<b>Status:</b> <code>{status}</code>"
                )
    except aiohttp.ServerTimeoutError:
        text = "<b>Error:</b> Waktu permintaan habis."
    except aiohttp.ServerConnectionError:
        text = "<b>Error:</b> Kesalahan koneksi."
    except Exception:
        text = "<b>Oops!</b> Terjadi kesalahan!"
    
    await sent_message.edit_text(text)
