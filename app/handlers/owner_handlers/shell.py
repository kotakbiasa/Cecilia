import subprocess
from io import BytesIO
from time import time

from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_shell(_, message: Message):
    chat = message.chat
    message = update.message
    command = extract_cmd_args(message.text, message.command).replace("'", "")
    
    if not command:
        await message.reply_text("Use `/shell dir/ls` [linux/Windows Depend on your hosting server]")
        return
    
    sent_message = await message.reply_text("**⌊ please wait... ⌉**")
    
    time_executing = time()

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    except Exception as e:
        await sent_message.edit_text(str(e))
        return
    
    time_executed = time()
    
    if not result.stdout and not result.stderr:
        await sent_message.edit_text("**⌊ None ⌉**")
        return

    result = result.stdout if result.stdout else result.stderr

    try:
        await sent_message.edit_text(f"<pre>{result}</pre>")
    except:
        shell = BytesIO(result.encode())
        shell.name = "shell.txt"

        await sent_message.delete()
        await message.reply_document(shell, f"**Command**: {command}\n**Execute time**: {(time_executed - time_executing):.2f}s")
