from app.utils.database import DBConstants, MemoryDB

def edit_database(chat_id, user_id, message):
    """
    Gets `update_data_value` from Edit Value query action & retuns `True` if is_editing.\n
    :param chat_id: update.effective_chat.id
    :param user_id: update.effective_user.id
    :param message: update.effective_message (Message Property)
    """
    data_center = MemoryDB.data_center.get(chat_id)
    if data_center and data_center.get("is_editing"):
        if user_id != data_center.get("user_id"): # Checking: is that same user?
            return
        
        data_value = None
        
        try:
            data_value = int(message.text)
        except ValueError:
            data_value = message.text
        except:
            pass
        
        data = {
            "update_data_value": data_value, # used for MongoDB Editing
            "message_id": message.id # mostly to delete the message
        }

        MemoryDB.insert(DBConstants.DATA_CENTER, chat_id, data)
        return True
