from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.modules.utils import UTILITY
from app.utils.database import DBConstants, database_search, MemoryDB, MongoDB
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("whisper", ["/", "!", "-", "."]))
@pm_error
async def func_whisper(_, message: Message):
    # Priority: Replied user > @username
    chat = message.chat
    user = message.from_user or message.sender_chat
    secret_message = extract_cmd_args(message.text, message.command)
    re_msg = message.reply_to_message
    victim = None
    
    if not secret_message:
        return await message.reply_text(
            f"Use `/{message.command[0]} @username message`\n"
            f"or reply user by `/{message.command[0]} message`\n"
            f"E.g. `/{message.command[0]} @bishalqx980 I'm Just A Man Who's Good At What He Does. Programming.`"
        )
    
    try:
        await message.delete()
    except Exception as e:
        return await message.reply_text(str(e))
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    if re_msg:
        victim = re_msg.from_user
    else:
        victim, secret_message = await GroupHelper.victim_reason_extractor(message, re_msg, secret_message)
        if not victim is False:
            return
    
    if victim.is_bot:
        return await message.reply_text("Huh! Whisper isn't for bots!")
    
    if len(secret_message) > 180:
        return await message.reply_text("Whisper message is too long. (Max limit: 180 Characters)")
    
    sent_message = await message.reply_text("Processing...")

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    whispers = chat_data.get("whispers") or {}
    whisper_key = UTILITY.randomString()

    whispers.update({
        whisper_key: {
            "sender_user_id": user.id,
            "user_id": victim.id,
            "username": victim.username, # contains @ prefix
            "message": secret_message
        }
    })

    response = MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"whispers": whispers})
    if not response:
        return await sent_message.edit_text("Hmm, Something went wrong! Try again or report the issue!")
    
    MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"whispers": whispers})

    btn = BuildKeyboard.cbutton([{"See the message 💭": f"misc_whisper_{whisper_key}"}])
    await sent_message.edit_text(f"Hey, {victim.mention}. You got a whisper message from _{user.full_name}_.", reply_markup=btn)
