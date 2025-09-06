from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_demote(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message
    re_msg = message.reply_to_message
    victim = re_msg.from_user if re_msg else None
    reason = extract_cmd_args(message.text, message.command)

    cmd_prefix = message.text[1]
    is_silent = False
    
    if cmd_prefix == "s":
        is_silent = True
        try:
            await message.delete()
        except:
            pass

    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    if not re_msg:
        await message.reply_text("I don't know who you are talking about! Reply the member whom you want to demote!\nE.g`/demote reason`")
        return
    
    if victim.id == context.bot.id:
        await message.reply_text("I'm not going to demote myself!")
        return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, context.bot.id, user.id, victim.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return

    if chat_admins.is_victim_owner:
        await message.reply_text("I'm not going to demote chat owner! You must be kidding!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_promote_members:
        await message.reply_text("You don't have enough permission to demote chat members!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    if not chat_admins.is_bot_admin.can_promote_members:
        await message.reply_text("I don't have enough permission to demote chat members!")
        return
    
    try:
        await chat.promote_member(victim.id)
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not is_silent:
        text = f"{victim.mention.HTML} has been demoted." + (f"\nReason: {reason}" if reason else "")
        await message.reply_text(text)
