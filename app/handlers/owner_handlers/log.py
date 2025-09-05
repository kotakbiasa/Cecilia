from telegram import Update
from telegram.ext import ContextTypes
from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    await message.reply_document(open("sys/log.txt", "rb"), filename="log.txt")
