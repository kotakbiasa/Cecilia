from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from app.handlers.group.auxiliary.chat_admins import ChatAdmins

async def query_groupManagement(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    query = update.callback_query

    # refined query data
    query_data = query.data.removeprefix("admin_")

    if query_data == "none":
        await query.answer()
        return
    
    elif query_data == "anonymous_verify":
        await query.answer("Verified!")
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"anonymous_admin": user})
        return
    
    elif query_data.startswith("remove_warn_"):
        # expecting remove_warn_[victim_id]
        victim_id = query_data.removeprefix("remove_warn_")

        
        await chat_admins.fetch_admins( user_id=user.id)
        
        if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
            await query.answer("You aren't an admin in this chat!", True)
            return
        
        chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
        if not chat_data:
            await query.answer("Chat isn't registered! Remove/Block me from this chat then add me again!", True)
            return
        
        warns = chat_data.get("warns") or {}
        victim_warns = warns.get(str(victim_id)) or {} # mongodb doesn't allow int doc key
        victim_mention = victim_warns.get("victim_mention")
        victim_warns.clear()
        
        response = MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"warns": warns})
        if response:
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"warns": warns})
        
        try:
            await chat.restrict_member(int(victim_id), ChatPermissions.all_permissions())
        except Exception as e:
            await query.edit_message_text(str(e))
            return
        
        await query.edit_message_text(f"Great! Admin {user.mention} has cleared all warnings of {victim_mention or f'`{victim_id}`'}.")
    
    elif query_data.startswith("leavechat_"):
        # expecting leavechat_[adminUserID]
        user_id = query_data.removeprefix("leavechat_")
        if user_id != str(user.id):
            await query.answer("Access Denied!")
            return
        
        await query.edit_message_text("Sorry, I couldn't help you! Bye..! 😕")
        await chat.leave()
