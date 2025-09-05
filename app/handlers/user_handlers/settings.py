from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB, database_search
from ..group.chat_settings import chat_settings

class PvtChatSettingsData:
    TEXT = (
        "<blockquote><b>Chat Settings</b></blockquote>\n\n"

        "• Name: {}\n"
        "• ID: <code>{}</code>\n\n"

        "• Language: <code>{}</code>\n"
        "• Auto translate: <code>{}</code>\n"
        "• Echo: <code>{}</code>"
    )

    BUTTONS = [
        {"Language": "csettings_lang", "Auto translate": "csettings_auto_tr"},
        {"Echo": "csettings_echo", "Close": "misc_close"}
    ]


async def func_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    effective_message = update.effective_message

    if chat.type not in [ChatType.PRIVATE]:
        await chat_settings(update, context)
        return
    
    data = {
        "user_id": user.id, # authorization
        "collection_name": DBConstants.USERS_DATA,
        "search_key": "user_id",
        "match_value": user.id
    }

    MemoryDB.insert(DBConstants.DATA_CENTER, user.id, data)

    user_data = database_search(DBConstants.USERS_DATA, "user_id", user.id)
    if not user_data:
        await effective_message.reply_text("<blockquote><b>Error:</b> Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    text = PvtChatSettingsData.TEXT.format(
        user.mention_html(),
        user.id,
        user_data.get('lang') or '-',
        'Enabled' if user_data.get('auto_tr') else 'Disabled',
        'Enabled' if user_data.get('echo') else 'Disabled'
    )

    btn = BuildKeyboard.cbutton(PvtChatSettingsData.BUTTONS)
    
    await effective_message.reply_text(text, reply_markup=btn)
