import aiohttp
from bot import logger

async def bilibili_downloader(url: str):
    """
    Downloads video from Bilibili using an external API.

    :param url: The Bilibili video URL.
    :return: A dictionary containing video data, or None if an error occurs.
    """
    api_url = "https://api.ryzumi.vip/api/downloader/bilibili"
    params = {"url": url}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=30) as response:
                if not response.ok:
                    logger.error(f"Bilibili API request failed: {response.status} - {await response.text()}")
                    return None

                data = await response.json()

                if data.get("status") and "data" in data:
                    return data["data"]
                else:
                    logger.error(f"Bilibili API returned an error: {data}")
                    return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Bilibili download: {e}")
        return None

