from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from app.helpers import BuildKeyboard
from .auxiliary.chat_admins import ChatAdmins
from .auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    effective_message = update.effective_message
    re_msg = effective_message.reply_to_message
    victim = re_msg.from_user if re_msg else None
    reason = " ".join(context.args)

    cmd_prefix = effective_message.text[1]
    
    if cmd_prefix == "d":
        try:
            await chat.delete_messages([effective_message.id, re_msg.id])
        except:
            pass
    
    if user.is_bot:
        user = await anonymousAdmin(chat, effective_message)
        if not user:
            return
    
    if not re_msg:
        await effective_message.reply_text("I don't know who you are talking about! Reply the member whom you want to warn!\nE.g<code>/warn [reason]</code>")
        return
    
    if victim.id == context.bot.id:
        await effective_message.reply_text("Ohh, haha!! I can remove my own warn's 😝!!")
        return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, context.bot.id, user.id, victim.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await effective_message.reply_text("You aren't an admin in this chat!")
        return

    if chat_admins.is_victim_admin or chat_admins.is_victim_owner:
        await effective_message.reply_text("Rule no. 1 - Admins are always right!\nRule no. 2 - If admins are wrong then read rule no. 1 !!")
        return
    
    if not chat_admins.is_bot_admin:
        await effective_message.reply_text("I'm not an admin in this chat!")
        return
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await effective_message.reply_text("<blockquote><b>Error:</b> Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    warns = chat_data.get("warns") or {}
    victim_warns = warns.get(str(victim.id)) or {} # mongodb doesn't allow int doc key

    warn_count = victim_warns.get("count") or 0
    warn_count += 1
    warn_reasons = victim_warns.get("reasons") or []
    warn_reasons.append(reason if reason else "")

    update_data = {
        "victim_mention": victim.mention_html(), # needed for remove warns
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
        f"Watchout, {victim.mention_html()} !!\n"
        f"<b>You got warning's:</b> <code>{warn_count}/3</code>\n"
        f"<b>Reason (current warn):</b> <code>{reason if reason else 'Not Given'}</code>"
    )

    btn = BuildKeyboard.cbutton([{"Remove Warn's (Admin only)": f"admin_remove_warn_{victim.id}"}])
    await effective_message.reply_text(text, reply_markup=btn)

    if warn_count >= 3:
        try:
            await chat.restrict_member(victim.id, ChatPermissions.no_permissions())
        except Exception as e:
            await effective_message.reply_text(str(e))
            return
        
        reasons = ""
        for reason in victim_warns.get("reasons"):
            reasons += f"<blockquote>{reason}</blockquote>\n"
        
        await effective_message.reply_text(f"{victim.mention_html()} has been muted!\nWarning's: {reasons}")
