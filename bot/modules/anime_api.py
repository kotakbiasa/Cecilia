import aiohttp
import asyncio
from html import escape

from bot import logger

# --- API Category Definitions ---

NEKOSBEST = {
    "husbando", "kitsune", "neko"
}
NEKOSLIFE = {
    'fox_girl', 'neko', 'waifu', 'wallpaper'
}

WAIFUPICS = {
    "loli", "megumin", "neko", "shinobu", "waifu"
}

NEKOSAPI = {
    "bikini", "black_hair", "blonde_hair", "blue_hair", "brown_hair", "catgirl", "dress",
    "exposed_girl_breasts", "flower", "girl", "horsegirl", "kemonomimi", "large_breasts",
    "medium_breasts", "mountain", "night", "pink_hair", "purple_hair", "rain", "red_hair",
    "school_uniform", "shorts", "skirt", "small_breasts", "sportswear", "tree", "usagimimi",
    "wet", "white_hair"
}

NEKOSIA = {
    "animal_ears", "blue-archive", "blue_eyes", "cat_ears", "catgirl", "cute", "fox_ears",
    "foxgirl", "girl", "pink_hair", "ribbon", "sailor_uniform", "skirt", "smile", "tail",
    "tail_with_ribbon", "thigh_high_socks", "thighs", "uniform", "vtuber",
    "white_hair", "white_thigh_high_socks", "young_girl"
}

NEKOBOT = {
    "coffee", "food", "holo", "kanna", "kemonomimi", "neko"
}

NEKOSMOE = {
    "nekosmoe", # This API provides random images, so we use a unique category name
}

WAIFUIM = {
    # Characters
    "kamisato-ayaka", "marin-kitagawa", "mori-calliope", "raiden-shogun",
    # Versatile
    "maid", "oppai", "selfies", "uniform", "waifu",
}

ANYANIME = {
    "anyanime",
}

PICRE = {
    "picre",
}


# --- API Fetcher Functions ---
# Each function returns a tuple: (list_of_media, error_string)
# list_of_media is a list of dicts, where each dict is {'url': str, 'caption': str}

