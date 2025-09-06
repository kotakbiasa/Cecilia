from telegram import Update
from telegram.ext import ContextTypes

from app.utils.decorators.pm_error import pm_error
from app.utils.database import DBConstants, MemoryDB, MongoDB, database_search
from app.helpers import BuildKeyboard
from ..auxiliary.chat_admins import ChatAdmins
from ..auxiliary.anonymous_admin import anonymousAdmin

@pm_error
async def func_filter(_, message: Message):
    chat = message.chat
    user = message.from_user
    message = update.message
    re_msg = message.reply_to_message
    value = re_msg.text_html or re_msg.caption if re_msg else None
    keyword = extract_cmd_args(message.text, message.command).lower()
    
    if user.is_bot:
        user = await anonymousAdmin(chat, message)
        if not user:
            return
    
    chat_admins = ChatAdmins()
    await chat_admins.fetch_admins(chat, user_id=user.id)
    
    if not (chat_admins.is_user_admin or chat_admins.is_user_owner):
        await message.reply_text("You aren't an admin in this chat!")
        return
    
    if chat_admins.is_user_admin and not chat_admins.is_user_admin.can_change_info:
        await message.reply_text("You don't have enough permission to manage this chat!")
        return
    
    if not value or not keyword:
        data = {
            "user_id": user.id,
            "chat_id": chat.id,
            "message_id": message.id
        }

        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, data)

        text = (
            "To set filters for this chat follow the instruction below...\n"
            "<blockquote>Reply the message with /filter which one you want to set as value for your keyword!</blockquote>"
            "Example: `/filter hi` send this by replying any message! suppose the message is `Hi, How are you!`\n"
            "Next time if you say `Hi` in chat, the bot will reply with `Hi, How are you!`\n\n"
            "<i>**Note:** Use comma for adding multiple filter. eg. `/filter hi, bye`</i>\n\n"
            "<i>Ques: How to remove a filter?\n Ans: /remove for instruction...</i>\n\n"
            "**<u>Text formatting</u>**\n"
            "`{first}` first name\n"
            "`{last}` last name\n"
            "`{fullname}` fullname\n"
            "`{username}` username\n"
            "`{mention}` mention\n"
            "`{id}` id\n"
            "`{chatname}` chat title\n"
        )

        btn = BuildKeyboard.cbutton([{"Close": "misc_close"}])
        await message.reply_text(text, reply_markup=btn)
        return

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
        return
    
    filters = chat_data.get("filters")

    modified_keyword = keyword.split(",")
    keywords = []
    for i in modified_keyword:
        keywords.append(i.strip())

    if not filters:
        data = {}
        for keyword in keywords:
            data.update({keyword: value})
        MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"filters": data})
    
    else:
        for keyword in keywords:
            filters[keyword] = value
        MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"filters": filters})
    
    chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
    MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)
    msg_keywords = ", ".join(keywords)
    
    await message.reply_text(f"{msg_keywords} filters added!")
