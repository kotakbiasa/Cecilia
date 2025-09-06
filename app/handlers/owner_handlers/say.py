from telegram import Update
from telegram.ext import ContextTypes
from app.utils.decorators.sudo_users import require_sudo

@require_sudo
async def func_say(_, message: Message):
    message = update.message
    re_msg = message.reply_to_message
    speech = extract_cmd_args(message.text, message.command) # the sentence to say
    
    try:
        await message.delete()
    except Exception as e:
        await message.reply_text(str(e))
        return
    
    if not speech:
        await message.reply_text("What should I say? Example: `/say Hi`")
        return
    
    await message.reply_text(speech, reply_to_message_id=re_msg.message_id if re_msg else None)
