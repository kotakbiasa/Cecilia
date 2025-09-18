from telegram import Update
from telegram.ext import ContextTypes

from bot import logger
from bot.modules.anilist import search_airing_anime

def format_time(total_seconds: int) -> str:
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

async def func_airing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mendapatkan informasi penayangan untuk sebuah anime."""
    message = update.effective_message
    query = " ".join(context.args)

    if not query:
        await message.reply_text("Gunakan <code>/airing [nama anime]</code>.")
        return

    sent_message = await message.reply_text("Mencari info penayangan...")
    
    try:
        airing_data = await search_airing_anime(query)

        if not airing_data:
            await sent_message.edit_text(f"Tidak dapat menemukan info penayangan untuk '<code>{query}</code>'.")
            return

        title = airing_data['title']['romaji']
        if airing_data['title']['english']:
            title = f"{title} ({airing_data['title']['english']})"

        text = f"<b>{title}</b>\n<b>ID:</b> <code>{airing_data['id']}</code>\n\n"

        next_airing = airing_data.get('nextAiringEpisode')
        if next_airing:
            time_until = format_time(next_airing['timeUntilAiring'])
            text += f"<b>Episode Berikutnya:</b> <code>{next_airing['episode']}</code>\n<b>Tayang Dalam:</b> <code>{time_until}</code>"
        else:
            status = airing_data.get('status', 'N/A').replace('_', ' ').title()
            text += f"<b>Status:</b> {status}\nAnime ini kemungkinan sudah selesai tayang."

        await sent_message.edit_text(text)
    except Exception as e:
        logger.error(f"Gagal dalam proses airing: {e}")
        await sent_message.edit_text(f"Terjadi error: {e}")