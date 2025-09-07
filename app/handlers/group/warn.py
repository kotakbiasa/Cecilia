from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from app.helpers import BuildKeyboard
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_warn(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    message = 
    re_msg = message.reply_to_message
    victim = re_msg.from_user if re_msg else None
    reason = extract_cmd_args(message.text, message.command)

    cmd_prefix = message.text[1]
    
    if cmd_prefix == "d":
        try:
            await chat.delete_messages([message.id, re_msg.id])
        except:
            pass
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    if not re_msg:
        await message.reply_text("I don't know who you are talking about! Reply the member whom you want to warn!\nE.g`/warn [reason]`")
        return
    
    if victim.id == bot.me.id:
        await message.reply_text("Ohh, haha!! I can remove my own warn's 😝!!")
        return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, bot.me.id, user.id, victim.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return

    if chat_admins.is_victim_admin or chat_admins.is_victim_owner:
        await message.reply_text("Rule no. 1 - Admins are always right!\nRule no. 2 - If admins are wrong then read rule no. 1 !!")
        return
    
    if not chat_admins.is_bot_admin:
        await message.reply_text("I'm not an admin in this chat!")
        return
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    warns = chat_data.get("warns") or {}
    victim_warns = warns.get(str(victim.id)) or {} # mongodb doesn't allow int doc key

    warn_count = victim_warns.get("count") or 0
    warn_count += 1
    warn_reasons = victim_warns.get("reasons") or []
    warn_reasons.append(reason if reason else "")

    update_data = {
        "victim_mention": victim.mention.HTML, # needed for remove warns
        "count": warn_count,
        "reasons": warn_reasons
    }
    
    if victim_warns:
        victim_warns.update(update_data)
    else:
        warns.update({str(victim.id): update_data})
    
    response = MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"warns": warns})
    if response:
        MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"warns": warns})
    
    text = (
        f"Watchout, {victim.mention.HTML} !!\n"
        f"**You got warning's:** `{warn_count}/3`\n"
        f"**Reason (current warn):** `{reason if reason else 'Not Given'}`"
    )

    btn = BuildKeyboard.cbutton([{"Remove Warn's (Admin only)": f"admin_remove_warn_{victim.id}"}])
    await message.reply_text(text, reply_markup=btn)

    if warn_count >= 3:
        try:
            await chat.restrict_member(victim.id, ChatPermissions.no_permissions())
        except Exception as e:
            await message.reply_text(str(e))
            return
        
        reasons = ""
        for reason in victim_warns.get("reasons"):
            reasons += f"<blockquote>{reason}</blockquote>\n"
        
        await message.reply_text(f"{victim.mention.HTML} has been muted!\nWarning's: {reasons}")
