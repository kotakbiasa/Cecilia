from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_invitelink(_, message: Message):
    message = update.message
    chat_id = extract_cmd_args(message.text, message.command)
    
    if not chat_id:
        await message.reply_text("`/invitelink ChatID` to get specified chat invite link.\n<i>Note: only works if this bot is in that chat and have enough permissions to get invite link!</i>")
        return
    
    sent_message = await message.reply_text("Please wait...")
    expire_date = datetime.now() + timedelta(days=1) # expire after 1day of creation

    try:
        invite_link = await context.bot.create_chat_invite_link(chat_id, expire_date, 1)
    except Exception as e:
        await sent_message.edit_text(str(e))
        return
    
    await sent_message.edit_text(f"**Generated link:** {invite_link.invite_link}")
