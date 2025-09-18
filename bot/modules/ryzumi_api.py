import aiohttp
from bot import logger

BASE_API_URL = "https://api.ryzumi.vip/api/"

async def _make_api_request(endpoint: str, params: dict, api_name: str):
    """
    A generic helper to make requests to the Ryzumi API.

    :param endpoint: The API endpoint path (e.g., "downloader/pinterest").
    :param params: A dictionary of parameters for the request.
    :param api_name: The name of the API for logging purposes (e.g., "Pinterest").
    :return: A dictionary with the API response, or None if an error occurs.
    """
    api_url = f"{BASE_API_URL}{endpoint}"
    headers = {"accept": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, headers=headers) as response:
                if not response.ok:
                    error_text = await response.text()
                    logger.error(f"{api_name} API request failed with status {response.status}: {error_text}")
                    return None
                return await response.json()
    except Exception as e:
        logger.error(f"An exception occurred while fetching from {api_name} API: {e}")
        return None

async def get_pinterest_media(pinterest_url: str):
    """
    Fetches media from a Pinterest URL using the Ryzumi API.

    :param pinterest_url: The full URL of the Pinterest pin.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not pinterest_url:
        logger.error("Pinterest URL was not provided.")
        return None
    params = {"url": pinterest_url}
    return await _make_api_request("downloader/pinterest", params, "Pinterest")

async def get_ytmp3_media(youtube_url: str):
    """
    Fetches audio from a YouTube URL using the Ryzumi API.

    :param youtube_url: The full URL of the YouTube video.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not youtube_url:
        logger.error("YouTube URL was not provided.")
        return None
    params = {"url": youtube_url}
    return await _make_api_request("downloader/ytmp3", params, "YTMP3")

async def get_ytmp4_media(youtube_url: str, quality: str):
    """
    Fetches video from a YouTube URL using the Ryzumi API.

    :param youtube_url: The full URL of the YouTube video.
    :param quality: The desired video quality (e.g., "480").
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not youtube_url:
        logger.error("YouTube URL was not provided.")
        return None
    params = {"url": youtube_url, "quality": quality}
    return await _make_api_request("downloader/ytmp4", params, "YTMP4")

async def get_fbdl_media(facebook_url: str):
    """
    Fetches media from a Facebook URL using the Ryzumi API.

    :param facebook_url: The full URL of the Facebook video.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not facebook_url:
        logger.error("Facebook URL was not provided.")
        return None
    params = {"url": facebook_url}
    return await _make_api_request("downloader/fbdl", params, "FBDL")

async def get_ttdl_media(tiktok_url: str):
    """
    Fetches media from a TikTok URL using the Ryzumi API.

    :param tiktok_url: The full URL of the TikTok video.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not tiktok_url:
        logger.error("TikTok URL was not provided.")
        return None
    params = {"url": tiktok_url}
    return await _make_api_request("downloader/ttdl", params, "TTDL")

async def get_igdl_media(instagram_url: str):
    """
    Fetches media from an Instagram URL using the Ryzumi API.

    :param instagram_url: The full URL of the Instagram post.
    :return: A dictionary with the API response, or None if an error occurs.
    """
    if not instagram_url:
        logger.error("Instagram URL was not provided.")
        return None
    params = {"url": instagram_url}
    return await _make_api_request("downloader/igdl", params, "IGDL")