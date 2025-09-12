from pyrogram import filters
from pyrogram.types import ChatMemberUpdated
from pyrogram.enums import ChatType, ChatMemberStatus

from app import bot
from app.utils.database import DBConstants, MemoryDB, MongoDB

@bot.on_chat_member_updated(filters.me)
async def bot_chats_tracker(_, member_update: ChatMemberUpdated):
    """**Tracks GROUP/PRIVATE chat (where bot is added/removed/promoted/demoted)**"""
    chat = member_update.chat
    user = member_update.from_user
    old_status = member_update.old_chat_member.status
    new_status = member_update.new_chat_member.status
    text = None

    if chat.type in [ChatType.PRIVATE]:
        # checking database entry
        user_data = MongoDB.find_one(DBConstants.USERS_DATA, "user_id", user.id)
        if not user_data:
            data = {
                "user_id": user.id,
                "name": user.full_name,
                "username": user.username,
                "lang": user.language_code
            }

            MongoDB.insert(DBConstants.USERS_DATA, data)
            MemoryDB.insert(DBConstants.USERS_DATA, user.id, data)
        
        # checking member status & updating database
        active_status = new_status == ChatMemberStatus.MEMBER
        MongoDB.update(DBConstants.USERS_DATA, "user_id", user.id, {"active_status": active_status})
    
    elif chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        # checking database entry
        chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
        if not chat_data:
            data = {
                "chat_id": chat.id,
                "title": chat.title
            }

            MongoDB.insert(DBConstants.CHATS_DATA, data)
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, data)
        
        if old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED] and new_status == ChatMemberStatus.MEMBER:
            text = (
                "Thanks for adding me in this nice chat!\n"
                "Please make me admin in chat, so I can help you managing this chat effectively!\n"
                "/help for bot help..."
            )
        
        # promotion
        elif old_status != ChatMemberStatus.ADMINISTRATOR and new_status == ChatMemberStatus.ADMINISTRATOR:
            text = (
                "Thanks for adding me as an admin!\n"
                "Don't forget to checkout /help section..."
            )
        
        # demotion
        elif old_status == ChatMemberStatus.ADMINISTRATOR and new_status == ChatMemberStatus.MEMBER:
            text = (
                "Ohh dear, have I done something wrong!\n"
                "I wish I could help..."
            )
        
        if text: await bot.send_message(chat.id, text)
    
    elif chat.type in [ChatType.CHANNEL] and new_status == ChatMemberStatus.ADMINISTRATOR:
        await bot.send_message(user.id, f"You have added me in {chat.title}\nChatID: `{chat.id}`")
