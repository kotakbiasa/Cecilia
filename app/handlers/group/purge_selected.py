from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.database import DBConstants, MemoryDB
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["purgefrom", "pf"], ["/", "!", "-", "."]))
@pm_error
async def func_purgefrom(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message

    if not re_msg:
        return await message.reply_text(
            "Reply the message where you want to purge from! Then use /purgeto to start.\n"
            "_**Note:** All messages between purgefrom and purgeto will be deleted!_"
        )
    
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
    
    await message.delete()
    sent_message = await message.reply_text("Now reply the last message to delete by /purgeto command.")
    
    data = {
        "purge_user_id": user.id,
        "purge_message_id": re_msg.id,
        "sent_message_id": sent_message.id
    }

    MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, data)


@bot.on_message(filters.command(["purgeto", "pt"], ["/", "!", "-", "."]))
@pm_error
async def func_purgeto(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message
    
    if not re_msg:
        return await message.reply_text(
            "Reply the last message to delete.\n"
            "_**Note:** All messages between `purgefrom` and `purgeto` will be deleted!_"
        )
    
    data_center = MemoryDB.data_center.get(chat.id)
    if not data_center:
        return await message.reply_text("Use /purgefrom for details.")
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    purge_user_id = data_center.get("purge_user_id") # for checking is that same user
    purge_message_id = data_center.get("purge_message_id")
    sent_message_id = data_center.get("sent_message_id") # for deleting this message

    if not purge_message_id:
        return await message.reply_text("Use /purgefrom for details.")
    
    if purge_user_id != user.id:
        return await message.reply_text("Task isn't yours!")
    
    message_ids = []
    for message_id in range(purge_message_id, re_msg.id):
        message_ids.append(message_id)
    
    message_ids.append(sent_message_id)

    try:
        await bot.delete_messages(chat.id, message_ids)
    except Exception as e:
        return await message.reply_text(str(e))
    
    # Cleaning Memory Data
    data = {
        "purge_user_id": None,
        "purge_message_id": None,
        "sent_message_id": None
    }

    MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, data)
    
    await message.reply_text("Purge completed!")
    await message.delete()
