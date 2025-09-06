import os
from time import time
from asyncio import sleep

from pyrogram import Client, filters
from pyrogram.types import Message

from app import bot, logger
from app.helpers.args_extractor import extract_cmd_args
from app.helpers.progress_updater import progress_updater
from app.modules.utils import UTILITY

@bot.on_message(filters.command(["unzip", "uz"], ["/", "!", "-", "."]))
async def func_unzip(_: Client, message: Message):
    re_msg = message.reply_to_message
    password = extract_cmd_args(message.text, message.command)

    if not re_msg or not re_msg.document:
        await message.edit_text(f"Reply any `.zip` file to extract the file. E.g. `/{message.command[0]} password (if needed)`")
        return
    
    if not re_msg.document.file_name.endswith(".zip"):
        await message.edit_text("Replied file isn't a `.zip` file!")
        return
    
    await message.edit_text("Please wait...")
    await message.pin(both_sides=True)

    startTime = time()
    zipFile = await re_msg.download(re_msg.document.file_name, progress=progress_updater, progress_args=[message, "Downloading...", startTime])
    if not zipFile:
        await message.edit_text("Unable to download!")
        return
    
    # Unzipping
    await message.edit_text("Unziping...")
    response = UTILITY.unzipFile(zipFile, password)

    # Remove Zip file
    try:
        os.remove(zipFile)
    except Exception as e:
        logger.error(e)
    
    # After Response
    if not isinstance(response, list):
        await message.edit_text(f"Error: {response}")
        return
    
    # File path list
    counter, uploaded, uploadfailed= 0, 0, ""
    startTime = time()
    for i in response:
        try:
            counter += 1
            is_uploaded = None
            percent = counter * 100/len(response)
            
            text = (
                f"Uploading...\n"
                f"**File:** `{i}`\n"
                f"**Total Percent:** `{UTILITY.createProgressBar(int(percent))}` `{percent:.2f}%`"
            )

            try:
                is_uploaded = await message.reply_photo(i, progress=progress_updater, progress_args=[message, text, startTime])
            except:
                try:
                    is_uploaded = await message.reply_video(i, width=1920, height=1080, progress=progress_updater, progress_args=[message, text, startTime])
                except:
                    is_uploaded = await message.reply_document(i, progress=progress_updater, progress_args=[message, text, startTime])
            
            if is_uploaded: uploaded += 1
        except Exception as e:
            uploadfailed += f"- {e}: `{i}`\n"
        
        await sleep(0.5)

        try:
            os.remove(i)
        except Exception as e:
            logger.error(e)
    
    await message.reply_text(f"Upload Completed! ({uploaded}/{len(response)})\n{uploadfailed}", reply_to_message_id=message.id)
