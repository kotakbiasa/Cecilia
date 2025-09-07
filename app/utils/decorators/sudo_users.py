from functools import wraps
from pyrogram.types import Message
from app import config
from app.utils.database import MemoryDB

def require_sudo(func):
    """
    :returns list: list of sudo's including **owner_id**
    """
    @wraps(func)
    async def wraper(_, message: Message):
        user = message.from_user or message.sender_chat
        owner_id = config.owner_id
        sudo_users = MemoryDB.bot_data.get("sudo_users") or []

        if owner_id not in sudo_users:
            sudo_users.append(owner_id)
        
        if user.id not in sudo_users:
            await message.reply_text("Access denied!")
            return
        
        return await func(_, message)
    return wraper
