from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.utils.database import DBConstants, database_search
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("triggers", ["/", "!", "-", "."]))
@pm_error
async def func_triggers(_, message: Message):
    chat = message.chat
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")

    triggers = chat_data.get("triggers")

    if triggers:
        text = "<blockquote>Chat triggers</blockquote>\n\n"
        for keyword in triggers:
            text += f"• `{keyword}`\n"
    
    else:
        text = "This chat doesn't have any triggers!"

    await message.reply_text(text)
