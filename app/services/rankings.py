import httpx
import logging
from app.models.player import RankingsResponse
from app.exceptions import RankingsAPIError
from httpx import HTTPStatusError
from app.config import settings

logger = logging.getLogger(__name__)


async def get_live_rankings() -> RankingsResponse:
    
    url = "https://tennisapi1.p.rapidapi.com/api/tennis/rankings/atp/live"
    headers = {
	"x-rapidapi-key": settings.rapidapi_key,
	"x-rapidapi-host": settings.rapidapi_host
    }

    logger.info("Fetching live rankings from Tennis API")

    try: 
        async with httpx.AsyncClient() as client:
        
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                api_data = RankingsResponse.model_validate(r.json())  
                logger.info(f"Successfully fetched {len(api_data.rankings)} players")

        return api_data
    
    except HTTPStatusError as e:
         logger.error(f"Tennis API HTTP error: {e.response.status_code}")
         raise RankingsAPIError(f"Tennis API returned error {e.response.status_code}")
    
    except Exception as e:
         logger.error(f"Failed to fetch rankings: {str(e)}")
         raise RankingsAPIError(f"Failed to fetch rankings: {str(e)}")

        
        
        