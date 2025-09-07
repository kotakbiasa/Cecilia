from time import time

from pyrogram import filters
from pyrogram.types import Message

from app import bot
from app.helpers.args_extractor import extract_cmd_args
from app.modules import llm

@bot.on_message(filters.command("gpt", ["/", "!", "-", "."]))
async def func_gpt(_, message: Message):
    user = message.from_user or message.sender_chat
    prompt = extract_cmd_args(message.txt, message.command)

    if not prompt:
        await message.reply_text(f"Use `/{message.command[0]} prompt`\nE.g. `/{message.command[0]} what is relativity? explain in simple and short way.`")
        return
    
    sent_message = await message.reply_text("💭 Generating...")
    
    start_time = time()
    response = await llm.text_gen(prompt)
    response_time = int(time() - start_time)

    if response:
        text = (
            f"<blockquote expandable>{user.mention.HTML}: {prompt}</blockquote>\n"
            f"<blockquote expandable>**{bot.me.first_name}:** {response}</blockquote>\n"
            f"**Process time:** `{response_time}s`\n"
            f"**UserID:** `{user.id}`"
        )
    else:
        text = "Oops! Something went wrong!"
    
    await sent_message.edit_text(text)
