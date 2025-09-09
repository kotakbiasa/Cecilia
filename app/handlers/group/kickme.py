from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("kickme", ["/", "!", "-", "."]))
@pm_error
async def func_kickme(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        # Instead of handling with func, bot will return bcz the user must be an admin anyway
        return await message.reply_text("I'm not going to kick you! You must be kidding!")
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    # Permission Checking...
    if (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("I'm not going to kick you! You must be kidding!")
    
    if not admin_roles["bot_admin"]:
        return await message.reply_text("I'm not an admin in this chat!")
    
    if not admin_roles["bot_admin"].privileges.can_restrict_members:
        return await message.reply_text("I don't have enough permission to kick members in this chat!")
    
    try:
        await chat.unban_member(user.id)
    except Exception as e:
        return await message.reply_text(str(e))
    
    await message.reply_text(f"Nice Choice! Get out of my sight!\n{user.mention} has chosen the easy way to out!")
