from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB, database_search

class PvtChatSettingsData:
    TEXT = (
        "<blockquote>**Chat Settings**</blockquote>\n\n"

        "• Name: {}\n"
        "• ID: `{}`\n\n"

        "• Language: `{}`\n"
        "• Auto translate: `{}`\n"
        "• Echo: `{}`"
    )

    BUTTONS = [
        {"Language": "csettings_lang", "Auto translate": "csettings_auto_tr"},
        {"Echo": "csettings_echo", "Close": "misc_close"}
    ]


@bot.on_message(filters.command("settings", ["/", "!", "-", "."]) & filters.private)
async def func_settings(_, message: Message):
    user = message.from_user or message.sender_chat

    data = {
        "user_id": user.id, # authorization
        "collection_name": DBConstants.USERS_DATA,
        "search_key": "user_id",
        "match_value": user.id
    }

    MemoryDB.insert(DBConstants.DATA_CENTER, user.id, data)

    user_data = database_search(DBConstants.USERS_DATA, "user_id", user.id)
    if not user_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    text = PvtChatSettingsData.TEXT.format(
        user.mention,
        user.id,
        user_data.get('lang') or '-',
        'Enabled' if user_data.get('auto_tr') else 'Disabled',
        'Enabled' if user_data.get('echo') else 'Disabled'
    )

    btn = BuildKeyboard.cbutton(PvtChatSettingsData.BUTTONS)
    await message.reply_text(text, reply_markup=btn)
