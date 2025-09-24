import io
import html
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.helpers import get_command_args
from bot.modules.teraboxdl import terabox_download


async def func_teraboxdl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /teraboxdl command.
    Initiates the download process for a given Terabox URL.
    """
    message = update.effective_message
    args = get_command_args(message)

    if not args:
        await message.reply_text(
            "Please provide a Terabox URL.\n\n"
            "<b>Usage:</b> <code>/teraboxdl &lt;url&gt; [password]</code>",
        )
        return

    url = args.split()[0]
    password = args.split()[1] if len(args.split()) > 1 else ""

    status_msg = await message.reply_text("⏳ Processing your link, please wait...")

    download_links = await terabox_download(url, password)

    if not download_links:
        await status_msg.edit_text(
            "❌ Failed to retrieve download links. The URL might be invalid, protected, or the service is down."
        )
        return

    response_text = "✅ <b>Download Links Generated:</b>\n\n"
    for i, item in enumerate(download_links, 1):
        # Escape filename to prevent any potential HTML injection
        filename = html.escape(item.get('filename', 'N/A'))
        response_text += (
            f"<b>{i}. {filename}</b>\n"
            f"   <b>Size:</b> {item['size_mb']} MB\n"
            f"   <b>Link:</b> <a href=\"{item['link']}\">Click here to download</a>\n\n"
        )

    # Telegram has a message length limit of 4096 characters.
    # If the message is too long, we send it as a file.
    if len(response_text) > 4096: # Telegram's message length limit
        await status_msg.edit_text("Message is too long, sending as a file.")
        # Create a plain text version for the file
        file_content = "Download Links Generated:\n\n"
        for i, item in enumerate(download_links, 1):
            file_content += (
                f"{i}. {item.get('filename', 'N/A')}\n"
                f"   Size: {item['size_mb']} MB\n"
                f"   Link: {item['link']}\n\n"
            )

        # Use BytesIO to create an in-memory file
        file_buffer = io.BytesIO(file_content.encode('utf-8'))
        file_buffer.name = "terabox_links.txt"

        await message.reply_document(document=file_buffer, caption="Here are your links:")
        await status_msg.delete() # Clean up the status message
    else:
        await status_msg.edit_text(response_text)
