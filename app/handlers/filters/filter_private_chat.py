from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from telegram.error import Forbidden

from app import TL_LANG_CODES_URL, config
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, database_search

from .edit_database import edit_database
from .auto_translate import autoTranslate

async def filter_private_chat(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message
    re_msg = message.reply_to_message

    
    user_data = MemoryDB.data_center.get(message.from_user.id) or {}
    support_status = user_data.get("support_status")
    support_state_one()

    # Support Conversation
    if re_msg:
        message_text = re_msg.text or re_msg.caption

        if message_text and "#uid" in message_text:
            try:
                support_conv_uid = int(message_text.split("#uid")[1].strip(), 16) # base 16: hex
                text = ""
                btn = None
                # if user sending message to owner/support-team then add userinfo
                if user.id != config.owner_id:
                    text += (
                        f"Name: {user.mention.HTML}\n"
                        f"UserID: `{user.id}`\n"
                    )

                    btn = BuildKeyboard.ubutton([{"User Profile": f"tg://user?id={user.id}"}]) if user.username else None
                
                # Common text for owner & user
                text += (
                    f"Message: {message.text_html}\n\n"
                    "<i>Reply to this message to continue conversation!</i>\n"
                    f"<tg-spoiler>#uid{hex(user.id)}</tg-spoiler>"
                )

                await context.bot.send_message(support_conv_uid, text, reply_markup=btn)
                reaction = "👍"
            except Forbidden:
                reaction = "👎"
            except:
                reaction = "🤷‍♂"
            # Confirm that message is sent or not
            await message.set_reaction([ReactionTypeEmoji(reaction)])
    
    is_editing = edit_database(chat.id, user.id, message)
    if is_editing:
        return
    
    user_data = database_search(DBConstants.USERS_DATA, "user_id", user.id)
    if not user_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    # Echo message
    if user_data.get("echo"):
        await message.reply_text(message.text_html or message.caption_html)
    
    # Auto Translator
    auto_tr = user_data.get("auto_tr")
    chat_lang = user_data.get("lang")

    if auto_tr and not chat_lang:
        btn = BuildKeyboard.ubutton([{"Language code's": TL_LANG_CODES_URL}])
        await message.reply_text("Chat language code wasn't found! Use /settings to set chat language.", reply_markup=btn)
    
    elif auto_tr:
        await autoTranslate(message, user, chat_lang)
