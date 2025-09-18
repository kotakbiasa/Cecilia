import aiohttp
from bot import logger

API_URL = "https://api.trace.moe/search"

async def get_anime_source(image_url: str):
    """
    Finds the anime source for a given image URL using trace.moe API.

    :param image_url: The URL of the image to search for.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not image_url:
        logger.error("Image URL was not provided for trace.moe search.")
        return None

    params = {"url": image_url}

    try:
        async with aiohttp.ClientSession() as session:
            # Increased timeout as anime search can be slow
            async with session.get(API_URL, params=params, timeout=120) as response:
                if response.ok:
                    data = await response.json()
                    if data.get("error"):
                        logger.error(f"trace.moe API returned an error: {data['error']}")
                        return None
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"trace.moe API request failed with status {response.status}: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"An exception occurred while fetching from trace.moe API: {e}")
        return None