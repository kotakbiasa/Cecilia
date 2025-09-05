import subprocess
from io import BytesIO
from time import time

from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    command = " ".join(context.args).replace("'", "")
    
    if not command:
        await message.reply_text("Use <code>/shell dir/ls</code> [linux/Windows Depend on your hosting server]")
        return
    
    sent_message = await message.reply_text("<b>⌊ please wait... ⌉</b>")
    
    time_executing = time()

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    except Exception as e:
        await sent_message.edit_text(str(e))
        return
    
    time_executed = time()
    
    if not result.stdout and not result.stderr:
        await sent_message.edit_text("<b>⌊ None ⌉</b>")
        return

    result = result.stdout if result.stdout else result.stderr

    try:
        await sent_message.edit_text(f"<pre>{result}</pre>")
    except:
        shell = BytesIO(result.encode())
        shell.name = "shell.txt"

        await sent_message.delete()
        await message.reply_document(shell, f"<b>Command</b>: {command}\n<b>Execute time</b>: {(time_executed - time_executing):.2f}s")
