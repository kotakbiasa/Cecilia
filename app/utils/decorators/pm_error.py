from functools import wraps
from pyrogram.types import Message
from pyrogram.enums import ChatType
from app import bot
from app.helpers import BuildKeyboard

def pm_error(func):
    @wraps(func)
    async def wraper(_, message: Message):
        chat = message.chat

        if chat.type in [ChatType.PRIVATE]:
            bot_info = await bot.get_me()

            btn = BuildKeyboard.ubutton([{"Add me to your chat": f"http://t.me/{bot_info.username}?startgroup=help"}])
            await message.reply_text("This command is made to be used in group chats, not in pm!", reply_markup=btn)
            return
        
        return await func(_, message)
    return wraper
