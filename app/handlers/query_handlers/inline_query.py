from uuid import uuid4
from base64 import b64decode, b64encode

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from app import logger
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB
from app.modules.utils import UTILITY

def inlineQueryMaker(title, message, reply_markup=None, description=None):
    """
    :param description: Type `same` if you want to keep the description same as message!
    """
    if not reply_markup:
        reply_markup = BuildKeyboard.cbutton([{"Try inline": "switch_to_inline"}])
    
    try:
        content = InlineQueryResultArticle(
            str(uuid4()),
            title=title,
            input_message_content=InputTextMessageContent(message),
            reply_markup=reply_markup,
            description=message if description == "same" else description
        )

        return content
    except Exception as e:
        logger.error(e)
        return


async def inline_query_handler(_, message: Message):
    query = update.inline_query
    user = query.from_user
    message = query.query
    results = []

    if not message:
        # instruction for user
        instruction_message = (
            "<blockquote>**Instructions: Available inline modes**</blockquote>\n\n"

            "**• Whisper: send someone a secret message in group chat! Similar command: /whisper**\n"
            f"   <i>- Example: `{context.bot.name} @bishalqx980 This is a secret message 😜`</i>\n\n"

            f"**• userinfo({user.full_name}): Get your userinfo! Similar command: /info**\n"
            f"   <i>- Example: `{context.bot.name} info`</i>\n\n"

            "**• Base64 Encode/Decode: Encode/Decode base64 in any chat! Similar commands: /encode | /decode**\n"
            f"   <i>- Example: `{context.bot.name} base64 data or normal text`</i>\n\n"

            f"**• Instructions: `{context.bot.name}` - to get this message!**\n\n"

            "**• Source code:** <a href='https://github.com/bishalqx980/tgbot'>GitHub</a>\n"
            "**• Report bug:** <a href='https://github.com/bishalqx980/tgbot/issues'>Report</a>\n"
            "**• Developer:** <a href='https://t.me/bishalqx680/22'>bishalqx980</a>"
        )

        results.append(inlineQueryMaker("ℹ️ Instructions", instruction_message, description="Click to see instructions...!"))
        await query.answer(results)
        return
    
    # whisper option: if chat isn't private | This whisper system is temporary store message, use /whisper cmd for permanent message store
    if query.chat_type not in [ChatType.PRIVATE, ChatType.SENDER]:
        splitted_message = message.split()
        whisper_username = splitted_message[0]
        secret_message = " ".join(splitted_message[1:])
        process_whisper = True

        if not whisper_username.startswith("@"):
            process_whisper = False
            results.append(inlineQueryMaker(
                "😮‍💨 Whisper: Error ❌",
                f"`{whisper_username}` isn't a valid username! Check instructions... Example: `{context.bot.name} @username Your Secret message!`",
                description=f"{whisper_username}, isn't a valid username!"
            ))
        
        elif whisper_username.endswith("bot"):
            process_whisper = False
            results.append(inlineQueryMaker(
                "😮‍💨 Whisper: Error ❌",
                "Whisper isn't for bots!",
                description="same"
            ))
        
        elif not secret_message:
            process_whisper = False
            results.append(inlineQueryMaker(
                "😮‍💨 Whisper: Error ❌",
                "What do you want to whisper? There is not whisper message!",
                description="same"
            ))
        
        elif len(secret_message) > 150:
            process_whisper = False
            results.append(inlineQueryMaker(
                "😮‍💨 Whisper: Error ❌",
                "Whisper message is too long. (Max limit: 150 Characters)",
                description="same"
            ))
        
        if process_whisper:
            data_center = MemoryDB.data_center.get("whisper_data") or {}
            whispers = data_center.get("whispers") or {}
            whisper_key = UTILITY.randomString()

            whispers.update({
                whisper_key: {
                    "sender_user_id": user.id,
                    "username": whisper_username, # contains @ prefix
                    "message": secret_message
                }
            })
            
            # Diffrent from normal /whisper cmd
            MemoryDB.insert(DBConstants.DATA_CENTER, "whisper_data", {"whispers": whispers})

            btn = BuildKeyboard.cbutton([
                {"See the message 💭": f"misc_tmp_whisper_{whisper_key}"},
                {"Try Yourself!": "switch_to_inline"}
            ])

            results.append(inlineQueryMaker(
                f"😮‍💨 Whisper: Send to {whisper_username}? ✅",
                f"Hey, {whisper_username}. You got a whisper message from {user.name}.",
                btn,
                f"Send whisper to {whisper_username}!"
            ))
    
    # need to be here after message update otherwise it shows cached info
    user_info = (
        "<blockquote>`» user.info()`</blockquote>\n\n"
        
        f"**• Full name:** `{user.full_name}`\n"
        f"**  » First name:** `{user.first_name}`\n"
        f"**  » Last name:** `{user.last_name}`\n"
        f"**• Mention:** {user.mention.HTML}\n"
        f"**• Username:** {user.name if user.username else ''}\n"
        f"**• ID:** `{user.id}`\n"
        f"**• Lang:** `{user.language_code}`\n"
        f"**• Is bot:** `{'Yes' if user.is_bot else 'No'}`\n"
        f"**• Is premium:** `{'Yes' if user.is_premium else 'No'}`"
    )

    results.append(inlineQueryMaker(f"❕ user.info({user.full_name})", user_info, description="See your info...!"))

    # base64 encode / decode
    try:
        b64_decode = b64decode(message).decode("utf-8")
        results.append(inlineQueryMaker("📦 Base64: Decode (base64 to text)", f"`{b64_decode}`", description=b64_decode)) if b64_decode else None
    except:
        pass

    try:
        b64_encode = b64encode(message.encode("utf-8")).decode("utf-8")
        results.append(inlineQueryMaker("📦 Base64: Encode (text to base64)", f"`{b64_encode}`", description=b64_encode)) if b64_encode else None
    except:
        pass

    # Final result
    if not results:
        return
    
    await query.answer(results)
