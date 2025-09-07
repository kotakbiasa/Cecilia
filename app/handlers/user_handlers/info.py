from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import MessageOriginType

from app import bot
from app.helpers import BuildKeyboard

@bot.on_message(filters.command("info", ["/", "!", "-", "."]))
async def func_info(_, message: Message):
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message
    victim = user

    if re_msg:
        forward_origin = re_msg.forward_origin
        from_user = re_msg.from_user
    
        if forward_origin and forward_origin.type == MessageOriginType.USER:
            victim = forward_origin.sender_user
        
        if from_user and not forward_origin:
            victim = from_user
        
        if not victim:
            await message.reply_text(f"**• Full name:** `{forward_origin.sender_user_name}`\n<i>Replied user account is hidden!</i>")
            return
    
    victim_pfp = None
    async for photo in bot.get_chat_photos(victim.id, 1):
        victim_pfp = photo.file_id # the high quality photo file_id
    
    text = (
        f"**• Full name:** `{victim.full_name}`\n"
        f"**  » First name:** `{victim.first_name}`\n"
        f"**  » Last name:** `{victim.last_name}`\n"
        f"**• Mention:** {victim.mention.HTML}\n"
        f"**• Username:** {victim.name if victim.username else ''}\n"
        f"**• ID:** `{victim.id}`\n"
        f"**• Lang:** `{victim.language_code}`\n"
        f"**• Is bot:** `{'Yes' if victim.is_bot else 'No'}`\n"
        f"**• Is premium:** `{'Yes' if victim.is_premium else 'No'}`"
    )

    btn = BuildKeyboard.ubutton([{"User Profile": f"tg://user?id={victim.id}"}]) if victim.username else None

    if victim_pfp:
        await message.reply_photo(victim_pfp, text, reply_markup=btn)
    else:
        await message.reply_text(text, reply_markup=btn)
