from telegram import Update
from telegram.ext import ContextTypes
from app.utils.database import DBConstants, database_search

async def join_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_request_update = update.chat_join_request
    chat = join_request_update.chat
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await chat.send_message("<blockquote><b>Error:</b> Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    chat_join_req = chat_data.get("chat_join_req")
    if not chat_join_req:
        return
    
    try:
        if chat_join_req == "approve":
            await join_request_update.approve()
        
        elif chat_join_req == "decline":
            await join_request_update.decline()
    except Exception as e:
        await chat.send_message(str(e))
