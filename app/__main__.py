import os
import asyncio
import aiohttp
import traceback
import importlib

from pyrogram import idle
from pyrogram.types import BotCommand, BotCommandScope, BotCommandScopeAllPrivateChats, BotCommandScopeAllChatAdministrators

from . import bot, logger, config, DEFAULT_ERROR_CHANNEL_ID, RUN_SERVER
from .utils.alive import alive
from .utils.update_db import update_database
from .modules import telegraph
from .utils.database import MemoryDB


async def post_init():
    # initializing telegraph
    # await telegraph.initialize()

    # bot pvt commands
    bot_pvt_commands = [
        BotCommand("start", "Introducing..."),
        BotCommand("help", "Bots help section..."),
        BotCommand("settings", "Chat settings..."),
        BotCommand("support", "Get Support or Report any bug related to bot...")
    ]

    # bot cadmin commands
    bot_cadmin_commands = [
        BotCommand("settings", "Chat settings...")
    ]
    
    try:
        # bot commands only for PRIVATE chats
        await bot.set_bot_commands(bot_pvt_commands, BotCommandScope(BotCommandScopeAllPrivateChats))
        # bot commands only for Chat admins
        await bot.set_bot_commands(bot_cadmin_commands, BotCommandScope(BotCommandScopeAllChatAdministrators))
    except Exception as e:
        logger.error(e)

    # Send alive message to bot owner
    try:
        await bot.send_message(config.owner_id, "<blockquote>**Bot Started!**</blockquote>")
    except Exception as e:
        logger.error(e)
    
    logger.info("Bot Started...")


async def server_alive():
    # executing after updating database so getting data from memory...
    if not RUN_SERVER:
        return
    
    server_url = MemoryDB.bot_data.get("server_url")
    if not server_url:
        logger.warning("'Server URL' wasn't found. Bot may fall asleep if deployed on Render (free instance)")
        return
    
    while True:
        # everytime check if there is new server_url
        server_url = MemoryDB.bot_data.get("server_url")
        if not server_url:
            return
        if server_url[0:4] != "http":
            server_url = f"http://{server_url}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(server_url) as response:
                    if not response.ok:
                        logger.warning(f"{server_url} is down or unreachable. ❌ - code - {response.status}")
        except Exception as e:
            logger.error(f"{server_url} > {e}")
        await asyncio.sleep(180) # 3 min


# async def default_error_handler(_, message: Message):
#     logger.error(context.error)
#     auto_del_message = False

#     if isinstance(context.error, (Conflict, NetworkError, TimedOut)):
#         text = f"<blockquote>An error occured</blockquote>\n\n`{context.error}`"
#         auto_del_message = True
    
#     else:
#         error_text = "".join(traceback.format_exception(type(context.error), context.error, context.error.__traceback__))
#         # Remove excessive path details for readability
#         error_text = "\n".join(line for line in error_text.split("\n") if "site-packages" not in line)
#         # telegram message limit ?
#         error_text = error_text[-2000:]

#         text = (
#             "<blockquote>An error occured</blockquote>\n\n"

#             f"**• Type:** `{type(context.error).__name__}`\n"
#             f"**• Message:** `{str(context.error)}`\n"
#             "**• Traceback:**\n\n"
#             f"<pre>{error_text}</pre>"
#         )
    
#     if DEFAULT_ERROR_CHANNEL_ID:
#         try:
#             sent_message = await context.bot.send_message(DEFAULT_ERROR_CHANNEL_ID, text)
#             if auto_del_message:
#                 await asyncio.sleep(60)
#                 await sent_message.delete()
#             return
#         except BadRequest:
#             pass
#         except Exception as e:
#             logger.error(e)
#             return
#     # if not DEFAULT_ERROR_CHANNEL_ID or BadRequest
#     try:
#         await context.bot.send_message(config.owner_id, text)
#     except Exception as e:
#         logger.error(e)


def load_handlers():
    handlers_dir = "app/handlers"
    for root, dirs, files in os.walk(handlers_dir):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_"):
                rel_path = os.path.relpath(root, handlers_dir)
                if rel_path == ".":
                    module_path = f"app.handlers.{filename[:-3]}"
                else:
                    rel_module_path = rel_path.replace(os.sep, ".")
                    module_path = f"app.handlers.{rel_module_path}.{filename[:-3]}"
                __import__(module_path)


async def app_init():
    if RUN_SERVER:
        alive() # Server breathing
    # maintain the sequence
    update_database()
    await post_init()
    await server_alive()
    await idle()


async def main():
    try:
        load_handlers() # Need to load `load_handlers` before bot.run()
        await bot.start()
        await app_init()
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
