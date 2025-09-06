from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_unpinall(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message

    cmd_prefix = message.text[1]
    is_silent = False
    
    if cmd_prefix == "s":
        is_silent = True
        try:
            await message.delete()
        except:
            pass
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, context.bot.id, user.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_pin_messages:
        await message.reply_text("You don't have enough permission to unpin messages!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_pin_messages:
        await message.reply_text("I don't have enough permission to unpin messages!")
        return
    
    try:
        await chat.unpin_all_messages()
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not is_silent:
        await message.reply_text("Chat's all pinned messages has been unpinned!")
