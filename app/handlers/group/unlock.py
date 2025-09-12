from pyrogram import filters
from pyrogram.types import Chat, Message, ChatPermissions

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["unlock", "sunlock"], ["/", "!", "-", "."]))
@pm_error
async def func_unlock(_, message: Message):
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
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_change_info:
        return await message.reply_text("You don't have enough permission to unlock this chat!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_change_info:
        return await message.reply_text("I don't have enough permission to unlock this chat!")
    
    try:
        await bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True
            )
        )
    except Exception as e:
        return await message.reply_text(str(e))
    
    if not is_silent:    
        await message.reply_text("Chat has been unlocked!")
