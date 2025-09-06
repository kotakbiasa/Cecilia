from time import time
from datetime import timedelta

from pyrogram.types import Message

from app import logger
from app.modules.utils import UTILITY

async def progress_updater(current, total, message: Message, extraText=None, startTime=None):
    """
    :param current: Bytes transferred so far
    :param total: Total bytes
    :param message: Message class
    :param extraText: info text (e.g. "Downloading" or "Uploading")
    :param startTime: Progress start timestamp (time.time())
    """
    try:
        if extraText is None:
            extraText = ""
        
        if startTime is None:
            startTime = time()
        
        percent = current * 100 / total
        elapsedTime = time() - startTime
        elapsed = timedelta(seconds=int(elapsedTime))

        # Speed in MB/s (bytes -> MB)
        currentSpeed = current / elapsedTime / (1024 * 1024)

        # Remaining time
        remainingSeconds = (total - current) / (currentSpeed * 1024 * 1024)
        remaining = timedelta(seconds=int(remainingSeconds))

        await message.edit_text(
            f"**{extraText}**\n"
            f"**Speed:** `{currentSpeed:.2f}MB/s`\n"
            f"**Elapsed:** `{elapsed}`\n"
            f"**ETA:** `{remaining}`\n"
            f"**Progress:** `{UTILITY.createProgressBar(int(percent))}` `{percent:.2f}%`"
        )
    except Exception as e:
        logger.error(e)
