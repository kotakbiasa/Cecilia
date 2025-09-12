from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from app import bot, config, logger
from app.helpers import BuildKeyboard
from app.utils.database import MemoryDB, DBConstants
from app.utils.decorators.pm_only import pm_only

@bot.on_message(filters.command("support", ["/", "!", "-", "."]))
@pm_only
async def init_support_conv(_, message: Message):
    await message.reply_text(
        "Hey, please send your request/report in one message.\n"
        "• /cancel to cancel conversation.\n\n"
        "<blockquote>**Note:** Request/Report should be related to this bot. And we don't provide any support for ban, mute or other things related to groups managed by this bot.</blockquote>"
    )

    MemoryDB.insert(DBConstants.DATA_CENTER, message.from_user.id, {"support_status": 1})


async def support_state_one(_, message: Message):
    user = message.from_user or message.sender_chat

    try:
        text = (
            f"Name: {user.mention}\n"
            f"UserID: `{user.id}`\n"
            f"Message: {message.text.html}\n\n"
            "<i>Reply to this message to continue conversation! or use /send</i>\n"
            f"<tg-spoiler>#uid{hex(user.id).upper()}</tg-spoiler>"
        )

        btn = InlineKeyboardMarkup([[InlineKeyboardButton("User Profile", user_id=victim.id)]]) if victim.username else None
        btn = BuildKeyboard.ubutton([{"User Profile": f"tg://user?id={user.id}"}]) if user.username else None
        await bot.send_message(config.owner_id, text, reply_markup=btn)
        # confirm message
        text = "Report has been submitted. Support team will contact you as soon as possible."
    except Exception as e:
        logger.error(e)
        text = "Oops, Something went wrong. Please try again."

    await message.reply_text(text)
    MemoryDB.insert(DBConstants.DATA_CENTER, message.from_user.id, {"support_status": 0})


@bot.on_message(filters.command("cancel", ["/", "!", "-", "."]))
@pm_only
async def cancel_support_conv(_, message: Message):
    user_data = MemoryDB.data_center.get(message.from_user.id) or {}
    support_status = user_data.get("support_status")

    if not support_status:
        text = "There is no active reporting conversation at the moment. /support to report/get support!"
    else:
        text = "Reporting has been cancelled."
        # Cancel Reporting
        MemoryDB.insert(DBConstants.DATA_CENTER, message.from_user.id, {"support_status": 0})

    await message.reply_text(text)
