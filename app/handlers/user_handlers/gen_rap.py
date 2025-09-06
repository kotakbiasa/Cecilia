from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules.psndl_module import PSNDL

@bot.on_message(filters.command("rap", ["/", "!", "-", "."]))
async def func_rap(_, message: Message):
    hex_data = extract_cmd_args(message.txt, message.command)

    if not hex_data:
        await message.reply_text(f"Use `/{message.command[0]} rapData (hex)`\nE.g. `/{message.command[0]} D78710F4C0979FAD9CDB40C612C94F60`\n<blockquote>**Note:** You will get the rap data after searching package using /psndl command.</blockquote>")
        return

    result = await PSNDL.gen_rap(hex_data)
    response = {
        404: "Error: fetching database!",
        500: "Package RAP wasn't found! Check HEX data again!",
        None: "Oops! Something went wrong!"
    }

    if type(result) is not dict and result in response:
        await message.reply_text(response[result])
        return

    caption = (
        f"**• ID:** `{result['packageData'].get('id')}`\n"
        f"**• Name:** `{result['packageData'].get('name')}`\n"
        f"**• Type:** `{result['packageData'].get('type')}`\n"
        f"**• Region:** `{result['packageData'].get('region')}`\n"
    )

    await message.reply_document(result["rapBytes"], caption)
