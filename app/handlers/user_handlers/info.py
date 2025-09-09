from pyrogram import filters
from pyrogram.types import Chat, Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import MessageOriginType

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.args_extractor import extract_cmd_args

@bot.on_message(filters.command("info", ["/", "!", "-", "."]))
async def func_info(_, message: Message):
    user = message.from_user or message.sender_chat
    # priority: @username > replied user > myself (user)
    username = extract_cmd_args(message.text, message.command)
    re_msg = message.reply_to_message
    victim = None # it will be assigned as myself (user) if no @username or replied user
    victim_photo = None
    
    if username:
        try:
            if message.entities[-1].user:
                username = message.entities[-1].user.id # for mention without @username
            victim = await bot.get_users(username)
        except Exception as e:
            return await message.reply_text(str(e))
    
    if re_msg and not victim:
        forward_origin = re_msg.forward_origin
        from_user = re_msg.from_user
    
        if forward_origin and forward_origin.type == MessageOriginType.USER:
            victim = forward_origin.sender_user
        
        if from_user and not forward_origin:
            victim = from_user
        
        if not victim:
            return await message.reply_text(f"**• Full name:** `{forward_origin.sender_user_name}`\n<i>Replied user account is hidden!</i>")
    
    if not victim: victim = user

    if isinstance(user, Chat) and victim.id is user.id:
        return await message.reply_text("Anonymous admin detected!\nCan't fetch info due to user privacy!")
    
    try:
        async for photo in bot.get_chat_photos(victim.id, 1):
            victim_photo = photo.file_id # the high quality photo file_id
    except:
        return await message.reply_text(str(e))
    
    text = (
        f"**• Full name:** `{victim.full_name}`\n"
        f"**  » First name:** `{victim.first_name}`\n"
        f"**  » Last name:** `{victim.last_name}`\n"
        f"**• Mention:** {victim.mention}\n"
        f"**• Username:** {f'@{victim.username}' if victim.username else '-'}\n"
        f"**• User ID:** `{victim.id}`\n"
        f"**• DC ID:** `{victim.dc_id}`\n"
        f"**• Lang:** `{victim.language_code}`\n"
        f"**• Is bot:** `{'Yes' if victim.is_bot else 'No'}`\n"
        f"**• Is premium:** `{'Yes' if victim.is_premium else 'No'}`"
    )
    
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("User Profile", user_id=victim.id)]]) if victim.username else None

    if victim_photo:
        await message.reply_photo(victim_photo, caption=text, reply_markup=btn)
    else:
        await message.reply_text(text, reply_markup=btn)
