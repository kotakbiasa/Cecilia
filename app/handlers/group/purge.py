from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["purge", "spurge"], ["/", "!", "-", "."]))
@pm_error
async def func_purge(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message

    is_silent = await GroupHelper.cmd_prefix_handler(chat, message, re_msg)
    
    if not re_msg:
        return await message.reply_text("Reply the message where you want to purge from!")
    
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
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_delete_messages:
        return await message.reply_text("You don't have enough permission to delete chat messages!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_delete_messages:
        return await message.reply_text("I don't have enough permission to delete chat messages!")
    
    sent_message = await message.reply_text("Purge started!")
    
    message_ids = []
    for message_id in range(re_msg.id, message.id):
        message_ids.append(message_id)
    
    try:
        await bot.delete_messages(message_ids)
        await message.delete()
    except Exception as e:
        return await sent_message.edit_text(str(e))
    
    if is_silent:
        await sent_message.delete()
    else:
        await sent_message.edit_text("Purge completed!")
