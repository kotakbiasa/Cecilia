import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB, MongoDB

async def query_db_editing(_, message: Message):
    """
    This function accepts (`edit_value`, `cancel_editing`, `value_[custom value]`, `rm_value`, `bool_[true/false]`) callback query data's\n
    `value_`: The data given after value_ takes as `update_data_value`\n
    `bool_`: Expects `bool_true` or `bool_false`\n
    `rm_value`: Sets `update_data_value` as None
    """
    chat = message.chat
    user = message.from_user or message.sender_chat
    query = update.callback_query

    # refined query data
    query_data = query.data.removeprefix("database_")

    # memory access
    data_center = MemoryDB.data_center.get(chat.id) # using chat_id bcz it could be chat settings too
    if not data_center:
        await query.answer("Session Expired.", True)
        try:
            message_id = query.message.message_id
            await bot.delete_messages([message_id, message_id - 1])
        except:
            try:
                await query.delete_message()
            except:
                pass
        return
    
    # verifying user
    user_id = data_center.get("user_id")
    if user_id != user.id:
        await query.answer("Access Denied!", True)
        return
    
    # memory accessed data
    collection_name = data_center.get("collection_name")
    search_key = data_center.get("search_key")
    match_value = data_center.get("match_value")
    update_data_key = data_center.get("update_data_key")
    is_list = data_center.get("is_list") # type of update_data_key
    is_int = data_center.get("is_int") # type of update_data_key
    update_data_value = None # this can't be False/None or any empty value

    # getting update_data_value
    if query_data == "edit_value":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"update_data_value": None, "is_editing": True})
        
        timeout = 10

        btn = BuildKeyboard.cbutton([{"Cancel": "database_cancel_editing"}])
        sent_message = await chat.send_message(f"Waiting for a new value (Timeout: {timeout}s): ", reply_markup=btn)

        for i in range(timeout):
            data_center = MemoryDB.data_center[chat.id]
            # to check > is operation cancelled
            is_editing = data_center.get("is_editing")
            if not is_editing:
                await query.answer()
                return
            
            await asyncio.sleep(1)
            update_data_value = data_center.get("update_data_value")
            if update_data_value:
                break
        
        try:
            message_ids = [sent_message.id]
            if data_center.get("message_id"):
                message_ids.append(data_center.get("message_id"))
            
            await bot.delete_messages(message_ids)
        except:
            pass

        # terminating editing mode
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"is_editing": False})

        if not update_data_value:
            await query.answer("Timeout.", True)
            return
        
        if is_list:
            values = str(update_data_value).split(",") if "," in str(update_data_value) else [str(update_data_value)]
            update_data_value = [int(v) if is_int else v.strip() for v in values]
        
        # Updating Database
        response = MongoDB.update(collection_name, search_key, match_value, {update_data_key: update_data_value})
        if response:
            identifier = None if collection_name == DBConstants.BOT_DATA else chat.id
            data = {update_data_key: update_data_value}

            MemoryDB.insert(collection_name, identifier, data)

            await query.answer("Database Updated Successfully.\nRefresh to see the updated value!", True)

        else:
            await query.answer("Something went wrong.", True)
    
    elif query_data == "cancel_editing":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"update_data_value": None, "is_editing": False})
        await query.answer("Operation cancelled.", True)
        try:
            await query.delete_message()
        except:
            pass
    
    elif query_data.startswith("value_"): # expecting value_ > a fixed value which is update_data_value
        # Updating Database
        update_data_value = query_data.removeprefix("value_")
        response = MongoDB.update(collection_name, search_key, match_value, {update_data_key: update_data_value})
        if response:
            identifier = None if collection_name == DBConstants.BOT_DATA else chat.id
            data = {update_data_key: update_data_value}

            MemoryDB.insert(collection_name, identifier, data)

            await query.answer("Database Updated Successfully.", True)

        else:
            await query.answer("Something went wrong.", True)
    
    elif query_data == "rm_value":
        # Updating Database (removing values)
        update_data_value = [] if is_list else update_data_value
        response = MongoDB.update(collection_name, search_key, match_value, {update_data_key: update_data_value})
        if response:
            identifier = None if collection_name == DBConstants.BOT_DATA else chat.id
            data = {update_data_key: update_data_value}

            MemoryDB.insert(collection_name, identifier, data)

            await query.answer("Database Updated Successfully.\nRefresh to see the updated value!", True)

        else:
            await query.answer("Something went wrong.", True)
    
    elif query_data.startswith("bool_"): # expecting bool_true or bool_false
        # Updating Database (boolean)
        update_data_value = query_data.strip("bool_") == "true"
        response = MongoDB.update(collection_name, search_key, match_value, {update_data_key: update_data_value})
        if response:
            identifier = None if collection_name == DBConstants.BOT_DATA else chat.id
            data = {update_data_key: update_data_value}

            MemoryDB.insert(collection_name, identifier, data)

            await query.answer("Database Updated Successfully.\nRefresh to see the updated value!", True)

        else:
            await query.answer("Something went wrong.", True)
