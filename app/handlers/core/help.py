import random

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from app import bot, logger
from app.helpers import BuildKeyboard
from app.utils.database import MemoryDB, database_add_user

class HelpMenuData:
    TEXT = (
        "<blockquote>**Help Menu**</blockquote>\n\n"
        "Hey! Welcome to the bot help section.\n"
        "I'm a Telegram bot that manages groups and handles various tasks effortlessly.\n\n"
        "• /start - Start the bot\n"
        "• /help - To see this message\n"
        "• /support - Get Support or Report any bug related to bot"
    )

    BUTTONS = [
        {"Group Management": "help_menu_gm1", "AI/LLM": "help_menu_ai_knowledge"},
        {"Misc": "help_menu_misc", "Owner/Sudo": "help_menu_owner"},
        {"» bot.info()": "help_menu_botinfo",  "Close": "misc_close", "Try inline": "switch_to_inline"}
    ]


@bot.on_message(filters.command("help", ["/", "!", "-", "."]) | filters.regex("^/start help$"))
async def func_help(_, message: Message):
    user = message.from_user or message.sender_chat
    chat = message.chat

    if chat.type not in [ChatType.PRIVATE]:
        btn = BuildKeyboard.ubutton([{"Click here for help": f"http://t.me/{bot.me.username}?start=help"}])
        await message.reply_text(f"Hey, {user.first_name or user.title}\nContact me in PM for help!", reply_markup=btn)
        return
    
    # database entry checking if user is registered.
    database_add_user(user)

    show_bot_pic = MemoryDB.bot_data.get("show_bot_pic")
    images = MemoryDB.bot_data.get("images")
    photo = None
    photo_file_id = None

    if images:
        photo = random.choice(images).strip()
    elif show_bot_pic:
        try:
            async for bp in bot.get_chat_photos("me", 1):
                photo_file_id = bp.file_id # the high quality photo file_id
        except:
            pass
    
    btn = BuildKeyboard.cbutton(HelpMenuData.BUTTONS)
    
    if photo or photo_file_id:
        try:
            await message.reply_photo(photo or photo_file_id, caption=HelpMenuData.TEXT, reply_markup=btn)
            return
        except BadRequest:
            pass
        except Exception as e:
            logger.error(e)
    
    # if BadRequest or No Photo or Other error
    await message.reply_text(HelpMenuData.TEXT, reply_markup=btn)
