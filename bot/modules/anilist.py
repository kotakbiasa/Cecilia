import aiohttp
from bot import logger

ANILIST_API_URL = "https://graphql.anilist.co"

# GraphQL query untuk mencari anime dan mendapatkan detailnya
ANIME_QUERY = """
query ($search: String) {
  Media (search: $search, type: ANIME, sort: SEARCH_MATCH) {
    id
    title {
      romaji
      english
      native
    }
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    status
    episodes
    duration
    format
    genres
    averageScore
    coverImage {
      extraLarge
      color
    }
    bannerImage
    siteUrl
    trailer {
      id
      site
    }
    studios(isMain: true) {
      nodes {
        name
      }
    }
    characters(sort: [ROLE, RELEVANCE, ID], perPage: 16) {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
  }
}
"""

AIRING_QUERY = """
query ($search: String) {
  Media (search: $search, type: ANIME, sort: SEARCH_MATCH) {
    id
    title {
      romaji
      english
      native
    }
    episodes
    status
    nextAiringEpisode {
       airingAt
       timeUntilAiring
       episode
    }
  }
}
"""

CHARACTER_QUERY = """
query ($search: String) {
    Character (search: $search) {
        id
        name {
            full
            native
        }
        siteUrl
        image {
            large
        }
        description(asHtml: false)
        media(sort: POPULARITY_DESC, perPage: 5) {
            nodes {
                title {
                    romaji
                    userPreferred
                }
            }
        }
    }
}
"""

MANGA_QUERY = """
query ($search: String) {
    Media (type: MANGA, search: $search, sort: SEARCH_MATCH) {
        id
        title {
            romaji
            english
            native
        }
        description(asHtml: false)
        chapters
        volumes
        format
        status
        siteUrl
        averageScore
        genres
        bannerImage
        coverImage {
            extraLarge
        }
    }
}
"""

async def _make_anilist_request(query: str, variables: dict):
    """Generic helper to make requests to the Anilist API."""
    if not variables.get("search"):
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(ANILIST_API_URL, json={"query": query, "variables": variables}) as response:
                if not response.ok:
                    logger.error(f"Permintaan API Anilist gagal dengan status {response.status}")
                    return None
                data = await response.json()
                if "errors" in data:
                    logger.error(f"Anilist API returned errors: {data['errors']}")
                    return None
                return data.get("data")
    except Exception as e:
        logger.error(f"Terjadi pengecualian saat melakukan query ke API Anilist: {e}")
        return None

async def search_anime(query_str: str):
    """
    Mencari anime di Anilist.

    :param query_str: Nama anime yang akan dicari.
    :return: Dictionary berisi data anime, atau None jika tidak ditemukan atau terjadi error.
    """
    variables = {"search": query_str}
    data = await _make_anilist_request(ANIME_QUERY, variables)
    return data.get("Media") if data else None

async def search_airing_anime(query_str: str):
    """Mencari info penayangan anime di Anilist."""
    variables = {"search": query_str}
    data = await _make_anilist_request(AIRING_QUERY, variables)
    return data.get("Media") if data else None

async def search_character(query_str: str):
    """Mencari karakter di Anilist."""
    variables = {"search": query_str}
    data = await _make_anilist_request(CHARACTER_QUERY, variables)
    return data.get("Character") if data else None

async def search_manga(query_str: str):
    """Mencari manga di Anilist."""
    variables = {"search": query_str}
    data = await _make_anilist_request(MANGA_QUERY, variables)
    return data.get("Media") if data else None