from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["unpin", "sunpin"], ["/", "!", "-", "."]))
@pm_error
async def func_unpin(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message

    is_silent = await GroupHelper.cmd_prefix_handler(chat, message, re_msg)

    if not re_msg:
        return await message.reply_text("I don't know which message to unpin! Reply the message to unpin!")
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    # Permission Checking...
    if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("You aren't an admin in this chat!")
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_pin_messages:
        return await message.reply_text("You don't have enough permission to unpin messages!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_pin_messages:
        return await message.reply_text("I don't have enough permission to unpin messages!")
    
    try:
        await bot.unpin_chat_message(chat.id, re_msg.id)
    except Exception as e:
        return await message.reply_text(str(e))
    
    if not is_silent:
        await message.reply_text(f"<a href='{re_msg.link}'>Message [{re_msg.id}]</a> has been unpinned!")
