from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus

from app import bot
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("adminlist", ["/", "!", "-", "."]))
@pm_error
async def func_adminlist(_, message: Message):
    chat = message.chat

    owner = "**Owner:**\n"
    admins = ""

    async for admin in chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS):
        admin_name = "Anonymous" if admin.privileges.is_anonymous else admin.user.mention
        formatted_text = f"• {admin_name} - <i>{admin.custom_title or '~'}</i>\n"
        
        if admin.status in [ChatMemberStatus.OWNER]:
            owner += formatted_text
        elif not admin.user.is_bot:
            admins += formatted_text
        
    if admins: admins = f"\n**Admin's:**\n{admins}"
    
    await message.reply_text(
        f"<blockquote>{chat.title}</blockquote>\n\n"
        f"{owner}{admins}"
    )
