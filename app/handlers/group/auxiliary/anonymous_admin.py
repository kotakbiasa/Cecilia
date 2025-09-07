import asyncio
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB

async def anonymousAdmin(chat, message, timeout=10):
    """
    :param chat: `message.chat`
    :param message: Message class
    :param timeout: waiting time in sec
    :returns User: User class
    """
    anonymous_admin = None
    MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"anonymous_admin": None})

    btn = BuildKeyboard.cbutton([{"Verify": "admin_anonymous_verify"}])
    sent_message = await message.reply_text(f"UwU, annoymous admin! Click on `Verify` to proceed next!", reply_markup=btn)

    for i in range(timeout):
        data_center = MemoryDB.data_center[chat.id]
        anonymous_admin = data_center.get("anonymous_admin")
        if anonymous_admin:
            break
        
        await asyncio.sleep(1)
    
    await sent_message.delete()
    if not anonymous_admin:
        try:
            await message.delete()
        except:
            pass
        
    return anonymous_admin
