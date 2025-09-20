from telegram import Update
from telegram.ext import ContextTypes
from bot.modules.omdb_info import fetch_movieinfo

async def func_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_message = update.effective_message
    movie_name = " ".join(context.args)

    if not movie_name:
        await effective_message.reply_text("Gunakan <code>/movie [nama film]</code>\nContoh: <code>/movie animal</code>\natau\n<code>/movie -i tt13751694</code> [ID IMDB]\natau\n<code>/movie bodyguard -y 2011</code>")
        return
    
    if "-i" in movie_name and "-y" in movie_name:
        await effective_message.reply_text("⚠ Anda tidak bisa menggunakan kedua argumen sekaligus!\nLihat /movie untuk detail.")
        return
    
    imdb_id = None
    year = None
    
    if "-i" in movie_name:
        index_i = movie_name.index("-i")
        imdb_id = movie_name[index_i + len("-i"):].strip()
        movie_name = None
    elif "-y" in movie_name:
        index_y = movie_name.index("-y")
        year = movie_name[index_y + len("-y"):].strip()
        movie_name = movie_name[0: index_y].strip()

    movie_info = await fetch_movieinfo(movie_name=movie_name, imdb_id=imdb_id, year=year)
    if not movie_info:
        await effective_message.reply_text("Oops! Terjadi kesalahan!")
        return
    elif movie_info["Response"] == "False":
        await effective_message.reply_text("Nama film tidak valid!")
        return
    
    runtime = movie_info["Runtime"]
    if runtime != "N/A":
        try:
            runtime = f"{int(runtime.split()[0]) // 60} Jam {int(runtime.split()[0]) % 60} Menit"
        except (ValueError, IndexError):
            runtime = movie_info["Runtime"] # Fallback to original if parsing fails

    text = (
        f"<b><a href='https://www.imdb.com/title/{movie_info.get('imdbID')}'>{movie_info.get('Title')} | {movie_info.get('imdbID')}</a></b>\n\n"
        f"<b>🎥 Tipe Konten:</b> {movie_info.get('Type')}\n"
        f"<b>📄 Judul:</b> {movie_info.get('Title')}\n"
        f"<b>👁‍🗨 Rilis:</b> {movie_info.get('Released')}\n"
        f"<b>🕐 Durasi:</b> {runtime}\n"
        f"<b>🎨 Genre:</b> {movie_info.get('Genre')}\n"
        f"<b>🤵‍♂️ Sutradara:</b> {movie_info.get('Director')}\n"
        f"<b>🧑‍💻 Penulis:</b> {movie_info.get('Writer')}\n"
        f"<b>👫 Aktor:</b> {movie_info.get('Actors')}\n"
        f"<b>🗣 Bahasa:</b> {movie_info.get('Language')}\n"
        f"<b>🌐 Negara:</b> {movie_info.get('Country')}\n"
        f"<b>🏆 Penghargaan:</b> {movie_info.get('Awards')}\n"
        f"<b>🎯 Skor Meta:</b> {movie_info.get('Metascore')}\n"
        f"<b>🎯 Peringkat IMDB:</b> {movie_info.get('imdbRating')}\n"
        f"<b>📊 Suara IMDB:</b> {movie_info.get('imdbVotes')}\n"
        f"<b>🏷 ID IMDB:</b> <code>{movie_info.get('imdbID')}</code>\n"
        f"<b>💰 Box Office:</b> {movie_info.get('BoxOffice')}\n\n"
        f"<blockquote expandable><b>📝 Plot:</b> {movie_info.get('Plot')}</blockquote>"
    )

    photo = movie_info["Poster"]
    if photo:
        await effective_message.reply_photo(photo, text)
    else:
        await effective_message.reply_text(text)
