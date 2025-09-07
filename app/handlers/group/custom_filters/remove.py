from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from ..auxiliary.chat_admins import ChatAdmins
from ..auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_remove(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    message = 
    keyword = extract_cmd_args(message.text, message.command).lower()
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, user_id=user.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_change_info:
        await message.reply_text("You don't have enough permission to manage this chat!")
        return
    
    if not keyword:
        text = (
            "To remove an existing filter use `/remove keyword`\n"
            "Use `clear_all` instead of keyword, to delete all filters of this chat!"
        )
        await message.reply_text(text)
        return

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    filters = chat_data.get("filters")

    if filters and keyword:
        if keyword == "clear_all":
            MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"filters": None})
            chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)

            await message.reply_text("All filters of this chat has been removed!")
            return
        
        try:
            if keyword.lower() in filters:
                del filters[keyword]
                MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"filters": filters})
                await message.reply_text(f"Filter `{keyword}` has been removed!")
            
            else:
                await message.reply_text("Filter doesn't exist! Chat filters /filters")
                return
            
            chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)
        except Exception as e:
            await message.reply_text(str(e))
