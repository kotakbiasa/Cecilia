from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_pin(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message
    re_msg = message.reply_to_message

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
    
    if not re_msg:
        await message.reply_text("I don't know which message to pin! Reply the message to pin!")
        return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, context.bot.id, user.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_pin_messages:
        await message.reply_text("You don't have enough permission to pin messages!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_pin_messages:
        await message.reply_text("I don't have enough permission to pin messages!")
        return
    
    try:
        await chat.pin_message(re_msg.id, disable_notification=is_silent)
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not is_silent:
        await message.reply_text(f"<a href='{re_msg.link}'>Message</a> has been pinned!")
