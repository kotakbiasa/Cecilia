from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from app import bot, TL_LANG_CODES_URL
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, database_search

from .edit_database import edit_database
from .auto_linkblocker import autoLinkBlocker
from .auto_translate import autoTranslate
from .auto_triggers import autoTriggers

@bot.on_message(filters.group & ~filters.regex(r"^[\/!\-.]"))
async def filter_public_chat(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    is_editing = edit_database(chat.id, user.id, message)
    if is_editing:
        return
    
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return await message.reply_text("<blockquote>**Error:** Chat isn't registered! Remove/Block me from this chat then add me again!</blockquote>")
    
    # Auto Link Blocker
    links_behave = chat_data.get("links_behave") # 3 values: delete; convert; None;
    filtered_text = None

    if links_behave:
        # check if user is admin or owner
        member_info = await chat.get_member(user.id)
        if member_info.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            link_rules = {"links_behave": links_behave, "allowed_links": chat_data.get("allowed_links")}
            is_forbidden = await autoLinkBlocker(message, user, link_rules)

            if is_forbidden:
                filtered_text = is_forbidden
    
    # Echo message
    if chat_data.get("echo") and not filtered_text:
        await message.reply_text(message.text.html or message.caption.html)
    
    # Auto Translator
    auto_tr = chat_data.get("auto_tr")
    chat_lang = chat_data.get("lang")

    if auto_tr and not chat_lang:
        btn = BuildKeyboard.ubutton([{"Language code's": TL_LANG_CODES_URL}])
        await message.reply_text("Chat language code wasn't found! Use /settings to set chat language.", reply_markup=btn)
    
    elif auto_tr and not filtered_text:
        await autoTranslate(message, user, chat_lang)
    
    # Auto Trigers
    triggers = chat_data.get("triggers")
    if triggers:
        await autoTriggers(message, user, chat, triggers)
