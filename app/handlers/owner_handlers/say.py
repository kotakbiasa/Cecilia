from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.utils.decorators.sudo_users import require_sudo

@bot.on_message(filters.command("say", ["/", "!", "-", "."]))
@require_sudo
async def func_say(_, message: Message):
    re_msg = message.reply_to_message
    speech = extract_cmd_args(message.text, message.command) # the sentence to say
    
    try:
        await message.delete()
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not speech:
        await message.reply_text(f"What should I say? Example: `/{message.command[0]} Hi`")
        return
    
    await message.reply_text(speech, reply_to_message_id=re_msg.id if re_msg else None)
