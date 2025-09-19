import json
import asyncio
import aiohttp
import traceback
import importlib

from telegram import Update, LinkPreviewOptions, BotCommand, BotCommandScope
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    ChosenInlineResultHandler,
    ConversationHandler,
    InlineQueryHandler,
    filters,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    Defaults,
)
from telegram.request import HTTPXRequest

from telegram.error import BadRequest, Conflict, NetworkError, TimedOut
from telegram.constants import ChatID, ParseMode

from bot.handlers.user_handlers.ytdl import ytdl_callback_handler
from bot.handlers.user_handlers.anime import anime_callback_handler

from . import COMMANDS_FILE_PATH, DEFAULT_ERROR_CHANNEL_ID, RUN_SERVER, bot, logger, config
from .utils.alive import alive
from .utils.update_db import update_database
from .modules import telegraph
from .utils.database import MemoryDB

from .handlers.conversation.support import (
    SUPPORT_STATES,
    init_support_conv,
    support_state_one,
    cancel_support_conv
)

from .handlers.filters import (
    filter_private_chat,
    filter_public_chat
)

from .handlers.core.help import func_help
from .handlers.group.chat_join_req import join_request_handler

from .handlers.query_handlers import (
    inline_query,
    query_admin_task,
    query_bot_settings,
    query_chat_settings,
    query_help_menu,
    query_misc,
    query_broadcast,
    query_db_editing
)

from .handlers.bot_chats_tracker import bot_chats_tracker
from .handlers.chat_status_update import chat_status_update


async def post_init():
    # initializing telegraph
    await telegraph.initialize()

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
        await bot.set_my_commands(bot_pvt_commands, BotCommandScope(BotCommandScope.ALL_PRIVATE_CHATS))
        # bot commands only for Chat admins
        await bot.set_my_commands(bot_cadmin_commands, BotCommandScope(BotCommandScope.ALL_CHAT_ADMINISTRATORS))
    except Exception as e:
        logger.error(e)

    # Send alive message to bot owner
    try:
        await bot.send_message(config.owner_id, "<blockquote><b>Bot Started!</b></blockquote>", parse_mode=ParseMode.HTML)
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
                # Using HEAD request to prevent downloading the body and avoid content-type errors.
                async with session.head(server_url, timeout=10, allow_redirects=False) as response: # type: aiohttp.ClientResponse
                    if not response.ok:
                        logger.warning(f"{server_url} is down or unreachable. ❌ - code - {response.status}")
        except Exception as e:
            logger.error(f"Server liveness check for {server_url} failed: {e}")
        await asyncio.sleep(180) # 3 min


async def default_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(context.error)
    auto_del_message = False

    if isinstance(context.error, (Conflict, NetworkError, TimedOut)):
        text = f"<blockquote>An error occured</blockquote>\n\n<code>{context.error}</code>"
        auto_del_message = True
    
    else:
        error_text = "".join(traceback.format_exception(type(context.error), context.error, context.error.__traceback__))
        # Remove excessive path details for readability
        error_text = "\n".join(line for line in error_text.split("\n") if "site-packages" not in line)
        # telegram message limit ?
        error_text = error_text[-2000:]

        text = (
            "<blockquote>An error occured</blockquote>\n\n"

            f"<b>• Type:</b> <code>{type(context.error).__name__}</code>\n"
            f"<b>• Message:</b> <code>{str(context.error)}</code>\n"
            "<b>• Traceback:</b>\n\n"
            f"<pre>{error_text}</pre>"
        )
    
    if DEFAULT_ERROR_CHANNEL_ID:
        try:
            sent_message = await context.bot.send_message(DEFAULT_ERROR_CHANNEL_ID, text)
            if auto_del_message:
                await asyncio.sleep(60)
                await sent_message.delete()
            return
        except BadRequest:
            pass
        except Exception as e:
            logger.error(e)
            return
    # if not DEFAULT_ERROR_CHANNEL_ID or BadRequest
    try:
        await context.bot.send_message(config.owner_id, text)
    except Exception as e:
        logger.error(e)


