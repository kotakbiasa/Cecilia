from youtubesearchpython.__future__ import VideosSearch
import re
from bot import logger

async def search_youtube(query: str, limit: int = 10):
    """
    Searches YouTube for a given query.

    :param query: The search term.
    :param limit: The maximum number of results to return.
    :return: A list of video details or None if an error occurs.
    """
    try:
        videos_search = VideosSearch(query, limit=limit)
        results = await videos_search.next()

        if not results or not results.get('result'):
            return []

        search_results = []
        for video in results['result']:
            views_count = 0
            views_text = video.get('viewCount', {}).get('text')
            if views_text:
                # Use regex to extract all digits from the string, making it language-agnostic
                digits = re.findall(r'\d', views_text)
                if digits:
                    try:
                        views_count = int("".join(digits))
                    except ValueError:
                        views_count = 0 # Failsafe

            search_results.append({
                'title': video.get('title'),
                'duration': video.get('duration'),
                'link': video.get('link'),
                'thumbnail': video.get('thumbnails')[0].get('url') if video.get('thumbnails') else None,
                'artist': video.get('channel', {}).get('name'),
                'views': views_count,
            })
        return search_results
    except Exception as e:
        logger.error(f"An exception occurred during YouTube search: {e}")
        return None