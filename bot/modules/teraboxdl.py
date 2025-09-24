import asyncio
import aiohttp
import json
import time
from bot import logger

API_BASE = "https://www.terabox.com"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "DNT": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": f"{API_BASE}/",
}

async def terabox_download(url: str, pwd: str = "") -> list[dict] | None:
    """
    Converts a Terabox share URL into a direct download link by simulating browser API calls.

    :param url: The Terabox share URL (e.g., https://terabox.com/s/...).
    :param pwd: The password for the link, if any.
    :return: A list of dictionaries containing file info, or None on failure.
    """
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            # 1. Get the initial page to extract shorturl and cookies
            async with session.get(url) as resp:
                if not resp.ok:
                    logger.error(f"Initial request to {url} failed with status {resp.status}")
                    return None
                
                # Extract shorturl from the final redirected URL
                final_url = str(resp.url)
                try:
                    shorturl = final_url.split('?surl=')[-1]
                except IndexError:
                    logger.error(f"Could not find 'surl' in the final URL: {final_url}")
                    return None

            # 2. Get file list information
            params = {
                "app_id": "250528",
                "shorturl": shorturl,
                "root": "1",
            }
            list_url = f"{API_BASE}/api/share/list"
            async with session.get(list_url, params=params) as resp:
                if not resp.ok:
                    logger.error(f"API request to {list_url} failed with status {resp.status}")
                    return None
                
                # Allow parsing JSON even if the content-type is text/html
                data = await resp.json(content_type=None)
                if data.get("errno") != 0:
                    logger.error(f"API error from share/list: {data.get('errmsg', 'Unknown error')}")
                    return None
                
                file_list = data.get("list")
                if not file_list:
                    logger.warning("API response from share/list contains no files.")
                    return None

            # 3. Get download parameters (sign, timestamp, etc.)
            share_info = data
            params = {
                "app_id": "250528",
                "shorturl": shorturl,
                "web": "1",
                "auth": "1",
                "encrypt": "1"
            }
            verify_url = f"{API_BASE}/share/verify"
            async with session.get(verify_url, params=params) as resp:
                if not resp.ok:
                    logger.error(f"API request to {verify_url} failed with status {resp.status}")
                    return None
                
                # Allow parsing JSON even if the content-type is text/html
                verify_data = await resp.json(content_type=None)
                if verify_data.get("errno") != 0:
                    logger.error(f"API error from share/verify: {verify_data.get('errmsg', 'Unknown error')}")
                    return None
                
                randsk = verify_data.get("randsk")

            # 4. Get the actual download link for each file
            download_links = []
            for item in file_list:
                if item.get("isdir") == "1":
                    continue # Skip directories for now

                fs_id = item.get("fs_id")
                params = {
                    "app_id": "250528",
                    "web": "1",
                    "auth": "1",
                    "encrypt": "1",
                    "shareid": share_info.get("shareid"),
                    "uk": share_info.get("uk"),
                    "sign": share_info.get("sign"),
                    "timestamp": share_info.get("timestamp"),
                    "primaryid": item.get("fs_id"),
                    "fid_list": f"[{fs_id}]",
                    "extra": '{"sekey":"' + randsk + '"}',
                }
                
                download_api_url = f"{API_BASE}/api/share/download"
                async with session.get(download_api_url, params=params) as resp:
                    if not resp.ok:
                        logger.warning(f"Download link request for fs_id {fs_id} failed with status {resp.status}")
                        continue
                    
                    # Allow parsing JSON even if the content-type is text/html
                    download_data = await resp.json(content_type=None)
                    if download_data.get("errno") != 0:
                        logger.warning(f"API error from share/download for fs_id {fs_id}: {download_data.get('errmsg')}")
                        continue
                    
                    dlink_info = download_data.get("dlink")
                    if not dlink_info:
                        logger.warning(f"No 'dlink' in response for fs_id {fs_id}")
                        continue

                    # The actual download URL is in the 'dlink' field.
                    # The API might return a direct link or a link that needs another redirect.
                    # We will use the direct link and let the downloader handle any redirects.
                    download_url = dlink_info

                    size_in_mb = int(item.get('size', 0)) / (1024 * 1024)
                    download_links.append({
                        "filename": item.get("server_filename"),
                        "link": download_url,
                        "size_mb": round(size_in_mb, 2)
                    })

            return download_links if download_links else None

    except Exception as e:
        logger.error(f"An unexpected error occurred in terabox_download: {e}", exc_info=True)
        return None