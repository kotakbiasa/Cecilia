import aiohttp
from app import logger
from app.utils.database import MemoryDB

async def shortener_url(url):
    shrinkme_api = MemoryDB.bot_data.get("shrinkme_api")
    if not shrinkme_api:
        logger.error("shrinkme_api not found!")
        return
    
    api_url = "https://shrinkme.io/api"
    params = {
        "api": shrinkme_api,
        "url": url
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if not response.ok:
                    return
                
                data = await response.json()
                return data["shortenedUrl"]
    except Exception as e:
        logger.error(e)
