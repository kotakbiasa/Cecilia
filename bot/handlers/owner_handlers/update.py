import asyncio
import sys
import git
import threading
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.decorators.sudo_users import require_sudo

from bot import logger, config

@require_sudo
async def run_command(command: str) -> tuple[str, str]:
    """Menjalankan perintah shell dan mengembalikan outputnya."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()


def restart() -> None:
    """Memulai ulang bot."""
    logger.info("Memulai ulang bot...")
    # Mengganti proses saat ini dengan instance baru
    # sys.executable adalah path ke interpreter Python saat ini
    # sys.argv adalah daftar argumen baris perintah saat ini
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)


async def _perform_update(message, sent_message) -> None:
    """Melakukan proses pembaruan bot."""
    UPSTREAM_REPO_URL = "https://github.com/kotakbiasa/Cecilia"

    try:
        repo = git.Repo('.', search_parent_directories=True)

        # Periksa apakah ada perubahan lokal yang belum di-commit
        await sent_message.edit_text("Memeriksa perubahan lokal...")
        if repo.is_dirty(untracked_files=True):
            await sent_message.edit_text("Ada perubahan lokal yang belum di-commit. Harap commit atau stash perubahan tersebut terlebih dahulu.")
            return

        # Fetch pembaruan dari upstream
        await sent_message.edit_text("Mengambil pembaruan dari repositori upstream (github.com/kotakbiasa/Cecilia)...")
        upstream = repo.remote('upstream')
        upstream.fetch()

        # Cek apakah requirements.txt berubah dengan membandingkan commit
        old_commit = repo.head.commit
        diff_output = repo.git.diff(f'{old_commit.hexsha}..upstream/main', '--', 'requirements.txt')
        requirements_changed = bool(diff_output)

        if requirements_changed:
            await sent_message.edit_text("requirements.txt telah berubah. Bot akan menginstal dependensi yang diperlukan setelah pembaruan.")

        # Lakukan pull dari upstream master
        await sent_message.edit_text("Menarik pembaruan dari repositori upstream...")
        upstream.pull('main')

        # Instal dependensi jika requirements.txt berubah
        if requirements_changed:
            await sent_message.edit_text("Menginstal dependensi baru dari requirements.txt...")

    except Exception as e:
        logger.error(f"Gagal memperbarui bot: {e}")
        await sent_message.edit_text(f"Gagal memperbarui bot: {e}")



async def func_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memperbarui bot dari repositori Git dan memulai ulang."""
    message = update.effective_message
    
    # Decorator @require_sudo akan menangani pemeriksaan izin
    # Tidak perlu pemeriksaan izin manual di sini

    sent_message = await message.reply_text("Mencoba memperbarui bot...")
    UPSTREAM_REPO_URL = "https://github.com/kotakbiasa/Cecilia"
    threading.Thread(target=asyncio.run, args=(_perform_update(message, sent_message),)).start()

    try:
        repo = git.Repo('.', search_parent_directories=True)
        await sent_message.edit_text("Pembaruan berhasil. Memulai ulang bot sekarang...")
        restart()
        

    except Exception as e:
        logger.error(f"Gagal memperbarui bot: {e}")
        await sent_message.edit_text(f"Gagal memperbarui bot: {e}")


async def func_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai ulang bot (hanya untuk pemilik)."""
    user_id = update.effective_user.id 
    sudo_users = getattr(config, 'sudo_users', [])
    if user_id == config.owner_id or user_id in sudo_users:
        await update.effective_message.reply_text("Memulai ulang bot...")
        restart()
    else:
        await update.effective_message.reply_text("Perintah ini hanya untuk pemilik bot.")