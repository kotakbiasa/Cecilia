import asyncio
import sys
import git
from telegram import Update
from telegram.ext import ContextTypes

from bot import logger, config


async def run_command(command: str) -> tuple[str, str]:
    """Menjalankan perintah shell dan mengembalikan outputnya."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()


def restart():
    """Memulai ulang bot."""
    logger.info("Memulai ulang bot...")
    # Mengganti proses saat ini dengan instance baru
    # sys.executable adalah path ke interpreter Python saat ini
    # sys.argv adalah daftar argumen baris perintah saat ini
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)


async def func_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memperbarui bot dari repositori Git dan memulai ulang."""
    message = update.effective_message
    user_id = update.effective_user.id

    if user_id != getattr(config, 'OWNER_ID', None):
        await message.reply_text("Perintah ini hanya untuk pemilik bot.")
        return

    sent_message = await message.reply_text("Mencoba memperbarui bot...")

    try:
        repo = git.Repo(search_parent_directories=True)
        
        # Periksa apakah ada perubahan lokal yang belum di-commit
        if repo.is_dirty(untracked_files=True):
            await sent_message.edit_text("Ada perubahan lokal yang belum di-commit. Harap commit atau stash perubahan tersebut terlebih dahulu.")
            return

        origin = repo.remotes.origin
        logger.info("Menarik pembaruan dari Git...")
        pull_info = origin.pull()

        # Cek apakah ada pembaruan
        if pull_info and pull_info[0].flags & git.remote.FetchInfo.HEAD_UPTODATE:
            await sent_message.edit_text("Bot sudah dalam versi terbaru. Tidak ada yang perlu diperbarui.")
            return

        # Cek apakah requirements.txt berubah
        diff_index = repo.index.diff("HEAD~1")
        requirements_changed = any(diff.a_path == 'requirements.txt' for diff in diff_index)

        if requirements_changed:
            logger.info("requirements.txt berubah, menginstal dependensi baru...")
            await sent_message.edit_text("Menginstal dependensi baru...")
            stdout, stderr = await run_command(f"{sys.executable} -m pip install -r requirements.txt")
            if stderr:
                await sent_message.edit_text(f"Gagal menginstal dependensi:\n<code>{stderr}</code>")
                return

        await sent_message.edit_text("Pembaruan berhasil. Memulai ulang bot sekarang...")
        restart()

    except Exception as e:
        logger.error(f"Gagal memperbarui bot: {e}")
        await sent_message.edit_text(f"Gagal memperbarui bot: {e}")


async def func_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai ulang bot (hanya untuk pemilik)."""
    if update.effective_user.id == getattr(config, 'OWNER_ID', None):
        await update.effective_message.reply_text("Memulai ulang bot...")
        restart()
    else:
        await update.effective_message.reply_text("Perintah ini hanya untuk pemilik bot.")