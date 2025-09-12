from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.utils.database import DBConstants, database_search, MemoryDB, MongoDB
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["remove", "rm"], ["/", "!", "-", "."]))
@pm_error
async def func_trigger_remove(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    keyword = extract_cmd_args(message.text, message.command).lower()

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
        return await message.reply_text("You don't have enough permission to manage this chat!")
    
    # add trigger remove button for all [X clearAll]
    if not keyword:
        return await message.reply_text(
            f"To remove an existing trigger use `/{message.command[0]} keyword`\n"
            "Use `clearAll` instead of keyword, to delete all triggers of this chat!"
        )

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    triggers = chat_data.get("triggers")

    if triggers and keyword:
        if keyword == "clearAll":
            MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"triggers": None})
            chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)

            return await message.reply_text("All triggers of this chat has been removed!")
        
        # Else
        try:
            if keyword.lower() in triggers:
                del triggers[keyword]
                MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"triggers": triggers})
                await message.reply_text(f"Filter `{keyword}` has been removed!")
            
            else:
                return await message.reply_text("Filter doesn't exist! Chat triggers /triggers")
            
            chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)
        except Exception as e:
            await message.reply_text(str(e))
