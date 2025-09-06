from telegram import Update
from telegram.ext import ContextTypes
from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_cadmins(_, message: Message):
    message = update.message
    chat_id = extract_cmd_args(message.text, message.command)
    
    if not chat_id:
        await message.reply_text("`/cadmins ChatID` to get specified chat admin list.\n<i>Note: only works if this bot is in that chat!</i>")
        return
    
    sent_message = await message.reply_text("Please wait...")
    owner_storage = "**Owner:**\n"
    admins_storage = ""

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
    except Exception as e:
        await sent_message.edit_text(str(e))
        return
    
    for admin in admins:
        custom_title = admin.custom_title if admin.custom_title else ""
        formatted_msg = f"• {admin.user.mention.HTML} - <i>{custom_title}</i>\n"

        if admin.status == "creator":
            owner_storage += formatted_msg
        elif not admin.user.is_bot:
            admins_storage += formatted_msg
        
    if admins_storage:
        admins_storage = f"\n**Admin's:**\n{admins_storage}"
    
    text = (
        f"Admins of `{chat_id}`\n\n"
        f"{owner_storage}{admins_storage}"
    )

    await sent_message.edit_text(text)
