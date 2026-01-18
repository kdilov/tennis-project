from fastapi import APIRouter
from app.services.rankings import get_live_rankings
from app.models.player import RankingsResponse


router = APIRouter()

@router.get("/rankings")
async def get_rankings():
    data = await get_live_rankings()
    return data


