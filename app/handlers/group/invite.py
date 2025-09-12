from datetime import datetime

from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command(["invite"], ["/", "!", "-", "."]))
@pm_error
async def func_invite(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    name = extract_cmd_args(message.text, message.command)
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("You aren't an admin in this chat!")
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_invite_users:
        return await message.reply_text("You don't have enough permission to invite members in this chat!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_invite_users:
        return await message.reply_text("I don't have enough permission to invite members in this chat!")
    
    try:
        expire_date = datetime.datetime.now() + datetime.timedelta(days=7)
        data = await bot.create_chat_invite_link(chat.id, name, expire_date)
    except Exception as e:
        return await message.reply_text(str(e))
    
    await message.reply_text(
        f"**Invite link:** `{data.invite_link}`\n"
        f"**Name:** `{data.name}`\n"
        f"**Expire date:** `{data.expire_date}`\n"
        f"**Member limit:** `{data.member_limit}`\n"
        f"**Created by:** `{data.creator}`"
    )
