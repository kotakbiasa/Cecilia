from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

from app.utils.decorators.pm_error import pm_error
from app.helpers import BuildKeyboard
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_leave(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    message = 
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    try:
        user_status = await chat.get_member(user.id)
    except Exception as e:
        await message.reply_text(str(e))
        return

    if user_status.status not in [ChatMemberStatus.OWNER]:
        await message.reply_text("Huh, you aren't the owner of this chat!")
        return
    
    btn = BuildKeyboard.cbutton([{"Leave": f"admin_leavechat_{user.id}", "Stay": "misc_close"}])
    await message.reply_text("Should I leave?", reply_markup=btn)
