import asyncio
import aiohttp
import json
import urllib.parse
from bot import logger

API_URL_TEMPLATE = "https://teradlrobot.cheemsbackup.workers.dev/?url={}"

async def terabox_download(url: str, pwd: str = "") -> list[dict] | None:
    """
    Converts a Terabox share URL into a direct download link using the new API endpoint.

    :param url: The Terabox share URL (e.g., https://terabox.com/s/...).
    :param pwd: The password for the link, if any.
    :return: A list of dictionaries containing file info, or None on failure.
    """
    if not url:
        logger.warning("Terabox URL was not provided.")
        return None

    # The new API takes the full URL as a parameter.
    encoded_url = urllib.parse.quote(url)
    final_url = API_URL_TEMPLATE.format(encoded_url)

    # We will make a HEAD request first to get file metadata without downloading the whole file.
    async with aiohttp.ClientSession() as session:
        try:
            # Use a HEAD request to get headers
            async with session.head(final_url, timeout=60, allow_redirects=True) as response:
                if not response.ok:
                    logger.error(f"Terabox API HEAD request failed with status: {response.status} for URL: {final_url}")
                    return None

                # --- Extract file info from headers ---
                content_disposition = response.headers.get("Content-Disposition")
                filename = "Unknown File"
                if content_disposition:
                    # Extract filename from 'Content-Disposition' header
                    filename_parts = [part for part in content_disposition.split(';') if 'filename=' in part]
                    if filename_parts:
                        # e.g., filename="example.mp4"
                        filename = filename_parts[0].split('=')[1].strip('"')

                content_length = response.headers.get("Content-Length")
                size_mb = 0
                if content_length and content_length.isdigit():
                    size_mb = round(int(content_length) / (1024 * 1024), 2)

                # Since this API seems to handle one file at a time, we return a list with one item.
                download_info = {
                    "filename": filename,
                    "link": final_url,  # The API URL itself is the download link
                    "size_mb": size_mb
                }

                return [download_info]

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error for Terabox API: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout error while getting Terabox info for {url}.")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error while getting Terabox info for {url}: {e}", exc_info=False)
            return None