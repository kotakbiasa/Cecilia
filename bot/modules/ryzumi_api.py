import aiohttp
from bot import logger

BASE_API_URLS = [
    "https://api.ryzumi.vip/api/",
    "https://apidl.asepharyana.tech/api/",
    "https://api-02.ryzumi.vip/api/",
]

async def _make_api_request(endpoint: str, params: dict, api_name: str):
    """
    A generic helper to make requests to the Ryzumi API, with fallbacks.

    :param endpoint: The API endpoint path (e.g., "downloader/pinterest").
    :param params: A dictionary of parameters for the request.
    :param api_name: The name of the API for logging purposes (e.g., "Pinterest").
    :return: A dictionary with the API response, or None if all fallbacks fail.
    """
    headers = {"accept": "application/json"}

    for base_url in BASE_API_URLS:
        api_url = f"{base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, headers=headers, timeout=30) as response:
                    if response.ok:
                        logger.info(f"Successfully fetched from {api_name} API at {api_url}")
                        return await response.json()
                    
                    error_text = await response.text()
                    logger.warning(f"{api_name} API request to {api_url} failed with status {response.status}: {error_text[:200]}")
        except Exception as e:
            logger.warning(f"An exception occurred while fetching from {api_name} API at {api_url}: {e}")
            continue
    
    logger.error(f"All API endpoints failed for {api_name} with params {params}.")
    return None

async def _make_api_request_binary(endpoint: str, params: dict, api_name: str, timeout: int = 600):
    """
    A generic helper to make requests to the Ryzumi API for binary content, with fallbacks.

    :param endpoint: The API endpoint path.
    :param params: A dictionary of parameters for the request.
    :param api_name: The name of the API for logging purposes.
    :param timeout: The request timeout in seconds.
    :return: The binary content (bytes), or None if all fallbacks fail.
    """
    headers = {"accept": "image/png"}

    for base_url in BASE_API_URLS:
        api_url = f"{base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, headers=headers, timeout=timeout) as response:
                    if response.ok:
                        logger.info(f"Successfully fetched binary from {api_name} API at {api_url}")
                        return await response.read()

                    error_text = await response.text()
                    logger.warning(f"{api_name} API binary request to {api_url} failed with status {response.status}: {error_text[:200]}")
        except Exception as e:
            logger.warning(f"An exception occurred while fetching binary from {api_name} API at {api_url}: {e}")
            continue

    logger.error(f"All API endpoints failed for binary {api_name} with params {params}.")
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

async def get_waifu2x_image(image_url: str):
    """
    Upscales an image using the Waifu2x API.

    :param image_url: The URL of the image to upscale.
    :return: The upscaled image as bytes, or None if an error occurs.
    """
    if not image_url:
        logger.error("Image URL was not provided for Waifu2x.")
        return None
    params = {"url": image_url}
    # Using the binary request helper with a longer timeout
    return await _make_api_request_binary("ai/waifu2x", params, "Waifu2x")

async def get_negro_image(image_url: str, filter_name: str = None):
    """
    Applies a filter to an image using the 'negro' API.

    :param image_url: The URL of the image to filter.
    :param filter_name: The name of the filter to apply (optional).
    :return: The filtered image as bytes, or None if an error occurs.
    """
    if not image_url:
        logger.error("Image URL was not provided for Penghitaman.")
        return None
    params = {"url": image_url}
    if filter_name:
        params["filter"] = filter_name

    return await _make_api_request_binary("ai/negro", params, "Penghitaman")