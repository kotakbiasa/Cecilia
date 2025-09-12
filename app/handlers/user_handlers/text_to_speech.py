from pyrogram import filters
from pyrogram.types import Message

from app import bot, TTS_LANG_CODES_URL
from app.helpers import BuildKeyboard
from app.helpers.args_extractor import extract_cmd_args
from app.modules.gtts import text_to_speech

@bot.on_message(filters.command("tts", ["/", "!", "-", "."]))
async def func_tts(_, message: Message):
    re_msg = message.reply_to_message
    lang_code = extract_cmd_args(message.text, message.command) or "en"

    if not re_msg:
        btn = BuildKeyboard.ubutton([{"Language code's": TTS_LANG_CODES_URL}])
        await message.reply_text(f"Reply any text to convert it into a voice message! E.g. Reply any message with `/{message.command[0]} en` to get english accent voice.", reply_markup=btn)
        return
    
    sent_message = await message.reply_text("Processing...")

    response = text_to_speech(re_msg.text or re_msg.caption, lang_code)
    if not response:
        await sent_message.edit_text("Oops! Something went wrong!")
        return
    
    file_name = f"Voice {re_msg.id} [ {lang_code} ].mp3"

    await sent_message.delete()
    await message.reply_audio(response, title=file_name)
