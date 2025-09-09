from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["unpinall", "sunpinall"], ["/", "!", "-", "."]))
@pm_error
async def func_unpinall(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    is_silent = await GroupHelper.cmd_prefix_handler(chat, message)
    
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
        await chat.unpin_all_messages()
    except Exception as e:
        return await message.reply_text(str(e))
    
    if not is_silent:
        await message.reply_text("Chat's all pinned messages has been unpinned!")
