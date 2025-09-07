from time import time
from datetime import timedelta

from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.utils.decorators.pm_only import pm_only
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command("log", ["/", "!", "-", "."]))
@pm_only
@require_sudo
async def func_log(_, message: Message):
    await message.reply_document(open("sys/log.txt", "rb"), file_name=f"log [{timedelta(seconds=time())}].txt")
