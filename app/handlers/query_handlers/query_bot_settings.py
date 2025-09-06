import json
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from app import logger
from app.utils.update_db import update_database
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB, MongoDB
from ..owner_handlers.bsettings import BotSettingsData

async def query_bot_settings(_, message: Message):
    user = message.from_user
    query = update.callback_query

    # refined query data
    query_data = query.data.removeprefix("bsettings_")

    # accessing bot_data
    bot_data = MemoryDB.bot_data

    # variable required for global reply
    is_editing_btn = None
    is_refresh_btn = True

    if query_data == "menu":
        text = BotSettingsData.TEXT.format(
            'Yes' if bot_data.get('show_bot_pic') else 'No',
            len(bot_data.get('images') or []),
            bot_data.get('support_chat') or '-',
            bot_data.get('server_url') or '-',
            len(bot_data.get('sudo_users') or []),
            bot_data.get('shrinkme_api') or '-',
            bot_data.get('omdb_api') or '-',
            bot_data.get('weather_api') or '-'
        )

        btn_data = BotSettingsData.BUTTONS
        is_refresh_btn = False
    
    elif query_data == "show_bot_pic":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "show_bot_pic",
            "is_list": False,
            "is_int": False
        })

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Show Bot Photo: `{}`\n\n"
            "<blockquote>**Note:** Send's /start message or other supported message with Bot photo.</blockquote>"
        ).format("Yes" if bot_data.get("show_bot_pic") else "No")

        btn_data = [
            {"YES": "database_bool_true", "NO": "database_bool_false"},
            {"Back": "bsettings_menu", "Close": "misc_close"}
        ]
    
    elif query_data == "images":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "images",
            "is_list": True,
            "is_int": False
        })

        images = bot_data.get("images")
        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Images (link): `{}`\n\n"
            "<blockquote>**Note:** Images that will be randomly shown with various command messages. Multiple links should be separated by comma.</blockquote>"
        ).format(len(images or []))

        if images:
            await query.answer("Sending images links...")

            images_binary = BytesIO(",\n".join(images).encode())
            images_binary.name = "images.txt"

            await user.send_document(images_binary, f"Total images: {len(images)}")
    
    elif query_data == "support_chat":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "support_chat",
            "is_list": False,
            "is_int": False
        })

        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Support Chat (link): `{}`\n\n"
            "<blockquote>**Note:** Group chat link for bot support (optional)</blockquote>"
        ).format(bot_data.get("support_chat") or '-')
    
    elif query_data == "server_url":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "server_url",
            "is_list": False,
            "is_int": False
        })

        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Server URL: `{}`\n\n"
            "<blockquote>**Note:** If `Server URL` isn't provided and bot is deployed on render (free) then bot will fall asleep. (Server Reboot Required)</blockquote>"
        ).format(bot_data.get("server_url") or '-')

    elif query_data == "sudo":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "sudo_users",
            "is_list": True,
            "is_int": True
        })

        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Sudo users: `{}`\n\n"
            "<blockquote>**Note: (Warning)** Sudo users have owner functions access!\nAdd UserID eg. `2134776547`\nMultiple ID should be separated by comma.</blockquote>"
        ).format(", ".join(str(user_id) for user_id in (bot_data.get("sudo_users") or [])))

    elif query_data == "shrinkme_api":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "shrinkme_api",
            "is_list": False,
            "is_int": False
        })
        
        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Shrinkme API: `{}`\n\n"
            "<blockquote>**Note:** This API is for /shorturl command.</blockquote>"
        ).format(bot_data.get("shrinkme_api") or '-')
    
    elif query_data == "omdb_api":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "omdb_api",
            "is_list": False,
            "is_int": False
        })
        
        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "OMDB API: `{}`\n\n"
            "<blockquote>**Note:** This API is for /movie command.</blockquote>"
        ).format(bot_data.get("omdb_api") or '-')
    
    elif query_data == "weather_api":
        MemoryDB.insert(DBConstants.DATA_CENTER, user.id, {
            "update_data_key": "weather_api",
            "is_list": False,
            "is_int": False
        })
        
        is_editing_btn = True

        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "Weather API: `{}`\n\n"
            "<blockquote>**Note:** This API is for /weather command.</blockquote>"
        ).format(bot_data.get("weather_api") or '-')
    
    elif query_data == "database":
        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "**• Restore Database**\n"
            "- <i>Delete MongoDB's `bot_data` and restore from backup in `config.env`</i>\n\n"

            "**• Wipe Memory Cache**\n"
            "- <i>This will clean memory cache.</i>\n\n"

            "<blockquote>**Note:** Use `Restore Database` with caution!</blockquote>"
        )

        btn_data = [
            {"Restore Database": "bsettings_restoredb", "Wipe Memory Cache": "bsettings_wipe_memory"},
            {"Back": "bsettings_menu", "Close": "misc_close"}
        ]
        is_refresh_btn = False
    
    elif query_data == "restoredb":
        text = (
            "<blockquote>**Bot Settings**</blockquote>\n\n"
            "**• Restore MongoDB Database?**"
        )

        btn_data = [
            {"YES": "bsettings_restoredb_confirm", "NO": "bsettings_database"},
            {"Back": "bsettings_database"}
        ]
        is_refresh_btn = False
    
    elif query_data == "restoredb_confirm":
        await query.answer("Restoring Bot Data...")

        # removing unnecessary files
        bot_data.pop("_id", "") # deleteing _id object
        
        db_backup = BytesIO(json.dumps(bot_data, indent=4).encode())
        db_backup.name = "backup_database.json"

        await user.send_document(db_backup, "Database Backup File")

        # process of deleting...
        response = MongoDB.delete_collection(DBConstants.BOT_DATA)
        if response:
            bot_data.clear()
            update_database()
            text = (
                "Database has been restored successfully from `config.env`\n"
                "<blockquote>**Note:** Reboot is recommended.</blockquote>"
            )
        else:
            text = "Something went wrong! Check /log"
        
        await user.send_message(text)
        return # don't want to edit message by global reply
    
    elif query_data == "wipe_memory":
        await query.answer("Cleaning Memory Cache...")

        MemoryDB.clear_all()
        update_database()

        await user.send_message("Memory Cache has been cleaned!")
        return # don't want to edit message by global reply
    
    # common editing keyboard buttons
    if is_editing_btn:
        btn_data = [
            {"Edit Value": "database_edit_value", "Remove Value": "database_rm_value"},
            {"Back": "bsettings_menu", "Close": "misc_close"}
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
