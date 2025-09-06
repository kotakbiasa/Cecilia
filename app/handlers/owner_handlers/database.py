import json
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from app.utils.database import DBConstants, MongoDB
from app.helpers import BuildKeyboard
from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_database(_, message: Message):
    message = update.message
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

        text = (
            f"{msg_storage}" # already has 2 escapes
            f"**• Active users:** `{active_users}`\n"
            f"**• Inactive users:** `{inactive_users}`\n\n"
            f"<blockquote>**Note:** `/database ChatID` to get specific chat database information.</blockquote>"
        )

        await message.reply_text(text)
        return
    
    try:
        victim_id = int(victim_id)
    except ValueError:
        await message.reply_text("Invalid ChatID!")
        return

    # if chat_id given
    if "-100" in str(victim_id):
        chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", victim_id) # victim_id as int
        if not chat_data:
            await message.reply_text("Chat not found!")
            return
        
        try:
            victim_info = await context.bot.get_chat(victim_id)
        except:
            victim_info = None
            btn = None
        
        chat_title = victim_info.title if victim_info else chat_data.get('title')
        chat_invite_link = victim_info.invite_link if victim_info else None

        text = (
            "<blockquote>**Database information**</blockquote>\n\n"

            f"• Title: {chat_title}\n"
            f"• ID: `{victim_id}`\n\n"

            f"• Language: `{chat_data.get('lang')}`\n"
            f"• Auto translate: `{chat_data.get('auto_tr') or False}`\n"
            f"• Echo: `{chat_data.get('echo') or False}`\n"
            f"• Antibot: `{chat_data.get('antibot') or False}`\n"
            f"• Welcome Members: `{chat_data.get('welcome_user') or False}`\n"
            f"• Farewell Members: `{chat_data.get('farewell_user') or False}`\n"
            f"• Join Request: `{chat_data.get('chat_join_req')}`\n"
            f"• Service Messages: `{chat_data.get('service_messages')}`\n"
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
        
        chat_filters = chat_data.get('filters')
        if chat_filters:
            filters_file = BytesIO(json.dumps(chat_filters, indent=4).encode())
            filters_file.name = f"filters_{victim_id}.json"

            await message.reply_document(filters_file, f"ChatID: `{victim_id}`")
    
    else:
        user_data = MongoDB.find_one(DBConstants.USERS_DATA, "user_id", victim_id) # victim_id as int
        if not user_data:
            await message.reply_text("User not found!")
            return
        
        try:
            victim_info = await context.bot.get_chat(victim_id)
        except:
            victim_info = None
            btn = None
        
        try:
            victim_name = victim_info.mention.HTML if victim_info else user_data.get('mention')
        except: # TypeError
            victim_name = user_data.get('mention')
        
        victim_username = victim_info.username if victim_info else user_data.get('username')
        text = "<blockquote>**Database information**</blockquote>\n\n"

        text += (
            f"• Name: {victim_name}\n"
            f"• ID: `{victim_id}`\n"
            f"• Username: @{victim_username or 'username'}\n\n"

            f"• Language: `{user_data.get('lang')}`\n"
            f"• Auto translate: `{user_data.get('auto_tr') or False}`\n"
            f"• Echo: `{user_data.get('echo') or False}`\n\n"

            f"• Active status: `{user_data.get('active_status')}`"
        )

        if victim_info:
            btn = BuildKeyboard.ubutton([{"User Profile": f"tg://user?id={victim_info.id}"}]) if victim_info.username else None
    
    # common message sender for both group chat & private chat database info
    await message.reply_text(text, reply_markup=btn)
