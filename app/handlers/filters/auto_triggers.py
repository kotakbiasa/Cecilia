from telegram import Message, User, Chat

async def autoTriggers(message: Message, user: User, chat: Chat, filters: dict):
    """
    :param message: Message Class
    :param user: `message.from_user`
    :param chat: `message.chat`
    :param filters: chat filters (from chat database)
    """
    text = message.text or message.caption

    for keyword in filters:
        try:
            filtered_text = text.lower()
        except AttributeError:
            filtered_text = text
        
        if keyword.lower() in filtered_text:
            filtered_text = filters.get(keyword)

            formattings = {
                "{first}": user.first_name or user.title,
                "{last}": user.last_name or "",
                "{fullname}": user.full_name,
                "{username}": user.name,
                "{mention}": user.mention.HTML,
                "{id}": user.id,
                "{chatname}": chat.title
            }

            for key, value in formattings.items():
                filtered_text = filtered_text.replace(key, str(value))
            
            await message.reply_text(filtered_text)
