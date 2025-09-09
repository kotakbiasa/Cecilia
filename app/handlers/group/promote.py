from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["promote", "spromote"], ["/", "!", "-", "."]))
@pm_error
async def func_promote(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    username_admintitle = extract_cmd_args(message.text, message.command)
    re_msg = message.reply_to_message

    is_silent = await GroupHelper.cmd_prefix_handler(chat, message, re_msg)
    victim, admintitle = await GroupHelper.victim_reason_extractor(message, re_msg, username_admintitle)
    if victim is False:
        return
    
    if not victim:
        return await message.reply_text(
            "I don't know who you are talking about! Mention or Reply the member whom you want to ban!\n"
            f"E.g`/{message.command[0]} @username AdminTitle`"
        )
    
    if victim.id == bot.me.id:
        return await message.reply_text("I wish I could promote myself!")
    
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
        return await message.reply_text(f"{victim.mention} is already an admin of this chat!")
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_promote_members:
        return await message.reply_text("You don't have enough permission to promote chat members!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_promote_members:
        return await message.reply_text("I don't have enough permission to promote chat members!")
    
    try:
        await chat.promote_member(victim.id)
        if admintitle:
            await bot.set_administrator_title(chat.id, victim.id, admintitle)
    except Exception as e:
        return await message.reply_text(str(e))
    
    if not is_silent:
        await message.reply_text(f"{victim.mention} has been promoted." + (f"\nTitle: {admintitle}" if admintitle else ""))
