import asyncio
import aiohttp
import json
import re
import base64
from bot import logger

WORKERS_ENDPOINTS = [
    "https://terabox.hnn.workers.dev",
    "https://plain-grass-58b2.comprehensiveaquamarine.workers.dev",
    "https://bold-hall-f23e.7rochelle.workers.dev",
    "https://winter-thunder-0360.belitawhite.workers.dev",
    "https://fragrant-term-0df9.elviraeducational.workers.dev",
    "https://purple-glitter-924b.miguelalocal.workers.dev",
]

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

def _extract_shorturl(url: str) -> str | None:
    """Extracts shorturl from a full TeraBox URL."""
    patterns = [r'terabox\.com/s/([^/?&]+)', r'1024tera\.com/s/([^/?&]+)', r'4funbox\.com/s/([^/?&]+)', r'mirrobox\.com/s/([^/?&]+)', r'teraboxapp\.com/s/([^/?&]+)', r'surl=([^&]+)', r'/s/([^/?&]+)']
    for pattern in patterns:
        if match := re.search(pattern, url):
            return match.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{10,25}$', url):
        return url
    return None

async def _get_info(session: aiohttp.ClientSession, shorturl: str) -> tuple[dict | None, str | None]:
    """Fetches file/folder info from TeraBox via workers, with fallbacks."""
    params = {"shorturl": shorturl, "pwd": ""}
    api_paths = ["/api/get-info-new", "/api/get-info"]

    for base_url in WORKERS_ENDPOINTS:
        headers = DEFAULT_HEADERS.copy()
        headers.update({"Referer": f"{base_url}/", "Origin": base_url})
        for api_path in api_paths:
            try:
                api_url = f"{base_url}{api_path}"
                async with session.get(api_url, params=params, headers=headers, timeout=20) as response:
                    if not response.ok:
                        continue
                    data = await response.json()
                    if data.get("ok"):
                        logger.info(f"Successfully got info from {api_url}")
                        return data, base_url
            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
                logger.warning(f"Exception on endpoint {base_url}{api_path}: {e}")
                continue
    return None, None

async def _get_download_link(session: aiohttp.ClientSession, params: dict, shorturl: str) -> dict | None:
    """Gets the direct download link, with fallback and token refresh logic."""
    api_path = "/api/get-downloadp"

    for base_url in WORKERS_ENDPOINTS:
        headers = DEFAULT_HEADERS.copy()
        headers.update({
            "Referer": f"{base_url}/",
            "Origin": base_url,
            "Content-Type": "application/json"
        })
        try:
            api_url = f"{base_url}{api_path}"
            async with session.post(api_url, json=params, headers=headers, timeout=20) as response:
                if not response.ok:
                    continue
                data = await response.json()

                if data.get("ok"):
                    logger.info(f"Successfully got download link from {api_url}")
                    return data

                # Handle token expiration
                error_msg = data.get('message', '').lower()
                if 'expired' in error_msg or 'invalid' in error_msg:
                    logger.warning(f"Token expired/invalid at {base_url}. Attempting to refresh...")
                    fresh_info, _ = await _get_info(session, shorturl)
                    if fresh_info and fresh_info.get('ok'):
                        params.update({
                            'shareid': int(fresh_info['shareid']),
                            'uk': int(fresh_info['uk']),
                            'sign': str(fresh_info['sign']),
                            'timestamp': int(fresh_info['timestamp'])
                        })
                        logger.info("Token refreshed. Retrying download link request...")
                        async with session.post(api_url, json=params, headers=headers, timeout=20) as retry_response:
                            if retry_response.ok:
                                retry_data = await retry_response.json()
                                if retry_data.get("ok"):
                                    logger.info("Successfully got link with refreshed token!")
                                    return retry_data
        except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
            logger.warning(f"Exception on download endpoint {base_url}{api_path}: {e}")
            continue

    logger.error(f"All download endpoints failed for fs_id: {params.get('fs_id')}")
    return None

async def terabox_download(url: str, pwd: str = "") -> list[dict] | None:
    """
    Converts a Terabox share URL into a direct download link with fallback and token refresh.

    :param url: The Terabox share URL (e.g., https://terabox.com/s/...).
    :param pwd: The password for the link, if any. (Currently unused by API).
    :return: A list of dictionaries containing file info, or None on failure.
    """
    shorturl = _extract_shorturl(url)
    if not shorturl:
        logger.warning(f"Could not extract a valid shorturl from: {url}")
        return None

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        info_data, successful_base_url = await _get_info(session, shorturl)

        if not info_data or not info_data.get("list"):
            logger.error(f"Failed to get file info for shorturl: {shorturl}")
            return None

        tasks = []
        for item in info_data.get("list", []):
            if not all(k in item for k in ["fs_id", "filename", "size"]):
                logger.warning(f"Skipping item due to missing keys: {item}")
                continue

            params = {
                "shareid": int(info_data['shareid']),
                "uk": int(info_data['uk']),
                "sign": str(info_data['sign']),
                "timestamp": int(info_data['timestamp']),
                "fs_id": int(item['fs_id']),
            }
            # Create a task to get the download link for each file
            tasks.append(
                _process_file_item(session, params, item, shorturl)
            )

        # Run all download link requests concurrently
        results = await asyncio.gather(*tasks)
        download_links = [res for res in results if res]  # Filter out None results

        return download_links if download_links else None

async def _process_file_item(session: aiohttp.ClientSession, params: dict, item_data: dict, shorturl: str) -> dict | None:
    """Helper to process a single file item and get its download link."""
    link_data = await _get_download_link(session, params, shorturl)
    if not link_data or not link_data.get("ok"):
        return None

    download_link = link_data.get("downloadLink")
    if not download_link:
        return None

    size_in_mb = int(item_data.get('size', 0)) / (1024 * 1024)
    return {
        "filename": item_data.get("filename"),
        "link": download_link,
        "size_mb": round(size_in_mb, 2)
    }