from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_anime
from bot.handlers.query_handlers.message_builder import (
    build_anime_info_message
)

async def func_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mencari informasi anime di Anilist."""
    message = update.effective_message
    query = " ".join(context.args)

    if not query:
        await message.reply_text(
            "Gunakan <code>/anime [nama anime]</code> untuk mencari informasi anime.\n"
            "Contoh: <code>/anime Steins;Gate</code>"
        )
        return

    sent_message = await message.reply_text("Mencari anime di Anilist...")

    try:
        anime_data = await search_anime(query)

        if not anime_data:
            await sent_message.edit_text(f"Maaf, anime dengan nama '<code>{query}</code>' tidak ditemukan.")
            return

        # Simpan data untuk digunakan di callback
        anime_id = anime_data['id']
        context.user_data[f"anime_{anime_id}"] = anime_data

        caption, reply_markup = await _build_anime_info_layout(anime_data)

        # Coba dapatkan URL gambar dari beberapa sumber, utamakan banner
        image_url = anime_data.get('bannerImage') or anime_data.get('coverImage', {}).get('extraLarge')
        final_caption = caption
        disable_preview = True

        if image_url:
            # Tambahkan zero-width space dengan link gambar untuk membuat pratinjau di atas teks
            final_caption = f"<a href='{image_url}'>&#8203;</a>{caption}"
            disable_preview = False

        # Edit pesan yang sudah ada untuk menampilkan hasil
        await sent_message.edit_text(
            text=final_caption,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview
        )

    except Exception as e:
        logger.error(f"Gagal dalam proses pencarian anime: {e}")
        await sent_message.edit_text(f"Terjadi error saat memproses permintaan Anda: {e}")

async def _build_anime_info_layout(anime_data: dict) -> tuple[str, InlineKeyboardMarkup]:
    """Membangun caption dan keyboard untuk tampilan info utama anime."""
    caption = await build_anime_info_message(anime_data)

    buttons = []
    first_row = [InlineKeyboardButton("Lihat di Anilist", url=anime_data['siteUrl'])]

    trailer = anime_data.get('trailer')
    if trailer and trailer.get('site') == 'youtube' and trailer.get('id'):
        # Log that a trailer was found to help with debugging
        youtube_url = f"https://www.youtube.com/watch?v={trailer['id']}"
        first_row.append(InlineKeyboardButton("🎬 Trailer", url=youtube_url))
    buttons.append(first_row)

    if anime_data.get('characters') and anime_data['characters'].get('edges'):
        buttons.append([InlineKeyboardButton("Karakter", callback_data=f"anime:chars:{anime_data['id']}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    return caption, reply_markup

async def _edit_message_with_preview(query: Update.callback_query, new_caption: str, new_markup: InlineKeyboardMarkup, anime_data: dict):
    """Helper to edit message while preserving the top image preview."""
    image_url = anime_data.get('bannerImage') or anime_data.get('coverImage', {}).get('extraLarge')
    final_text = new_caption
    disable_preview = True

    if image_url:
        final_text = f"<a href='{image_url}'>&#8203;</a>{new_caption}"
        disable_preview = False

    await query.edit_message_text(text=final_text, reply_markup=new_markup, disable_web_page_preview=disable_preview)

async def anime_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani penekanan tombol untuk modul anime."""
    query = update.callback_query
    logger.info(f"Anime callback received: {query.data} from user {query.from_user.id}")
    await query.answer()

    try:
        _, action, anime_id_str = query.data.split(':')
        anime_id = int(anime_id_str)
    except (ValueError, IndexError):
        await query.edit_message_text("Error: Callback data tidak valid.")
        return

    anime_data = context.user_data.get(f"anime_{anime_id}")
    if not anime_data:
        await query.edit_message_text(text="Sesi telah berakhir. Silakan mulai pencarian baru.", reply_markup=None)
        return

    if action == 'chars':
        title = anime_data['title']['romaji']
        character_edges = anime_data.get('characters', {}).get('edges', [])
        
        if not character_edges:
            caption = f"<b>Karakter: {title}</b>\n\nTidak ada informasi karakter yang tersedia."
        else:
            main_chars = []
            supporting_chars = []
            for edge in character_edges:
                char_name = edge.get('node', {}).get('name', {}).get('full')
                if not char_name:
                    continue
                
                if edge.get('role') == 'MAIN':
                    main_chars.append(f"• <code>{char_name}</code>")
                elif edge.get('role') == 'SUPPORTING':
                    supporting_chars.append(f"• <code>{char_name}</code>")

            caption_parts = [f"<b>Karakter: {title}</b>"]

            if main_chars:
                caption_parts.append("\n<b>Utama:</b>\n" + "\n".join(main_chars))
            
            if supporting_chars:
                caption_parts.append("\n<b>Pendukung:</b>\n" + "\n".join(supporting_chars))

            caption = "\n".join(caption_parts)
        
        buttons = [[InlineKeyboardButton("« Kembali", callback_data=f"anime:info:{anime_id}")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await _edit_message_with_preview(query, caption, reply_markup, anime_data)

    elif action == 'info':
        caption, reply_markup = await _build_anime_info_layout(anime_data)
        await _edit_message_with_preview(query, caption, reply_markup, anime_data)