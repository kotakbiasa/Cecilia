from pyrogram import filters
from pyrogram.types import Chat, Message, ChatPermissions

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.utils.database import DBConstants, database_search, MemoryDB, MongoDB
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["warn", "dwarn"], ["/", "!", "-", "."]))
@pm_error
async def func_warn(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    username_reason = extract_cmd_args(message.text, message.command)
    re_msg = message.reply_to_message

    await GroupHelper.cmd_prefix_handler(chat, message, re_msg)
    victim, reason = await GroupHelper.victim_reason_extractor(message, re_msg, username_reason)
    if victim is False:
        return
    
    if not victim:
        return await message.reply_text(
            "I don't know who you are talking about! Mention or Reply the member whom you want to warn!\n"
            f"E.g`/{message.command[0]} @username reason`"
        )
    
    if victim.id == bot.me.id:
        return await message.reply_text("Ohh, haha!!")
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id, victim.id)
    
    # Permission Checking...
    if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("You aren't an admin in this chat!")

    if admin_roles["victim_admin"] or admin_roles["victim_owner"]:
        return await message.reply_text(
            "Rule no. 1 - Admins are always right!\n"
            "Rule no. 2 - If admins are wrong then read rule no. 1 !!"
        )
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    warns = chat_data.get("warns") or {}
    victim_warns = warns.get(str(victim.id)) or {} # mongodb doesn't allow int doc key

    warn_count = victim_warns.get("count") or 0
    warn_count += 1
    warn_reasons = victim_warns.get("reasons") or []
    warn_reasons.append(reason if reason else "")

    update_data = {
        "victim_mention": victim.mention, # needed for remove warns
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
        f"Watchout, {victim.mention} !!\n"
        f"**You got warning's:** `{warn_count}/3`\n"
        f"**Reason (current warn):** `{reason if reason else 'Not Given'}`"
    )

    btn = BuildKeyboard.cbutton([{"Remove Warn's (Admin only)": f"admin_remove_warn_{victim.id}"}])
    await message.reply_text(text, reply_markup=btn)

    if warn_count >= 3:
        try:
            await chat.restrict_member(
                victim.id,
                ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_send_polls=False
                )
            )
        except Exception as e:
            return await message.reply_text(str(e))
        
        reasons = ""
        for reason in victim_warns.get("reasons"):
            reasons += f"<blockquote>{reason}</blockquote>\n"
        
        await message.reply_text(f"{victim.mention} has been muted!\nWarning's: {reasons}")
