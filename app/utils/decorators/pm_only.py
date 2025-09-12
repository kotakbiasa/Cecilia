import asyncio
from functools import wraps
from pyrogram.types import Message
from pyrogram.enums import ChatType
from app import bot

def pm_only(func):
    @wraps(func)
    async def wraper(_, message: Message):
        chat = message.chat

        if chat.type not in [ChatType.PRIVATE]:
            sent_message = await message.reply_text("This command is made to be used in pm, not in public chat!")
            await asyncio.sleep(3)
            await bot.delete_messages(chat.id, [message.id, sent_message.id])
            return
        
        return await func(_, message)
    return wraper
