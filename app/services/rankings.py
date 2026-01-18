import httpx
from app.models.player import RankingsResponse
from app.config import settings



async def get_live_rankings() -> RankingsResponse:
    
    url = "https://tennisapi1.p.rapidapi.com/api/tennis/rankings/atp/live"
    headers = {
	"x-rapidapi-key": settings.rapidapi_key,
	"x-rapidapi-host": settings.rapidapi_host
    }

    async with httpx.AsyncClient() as client:
       
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            api_data = RankingsResponse.model_validate(r.json())  
        

    return api_data

        
        
        