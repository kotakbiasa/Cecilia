from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from telegram.error import Forbidden
from app.utils.decorators.sudo_users import require_sudo
from app.utils.decorators.pm_only import pm_only

@pm_only
@require_sudo
async def func_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    re_msg = message.reply_to_message
    context_args = " ".join(context.args) # contains something if forward is true and contains victim_id >> /send f chat_id
    
    if not context_args or not re_msg:
        text = (
            "Use <code>/send ChatID</code> by replying a message!\n"
            "<code>/send f ChatID</code> to forward the replied message to ChatID!\n"
            "<blockquote expandable>Returns reaction on message\n"
            "- Sent: 👍\n"
            "- Forbidden: 👎\n"
            "- Something went wrong: 🤷‍♂ </blockquote>"
        )
        await message.reply_text(text)
        return
    
    forward_confirm = None
    victim_id = context_args
    reaction = "👍"

    splited_text = context_args.split()
    if len(splited_text) == 2:
        forward_confirm, victim_id = splited_text
    
    try:
        if forward_confirm:
            await context.bot.forward_message(victim_id, chat.id, re_msg.id)
        
        else:
            if str(victim_id).startswith("-100"):
                text = re_msg.text_html
                caption = re_msg.caption_html
            else:
                text = (
                    f"Message: {re_msg.text_html}\n\n"
                    "<i>Reply to this message to continue conversation!</i>\n"
                    f"<tg-spoiler>#uid{hex(user.id)}</tg-spoiler>"
                )
                caption = (
                    f"Message: {re_msg.caption_html}\n\n"
                    "<i>Reply to this message to continue conversation!</i>\n"
                    f"<tg-spoiler>#uid{hex(user.id)}</tg-spoiler>"
                )
            
            photo = re_msg.photo
            audio = re_msg.audio
            video = re_msg.video
            document = re_msg.document
            voice = re_msg.voice
            video_note = re_msg.video_note
            btn = re_msg.reply_markup

            if text:
                await context.bot.send_message(victim_id, text, reply_markup=btn)

            elif photo:
                await context.bot.send_photo(victim_id, photo[-1].file_id, caption, reply_markup=btn)

            elif audio:
                await context.bot.send_audio(victim_id, audio.file_id, title=audio.file_name, caption=caption, reply_markup=btn, filename=audio.file_name)

            elif video:
                await context.bot.send_video(victim_id, video.file_id, caption=caption, reply_markup=btn)

            elif document:
                await context.bot.send_document(victim_id, document.file_id, caption, reply_markup=btn, filename=document.file_name)
            
            elif voice:
                await context.bot.send_voice(victim_id, voice.file_id, caption=caption, reply_markup=btn)
            
            elif video_note:
                await context.bot.send_video_note(victim_id, video_note.file_id, reply_markup=btn)
            
            else:
                await message.reply_text("Replied content isn't added yet. Stay tuned for future update.")
                return
            
    except Forbidden:
        reaction = "👎"
    except:
        reaction = "🤷‍♂"

    await message.set_reaction([ReactionTypeEmoji(reaction)])
