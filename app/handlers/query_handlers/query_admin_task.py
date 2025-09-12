from pyrogram import filters
from pyrogram.types import CallbackQuery, ChatPermissions

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.database import DBConstants, database_search, MemoryDB, MongoDB

@bot.on_callback_query(filters.regex(r"admin_[A-Za-z0-9]+"))
async def query_groupManagement(_, query: CallbackQuery):
    chat = query.message.chat
    user = query.from_user

    # refined query data
    query_data = query.data.removeprefix("admin_")

    if query_data == "none":
        return await query.answer()
    
    elif query_data == "anonymous_verify":
        await query.answer("Verified!")
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"anonymous_admin": user})
        return
    
    elif query_data.startswith("remove_warn_"):
        # expecting remove_warn_[victim_id]
        victim_id = query_data.removeprefix("remove_warn_")

        # Getting Admin roles
        admin_roles = await GroupHelper.get_admin_roles(chat, user.id, victim_id)
        
        # Permission Checking...
        if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
            return await query.answer("You aren't an admin in this chat!", True)
        
        chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
        if not chat_data:
            return await query.answer("Chat isn't registered! Remove/Block me from this chat then add me again!", True)
        
        warns = chat_data.get("warns") or {}
        victim_warns = warns.get(str(victim_id)) or {} # mongodb doesn't allow int doc key
        victim_mention = victim_warns.get("victim_mention")
        victim_warns.clear()
        
        response = MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"warns": warns})
        if response:
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"warns": warns})
        
        try:
            await chat.restrict_member(
                victim_id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_send_polls=True
                )
            )
        except Exception as e:
            return await query.edit_message_text(str(e))
        
        await query.edit_message_text(f"Good luck {victim_mention or f'`{victim_id}`'}! Your warnings has been removed by _{user.mention}_.")
    
    elif query_data.startswith("leavechat_"):
        # expecting leavechat_[adminUserID]
        user_id = query_data.removeprefix("leavechat_")
        if user_id != str(user.id):
            return await query.answer("Access Denied!")
        
        await query.edit_message_text("Sorry, I couldn't help you! Bye..! 😕")
        await chat.leave()
