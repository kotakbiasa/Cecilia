from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp

from bot import logger
from bot.modules.anilist import search_anime
from bot.modules.ryzumi_api import get_ytmp4_media
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

        # Construct image URL using img.anili.st service, which is often higher quality
        thumbnail_url = anime_data['siteUrl'].replace("anilist.co/anime/", "img.anili.st/media/")

        try:
            # Kirim sebagai foto dengan caption untuk menampilkan gambar di atas
            await message.reply_photo(
                photo=thumbnail_url,
                caption=caption,
                reply_markup=reply_markup
            )
            await sent_message.delete()
            return
        except Exception as e:
            logger.warning(f"Gagal mengirim dengan thumbnail_url {thumbnail_url}: {e}. Mencoba fallback.")

        # Fallback to bannerImage or coverImage if the primary URL fails
        fallback_url = anime_data.get('bannerImage') or anime_data.get('coverImage', {}).get('extraLarge')
        if fallback_url:
            try:
                await message.reply_photo(
                    photo=fallback_url,
                    caption=caption,
                    reply_markup=reply_markup
                )
                await sent_message.delete()
                return
            except Exception as final_e:
                logger.error(f"Gagal mengirim dengan fallback_url {fallback_url}: {final_e}")
        
        # If all image attempts fail, send as text by editing the wait message
        await sent_message.edit_text(caption, reply_markup=reply_markup)

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
        logger.info(f"Trailer ditemukan untuk anime ID {anime_data['id']}: {trailer}")
        first_row.append(InlineKeyboardButton("🎬 Trailer", callback_data=f"anime:trailer:{anime_data['id']}"))
    buttons.append(first_row)

    if anime_data.get('characters') and anime_data['characters'].get('edges'):
        buttons.append([InlineKeyboardButton("Karakter", callback_data=f"anime:chars:{anime_data['id']}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    return caption, reply_markup

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
        await query.edit_message_caption(caption="Sesi telah berakhir. Silakan mulai pencarian baru.", reply_markup=None)
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
        
        await query.edit_message_caption(caption=caption, reply_markup=reply_markup)

    elif action == 'info':
        caption, reply_markup = await _build_anime_info_layout(anime_data)
        await query.edit_message_caption(caption=caption, reply_markup=reply_markup)

    elif action == 'trailer':
        await query.edit_message_reply_markup(reply_markup=None)
        sent_msg = await query.message.reply_text("Memproses trailer, mohon tunggu...")

        trailer_data = anime_data.get('trailer')
        youtube_url = None
        if trailer_data and trailer_data.get('site') == 'youtube' and trailer_data.get('id'):
            youtube_url = f"https://www.youtube.com/watch?v={trailer_data['id']}"

        if not youtube_url:
            await sent_msg.edit_text("Trailer YouTube tidak ditemukan untuk anime ini.")
            return

        # Menggunakan API untuk mendapatkan link video langsung, default ke 480p
        video_data = await get_ytmp4_media(youtube_url, "480")

        if not (video_data and video_data.get("url")):
            error_detail = video_data.get("message", "Kualitas tidak tersedia.") if video_data else "Gagal mendapatkan respons dari API."
            await sent_msg.edit_text(f"Maaf, gagal memproses video trailer. {error_detail}\n\nCoba manual: {youtube_url}")
            return
        
        direct_video_url = video_data["url"]
        
        # Build caption with description from the API response
        trailer_title = video_data.get("title", anime_data['title']['romaji'])
        trailer_desc_en = video_data.get("description")
        trailer_desc = ""
        from bot.modules.translator import translate

        if trailer_desc_en:
            translated_desc = await asyncio.to_thread(translate, trailer_desc_en, 'id')
            if translated_desc:
                trailer_desc = translated_desc
            else:
                trailer_desc = trailer_desc_en # Fallback

        caption = f"<b>Trailer: {trailer_title}</b>"
        if trailer_desc:
            # Truncate description if it's too long for a caption
            if len(trailer_desc) > 250:
                trailer_desc = trailer_desc[:250].strip() + "..."
            caption += f"\n\n<blockquote expandable>{trailer_desc}</blockquote>"
        
        try:
            await sent_msg.edit_text("Mengunduh video trailer...")
            async with aiohttp.ClientSession() as session:
                # Set a reasonable timeout for the download itself
                async with session.get(direct_video_url, timeout=300) as resp:
                    if not resp.ok:
                        await sent_msg.edit_text(f"Gagal mengunduh trailer dari sumber (HTTP {resp.status}).\n\nLink Manual: {youtube_url}")
                        return
                    video_content = await resp.read()

            await sent_msg.edit_text("Mengirim video trailer...")
            # Send the downloaded bytes instead of the URL
            await query.message.reply_video(video=video_content, caption=caption, write_timeout=600)
            await sent_msg.delete()
        except aiohttp.ServerTimeoutError:
            logger.error(f"Gagal mengunduh video trailer anime (timeout saat mengunduh): {youtube_url}")
            await sent_msg.edit_text(f"Gagal mengunduh trailer karena timeout.\n\nLink Manual: {youtube_url}")
        except Exception as e:
            logger.error(f"Gagal mengirim video trailer anime: {e}")
            await sent_msg.edit_text(f"Gagal mengirim video. Mungkin file terlalu besar atau terjadi error.\n\nLink Manual: {youtube_url}")