async def fetch_nekos_life(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekos.life API by making multiple requests."""
    
    async def _fetch_one():
        async with session.get(f"https://nekos.life/api/v2/img/{category}") as resp:
            if resp.status == 200:
                try:
                    data = await resp.json()
                    return data.get("url")
                except aiohttp.ContentTypeError:
                    return None # API sometimes returns non-json, ignore it
        return None

    tasks = [_fetch_one() for _ in range(limit)]
    
    try:
        urls = await asyncio.gather(*tasks)
        media_list = [{"url": url, "caption": ""} for url in urls if url]
        
        return (media_list, None) if media_list else (None, f"nekos.life API did not return any images for `{category}`.")
    except Exception as e:
        return None, f"An error occurred while fetching from nekos.life: {e}"

async def fetch_nekos_best(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekos.best API."""
    params = {"amount": limit}
    async with session.get(f"https://nekos.best/api/v2/{category}", params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            results = data.get("results")
            if not results:
                return None, f"nekos.best API did not return any results for `{category}`."

            media_list = []
            for result_data in results[:limit]:
                image_url = result_data.get("url")
                if not image_url:
                    continue

                # Build caption
                caption_parts = []
                artist_name = result_data.get("artist_name")
                artist_href = result_data.get("artist_href")
                source_url = result_data.get("source_url")

                if artist_name and artist_href:
                    caption_parts.append(f"<b>Artist:</b> <a href=\"{escape(artist_href)}\">{escape(artist_name)}</a>")
                elif artist_name:
                    caption_parts.append(f"<b>Artist:</b> {escape(artist_name)}")

                if source_url:
                    caption_parts.append(f"<b>Source:</b> <a href=\"{escape(source_url)}\">Link</a>")

                caption = "\n".join(caption_parts)
                media_list.append({"url": image_url, "caption": caption})

            return (media_list, None) if media_list else (None, f"nekos.best API did not return any images for `{category}`.")
        return None, f"nekos.best API returned status `{resp.status}`."

async def fetch_waifu_pics(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from waifu.pics API."""
    wp_category = "neko" if category == "loli" else category
    if limit == 1:
        # Use the simple GET endpoint for single images
        async with session.get(f"https://api.waifu.pics/sfw/{wp_category}") as resp:
            if resp.status == 200:
                data = await resp.json()
                image_url = data.get("url")
                if image_url:
                    return ([{"url": image_url, "caption": ""}], None)
                return None, f"waifu.pics API did not return an image for `{category}`."
            return None, f"waifu.pics API returned status `{resp.status}`."
    else:
        # Use the POST endpoint for multiple images
        # The API returns up to 30 images, we'll take as many as we need up to the limit.
        async with session.post(f"https://api.waifu.pics/many/sfw/{wp_category}", json={}) as resp:
            if resp.status == 200:
                data = await resp.json()
                files = data.get("files")
                if not files:
                    return None, f"waifu.pics API did not return any images for `{category}`."
                
                media_list = [{"url": url, "caption": ""} for url in files[:limit]]
                return (media_list, None)
            return None, f"waifu.pics API returned status `{resp.status}`."

async def fetch_nekosia(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekosia.cat API."""
    params = {}
    is_multi = limit > 1
    if is_multi:
        params["count"] = limit

    if tags:
        params["additionalTags"] = ",".join(tags)

    async with session.get(f"https://api.nekosia.cat/api/v1/images/{category}", params=params) as resp:
        if resp.status != 200:
            return None, f"nekosia.cat API returned status `{resp.status}`."

        data = await resp.json()
        if not data.get("success"):
            # The API can return success: false with a message
            error_message = data.get("message", f"nekosia.cat API reported an error for `{category}`.")
            return None, error_message

        images_to_process = data.get("images") if is_multi else [data]

        # Fallback for categories that might not support `count`
        if is_multi and not images_to_process:
            logger.warning(f"nekosia.cat returned no images array for '{category}' with count={limit}. Checking for single image response.")
            # The API might have ignored 'count' and returned a single image.
            if data.get("image"):
                images_to_process = [data]

        if not images_to_process:
             return None, f"nekosia.cat API did not return any images for `{category}`."

        media_list = []
        for image_data in images_to_process[:limit]:
            # The image URL is always nested inside the 'image' key.
            # The metadata for caption is at the top level of image_data.
            image_details = image_data.get("image")
            if not image_details:
                continue
            
            image_url = image_details.get("original", {}).get("url")
            if not image_url:
                continue

            # Build caption from the rich metadata which is at the top level of image_data
            caption_parts = []
            if artist_info := image_data.get("attribution", {}).get("artist"):
                if artist_name := artist_info.get("username"):
                    if artist_profile := artist_info.get("profile"):
                        caption_parts.append(f'<b>Artist:</b> <a href="{escape(artist_profile)}">{escape(artist_name)}</a>')
                    else:
                        caption_parts.append(f'<b>Artist:</b> {escape(artist_name)}')

            if source_url := image_data.get("source", {}).get("url"):
                caption_parts.append(f'<b>Source:</b> <a href="{escape(source_url)}">Link</a>')

            caption = "\n".join(caption_parts)
            media_list.append({"url": image_url, "caption": caption})

        return (media_list, None) if media_list else (None, f"nekosia.cat API did not return any images for `{category}`.")

async def fetch_nekosapi(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekosapi.com API."""
    all_tags = []
    if category != "random":
        all_tags.append(category)
    if tags:
        all_tags.extend(tags)

    params = {
        "rating": "safe,suggestive",
        "count": limit
    }
    if all_tags:
        params["tags"] = ",".join(all_tags)

    async with session.get("https://api.nekosapi.com/v4/images/random", params=params) as resp:
        if resp.status != 200:
            if resp.status == 404:
                return None, f"nekosapi.com API found no images for `{category}`."
            return None, f"nekosapi.com API returned status `{resp.status}`."
        
        data = await resp.json()
        # The API returns a list of images directly.
        images = data
        if not images:
            return None, f"nekosapi.com API did not return any images for `{category}`."

        media_list = []
        for image_data in images[:limit]:
            if image_url := image_data.get("url"):
                media_list.append({"url": image_url, "caption": ""})

        return (media_list, None) if media_list else (None, f"nekosapi.com API did not return any images for `{category}`.")

async def fetch_pic_re(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches random images from pic.re API by making multiple requests."""

    async def _fetch_one():
        request_url = "https://pic.re/images"
        try:
            async with session.get(request_url, allow_redirects=True) as resp:
                if resp.status == 200:
                    final_url = str(resp.url)
                    source_url = resp.headers.get("image_source")
                    caption_parts = []
                    if source_url:
                        caption_parts.append(f"<b>Source:</b> <a href=\"{escape(source_url)}\">Link</a>")
                    caption = "\n".join(caption_parts)
                    return {"url": final_url, "caption": caption}
        except Exception:
            return None
        return None

    tasks = [_fetch_one() for _ in range(limit)]
    try:
        results = await asyncio.gather(*tasks)
        media_list = [res for res in results if res]
        return (media_list, None) if media_list else (None, f"pic.re API did not return any images.")
    except Exception as e:
        return None, f"An error occurred while fetching from pic.re: {e}"

async def fetch_nekobot(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekobot.xyz API by making multiple requests."""

    async def _fetch_one():
        async with session.get(f"https://nekobot.xyz/api/image?type={category}") as resp:
            if resp.status == 200:
                try:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("message")
                except aiohttp.ContentTypeError:
                    return None
        return None

    tasks = [_fetch_one() for _ in range(limit)]
    try:
        urls = await asyncio.gather(*tasks)
        media_list = [{"url": url, "caption": ""} for url in urls if url]
        return (media_list, None) if media_list else (None, f"nekobot.xyz API did not return any images for `{category}`.")
    except Exception as e:
        return None, f"An error occurred while fetching from nekobot.xyz: {e}"

async def fetch_nekos_moe(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from nekos.moe API by making multiple requests."""

    async def _fetch_one():
        params = {"nsfw": "false"}
        async with session.get("https://nekos.moe/api/v1/random/image", params=params) as resp:
            if resp.status == 200:
                try:
                    data = await resp.json()
                    if images := data.get("images"):
                        return images[0]  # Return the whole image data object
                except aiohttp.ContentTypeError:
                    return None
        return None

    tasks = [_fetch_one() for _ in range(limit)]
    try:
        results = await asyncio.gather(*tasks)
        media_list = []
        for image_data in results:
            if not image_data: continue
            if not (image_id := image_data.get("id")): continue

            image_url = f"https://nekos.moe/image/{image_id}"
            caption_parts = []
            if artist := image_data.get("artist"):
                caption_parts.append(f"<b>Artist:</b> {escape(artist)}")
            source_url = f"https://nekos.moe/post/{image_id}"
            caption_parts.append(f"<b>Source:</b> <a href=\"{source_url}\">Link</a>")
            caption = "\n".join(caption_parts)
            media_list.append({"url": image_url, "caption": caption})
        return (media_list, None) if media_list else (None, f"nekos.moe API did not return any images for `{category}`.")
    except Exception as e:
        return None, f"An error occurred while fetching from nekos.moe: {e}"

async def fetch_waifu_im(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from waifu.im API."""
    all_tags = [category]
    if tags:
        all_tags.extend(tags)

    params = {
        "included_tags": all_tags,
        "is_nsfw": "false",
        "many": "true" if limit > 1 else "false"
    }
    async with session.get("https://api.waifu.im/search", params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            images = data.get("images")
            if not images:
                return None, f"waifu.im API did not return any images for `{category}`."

            media_list = []
            for image_data in images[:limit]:
                image_url = image_data.get("url")
                if not image_url:
                    continue

                # Build caption
                caption_parts = []
                artist = image_data.get("artist")
                source = image_data.get("source")
                tags = image_data.get("tags")

                if artist and artist.get("name"):
                    artist_name = escape(artist["name"])
                    links = []
                    if pixiv_url := artist.get("pixiv"):
                        links.append(f'<a href="{escape(pixiv_url)}">Pixiv</a>')
                    if twitter_url := artist.get("twitter"):
                        links.append(f'<a href="{escape(twitter_url)}">Twitter</a>')
                    
                    if links:
                        caption_parts.append(f"<b>Artist:</b> {artist_name} ({', '.join(links)})")
                    else:
                        caption_parts.append(f"<b>Artist:</b> {artist_name}")

                if source:
                    caption_parts.append(f"<b>Source:</b> <a href=\"{escape(source)}\">Link</a>")

                if tags:
                    tag_names = [f"<code>{escape(tag.get('name'))}</code>" for tag in tags if tag.get('name')]
                    if tag_names:
                        caption_parts.append(f"<b>Tags:</b> {', '.join(tag_names)}")

                caption = "\n".join(caption_parts)
                media_list.append({"url": image_url, "caption": caption})
            
            return (media_list, None) if media_list else (None, f"waifu.im API did not return any images for `{category}`.")
        
        return None, f"waifu.im API returned status `{resp.status}`."

async def fetch_any_anime(session: aiohttp.ClientSession, category: str, limit: int = 1, tags: list[str] | None = None) -> tuple[list[dict] | None, str | None]:
    """Fetches images from any-anime-api.vercel.app API."""
    # The category is ignored as the API provides random images.
    async with session.get(f"https://any-anime-api.vercel.app/v1/anime/png/{limit}") as resp:
        if resp.status == 200:
            data = await resp.json()
            if data.get("status") == "200":
                images = data.get("images")
                if images and isinstance(images, list) and len(images) > 0:
                    # This API doesn't provide artist/source info.
                    media_list = [{"url": url, "caption": ""} for url in images]
                    return (media_list, None)
                return None, "any-anime-api did not return an image."
            else:
                error_msg = data.get("message", "any-anime-api reported an unknown error.")
                return None, error_msg
        return None, f"any-anime-api returned status `{resp.status}`."