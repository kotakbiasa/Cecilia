from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins

@pm_error
async def func_kickme(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, context.bot.id, user.id)
    
    if (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("I'm not going to kick you! You must be kidding!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_restrict_members:
        await message.reply_text("I don't have enough permission to kick members in this chat!")
        return
    
    try:
        await chat.unban_member(user.id)
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    await message.reply_text(f"Nice Choice! Get out of my sight!\n{user.mention.HTML} has chosen the easy way to out!")
