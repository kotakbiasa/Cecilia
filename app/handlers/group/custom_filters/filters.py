from telegram import Update
from telegram.ext import ContextTypes

from app.utils.database import DBConstants, database_search
from app.utils.decorators.pm_error import pm_error

@pm_error
async def func_filters(_, message: Message):
    chat = message.chat
    message = 
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return

    filters = chat_data.get("filters")

    if filters:
        text = "<blockquote>Chat filters</blockquote>\n\n"
        for keyword in filters:
            text += f"• `{keyword}`\n"
    
    else:
        text = "This chat doesn't have any filters!"

    await message.reply_text(text)
