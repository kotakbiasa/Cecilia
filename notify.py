import os
import json
import asyncio
import aiohttp

# Constants
GITHUB_OWNER_USERNAME = "bishalqx980"
REPO_NAME = "tgbot"
# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


async def get_git_commits(session):
    """Fetches the latest commits from the GitHub repository."""
    url = f"https://api.github.com/repos/{GITHUB_OWNER_USERNAME}/{REPO_NAME}/commits"
    try:
        async with session.get(url) as response:
            if not response.ok:
                print(f"GitHub API Error: {response.status} - {await response.text()}")
                return None
            return await response.json()
    except Exception as e:
        print(f"An error occurred while fetching commits: {e}")
        return None


async def send_telegram_message(session, text):
    """Sends a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": int(CHAT_ID),
        "text": text,
        "disable_web_page_preview": True,
        "parse_mode": "HTML"
    }
    try:
        async with session.post(url, json=data) as response:
            if response.ok:
                print("Notification sent successfully!")
                return await response.json()
            else:
                print(f"Telegram API Error: {response.status} - {await response.text()}")
                return None
    except Exception as e:
        print(f"An error occurred while sending message: {e}")
        return None


async def main():
    """Main asynchronous function."""
    async with aiohttp.ClientSession() as session:
        commits_data = await get_git_commits(session)
        if not commits_data:
            return

        latest_commit = commits_data[0]
        committer = latest_commit['commit']['committer']
        latest_commit_url = latest_commit['html_url']
        commit_message = latest_commit['commit']['message']

        message = (
            f"A new <b><a href='{latest_commit_url}'>commit {latest_commit['sha'][:7]}</a></b> has been made to <a href='https://github.com/{GITHUB_OWNER_USERNAME}/{REPO_NAME}'>{REPO_NAME}</a>\n\n"
            f"<blockquote>{commit_message}</blockquote>\n\n"
            f"<b>Signed by:</b> <i>{committer['name']}</i>"
        )

        await send_telegram_message(session, message)

# calling the function
if all([BOT_TOKEN, CHAT_ID, GITHUB_OWNER_USERNAME, REPO_NAME]):
    asyncio.run(main())
else:
    print("One or more environment variables are missing (BOT_TOKEN, CHAT_ID).")
