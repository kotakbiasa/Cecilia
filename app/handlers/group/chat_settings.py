from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.utils.database import DBConstants, MemoryDB, database_search

class GroupChatSettingsData:
    TEXT = (
        "<blockquote>**Chat Settings**</blockquote>\n\n"

        "• Title: {}\n"
        "• ID: `{}`\n\n"

        "• Language: `{}`\n"
        "• Auto translate: `{}`\n"
        "• Echo: `{}`\n"
        "• Antibot: `{}`\n"
        "• Welcome Members: `{}`\n"
        "• Farewell Members: `{}`\n"
        "• Join Request: `{}`\n"
        "• Service Messages: `{}`\n"
        "• Links Behave: `{}`\n"
        "• Allowed Links: `{}`"
    )

    BUTTONS = [
        {"Language": "csettings_lang", "Auto translate": "csettings_auto_tr"},
        {"Echo": "csettings_echo", "Antibot": "csettings_antibot"},
        {"Welcome Members": "csettings_welcome_user", "Farewell Members": "csettings_farewell_user"},
        {"Links Behave": "csettings_links_behave", "Allowed Links": "csettings_allowed_links"},
        {"Join Request": "csettings_chat_join_req", "Service Messages": "csettings_service_messages"},
        {"Close": "csettings_close"}
    ]


@bot.on_message(filters.command("settings", ["/", "!", "-", "."]) & filters.group)
async def func_chat_settings(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    # Permission Checking...
    if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("You aren't an admin in this chat!")
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_change_info:
        return await message.reply_text("You don't have enough permission to manage this chat!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    data = {
        "user_id": user.id, # authorization
        "collection_name": DBConstants.CHATS_DATA,
        "search_key": "chat_id",
        "match_value": chat.id
    }
    
    MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, data)

    text = GroupChatSettingsData.TEXT.format(
        chat.title,
        chat.id,
        chat_data.get('lang') or '-',
        'Enabled' if chat_data.get('auto_tr') else 'Disabled',
        'Enabled' if chat_data.get('echo') else 'Disabled',
        'Enabled' if chat_data.get('antibot') else 'Disabled',
        'Enabled' if chat_data.get('welcome_user') else 'Disabled',
        'Enabled' if chat_data.get('farewell_user') else 'Disabled',
        chat_data.get('chat_join_req'),
        'Enabled' if chat_data.get('service_messages') else 'Disabled',
        chat_data.get('links_behave'), # this contains a value
        ', '.join(chat_data.get('allowed_links') or [])
    )

    btn = BuildKeyboard.cbutton(GroupChatSettingsData.BUTTONS)
    await message.reply_text(text, reply_markup=btn)
