from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from app.utils.decorators.pm_error import pm_error

@pm_error
async def func_adminlist(_, message: Message):
    chat = message.chat
    message = update.message

    owner = "**Owner:**\n"
    admins = ""

    chat_admins = await chat.get_administrators()

    for admin in chat_admins:
        custom_title = f"- <i>{admin.custom_title}</i>" if admin.custom_title else ""
        admin_name = "Anonymous" if admin.is_anonymous else admin.user.mention.HTML
        formatted_text = f"• {admin_name} {custom_title}\n"

        if admin.status == ChatMember.OWNER:
            owner += formatted_text
        elif not admin.user.is_bot:
            admins += formatted_text
        
    if admins:
        admins = f"\n**Admin's:**\n{admins}"
    
    text = (
        f"<blockquote>{chat.title}</blockquote>\n\n"
        f"{owner}{admins}"
    )

    await message.reply_text(text)
