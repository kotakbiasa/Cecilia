from telegram import Update
from telegram.ext import ContextTypes
from app import TTS_LANG_CODES_URL
from app.helpers import BuildKeyboard
from app.modules.gtts import text_to_speech

async def func_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    effective_message = update.effective_message
    re_msg = effective_message.reply_to_message
    lang_code = " ".join(context.args) or "en"

    if not re_msg:
        btn = BuildKeyboard.ubutton([{"Language code's": TTS_LANG_CODES_URL}])
        await effective_message.reply_text("Reply any text to convert it into a voice message! E.g. Reply any message with <code>/tts en</code> to get english accent voice.", reply_markup=btn)
        return
    
    sent_message = await effective_message.reply_text("Processing...")

    response = text_to_speech(re_msg.text or re_msg.caption, lang_code)
    if not response:
        await sent_message.edit_text("Oops! Something went wrong!")
        return
    
    file_name = f"Voice {re_msg.id} [ {lang_code} ].mp3"

    await sent_message.delete()
    await effective_message.reply_audio(response, title=file_name, filename=file_name)
