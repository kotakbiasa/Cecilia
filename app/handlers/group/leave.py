from pyrogram import filters
from pyrogram.types import Chat, Message
from pyrogram.enums import ChatMemberStatus

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("leave", ["/", "!", "-", "."]))
@pm_error
async def func_leave(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    try:
        user_status = await chat.get_member(user.id)
    except Exception as e:
        return await message.reply_text(str(e))

    if user_status.status != ChatMemberStatus.OWNER:
        return await message.reply_text("Huh, you aren't the owner of this chat!")
    
    btn = BuildKeyboard.cbutton([{"Leave": f"admin_leavechat_{user.id}", "Stay": "misc_close"}, {"Close": "misc_close"}])
    await message.reply_text("Should I leave?", reply_markup=btn)
