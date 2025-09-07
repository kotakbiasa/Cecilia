from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.psndl_module import PSNDL
from app.modules import telegraph

@bot.on_message(filters.command("psndl", ["/", "!", "-", "."]))
async def func_psndl(_, message: Message):
    user = message.from_user or message.sender_chat
    game_name = extract_cmd_args(message.text, message.command)

    if not game_name:
        await message.reply_text(
            f"Use `/{message.command[0]} game name`\n"
            f"E.g. `/{message.command[0]} red dead redemption`\n\n"
            "PSNDL Website: https://bishalqx980.github.io/psndl/"
        )
        return

    if len(message.text) < 4:
        await message.reply_text("Search keyword is too short...")
        return

    sent_message = await message.reply_text(f"Searching...")

    result = await PSNDL.search(game_name)
    response = {
        404: "Error: fetching database!",
        500: "Package wasn't found! Check package name again!",
        None: "Oops! Something went wrong!"
    }

    if type(result) is not dict and result in response:
        await sent_message.edit_text(response[result])
        return
    
    msg_list, counter = [], 0
    for game_type in result:
        collections = result.get(game_type)
        for game_id in collections:
            game_data = collections.get(game_id)
            counter += 1
            msg_list.append(
                f"**No. {counter}**\n"
                f"**• ID:** `{game_data.get('id')}`\n"
                f"**• Name:** `{game_data.get('name')}`\n"
                f"**• Type:** `{game_data.get('type')}`\n"
                f"**• Region:** `{game_data.get('region')}`\n"
                f"**• Link:** <a href='{game_data.get('link')}'>Download</a>\n"
                f"**• Rap:** `{game_data.get('rap_name')}`\n"
                f"**• Rap data »** `/rap {game_data.get('rap_data')}`\n"
                f"**• Desc:** `{game_data.get('desc')}`\n"
                f"**• Author:** `{game_data.get('author')}`\n\n"
                "<blockquote>**Note:** To get rap file send the rap data with command /rap</blockquote>\n\n"
            )
    
    msg, counter, links = "", 0, []
    for one_msg in msg_list:
        msg += one_msg.replace("\n", "<br>")
        counter += 1
        if len(msg_list) > 50 and counter == 50:
            link = await telegraph.paste(msg, f"{user.full_name} | {user.id}")
            links.append(link if link else "Missing link!")
            msg, counter = "", 0
    
    if counter != 0:
        link = await telegraph.paste(msg, f"{user.full_name} | {user.id}")
        links.append(link if link else "Missing link!")
        msg, counter = "", 0
    
    for link in links:
        msg += f"• {link}\n"

    await sent_message.edit_text(f"{msg}\nPSNDL Website: https://bishalqx980.github.io/psndl/")
