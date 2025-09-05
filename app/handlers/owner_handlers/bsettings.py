import random

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from app import logger
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB
from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

class BotSettingsData:
    TEXT = (
        "<blockquote><b>Bot Settings</b></blockquote>\n\n"
        "• Show Bot Photo: <code>{}</code>\n"
        "• Images: <code>{}</code>\n"
        "• Support chat: <code>{}</code>\n"
        "• Server url: <code>{}</code>\n"
        "• Sudo: <code>{}</code>\n"
        "• Shrinkme API: <code>{}</code>\n"
        "• OMDB API: <code>{}</code>\n"
        "• Weather API: <code>{}</code>"
    )

    BUTTONS = [
        {"Show Bot Photo": "bsettings_show_bot_pic", "Images": "bsettings_images"},
        {"Support Chat": "bsettings_support_chat", "Server URL": "bsettings_server_url"},
        {"Sudo": "bsettings_sudo", "Shrinkme API": "bsettings_shrinkme_api"},
        {"OMDB API": "bsettings_omdb_api", "Weather API": "bsettings_weather_api"},
        {"> ⁅ Database ⁆": "bsettings_database", "Close": "misc_close"}
    ]

@pm_only
@require_sudo
async def func_bsettings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    
    # requied data needed for editing
    data = {
        "user_id": user.id, # authorization
        "collection_name": DBConstants.BOT_DATA,
        "search_key": "_id",
        "match_value": MemoryDB.bot_data.get("_id")
    }

    MemoryDB.insert(DBConstants.DATA_CENTER, user.id, data)

    # accessing bot data
    bot_data = MemoryDB.bot_data

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

    btn = BuildKeyboard.cbutton(BotSettingsData.BUTTONS)
    
    show_bot_pic = MemoryDB.bot_data.get("show_bot_pic")
    images = MemoryDB.bot_data.get("images")
    photo = None
    photo_file_id = None

    if images:
        photo = random.choice(images).strip()
    elif show_bot_pic:
        try:
            bot_photos = await context.bot.get_user_profile_photos(context.bot.id)
            photo_file_id = bot_photos.photos[0][-1].file_id # the high quality photo file_id
        except:
            pass
    
    if photo or photo_file_id:
        try:
            await message.reply_photo(photo or photo_file_id, text, reply_markup=btn, protect_content=True)
            return
        except BadRequest:
            pass
        except Exception as e:
            logger.error(e)
    
    # if BadRequest or No Photo or Other error
    await message.reply_text(text, reply_markup=btn, protect_content=True)
