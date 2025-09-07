from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_invite(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    message = 
    
    cmd_prefix = message.text[1]
    
    if cmd_prefix == "s":
        try:
            await message.delete()
        except:
            pass
    
    if chat.link:
        await message.reply_text(f"Invite link: {chat.link}")
        return
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, bot.me.id, user.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_invite_users:
        await message.reply_text("You don't have enough permission to invite members in this chat!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_invite_users:
        await message.reply_text("I don't have enough permission to invite members in this chat!")
        return
    
    try:
        invite_link = await chat.create_invite_link(name=user.full_name)
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    await message.reply_text(f"Invite link: {invite_link.invite_link}")
