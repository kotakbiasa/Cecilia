import json
from io import BytesIO

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.args_extractor import extract_cmd_args
from app.utils.database import DBConstants, MongoDB
from app.utils.decorators.pm_only import pm_only
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command(["database", "db"], ["/", "!", "-", "."]))
@pm_only
@require_sudo
async def func_database(_, message: Message):
    # CHAT/USER ID // not username
    victim_id = extract_cmd_args(message.text, message.command)
    
    if not victim_id:
        database_info = MongoDB.info()
        msg_storage = "<blockquote>**Database information**</blockquote>\n\n"
        for info in database_info:
            info = database_info[info]
            msg_storage += (
                f"**• Document:** <i>{info.get('name')}</i>\n"
                f"**• Quantity:** `{info.get('quantity')}`\n"
                f"**• Size:** `{info.get('size')}`\n"
                f"**• A. size:** `{info.get('acsize')}`\n\n"
            )
        
        active_status = MongoDB.find(DBConstants.USERS_DATA, "active_status")
        active_users = active_status.count(True)
        inactive_users = active_status.count(False)

        await message.reply_text(
            f"{msg_storage}" # already has 2 escapes
            f"**• Active users:** `{active_users}`\n"
            f"**• Inactive users:** `{inactive_users}`\n\n"
            f"<blockquote>**Note:** `/{message.command[0]} ChatID` to get specific chat database information.</blockquote>"
        )
        return
    
    try:
        victim_id = int(victim_id)
    except ValueError:
        await message.reply_text("Invalid ChatID!")
        return
    
    if "-100" in str(victim_id):
        chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", victim_id) # victim_id as int
        if not chat_data:
            await message.reply_text("Chat not found!")
            return
        
        try:
            victim_info = await bot.get_chat(victim_id)
        except:
            victim_info = None
            btn = None
        
        chat_title = victim_info.title if victim_info else chat_data.get('title')
        chat_invite_link = victim_info.invite_link if victim_info else None

        text = (
            "<blockquote>**Database information**</blockquote>\n\n"

            f"• Title: {chat_title}\n"
            f"• ID: `{victim_id}`\n\n"

            f"• Language: `{chat_data.get('lang') or '-'}`\n"
            f"• Auto translate: `{'Enabled' if chat_data.get('auto_tr') else 'Disabled'}`\n"
            f"• Echo: `{'Enabled' if chat_data.get('echo') else 'Disabled'}`\n"
            f"• Antibot: `{'Enabled' if chat_data.get('antibot') else 'Disabled'}`\n"
            f"• Welcome Members: `{'Enabled' if chat_data.get('welcome_user') else 'Disabled'}`\n"
            f"• Farewell Members: `{'Enabled' if chat_data.get('farewell_user') else 'Disabled'}`\n"
            f"• Join Request: `{chat_data.get('chat_join_req')}`\n"
            f"• Service Messages: `{'Enabled' if chat_data.get('service_messages') else 'Disabled'}`\n"
            f"• Links Behave: `{chat_data.get('links_behave')}`\n"
            f"• Allowed Links: `{', '.join(chat_data.get('allowed_links') or [])}`"
        )

        btn = BuildKeyboard.ubutton([{"Invite Link": chat_invite_link}]) if chat_invite_link else None
        
        custom_welcome_msg = chat_data.get('custom_welcome_msg')
        if custom_welcome_msg:
            text += (
                "\n\n<blockquote>**Custom Welcome message**</blockquote>\n\n"
                f"<blockquote>{custom_welcome_msg}</blockquote>"
            )
        
        chat_triggers = chat_data.get("triggers")
        if chat_triggers:
            triggers_file = BytesIO(json.dumps(chat_triggers, indent=4).encode())
            triggers_file.name = f"triggers [{victim_id}].json"

            await message.reply_document(triggers_file, caption=f"ChatID: `{victim_id}`")
    
    else:
        user_data = MongoDB.find_one(DBConstants.USERS_DATA, "user_id", victim_id) # victim_id as int
        if not user_data:
            await message.reply_text("User not found!")
            return
        
        try:
            victim_info = await bot.get_users(victim_id)
        except:
            victim_info = None
            btn = None
        
        try:
            victim_name = victim_info.mention if victim_info else user_data.get('mention')
        except: # TypeError ?
            victim_name = user_data.get('mention')
        
        victim_username = victim_info.username if victim_info else user_data.get('username')
        text = "<blockquote>**Database information**</blockquote>\n\n"

        text += (
            f"• Name: {victim_name}\n"
            f"• ID: `{victim_id}`\n"
            f"• Username: @{victim_username or 'username'}\n\n"

            f"• Language: `{user_data.get('lang') or '-'}`\n"
            f"• Auto translate: `{'Enabled' if user_data.get('auto_tr') else 'Disabled'}`\n"
            f"• Echo: `{'Enabled' if user_data.get('echo') else 'Disabled'}`\n\n"

            f"• Active status: `{user_data.get('active_status')}`"
        )

        if victim_info:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("User Profile", user_id=victim_info.id)]]) if victim_info.username else None
    
    # common message sender for both group chat & private chat database info
    await message.reply_text(text, reply_markup=btn)
