import asyncio

from pyrogram.types import Chat, Message
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus

from app import bot
from app.helpers import BuildKeyboard
from app.utils.database import DBConstants, MemoryDB

class GroupHelper:
    @staticmethod
    async def get_admin_roles(chat: Chat, user_id=None, victim_id=None):
        """
        :param chat: Chat class
        :param user_id: user.id
        :param victim_id: victim.id
        :returns roles: `dict` of admin roles (including bot)
        """
        roles = {
            "user_admin": None,
            "user_owner": None,
            "victim_admin": None,
            "victim_owner": None,
            "bot_admin": None
        }

        async for admin in chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS):
            uid, status = admin.user.id, admin.status

            if user_id and uid == user_id:
                if status == ChatMemberStatus.ADMINISTRATOR:
                    roles["user_admin"] = admin
                elif status == ChatMemberStatus.OWNER:
                    roles["user_owner"] = admin
            elif victim_id and uid == victim_id:
                if status == ChatMemberStatus.ADMINISTRATOR:
                    roles["victim_admin"] = admin
                elif status == ChatMemberStatus.OWNER:
                    roles["victim_owner"] = admin
            elif uid == bot.me.id:
                roles["bot_admin"] = admin
        
        return roles
    

    @staticmethod
    async def anonymousAdmin(chat: Chat, message: Message, timeout=10):
        """
        :param chat: Chat class
        :param message: Message class
        :param timeout: waiting time in sec
        :returns User: User class
        """
        anonymous_admin = None
        MemoryDB.insert(DBConstants.DATA_CENTER, chat.id, {"anonymous_admin": None})

        btn = BuildKeyboard.cbutton([{"Verify": "admin_anonymous_verify"}])
        sent_message = await message.reply_text("UwU, annoymous admin! Click on `Verify` to proceed next!", reply_markup=btn)
        
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
    
    
    @staticmethod
    async def cmd_prefix_handler(chat: Chat, message: Message, re_msg: Message = None) -> bool:
        """
        Detects `s` or `d` in command

        :param chat: Chat class
        :param message: Message class
        :param re_msg: Replied message (if available)
        """
        cmd_prefix = message.text[1]
        is_silent = False
        
        try:
            if cmd_prefix == "s":
                is_silent = True
                await message.delete()
            elif cmd_prefix == "d":
                await bot.delete_messages(chat.id, [message.id, re_msg.id])
        except:
            pass

        return is_silent
    

    @staticmethod
    async def victim_reason_extractor(message: Message, re_msg: Message, username_reason):
        """
        Extract Victim & Action reason from message

        :param message: Message class
        :param re_msg: Replied message
        :param username_reason: str cmd args
        """
        victim, reason = None, None

        # priority: replied user > @username
        if not re_msg and username_reason:
            try:
                # taking only username from username_reason
                username = username_reason.split()[0]
                reason = " ".join(username_reason.split()[1:])
                if message.entities[-1].user:
                    username = message.entities[-1].user.id # for mention without @username
                    reason = username_reason
                victim = await bot.get_users(username)
            except Exception as e:
                await message.reply_text(str(e))
                return False, False
        
        elif re_msg and not victim:
            victim = re_msg.from_user
            reason = username_reason
        
        return victim, reason
