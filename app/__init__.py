import os
import json
import shutil
from time import time

from pyrogram import Client, __version__ as __pyroversion__
from pyrogram.types import LinkPreviewOptions

from .utils.logger import setup_logging
from config import CONFIG

# constants
__version__ = json.load(open("version.json", "rb"))["__version__"] # major.minor.patch.commits
REQUIRED_DIRS = ["downloads", "sys"]
ORIGINAL_BOT_USERNAME = "MissCiri_bot"
ORIGINAL_BOT_ID = 6845693976
DEFAULT_ERROR_CHANNEL_ID = -1002675104487
BOT_UPTIME = time()
PSNDL_DATABASE_URL = "https://psndl.pages.dev/database.json"
TL_LANG_CODES_URL = "https://telegra.ph/Language-Code-12-24"
TTS_LANG_CODES_URL = "https://telegra.ph/Text-to-speech---language-codes-tts-01-23"
RUN_SERVER = False # switch to run flask server

# Creating Required Folder/Directories
try:
    for dir_name in REQUIRED_DIRS:
        if os.path.exists(dir_name):
            if dir_name != "sys": # Exception for sys dir (to keep client cache file on restart)
                shutil.rmtree(dir_name)
        os.makedirs(dir_name, exist_ok=True)
except Exception as e:
    print(e)
    exit()

# logger & .env config file
logger = setup_logging() # need to execute after creating Required folders
config = CONFIG()

if not config.validate():
    raise ValueError("Missing required configuration.")

# Bot Client
bot = Client(
    name=ORIGINAL_BOT_USERNAME,
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    workdir="sys",
    link_preview_options=LinkPreviewOptions(is_disabled=True)
)

logger.info(f"""
Developed by
 ______     __     ______     __  __     ______     __        
/\  == \   /\ \   /\  ___\   /\ \_\ \   /\  __ \   /\ \       
\ \  __<   \ \ \  \ \___  \  \ \  __ \  \ \  __ \  \ \ \____  
 \ \_____\  \ \_\  \/\_____\  \ \_\ \_\  \ \_\ \_\  \ \_____\ 
  \/_____/   \/_/   \/_____/   \/_/\/_/   \/_/\/_/   \/_____/ 
   
    Version: {__version__}
    Library: kurigram {__pyroversion__}
    GitHub: https://github.com/bishalqx980
""")
