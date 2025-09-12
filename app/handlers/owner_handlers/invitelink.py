from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.utils.decorators.pm_only import pm_only
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command("invitelink", ["/", "!", "-", "."]))
@pm_only
@require_sudo
async def func_invitelink(_, message: Message):
    chat_id = extract_cmd_args(message.text, message.command)
    
    if not chat_id:
        return await message.reply_text(f"`/{message.command[0]} ChatID` to get specified chat invite link.\n<i>Note: only works if this bot is in that chat and have enough permissions to get invite link!</i>")
    
    sent_message = await message.reply_text("Please wait...")

    try:
        res = await bot.create_chat_invite_link(chat_id, "GHOST")
    except Exception as e:
        return await sent_message.edit_text(str(e))
    
    await sent_message.edit_text(f"**Generated link:** {res.invite_link}")
