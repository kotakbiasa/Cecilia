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

    # Izinkan owner dan sudo users
    sudo_users = getattr(config, 'sudo_users', [])
    if user_id != config.owner_id and user_id not in sudo_users:
        await message.reply_text("Perintah ini hanya untuk pemilik bot.")
        return

    sent_message = await message.reply_text("Mencoba memperbarui bot...")
    UPSTREAM_REPO_URL = "https://github.com/kotakbiasa/Cecilia"

    try:
        repo = git.Repo('.', search_parent_directories=True)
        
        # Periksa apakah ada perubahan lokal yang belum di-commit
        if repo.is_dirty(untracked_files=True):
            await sent_message.edit_text("Ada perubahan lokal yang belum di-commit. Harap commit atau stash perubahan tersebut terlebih dahulu.")
            return

        # Periksa dan siapkan remote 'upstream'
        try:
            upstream = repo.remote('upstream')
            if upstream.url != UPSTREAM_REPO_URL:
                logger.info(f"Memperbarui URL remote upstream ke {UPSTREAM_REPO_URL}")
                upstream.set_url(UPSTREAM_REPO_URL)
        except ValueError:
            logger.info(f"Membuat remote upstream baru untuk {UPSTREAM_REPO_URL}")
            upstream = repo.create_remote('upstream', UPSTREAM_REPO_URL)

        # Fetch pembaruan dari upstream
        await sent_message.edit_text("Mengambil pembaruan dari repositori upstream...")
        upstream.fetch()

        old_commit = repo.head.commit
        if old_commit == repo.remotes.upstream.refs.main.commit:
            await sent_message.edit_text("Bot sudah dalam versi terbaru dari repositori upstream. Tidak ada yang perlu diperbarui.")
            return

        # Cek apakah requirements.txt berubah dengan membandingkan commit
        diff_output = repo.git.diff(f'{old_commit.hexsha}..upstream/main', '--', 'requirements.txt')
        requirements_changed = bool(diff_output)

        # Lakukan pull dari upstream master
        logger.info("Menarik pembaruan dari upstream/main...")
        upstream.pull('main')

        if requirements_changed:
            logger.info("requirements.txt berubah, menginstal dependensi baru...")
            await sent_message.edit_text("Menginstal dependensi baru...")
            stdout, stderr = await run_command(f"{sys.executable} -m pip install -r requirements.txt")
            if stderr and "Requirement already satisfied" not in stderr:
                await sent_message.edit_text(f"Gagal menginstal dependensi:\n<code>{stderr}</code>")
                return

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