def load_handlers():
    handlers = []

    with open(COMMANDS_FILE_PATH, "r") as f:
        config = json.load(f)
    
    for handler_config in config["handlers"]:
        # Import the module
        module = importlib.import_module(handler_config["module"], __package__)
        # Get the function
        func = getattr(module, handler_config["function"])

        # Create handler for main command
        handlers.append(CommandHandler(handler_config["command"], func))
    
    return handlers


async def main():
    # Configure custom timeouts for the HTTP client to make it more resilient
    # to network fluctuations.
    httpx_request = HTTPXRequest(
        connect_timeout=10.0,  # Time to establish a connection (default: 5.0)
        read_timeout=20.0,     # Time to wait for a response (default: 5.0)
        write_timeout=20.0,    # Time to wait for a write operation (default: 5.0)
        pool_timeout=10.0,     # Time to wait for a connection from the pool (default: 5.0)
    )

    default_param = Defaults(
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
        block=False,
        allow_sending_without_reply=True
    )
    # Bot instance
    application = ApplicationBuilder().token(config.bot_token).defaults(default_param).request(httpx_request).build()

    # --- Logic from app_init() moved here ---
    if RUN_SERVER:
        alive()  # Starts Flask server in a thread
    update_database()  # Synchronous, run it before the loop
    # -----------------------------------------

    # Conversation handlers
    application.add_handler(
        ConversationHandler(
            [CommandHandler("support", init_support_conv)],
            {
                SUPPORT_STATES.STATE_ONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_state_one)]
            },
            [CommandHandler("cancel", cancel_support_conv)]
        )
    )

    # main handlers register
    main_handlers = load_handlers()
    # this need to register before main start handler
    main_handlers.insert(0, CommandHandler("start", func_help, filters.Regex("help")))
    
    application.add_handlers(main_handlers)
    
    # Chat Join Request Handler
    application.add_handler(ChatJoinRequestHandler(join_request_handler))

    # filter private chat
    application.add_handler(MessageHandler(
        # SERVICE_CHAT is Linked channel with Group
        ~ filters.User(ChatID.SERVICE_CHAT) & filters.ChatType.PRIVATE & (filters.TEXT | filters.CAPTION),
        filter_private_chat.filter_private_chat
    ))
    # filter public chat
    application.add_handler(MessageHandler(
        # SERVICE_CHAT is Linked channel with Group
        ~ filters.User(ChatID.SERVICE_CHAT) & filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION),
        filter_public_chat.filter_public_chat
    ))
    # filter Chat Status Updates
    application.add_handler(MessageHandler(filters.StatusUpdate.ALL, chat_status_update))

    # Bot chat tracker (PRIVATE: only if bot is blocked or unblocked; PIUBLIC: any)
    application.add_handler(ChatMemberHandler(bot_chats_tracker, ChatMemberHandler.MY_CHAT_MEMBER))

    # Inline Query Handler
    application.add_handler(InlineQueryHandler(inline_query.inline_query_handler))
    # Chosen Inline Result Handler for Gemini

    # Callback query handlers
    application.add_handlers([
        CallbackQueryHandler(query_help_menu.query_help_menu, "help_menu_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_bot_settings.query_bot_settings, "bsettings_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_chat_settings.query_chat_settings, "csettings_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_admin_task.query_groupManagement, "admin_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_misc.query_misc, "misc_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_broadcast.query_broadcast, "broadcast_[A-Za-z0-9]+"),
        CallbackQueryHandler(query_db_editing.query_db_editing, "database_[A-Za-z0-9]+")
    ])

    # Registering ytdl callback handler
    application.add_handler(CallbackQueryHandler(ytdl_callback_handler, pattern="^ytdl:"))

    # Registering anime callback handler
    application.add_handler(CallbackQueryHandler(anime_callback_handler, pattern="^anime:"))

    # Error handler
    application.add_error_handler(default_error_handler)

    # Run the bot and other async tasks concurrently
    async with application:
        await post_init()
        await application.start()
        # Start polling in the background
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
        # Run the server liveness check if enabled (this is a long-running task)
        if RUN_SERVER:
            await server_alive()


if __name__ == "__main__":
    asyncio.run(main())
