from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from app import bot, logger, ORIGINAL_BOT_USERNAME, ORIGINAL_BOT_ID
from app.helpers import BuildKeyboard
from app.utils.database import MemoryDB, database_add_user

@bot.on_message(filters.command("start", ["/", "!", "-", "."]))
async def func_start(_, message: Message):
    user = message.from_user
    chat = message.chat
    bot_info = await bot.get_me()

    if chat.type not in [ChatType.PRIVATE]:
        btn = BuildKeyboard.ubutton([{"Start me in PM": f"http://t.me/{bot_info.username}?start=start"}])
        await message.reply_text(f"Hey, {user.first_name}\nStart me in PM!", reply_markup=btn)
        return
    
    # database entry checking if user is registered.
    database_add_user(user)

    show_bot_pic = MemoryDB.bot_data.get("show_bot_pic") # Boolean
    support_chat = MemoryDB.bot_data.get("support_chat")
    photo_file_id = None

    if show_bot_pic:
        try:
            async for photo in bot.get_chat_photos("me", 1):
                photo_file_id = photo.file_id # the high quality photo file_id
        except:
            pass

    text = (
        f"Hey, {user.first_name}! I'm {bot_info.first_name}!\n\n"
        "I can help you to manage your chat with a lots of useful features!\n"
        "Feel free to add me to your chat.\n\n"
        "• /help - Get bot help menu\n\n"
        "<b>• Source code:</b> <a href='https://github.com/bishalqx980/tgbot'>GitHub</a>\n"
        "<b>• Report bug:</b> <a href='https://github.com/bishalqx980/tgbot/issues'>Report</a>\n"
        "<b>• Developer:</b> <a href='https://t.me/bishalqx680/22'>bishalqx980</a>"
    )

    if bot_info.id != ORIGINAL_BOT_ID:
        text += f"\n\n<blockquote>Cloned bot of @{ORIGINAL_BOT_USERNAME}</blockquote>"

    btn_data = {"Add me to your chat": f"http://t.me/{bot_info.username}?startgroup=help"}
    if support_chat:
        btn_data.update({"Support Chat": support_chat})
    
    btn = BuildKeyboard.ubutton([btn_data])

    if photo_file_id:
        try:
            await message.reply_photo(photo_file_id, caption=text, reply_markup=btn)
            return
        except BadRequest:
            pass
        except Exception as e:
            logger.error(e)
    
    # if BadRequest or No Photo or Other error
    await message.reply_text(text, reply_markup=btn)
