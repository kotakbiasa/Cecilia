import asyncio
from html import escape
import re
from uuid import uuid4
from base64 import b64decode, b64encode
from calendar import month_name

from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from bot import logger
from bot.helpers import BuildKeyboard
from bot.utils.database import DBConstants, MemoryDB
from bot.modules.utils import Utils
from bot.modules.anilist import search_anime, search_manga, search_character
from bot.handlers.query_handlers.message_builder import (
    build_anime_info_message,
    build_manga_info_message,
    build_character_info_message,
    inlineQueryMaker,
)

# --- Helper functions to build message content ---


# --- Sub-handlers for Inline Features ---

async def _handle_instructions(query: Update.inline_query, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan petunjuk penggunaan mode inline."""
    instruction_message = (
        "<blockquote><b>Petunjuk: Mode inline yang tersedia</b></blockquote>\n\n"
        "<b>• Cari:</b> Ketik untuk mencari Anime, Manga, atau Karakter.\n"
        f"   <i>- Contoh: <code>@{context.bot.name} Steins;Gate</code> atau <code>@{context.bot.name} @username Steins;Gate</code></i>\n\n"
        "<b>• Bisikan:</b> Kirim pesan rahasia di grup!\n"
        f"   <i>- Contoh: <code>@{context.bot.name} whisper @username Pesan rahasia ini 😜</code></i>\n\n"
        f"<b>• Info Pengguna:</b> Dapatkan info Anda!\n"
        f"   <i>- Contoh: <code>@{context.bot.name} info</code></i>\n\n"
        "<b>• Base64:</b> Encode/Decode base64 di obrolan manapun!\n"
        f"   <i>- Contoh: <code>@{context.bot.name} base64 data atau teks biasa</code></i>\n\n"
        "<b>• Gemini AI:</b> Tanyakan apa saja pada Gemini.\n"
        f"   <i>- Contoh: <code>@{context.bot.name} gpt apa itu cinta?</code></i>\n\n"
        "<b>• Kode Sumber:</b> <a href='https://github.com/kotakbiasa/Cecilia'>GitHub</a>\n"
    )
    results = [inlineQueryMaker("ℹ️ Petunjuk", instruction_message, description="Klik untuk melihat petunjuk...!")]
    await query.answer(results, cache_time=300)

async def _handle_user_info(query: Update.inline_query, user: Update.effective_user):
    """Menampilkan informasi pengguna yang meminta."""
    user_info = (
        "<blockquote><code>» user.info()</code></blockquote>\n\n"
        f"<b>• Nama lengkap:</b> <code>{user.full_name}</code>\n"
        f"<b>  » Nama depan:</b> <code>{user.first_name}</code>\n"
        f"<b>  » Nama belakang:</b> <code>{user.last_name}</code>\n"
        f"<b>• Mention:</b> {user.mention_html()}\n"
        f"<b>• Username:</b> {user.name if user.username else ''}\n"
        f"<b>• ID:</b> <code>{user.id}</code>\n"
        f"<b>• Bahasa:</b> <code>{user.language_code}</code>\n"
        f"<b>• Apakah bot:</b> <code>{'Ya' if user.is_bot else 'Tidak'}</code>\n"
        f"<b>• Apakah premium:</b> <code>{'Ya' if user.is_premium else 'Tidak'}</code>"
    )
    results = [inlineQueryMaker(f"❕ user.info({user.full_name})", user_info, description="Lihat info Anda...!")]
    await query.answer(results, cache_time=10)

async def _handle_base64(query: Update.inline_query, message: str):
    """Menangani encode dan decode Base64."""
    b64_query = message[7:]
    results = []
    if b64_query:
        try:
            b64_decode = b64decode(b64_query).decode("utf-8")
            results.append(inlineQueryMaker("📦 Base64: Decode", f"<code>{b64_decode}</code>", description=b64_decode))
        except Exception:
            pass
        try:
            b64_encode = b64encode(b64_query.encode("utf-8")).decode("utf-8")
            results.append(inlineQueryMaker("📦 Base64: Encode", f"<code>{b64_encode}</code>", description=b64_encode))
        except Exception:
            pass
    if results:
        await query.answer(results, cache_time=10)

async def _handle_gemini(query: Update.inline_query, message: str):
    """Meneruskan permintaan ke Gemini AI."""
    gpt_query = message[4:]
    if gpt_query:
        results = [
            InlineQueryResultArticle(
                id="gemini_ai_result",
                title="Tanya Gemini AI",
                input_message_content=InputTextMessageContent(
                    f"🤔 <b>Gemini:</b> {gpt_query}\n\n<i>Sedang berpikir...</i>"
                ),
                description=f"Tanyakan pada Gemini: {gpt_query}",
                thumbnail_url="https://i.imgur.com/K2unH4z.png"
            )
        ]
        await query.answer(results, cache_time=10)

async def _handle_whisper(query: Update.inline_query, user: Update.effective_user, message: str):
    """Membuat pesan bisikan."""
    splitted_message = message.split()
    if len(splitted_message) > 1:
        whisper_username = splitted_message[0]
        secret_message = " ".join(splitted_message[1:])
        
        data_center = MemoryDB.data_center.get("whisper_data") or {}
        whispers = data_center.get("whispers") or {}
        whisper_key = Utils.randomString()

        whispers[whisper_key] = {"sender_user_id": user.id, "username": whisper_username, "message": secret_message}
        MemoryDB.insert(DBConstants.DATA_CENTER, "whisper_data", {"whispers": whispers})

        btn = BuildKeyboard.cbutton([{"Lihat pesan 💭": f"misc_tmp_whisper_{whisper_key}"}, {"Coba Sendiri!": "switch_to_inline"}])
        results = [inlineQueryMaker(f"😮‍💨 Bisikan: Kirim ke {whisper_username}? ✅", f"Hey, {whisper_username}. Kamu dapat pesan bisikan dari {user.name}.", btn, f"Kirim bisikan ke {whisper_username}!")]
        await query.answer(results, cache_time=10)

async def _handle_anilist_search(query: Update.inline_query, message: str, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pencarian anime, manga, dan karakter."""
    # Pisahkan target user (jika ada) dari query pencarian
    target_user = None
    search_query = message
    if query.chat_type != ChatType.PRIVATE and message.startswith("@"):
        parts = message.split(maxsplit=1)
        if len(parts) > 1 and re.match(r"@[a-zA-Z0-9_]{5,}", parts[0]):
            target_user = parts[0]
            search_query = parts[1]

    results = []
    # Jalankan semua pencarian secara bersamaan
    anime_task = search_anime(search_query)
    manga_task = search_manga(search_query)
    character_task = search_character(search_query)

    anime_data, manga_data, char_data = await asyncio.gather(
        anime_task, manga_task, character_task
    )

    # Proses hasil anime
    if anime_data:
        message_content = await build_anime_info_message(anime_data, target_user, is_inline=True)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Lihat di Anilist", url=anime_data['siteUrl'])]])
        results.append(
            InlineQueryResultArticle(
                id=f"anime_{anime_data['id']}",
                title=f"Anime: {anime_data['title']['romaji']}",
                description=f"Format: {anime_data.get('format', 'N/A')} | Skor: {anime_data.get('averageScore') / 10 if anime_data.get('averageScore') else 'N/A'}",
                input_message_content=InputTextMessageContent(message_content, disable_web_page_preview=False),
                thumbnail_url=anime_data.get('coverImage', {}).get('extraLarge'),
                reply_markup=reply_markup,
            )
        )

    # Proses hasil manga
    if manga_data:
        message_content = build_manga_info_message(manga_data, target_user, is_inline=True)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Lihat di Anilist", url=manga_data['siteUrl'])]])
        results.append(
            InlineQueryResultArticle(
                id=f"manga_{manga_data['id']}",
                title=f"Manga: {manga_data['title']['romaji']}",
                description=f"Format: {manga_data.get('format', 'N/A')} | Chapter: {manga_data.get('chapters', 'N/A')}",
                input_message_content=InputTextMessageContent(message_content, disable_web_page_preview=False),
                thumbnail_url=manga_data.get('coverImage', {}).get('extraLarge'),
                reply_markup=reply_markup,
            )
        )

    # Proses hasil karakter
    if char_data:
        message_content = build_character_info_message(char_data, target_user, is_inline=True)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Lihat di Anilist", url=char_data['siteUrl'])]])
        first_media_title = "N/A"
        if char_data.get('media', {}).get('nodes'):
            first_media_title = char_data['media']['nodes'][0].get('title', {}).get('romaji', 'N/A')
        results.append(
            InlineQueryResultArticle(
                id=f"char_{char_data['id']}",
                title=f"Karakter: {char_data['name']['full']}",
                description=f"Muncul di: {first_media_title}",
                input_message_content=InputTextMessageContent(message_content, disable_web_page_preview=False),
                thumbnail_url=char_data.get('image', {}).get('large'),
                reply_markup=reply_markup,
            )
        )

    if not results:
        await context.bot.answer_inline_query(
            query.id,
            results=[],
            switch_pm_text=f"Tidak ada hasil untuk '{search_query}'",
            switch_pm_parameter="inline_no_results"
        )
    else:
        await query.answer(results, cache_time=10)


# --- Main Inline Handler (Dispatcher) ---

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani permintaan inline query dengan mendelegasikan ke sub-handler yang sesuai."""
    query = update.inline_query
    user = query.from_user
    message = query.query.strip()

    if not message:
        await _handle_instructions(query, context)
        return

    # Prioritaskan perintah eksplisit terlebih dahulu
    if message.lower() == "info":
        await _handle_user_info(query, user)
    elif message.lower().startswith("base64 "):
        await _handle_base64(query, message)
    elif message.lower().startswith("gpt "):
        await _handle_gemini(query, message)
    elif message.lower().startswith("whisper "):
        if query.chat_type != ChatType.PRIVATE:
            whisper_query = message[8:] # Ambil teks setelah "whisper "
            await _handle_whisper(query, user, whisper_query)
    else:
        # Jika tidak ada perintah eksplisit, anggap sebagai pencarian umum atau bertarget.
        # Logika parsing untuk target user sekarang ada di dalam _handle_anilist_search.
        await _handle_anilist_search(query, message, context)