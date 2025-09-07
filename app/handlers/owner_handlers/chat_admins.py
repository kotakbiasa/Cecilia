from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.utils.decorators.pm_only import pm_only
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command("cadmins", ["/", "!", "-", "."]))
@pm_only
@require_sudo
async def func_cadmins(_, message: Message):
    chat_id = extract_cmd_args(message.text, message.command) # chatID or username

    if not chat_id:
        await message.reply_text(f"`/{message.command[0]} ChatID or Username` to get specified chat admin list.\n<i>Note: only works if this bot is in that chat!</i>")
        return
    
    sent_message = await message.reply_text("Please wait...")
    owner_storage = "**Owner:**\n"
    admins_storage = ""

    try:
        async for admin in message.chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS):
            formatted_msg = f"• {admin.user.mention.HTML} - <i>{admin.custom_title}</i>\n"

            if admin.status in [ChatMemberStatus.OWNER]:
                owner_storage += formatted_msg
            elif not admin.user.is_bot:
                admins_storage += formatted_msg
    except Exception as e:
        await sent_message.edit_text(str(e))
        return
    
    if admins_storage: admins_storage = f"\n**Admin's:**\n{admins_storage}"

    await sent_message.edit_text(
        f"Admins of `{chat_id}`\n\n"
        f"{owner_storage}{admins_storage}"
    )
