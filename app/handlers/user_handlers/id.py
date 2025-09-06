from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import MessageOriginType
from app import bot

@bot.on_message(filters.command("id", ["/", "!", "-", "."]))
async def func_id(_, message: Message):
    chat = message.chat
    user = message.from_user
    re_msg = message.reply_to_message
    victim = None

    if re_msg:
        forward_origin = re_msg.forward_origin
        from_user = re_msg.from_user

        if forward_origin:
            if forward_origin.type == MessageOriginType.USER:
                victim = forward_origin.sender_user
            elif forward_origin.type == MessageOriginType.CHANNEL:
                victim = forward_origin.chat
        elif from_user:
            victim = from_user
        
        if not victim:
            text = (
                f"• {user.full_name}\n"
                f"  » **ID:** `{user.id}`\n"
                f"• {forward_origin.sender_user_name}\n"
                f"  » **ID:** `Replied user account is hidden!`\n"
                f"• **ChatID:** `{chat.id}`"
            )
        else:
            text = (
                f"• {user.full_name}\n"
                f"  » **ID:** `{user.id}`\n"
                f"• {victim.full_name or victim.title}\n" # this title can cause error (title for channel)
                f"  » **ID:** `{victim.id}`\n"
                f"• **ChatID:** `{chat.id}`"
            )
    else:
        text = (
            f"• {user.full_name}\n"
            f"  » **ID:** `{user.id}`\n"
            f"• **ChatID:** `{chat.id}`"
        )
    
    await message.reply_text(text)
