from pyrogram import filters
from pyrogram.types import CallbackQuery

from app import bot
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search

@bot.on_callback_query(filters.regex(r"misc_[A-Za-z0-9]+"))
async def query_misc(_, query: CallbackQuery):
    chat = query.message.chat
    user = query.from_user

    # refined query data
    query_data = query.data.removeprefix("misc_")

    if query_data == "none":
        return await query.answer()
    
    elif query_data.startswith("tmp_whisper_"):
        data_center = MemoryDB.data_center.get("whisper_data") or {}
        whispers = data_center.get("whispers") or {}
        # other variables
        whisper_key = query_data.removeprefix("tmp_whisper_")
        whisper_user_data = whispers.get(whisper_key)

        if not whisper_user_data:
            return await query.answer("Whisper has been expired!", True)
        
        whisper_sender_user_id = whisper_user_data.get("sender_user_id")
        whisper_username = whisper_user_data.get("username") # contains @ prefix
        whisper_message = whisper_user_data.get("message")

        # delete the whisper if seen
        whisper_seen = True

        if whisper_sender_user_id == user.id:
            # access granted for message sender
            # If sender & receiver are same user then mark the message as seen
            whisper_seen = True if whisper_username == user.name else False

        # verifying user (only by username)
        elif whisper_username != user.name:
            return await query.answer("This whisper isn't for you. (if you believe it's yours then maybe you changed your `username`)", True)
        
        await query.answer(whisper_message, True)
        # delete whisper is seen
        if whisper_seen:
            whispers.pop(whisper_key)
            # Diffrent from normal /whisper cmd
            MemoryDB.insert(DBConstants.DATA_CENTER, "whisper_data", {"whispers": whispers})

            btn = BuildKeyboard.cbutton([{"Try Yourself!": "switch_to_inline"}])
            await query.edit_message_text(f"<i>The whisper message is seen by {user.full_name}!</i>", reply_markup=btn)
    
    elif query_data.startswith("whisper_"):
        chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
        if not chat_data:
            return await query.answer("Chat isn't registered! Remove/Block me from this chat then add me again!", True)
        
        whispers = chat_data.get("whispers") or {}
        # other variables
        whisper_key = query_data.removeprefix("whisper_")
        whisper_user_data = whispers.get(whisper_key)

        if not whisper_user_data:
            return await query.answer("What? There is no whisper message!!", True)
        
        whisper_sender_user_id = whisper_user_data.get("sender_user_id")
        whisper_user_id = whisper_user_data.get("user_id")
        whisper_username = whisper_user_data.get("username") # contains @ prefix
        whisper_message = whisper_user_data.get("message")

        # delete the whisper if seen
        whisper_seen = True

        if whisper_sender_user_id == user.id:
            # access granted for message sender
            # If sender & receiver are same user then mark the message as seen
            whisper_seen = True if (whisper_user_id and whisper_user_id == user.id) or (whisper_username and whisper_username == user.name) else False
            pass

        # verifying user
        elif (whisper_user_id and whisper_user_id != user.id) or (whisper_username and whisper_username != user.name):
            return await query.answer("This whisper isn't for you. (if you believe it's yours then maybe you changed your `username`)", True)
        
        await query.answer(whisper_message, True)
        # delete whisper is seen
        if whisper_seen:
            whispers.pop(whisper_key)
            MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"whispers": whispers})
            MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"whispers": whispers})

            await query.edit_message_text(f"<i>The whisper message is seen by {user.full_name}!</i>")
    
    elif query_data == "close":
        try:
            message_id = query.message.message_id
            await bot.delete_messages([message_id, message_id - 1])
        except:
            try:
                await query.delete_message()
            except:
                pass
