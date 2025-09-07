from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_kick(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    message = 
    re_msg = message.reply_to_message
    victim = re_msg.from_user if re_msg else None
    reason = extract_cmd_args(message.text, message.command)

    cmd_prefix = message.text[1]
    is_silent = False
    
    try:
        if cmd_prefix == "s":
            is_silent = True
            await message.delete()
        elif cmd_prefix == "d":
            await chat.delete_messages([message.id, re_msg.id])
    except:
        pass
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return

    if not re_msg:
        await message.reply_text("I don't know who you are talking about! Reply the member whom you want to kick!\nE.g`/kick reason`")
        return
    
    if victim.id == bot.me.id:
        await message.reply_text("I'm not going to kick myself!")
        return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, bot.me.id, user.id, victim.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return

    if chat_admins.is_victim_admin or chat_admins.is_victim_owner:
        await message.reply_text("I'm not going to kick an admin! You must be kidding!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_restrict_members:
        await message.reply_text("You don't have enough permission to restrict chat members!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_restrict_members:
        await message.reply_text("I don't have enough permission to restrict chat members!")
        return
    
    try:
        await chat.unban_member(victim.id)
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not is_silent:
        text = f"{victim.mention.HTML} has been kicked out from this chat." + (f"\nReason: {reason}" if reason else "")
        await message.reply_text(text)
