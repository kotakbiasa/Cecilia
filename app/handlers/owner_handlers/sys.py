import psutil
from time import time
from datetime import timedelta

from pyrogram import filters
from pyrogram.types import Message

from app import bot, BOT_UPTIME
from app.utils.database import MemoryDB
from app.modules.utils import UTILITY
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command("sys", ["/", "!", "-", "."]))
@require_sudo
async def func_sys(_, message: Message):
    # Loading Sticker ID
    sent_message = await message.reply_sticker("CAACAgUAAxkBAAEM96JovVa1TPS6ytZFdDe2W2XCNPV8vgADEQACtxIQVjlyOTplekF7NgQ")
    
    # Systen Uptime Calculating
    sys_uptime = timedelta(seconds=time() - psutil.boot_time())

    sys_days = sys_uptime.days
    sys_hours, remainder = divmod(sys_uptime.seconds, 3600)
    sys_minute = remainder / 60

    # Bot Uptime Calculating
    bot_uptime = timedelta(seconds=time() - BOT_UPTIME)
    
    bot_days = bot_uptime.days
    bot_hours, remainder = divmod(bot_uptime.seconds, 3600)
    bot_minute = remainder / 60

    # System info variables
    ramPercent = psutil.virtual_memory()[2]
    swapRamPercent = psutil.swap_memory()[3]
    diskUsagePercent = psutil.disk_usage('/')[3]

    # percent vizualize
    ramBar = UTILITY.createProgressBar(ramPercent)
    swapRamBar = UTILITY.createProgressBar(swapRamPercent)
    diskUsageBar = UTILITY.createProgressBar(diskUsagePercent)

    # pinging server
    server_url = MemoryDB.bot_data.get("server_url")
    server_ping = "~ infinite ~" # pre-determined
    if server_url:
        if not server_url.startswith("http"):
            server_url = f"http://{server_url}"
        
        server_ping = await UTILITY.pingServer(server_url)
    # Telegram Server Ping Check
    tg_server_ping = await UTILITY.pingServer("http://api.telegram.org/")
    
    sys_info = (
        "<blockquote>**🖥️ System information**</blockquote>\n\n"

        "**🔹 CPU**\n"
        f"**├ CPU:** `{psutil.cpu_count()}`\n"
        f"**├ CPU (Logical):** `{psutil.cpu_count(False)}`\n"
        f"**├ CPU freq Current:** `{psutil.cpu_freq()[0]/1024:.2f} Ghz`\n"
        f"**└ CPU freq Max:** `{psutil.cpu_freq()[2]/1024:.2f} Ghz`\n\n"

        "**🔸 RAM**\n"
        f"**├ RAM Total:** `{psutil.virtual_memory()[0]/(1024**3):.2f} GB`\n"
        f"**├ RAM Avail:** `{psutil.virtual_memory()[1]/(1024**3):.2f} GB`\n"
        f"**├ RAM Used:** `{psutil.virtual_memory()[3]/(1024**3):.2f} GB`\n"
        f"**├ RAM Free:** `{psutil.virtual_memory()[4]/(1024**3):.2f} GB`\n"
        f"**└ RAM Percent:** `{ramPercent} %`\n"
        f"**{ramBar}**\n\n"

        "**🔸 RAM (Swap)**\n"
        f"**├ RAM Total (Swap):** `{psutil.swap_memory()[0]/(1024**3):.2f} GB`\n"
        f"**├ RAM Used (Swap):** `{psutil.swap_memory()[1]/(1024**3):.2f} GB`\n"
        f"**├ RAM Free (Swap):** `{psutil.swap_memory()[2]/(1024**3):.2f} GB`\n"
        f"**└ RAM Percent (Swap):** `{swapRamPercent} %`\n"
        f"**{swapRamBar}**\n\n"

        "**📦 Storage**\n"
        f"**├ Total Partitions:** `{len(psutil.disk_partitions())}`\n"
        f"**├ Disk Usage Total:** `{psutil.disk_usage('/')[0]/(1024**3):.2f} GB`\n"
        f"**├ Disk Usage Used:** `{psutil.disk_usage('/')[1]/(1024**3):.2f} GB`\n"
        f"**├ Disk Usage Free:** `{psutil.disk_usage('/')[2]/(1024**3):.2f} GB`\n"
        f"**└ Disk Usage Percent:** `{diskUsagePercent} %`\n"
        f"**{diskUsageBar}**\n\n"

        "**⚜️ Uptime**\n"
        f"**├ System uptime:** `{int(sys_days)}d {int(sys_hours)}h {int(sys_minute)}m`\n"
        f"**└ Bot uptime:** `{int(bot_days)}d {int(bot_hours)}h {int(bot_minute)}m`\n\n"

        "**🌐 Server**\n"
        f"**├ Ping:** `{server_ping}`\n"
        f"**└ Telegram:** `{tg_server_ping}`"
    )

    await sent_message.delete()
    await message.reply_text(sys_info)
