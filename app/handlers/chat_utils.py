from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.utils.database import DBConstants, database_search
from .group.auxiliary.chat_admins import ChatAdmins

@bot.on_message(filters.service)
async def func_del_service_msg(_, message: Message):
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", message.chat.id)
    if not chat_data:
        return
    
    service_messages = chat_data.get("service_messages") # boolean (delete service messages)
    if not service_messages:
        return
    
    try:
        await message.delete()
    except:
        pass


@bot.on_message(filters.new_chat_members)
async def func_new_chat_member(_, message: Message):
    chat = message.chat
    user = message.from_user or message.sender_chat

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return
    
    welcome_user = chat_data.get("welcome_user")
    welcome_photo = chat_data.get("welcome_photo") # related to new_chat_members
    custom_welcome_msg = chat_data.get("custom_welcome_msg") # related to new_chat_members
    antibot = chat_data.get("antibot") # related to new_chat_members
    
    victims = message.new_chat_members
    for victim in victims:
        # Antibot
        if victim.is_bot and antibot:
            chat_admins = ChatAdmins()
            await chat_admins.fetch_admins(chat, bot.me.id, user.id)

            if chat_admins.is_user_owner:
                return
            
            elif chat_admins.is_user_admin and (chat_admins.is_user_admin.privileges.can_invite_users or chat_admins.is_user_admin.privileges.can_promote_members):
                return
            
            if not chat_admins.is_bot_admin:
                await chat.send_message("Antibot Error: I'm not an admin in this chat!")
                return
            
            if not chat_admins.is_bot_admin.privileges.can_restrict_members:
                await chat.send_message("Antibot Error: I don't have enough permission to restrict chat members!")
                return
            
            try:
                await chat.unban_member(victim.id)
            except Exception as e:
                await chat.send_message(str(e))
                return
            
            await bot.send_message(chat.id, f"Antibot: {victim.mention.HTML} has been kicked from this chat!")
        
        # Greeting new chat member
        elif welcome_user:
            if custom_welcome_msg:
                formattings = {
                    "{first}": victim.first_name,
                    "{last}": victim.last_name or "",
                    "{fullname}": victim.full_name,
                    "{username}": victim.username,
                    "{mention}": victim.mention.HTML,
                    "{id}": victim.id,
                    "{chatname}": chat.title
                }

                for key, value in formattings.items():
                    custom_welcome_msg = custom_welcome_msg.replace(key, str(value))
                # needs to keep everything simple
                greeting_message = custom_welcome_msg
            
            else:
                greeting_message = f"Hi, {victim.mention.HTML}! Welcome to {chat.title}!"
            
            if welcome_photo:
                try:
                    await chat.send_photo(welcome_photo, greeting_message)
                    return
                except Exception as e:
                    await chat.send_message(str(e))
            
            await chat.send_message(greeting_message)


@bot.on_message(filters.left_chat_member)
async def func_left_chat_member(_, message: Message):
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", message.chat.id)
    if not chat_data:
        return
    
    farewell_user = chat_data.get("farewell_user")
    if farewell_user:
        await bot.send_message(message.chat.id, f"Nice to see you! {message.left_chat_member.mention.HTML} has left us!")
