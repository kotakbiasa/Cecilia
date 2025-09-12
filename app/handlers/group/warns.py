from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.database import DBConstants, database_search
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("warns", ["/", "!", "-", "."]))
@pm_error
async def func_warns(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    # Permission Checking...
    if admin_roles["user_admin"] or admin_roles["user_owner"]:
        return await message.reply_text("How could someone give you a warning?")
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    warns = chat_data.get("warns") or {}
    victim_warns = warns.get(str(user.id)) or {} # mongodb doesn't allow int doc key
    warn_count = victim_warns.get("count") or 0

    if not warn_count:
        text = "🎉 Congratulations, you don't have any warning in this chat!"
    else:
        text = f"You have {warn_count}/3 warnings!! Be careful...!"
    
    await message.reply_text(text)
