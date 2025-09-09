from pyrogram import filters
from pyrogram.types import Message, ChatJoinRequest

from app import bot
from app.helpers.group_helper import GroupHelper
from app.utils.database import DBConstants, database_search

@bot.on_message(filters.service)
async def filter_service_message(_, message: Message):
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


@bot.on_chat_join_request()
async def chat_join_request(_, join_req: ChatJoinRequest):
    chat = join_req.chat

    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", chat.id)
    if not chat_data:
        return
    
    chat_join_req = chat_data.get("chat_join_req")
    if not chat_join_req:
        return
    
    try:
        if chat_join_req == "approve":
            await join_req.approve()
        
        elif chat_join_req == "decline":
            await join_req.decline()
    except Exception as e:
        await chat.send_message(str(e))


@bot.on_message(filters.new_chat_members)
async def new_chat_members(_, message: Message):
    chat = message.chat
    user = message.from_user

    # NEED TO WORK ON THIS LATER (MAYBE IT COULD BE GROUP / CHANNEL ) ??
    if not user:
        return

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
            # Getting Admin roles
            admin_roles = await GroupHelper.get_admin_roles(chat, user.id)

            # Permission Checking...
            if admin_roles["user_owner"]:
                return
            
            elif admin_roles["user_admin"] and (admin_roles["user_admin"].privileges.can_invite_users or admin_roles["user_admin"].privileges.can_promote_members):
                return
            
            if not admin_roles["bot_admin"]:
                return await chat.send_message("Antibot Error: I'm not an admin in this chat!")
            
            if not admin_roles["bot_admin"].privileges.can_restrict_members:
                return await chat.send_message("Antibot Error: I don't have enough permission to restrict chat members!")
            
            try:
                await chat.unban_member(victim.id)
            except Exception as e:
                return await chat.send_message(str(e))
            
            await bot.send_message(chat.id, f"Antibot: {victim.mention} has been kicked from this chat!")
        
        # Greeting new chat member
        elif welcome_user:
            if custom_welcome_msg:
                formattings = {
                    "{first}": victim.first_name,
                    "{last}": victim.last_name or "",
                    "{fullname}": victim.full_name,
                    "{username}": victim.username,
                    "{mention}": victim.mention,
                    "{id}": victim.id,
                    "{chatname}": chat.title
                }

                for key, value in formattings.items():
                    custom_welcome_msg = custom_welcome_msg.replace(key, str(value))
                # needs to keep everything simple
                greeting_message = custom_welcome_msg
            
            else:
                greeting_message = f"Hi, {victim.mention}! Welcome to {chat.title}!"
            
            if welcome_photo:
                try:
                    await chat.send_photo(welcome_photo, greeting_message)
                    return
                except Exception as e:
                    await chat.send_message(str(e))
            
            await chat.send_message(greeting_message)


@bot.on_message(filters.left_chat_member)
async def left_chat_member(_, message: Message):
    chat_data = database_search(DBConstants.CHATS_DATA, "chat_id", message.chat.id)
    if not chat_data:
        return
    
    farewell_user = chat_data.get("farewell_user")
    if farewell_user:
        await bot.send_message(message.chat.id, f"Nice to see you! {message.left_chat_member.mention} has left us!")
