from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from app import logger, TL_LANG_CODES_URL
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB
from ..user_handlers.settings import PvtChatSettingsData
from ..group.chat_settings import GroupChatSettingsData

async def query_chat_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query

    # refined query data
    query_data = query.data.removeprefix("csettings_")

    # memory access
    data_center = MemoryDB.data_center.get(chat.id) # ChatID bcz its for both Private & Public Chat
    if not data_center:
        await query.answer("Session Expired.", True)
        try:
            message_id = query.message.message_id
            await chat.delete_messages([message_id, message_id - 1])
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
    
    # common variable for chat_data and user_data
    memory_data = MemoryDB.chats_data.get(chat.id) or MemoryDB.users_data.get(chat.id)

    # variable required for global reply
    is_editing_btn = None
    is_boolean_btn = None
    is_refresh_btn = True

    if query_data == "menu":
        # Handling PRIVATE chat setting
        if chat.type in [ChatType.PRIVATE]:
            text = PvtChatSettingsData.TEXT.format(
                user.mention_html(),
                user.id,
                memory_data.get('lang') or '-',
                'Enabled' if memory_data.get('auto_tr') else 'Disabled',
                'Enabled' if memory_data.get('echo') else 'Disabled'
            )

            btn_data = PvtChatSettingsData.BUTTONS
            is_refresh_btn = False
        
        else:
            text = GroupChatSettingsData.TEXT.format(
                chat.title,
                chat.id,
                memory_data.get('lang') or '-',
                'Enabled' if memory_data.get('auto_tr') else 'Disabled',
                'Enabled' if memory_data.get('echo') else 'Disabled',
                'Enabled' if memory_data.get('antibot') else 'Disabled',
                'Enabled' if memory_data.get('welcome_user') else 'Disabled',
                'Enabled' if memory_data.get('farewell_user') else 'Disabled',
                memory_data.get('chat_join_req'),
                'Enabled' if memory_data.get('service_messages') else 'Disabled',
                memory_data.get('links_behave'),
                ', '.join(memory_data.get('allowed_links') or [])
            )

            btn_data = GroupChatSettingsData.BUTTONS
            is_refresh_btn = False
    
    elif query_data == "lang":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "lang",
            "is_list": False,
            "is_int": False
        })

        is_editing_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Language: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> <a href='{}'>Available language codes</a>\nExample: <code>en</code> for English language.</blockquote>"
        ).format(memory_data.get("lang") or "-", TL_LANG_CODES_URL)
    
    elif query_data == "auto_tr":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "auto_tr",
            "is_list": False,
            "is_int": False
        })

        is_boolean_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Auto translate: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will automatically translate chat messages to seleted language.</blockquote>"
        ).format("Enabled" if memory_data.get("auto_tr") else "Disabled")
    
    elif query_data == "echo":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "echo",
            "is_list": False,
            "is_int": False
        })

        is_boolean_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Echo: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will echo user messages.</blockquote>"
        ).format("Enabled" if memory_data.get("echo") else 'Disabled')
    
    elif query_data == "antibot":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "antibot",
            "is_list": False,
            "is_int": False
        })

        is_boolean_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Antibot: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> If someone try to add bots in chat, this will kick the bot, if enabled.</blockquote>"
        ).format("Enabled" if memory_data.get("antibot") else 'Disabled')
    
    elif query_data == "welcome_user":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "welcome_user",
            "is_list": False,
            "is_int": False
        })

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Welcome Members: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will welcome new chat member, if enabled.</blockquote>"
        ).format("Enabled" if memory_data.get("welcome_user") else 'Disabled')

        btn_data = [
            {"Enable": "database_bool_true", "Disable": "database_bool_false"},
            {"Welcome Photo": "csettings_welcome_photo"},
            {"Custom Welcome Message": "csettings_custom_welcome_msg"},
            {"Back": "csettings_menu", "Close": "csettings_close"}
        ]
    
    elif query_data == "welcome_photo":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "welcome_photo",
            "is_list": False,
            "is_int": False
        })

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Welcome Photo: <code>{}</code>\n"
            "<blockquote><b>Note:</b>Welcome photo to greet new chat members. (Currently only supports URL photo link)</blockquote>"
        ).format(memory_data.get("welcome_photo") or "-")

        btn_data = [
            {"Edit Value": "database_edit_value", "Remove Value": "database_rm_value"},
            {"Back": "csettings_welcome_user", "Close": "csettings_close"}
        ]
    
    elif query_data == "custom_welcome_msg":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "custom_welcome_msg",
            "is_list": False,
            "is_int": False
        })

        custom_message = memory_data.get("custom_welcome_msg") or "-"

        if len(str(custom_message)) > 500:
            await chat.send_message(f"Custom Greeting Message:\n\n{custom_message}")
            custom_message = "Message is too long."
        
        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Custom Welcome Message:\n<code>{}</code>\n"
            "<blockquote><b>Note:</b> Custom welcome message to greet new chat members. (supports telegram formatting)</blockquote>"
        ).format(custom_message)

        btn_data = [
            {"Set Custom Message": "database_edit_value", "Remove Custom Message": "database_rm_value"},
            {"Formattings": "csettings_formattings"},
            {"Back": "csettings_welcome_user", "Close": "csettings_close"}
        ]
    
    elif query_data == "formattings":
        text = (
            "<blockquote><b>Formattings</b></blockquote>\n\n"
            "• <code>{first}</code> - users firstname\n"
            "• <code>{last}</code> - users lastname\n"
            "• <code>{fullname}</code> - users fullname\n"
            "• <code>{username}</code> - users username\n"
            "• <code>{mention}</code> - mention user\n"
            "• <code>{id}</code> - users ID\n"
            "• <code>{chatname}</code> - chat title"
        )

        btn_data = [{"Back": "csettings_custom_welcome_msg", "Close": "csettings_close"}]
        is_refresh_btn = False
    
    elif query_data == "farewell_user":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "farewell_user",
            "is_list": False,
            "is_int": False
        })

        is_boolean_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Farewell Members: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will send a farewell message to chat when a member left, if enabled.</blockquote>"
        ).format("Enabled" if memory_data.get("farewell_user") else 'Disabled')
    
    elif query_data == "chat_join_req":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "chat_join_req",
            "is_list": False,
            "is_int": False
        })

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Join Request: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will auto Approve or Decline or Do Nothing while a member request to join this Group. (Bot should have add/invite member permission.)</blockquote>"
        ).format(memory_data.get("chat_join_req"))

        btn_data = [
            {"Approve": "database_value_approve", "Decline": "database_value_decline", "Do Nothing": "database_rm_value"},
            {"Back": "csettings_menu", "Close": "csettings_close"}
        ]
    
    elif query_data == "service_messages":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "service_messages",
            "is_list": False,
            "is_int": False
        })

        is_boolean_btn = True
        
        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Service Messages: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> This will auto delete chat service messages (new member join, chat photo update etc.)</blockquote>"
        ).format("Enabled" if memory_data.get("service_messages") else 'Disabled')
    
    elif query_data == "links_behave":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "links_behave",
            "is_list": False,
            "is_int": False
        })

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Links Behave: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> Links has 3 behaves: [ Delete / Convert to base64 / Do Nothing ]\n"
            "The Links Behave action will be triggered if any non-admin member shares a link in the chat.</blockquote>"
        ).format(memory_data.get("links_behave"))

        btn_data = [
            {"Delete": "database_value_delete", "Convert to base64": "database_value_convert", "Do Nothing": "database_rm_value"},
            {"Back": "csettings_menu", "Close": "csettings_close"}
        ]
    
    elif query_data == "allowed_links":
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {
            "update_data_key": "allowed_links",
            "is_list": True,
            "is_int": False
        })

        is_editing_btn = True

        text = (
            "<blockquote><b>Chat Settings</b></blockquote>\n\n"
            "Allowed links: <code>{}</code>\n\n"
            "<blockquote><b>Note:</b> Send link/domain of allowed links. Example: <code>google.com or https://google.com</code> ! Multiple domain should be separated by comma."
            "Allowed links won't be affected by <code>Links Behave</code></blockquote>"
        ).format(", ".join(memory_data.get("allowed_links") or []))
    
    elif query_data == "close":
        try:
            message_id = query.message.message_id
            await chat.delete_messages([message_id, message_id - 1])
        except:
            try:
                await query.delete_message()
            except:
                pass
        return

    # common editing keyboard buttons
    if is_editing_btn:
        btn_data = [
            {"Edit Value": "database_edit_value", "Remove Value": "database_rm_value"},
            {"Back": "csettings_menu", "Close": "csettings_close"}
        ]
    
    if is_boolean_btn:
        btn_data = [
            {"Enable": "database_bool_true", "Disable": "database_bool_false"},
            {"Back": "csettings_menu", "Close": "csettings_close"}
        ]
    
    # `btn_data` pre-determined & added Refresh btn
    if is_refresh_btn: btn_data.insert(0, {"Refresh": query.data})
    btn = BuildKeyboard.cbutton(btn_data)
    # Global Reply
    try:
        await query.edit_message_caption(text, reply_markup=btn)
    except BadRequest:
        try:
            await query.edit_message_text(text, reply_markup=btn)
        except BadRequest:
            await query.answer()
        except Exception as e:
            logger.error(e)
    except Exception as e:
        logger.error(e)
