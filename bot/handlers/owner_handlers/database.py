import json
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.database import DBConstants, MongoDB
from bot.helpers import BuildKeyboard
from bot.utils.decorators.sudo_users import require_sudo
from bot.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    victim_id = " ".join(context.args)
    
    if not victim_id:
        database_info = MongoDB.info()
        msg_storage = "<blockquote><b>Database information</b></blockquote>\n\n"
        for info in database_info.values():
            msg_storage += (
                f"<b>• Document:</b> <i>{info.get('name')}</i>\n"
                f"<b>• Quantity:</b> <code>{info.get('quantity')}</code>\n"
                f"<b>• Size:</b> <code>{info.get('size')}</code>\n"
                f"<b>• A. size:</b> <code>{info.get('acsize')}</code>\n\n"
            )
        
        active_status = MongoDB.find(DBConstants.USERS_DATA, "active_status")
        active_users = active_status.count(True)
        inactive_users = active_status.count(False)

        text = (
            f"{msg_storage}" # already has 2 escapes
            f"<b>• Active users:</b> <code>{active_users}</code>\n"
            f"<b>• Inactive users:</b> <code>{inactive_users}</code>\n\n"
            f"<blockquote><b>Note:</b> <code>/database ChatID</code> to get specific chat database information.</blockquote>"
        )

        await message.reply_text(text)
        return
    
    try:
        victim_id = int(victim_id)
    except ValueError:
        await message.reply_text("Invalid ChatID!")
        return

    btn = None
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
        
        chat_title = victim_info.title if victim_info else chat_data.get('title')
        chat_invite_link = victim_info.invite_link if victim_info else None

        text = (
            "<blockquote><b>Database information</b></blockquote>\n\n"

            f"• Title: {chat_title}\n"
            f"• ID: <code>{victim_id}</code>\n\n"

            f"• Language: <code>{chat_data.get('lang')}</code>\n"
            f"• Auto translate: <code>{chat_data.get('auto_tr') or False}</code>\n"
            f"• Echo: <code>{chat_data.get('echo') or False}</code>\n"
            f"• Antibot: <code>{chat_data.get('antibot') or False}</code>\n"
            f"• Welcome Members: <code>{chat_data.get('welcome_user') or False}</code>\n"
            f"• Farewell Members: <code>{chat_data.get('farewell_user') or False}</code>\n"
            f"• Join Request: <code>{chat_data.get('chat_join_req')}</code>\n"
            f"• Service Messages: <code>{chat_data.get('service_messages')}</code>\n"
            f"• Links Behave: <code>{chat_data.get('links_behave')}</code>\n"
            f"• Allowed Links: <code>{', '.join(chat_data.get('allowed_links') or [])}</code>"
        )

        btn = BuildKeyboard.ubutton([{"Invite Link": chat_invite_link}]) if chat_invite_link else None
        
        custom_welcome_msg = chat_data.get('custom_welcome_msg')
        if custom_welcome_msg:
            text += (
                "\n\n<blockquote><b>Custom Welcome message</b></blockquote>\n\n"
                f"<blockquote>{custom_welcome_msg}</blockquote>"
            )
        
        chat_filters = chat_data.get('filters')
        if chat_filters:
            filters_file = BytesIO(json.dumps(chat_filters, indent=4).encode())
            filters_file.name = f"filters_{victim_id}.json"

            await message.reply_document(filters_file, f"ChatID: <code>{victim_id}</code>")
    
    else:
        user_data = MongoDB.find_one(DBConstants.USERS_DATA, "user_id", victim_id) # victim_id as int
        if not user_data:
            await message.reply_text("User not found!")
            return
        
        try:
            victim_info = await context.bot.get_chat(victim_id)
        except:
            victim_info = None
        
        try:
            victim_name = victim_info.mention_html() if victim_info else user_data.get('mention')
        except: # TypeError
            victim_name = user_data.get('mention')
        
        victim_username = victim_info.username if victim_info else user_data.get('username')
        text = "<blockquote><b>Database information</b></blockquote>\n\n"

        text += (
            f"• Name: {victim_name}\n"
            f"• ID: <code>{victim_id}</code>\n"
            f"• Username: @{victim_username or 'username'}\n\n"

            f"• Language: <code>{user_data.get('lang')}</code>\n"
            f"• Auto translate: <code>{user_data.get('auto_tr') or False}</code>\n"
            f"• Echo: <code>{user_data.get('echo') or False}</code>\n\n"

            f"• Active status: <code>{user_data.get('active_status')}</code>"
        )

        if victim_info:
            btn = BuildKeyboard.ubutton([{"User Profile": f"tg://user?id={victim_info.id}"}]) if victim_info.username else None
    
    # common message sender for both group chat & private chat database info
    await message.reply_text(text, reply_markup=btn)
