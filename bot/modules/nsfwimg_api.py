import aiohttp
import asyncio
from html import escape

# --- API Category Definitions ---

NEKOBOT_NSFW = {
    "anal", "ass", "boobs", "gah", "gonewild", "hanal", "hass", "hboobs",
    "hentai", "hkitsune", "hmidriff", "hneko", "hthigh",
    "paizuri", "pgif", "pussy", "tentacle", "thigh", "yaoi",
}

WAIFUIM_NSFW = {
    "ass", "ecchi", "ero", "hentai", "milf", "oral", "paizuri", "pussy"
}

WAIFUPICS_NSFW = {
    "blowjob", "neko", "trap", "waifu"
}

NEKOSAPI_NSFW = {
    "bikini", "dick", "dress", "exposed_anus", "exposed_girl_breasts", "girl",
    "kissing", "large_breasts", "medium_breasts", "nekosapi-nsfw", "pussy",
    "small_breasts", "threesome", "wet",
}

# --- API Fetcher Functions ---

async def fetch_nekobot_nsfw(session: aiohttp.ClientSession, category: str, limit: int = 1) -> tuple[list[dict] | None, str | None]:
    """Fetches NSFW images from nekobot.xyz API by making multiple requests."""

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
        return (media_list, None) if media_list else (None, f"nekobot.xyz API did not return any NSFW images for `{category}`.")
    except Exception as e:
        return None, f"An error occurred while fetching from nekobot.xyz: {e}"

async def fetch_waifu_im_nsfw(session: aiohttp.ClientSession, category: str, limit: int = 1) -> tuple[list[dict] | None, str | None]:
    """Fetches NSFW images from waifu.im API."""
    params = {
        "included_tags": category,
        "is_nsfw": "true",
        "many": "true" if limit > 1 else "false"
    }
    async with session.get("https://api.waifu.im/search", params=params) as resp:
        if resp.status == 200:
            data = await resp.json()
            images = data.get("images")
            if not images:
                return None, f"waifu.im API did not return any NSFW images for `{category}`."

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
            
            return (media_list, None) if media_list else (None, f"waifu.im API did not return any NSFW images for `{category}`.")
        
        return None, f"waifu.im API returned status `{resp.status}`."

async def fetch_waifu_pics_nsfw(session: aiohttp.ClientSession, category: str, limit: int = 1) -> tuple[list[dict] | None, str | None]:
    """Fetches NSFW images from waifu.pics API."""
    if limit == 1:
        async with session.get(f"https://api.waifu.pics/nsfw/{category}") as resp:
            if resp.status == 200:
                data = await resp.json()
                image_url = data.get("url")
                if image_url:
                    return ([{"url": image_url, "caption": ""}], None)
                return None, f"waifu.pics API did not return an NSFW image for `{category}`."
            return None, f"waifu.pics API returned status `{resp.status}`."
    else:
        async with session.post(f"https://api.waifu.pics/many/nsfw/{category}", json={}) as resp:
            if resp.status == 200:
                data = await resp.json()
                files = data.get("files")
                if not files:
                    return None, f"waifu.pics API did not return any NSFW images for `{category}`."
                
                media_list = [{"url": url, "caption": ""} for url in files[:limit]]
                return (media_list, None)
            return None, f"waifu.pics API returned status `{resp.status}`."

async def fetch_nekosapi_nsfw(session: aiohttp.ClientSession, category: str, limit: int = 1) -> tuple[list[dict] | None, str | None]:
    """Fetches NSFW images from nekosapi.com API."""
    params = {
        "rating": "borderline,explicit",
        "count": limit
    }
    # If a specific category is used, add it to tags. Otherwise, it's random.
    if category != "nekosapi-nsfw":
        params["tags"] = category
 
    async with session.get("https://api.nekosapi.com/v4/images/random", params=params) as resp:
        if resp.status != 200:
            # The API might return 404 if no image matches the tags.
            if resp.status == 404:
                return None, f"nekosapi.com API found no images for `{category}` with the specified rating."
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