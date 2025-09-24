import re
import asyncio
from html import escape
from calendar import month_name
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent
from bot.helpers import BuildKeyboard
from bot.modules.translator import translate
from bot import logger

def inlineQueryMaker(title, message, reply_markup=None, description=None):
    """
    :param description: Type `same` if you want to keep the description same as message!
    """
    if not reply_markup:
        reply_markup = BuildKeyboard.cbutton([{"Try inline": "switch_to_inline"}])
    
    try:
        content = InlineQueryResultArticle(
            str(uuid4()),
            title=title,
            input_message_content=InputTextMessageContent(message),
            reply_markup=reply_markup,
            description=message if description == "same" else description
        )

        return content
    except Exception as e:
        logger.error(e)
        return

def clean_html(raw_html: str) -> str:
    """Menghapus tag HTML dari string."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def _format_airing_time(total_seconds: int) -> str:
    """Formats time in seconds to a human-readable string."""
    if not total_seconds or total_seconds < 0:
        return "N/A"
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if seconds > 0 and not parts: # Only show seconds if it's less than a minute
        parts.append(f"{seconds} detik")
        
    return ", ".join(parts) if parts else "sekarang"

async def build_anime_info_message_md(anime_data: dict, is_inline: bool = False) -> str:
    """Membangun teks caption untuk anime dalam format HTML."""
    title = anime_data['title']['romaji']
    native_title = anime_data['title'].get('native', '')    
    msg = f"<b>{escape(title)}</b> (<code>{escape(native_title)}</code>)\n\n"

    description_en = clean_html(anime_data.get('description', ''))
    description_id = ""
    if description_en:
        try:
            description_id = await asyncio.to_thread(translate, description_en, 'id')
        except Exception as e:
            logger.error(f"Gagal menerjemahkan deskripsi anime: {e}")

    status = anime_data.get('status', 'N/A').replace('_', ' ').title()
    duration = f"{anime_data.get('duration', 'N/A')} Per Ep." if anime_data.get('duration') else 'N/A'
    score = anime_data.get('averageScore', 'N/A')
    if score and score != 'N/A':
        score = score / 10

    msg += f"<b>Type</b>: {anime_data.get('format', 'N/A')}\n"
    msg += f"<b>Status</b>: {status}\n"
    msg += f"<b>Episodes</b>: {anime_data.get('episodes', 'N/A')}\n"
    msg += f"<b>Duration</b>: {duration}\n"
    msg += f"<b>Score</b>: {score}\n"

    genres = anime_data.get('genres', [])
    if genres:
        msg += f"<b>Genres</b>: <code>{escape(', '.join(genres))}</code>\n"

    studios = anime_data.get('studios', {}).get('nodes', [])
    if studios:
        studio_names = [s['name'] for s in studios]
        msg += f"<b>Studios</b>: <code>{escape(', '.join(studio_names))}</code>\n"

    final_description = description_id or description_en
    if final_description:
        msg += f"\n<b>Description</b>: <blockquote expandable>{escape(final_description)}</blockquote>"

    return msg

async def build_manga_info_message(manga_data: dict, target_user: str | None = None, is_inline: bool = False) -> str:
    """Membangun teks caption untuk manga."""
    title = manga_data['title']['romaji']
    if manga_data['title']['english']:
        title = f"{title} ({manga_data['title']['english']})"
    
    caption_parts = []
    if target_user:
        caption_parts.append(f"Untuk {escape(target_user)},\n\n")

    description_en = clean_html(manga_data.get('description', ''))
    description_id = ""
    if description_en:
        try:
            description_id = await asyncio.to_thread(translate, description_en, 'id')
        except Exception as e:
            logger.error(f"Gagal menerjemahkan deskripsi manga: {e}")
    status = manga_data.get('status', 'N/A').replace('_', ' ').title()
    
    title_link = f"<b><a href=\"{manga_data['siteUrl']}\">{title}</a></b>" if is_inline else f"<b>{title}</b>"

    caption_parts.extend([
        f"{title_link}\n\n",
        f"<b>Format:</b> {manga_data.get('format', 'N/A')}\n",
        f"<b>Status:</b> {status}\n",
        f"<b>Chapter:</b> {manga_data.get('chapters', 'N/A')}\n",
        f"<b>Volume:</b> {manga_data.get('volumes', 'N/A')}\n",
        f"<b>Skor:</b> {manga_data.get('averageScore', 0) / 10 if manga_data.get('averageScore') else 'N/A'}/10\n",
        f"<b>Genre:</b> {', '.join(manga_data.get('genres', []))}\n\n",
    ])
    final_description = description_id or description_en
    if final_description:
        caption_parts.append(f"<blockquote expandable>{escape(final_description)}</blockquote>")
    return "".join(caption_parts)

async def build_character_info_message(char_data: dict, target_user: str | None = None, is_inline: bool = False) -> str:
    """Membangun teks caption untuk karakter."""
    title = char_data['name']['full']
    if char_data['name']['native']:
        title = f"{title} ({char_data['name']['native']})"
    
    caption_parts = []
    if target_user:
        caption_parts.append(f"Untuk {escape(target_user)},\n\n")

    description_html = char_data.get('description', '')
    description_en = clean_html(description_html)
    description_id = ""
    if description_en:
        try:
            description_id = await asyncio.to_thread(translate, description_en, 'id')
        except Exception as e:
            logger.error(f"Gagal menerjemahkan deskripsi karakter: {e}")

    title_link = f"<b><a href=\"{char_data['siteUrl']}\">{title}</a></b>" if is_inline else f"<b>{title}</b>"
    caption_parts.append(title_link)

    final_description = description_id or description_en
    if final_description:
        caption_parts.append(f"\n\n<blockquote expandable>{escape(final_description)}</blockquote>")

    media_nodes = char_data.get('media', {}).get('nodes', [])
    if media_nodes and not is_inline: # Don't show media in inline results to keep it clean
        media_list = [
            f"• <code>{escape(media.get('title', {}).get('userPreferred') or media.get('title', {}).get('romaji'))}</code>"
            for media in media_nodes[:5] if media.get('title')
        ]
        if media_list:
            caption_parts.append("\n\n<b>Muncul di:</b>\n" + "\n".join(media_list))

    return "".join(caption_parts)