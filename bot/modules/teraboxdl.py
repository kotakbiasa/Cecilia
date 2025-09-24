import asyncio
import aiohttp
import json
import re
from bot import logger

API_BASE_URL = "https://terabox.hnn.workers.dev/api"
DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "terabox.hnn.workers.dev",
    "Referer": "https://terabox.hnn.workers.dev/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

async def _get_download_link(session: aiohttp.ClientSession, data: dict) -> dict | None:
    """
    Fetches the final download link for a specific file ID.
    """
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://terabox.hnn.workers.dev",
        "Referer": "https://terabox.hnn.workers.dev/",
        "User-Agent": DEFAULT_HEADERS["User-Agent"], # Add User-Agent here as well
    }
    try:
        async with session.post(f"{API_BASE_URL}/get-download", json=data, headers=headers, timeout=30) as response:
            if not response.ok:
                logger.error(f"Terabox API (get-download) failed with status: {response.status}")
                return None

            res_json = await response.json()
            if res_json.get("ok"):
                size_in_mb = int(data.get('size', 0)) / (1024 * 1024)
                return {
                    "filename": data.get("filename"),
                    "link": res_json.get("downloadLink"),
                    "size_mb": round(size_in_mb, 2)
                }
            else:
                logger.warning(f"Terabox API (get-download) returned not ok: {res_json}")
                return None
    except asyncio.TimeoutError:
        logger.error("Timeout error while fetching Terabox download link.")
        return None
    except (aiohttp.ClientError, json.JSONDecodeError) as e:
        logger.error(f"Error fetching Terabox download link: {e}", exc_info=False)
        return None

async def terabox_download(url: str, pwd: str = "") -> list[dict] | None:
    """
    Converts a Terabox share URL into a direct download link.

    :param url: The Terabox share URL (e.g., https://terabox.com/s/...).
    :param pwd: The password for the link, if any.
    :return: A list of dictionaries containing file info, or None on failure.
    """
    match = re.search(r'/s/([^/?]*)', url)
    if not match:
        logger.warning(f"Invalid Terabox URL format: {url}")
        return None
    shorturl = match.group(1)

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        try:
            params = {"shorturl": shorturl, "pwd": pwd}
            async with session.get(f"{API_BASE_URL}/get-info", params=params, timeout=30) as response:
                if not response.ok:
                    logger.error(f"Terabox API (get-info) failed with status: {response.status}")
                    return None
                
                # Attempt to parse JSON, handle cases where API returns non-JSON error page
                try:
                    res_json = await response.json()
                except (aiohttp.ContentTypeError, json.JSONDecodeError):
                    res_text = await response.text()
                    logger.warning(f"Terabox API (get-info) returned non-JSON response. Status: {response.status}, Body: {res_text[:200]}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout error getting Terabox info for {url}.")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error getting Terabox info for {url}: {e}", exc_info=False)
            return None

        if not res_json.get("list"):
            logger.warning("Terabox API response does not contain a file list.")
            return None

        download_links = []
        tasks = []
        for item in res_json.get("list", []):
            if not all(k in item for k in ["fs_id", "filename", "size"]):
                logger.warning(f"Skipping item due to missing keys: {item}")
                continue

            # Prepare data for each file and create a task
            tasks.append(
                _get_download_link(session, {
                    "shareid": res_json.get("shareid"),
                    "uk": res_json.get("uk"),
                    "sign": res_json.get("sign"),
                    "timestamp": res_json.get("timestamp"),
                    "fs_id": item["fs_id"],
                    "filename": item["filename"],
                    "size": item["size"],
                })
            )
        
        # Run all download link requests concurrently
        results = await asyncio.gather(*tasks)
        download_links = [res for res in results if res] # Filter out None results from failed requests

        return download_links if download_links else None