from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from app.modules.utils import Utils
from app.helpers import BuildKeyboard

@pm_error
async def func_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    effective_message = update.effective_message
    re_msg = effective_message.reply_to_message
    secret_message = " ".join(context.args)
    
    if not secret_message:
        await effective_message.reply_text("Use <code>/whisper @username message</code>\nor reply user by <code>/whisper message</code>\nE.g. <code>/whisper @bishalqx980 This is a secret message 😜</code>")
        return
    
    try:
        await effective_message.delete()
    except Exception as e:
        await effective_message.reply_text(str(e))
        return

    if re_msg and re_msg.from_user.is_bot:
        await effective_message.reply_text("Whisper isn't for bots!")
        return
    
    elif re_msg:
        whisper_username = re_msg.from_user.name if re_msg.from_user.username else None
        whisper_user_id = re_msg.from_user.id
        # secret_message is already taken as context args

    elif secret_message:
        splitted_message = secret_message.split()

        whisper_username = splitted_message[0]
        whisper_user_id = None
        secret_message = " ".join(splitted_message[1:])

        if not whisper_username.startswith("@"):
            await effective_message.reply_text(f"<code>{whisper_username}</code> isn't a valid username!\nTry to reply the user. /whisper for more details.")
            return
        
        if whisper_username.endswith("bot"):
            await effective_message.reply_text("Whisper isn't for bots!")
            return
    
    if len(secret_message) > 150:
        await effective_message.reply_text("Whisper message is too long. (Max limit: 150 Characters)")
        return
    
    sent_message = await effective_message.reply_text("Processing...")

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await effective_message.reply_text("<blockquote><b>Error:</b> Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    whispers = chat_data.get("whispers") or {}
    whisper_key = Utils.randomString()

    whispers.update({
        whisper_key: {
            "sender_user_id": user.id,
            "user_id": whisper_user_id,
            "username": whisper_username, # contains @ prefix
            "message": secret_message
        }
    })

    response = MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"whispers": whispers})
    if not response:
        await sent_message.edit_text("Hmm, Something went wrong! Try again or report the issue!")
        return
    
    MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, {"whispers": whispers})
    
    if re_msg and whisper_username is None:
        whisper_username = re_msg.from_user.mention_html()
    
    btn = BuildKeyboard.cbutton([{"See the message 💭": f"misc_whisper_{whisper_key}"}])
    await sent_message.edit_text(f"Hey, {whisper_username}. You got a whisper message from {user.name}.", reply_markup=btn)
