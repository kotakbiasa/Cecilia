from pyrogram import filters
from pyrogram.types import Chat, Message

from app import bot
from app.helpers import BuildKeyboard
from app.helpers.group_helper import GroupHelper
from app.helpers.args_extractor import extract_cmd_args
from app.utils.database import DBConstants, database_search, MemoryDB, MongoDB
from app.utils.decorators.pm_error import pm_error

@bot.on_message(filters.command("trigger", ["/", "!", "-", "."]))
@pm_error
async def func_trigger(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat
    re_msg = message.reply_to_message
    value = re_msg.text.html or re_msg.caption.html if re_msg else None
    keyword = extract_cmd_args(message.text, message.command).lower()
    
    # Handle anonymous admin
    if isinstance(user, Chat) or user.is_bot:
        user = await GroupHelper.anonymousAdmin(chat, message)
        if not user:
            return
    
    # Getting Admin roles
    admin_roles = await GroupHelper.get_admin_roles(chat, user.id)
    
    # Permission Checking...
    if not (admin_roles["user_admin"] or admin_roles["user_owner"]):
        return await message.reply_text("You aren't an admin in this chat!")
    
    if admin_roles["user_admin"] and not admin_roles["user_admin"].privileges.can_change_info:
        return await message.reply_text("You don't have enough permission to manage this chat!")
    
    if not value or not keyword:
        data = {
            "user_id": user.id,
            "chat_id": chat.id,
            "message_id": message.id
        }

        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, data)

        btn = BuildKeyboard.cbutton([{"Close": "misc_close"}])

        # send a small video demo instead of long message and formatting button
        return await message.reply_text(
            "To set triggers for this chat follow the instruction below...\n"
            f"<blockquote>Reply the message with /{message.command[0]} which one you want to set as value for your keyword!</blockquote>"
            f"Example: `/{message.command[0]} hi` send this by replying any message! suppose the message is `Hi, How are you!`\n"
            "Next time if you say `Hi` in chat, the bot will reply with `Hi, How are you!`\n\n"
            f"<i>**Note:** Use comma for adding multiple filter. eg. `/{message.command[0]} hi, bye`</i>\n\n"
            "<i>Ques: How to remove a filter?\n Ans: /remove for instruction...</i>\n\n"
            "**<u>Text formatting</u>**\n"
            "`{first}` first name\n"
            "`{last}` last name\n"
            "`{fullname}` fullname\n"
            "`{username}` username\n"
            "`{mention}` mention\n"
            "`{id}` id\n"
            "`{chatname}` chat title\n",
            reply_markup=btn
        )
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    triggers = chat_data.get("triggers")

    modified_keyword = keyword.split(",")
    keywords = []
    for i in modified_keyword:
        keywords.append(i.strip())

    if not triggers:
        data = {}
        for keyword in keywords:
            data.update({keyword: value})
        MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"triggers": data})
    
    else:
        for keyword in keywords:
            triggers[keyword] = value
        MongoDB.update(DBConstants.CHATS_DATA, "chat_id", chat.id, {"triggers": triggers})
    
    chat_data = MongoDB.find_one(DBConstants.CHATS_DATA, "chat_id", chat.id)
    MemoryDB.insert(DBConstants.CHATS_DATA, chat.id, chat_data)
    
    await message.reply_text(f"{", ".join(keywords)} triggers added!")
