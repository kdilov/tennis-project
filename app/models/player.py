from pydantic import BaseModel

class Country(BaseModel):
    alpha2 : str | None = None
    alpha3 : str | None = None
    name : str | None = None

class Team(BaseModel):
    id : int
    name : str
    country : Country

class PlayerRanking(BaseModel):
    ranking : int
    points : int
    previousRanking : int
    rowName: str
    team : Team

class RankingsResponse(BaseModel):
    rankings : list[PlayerRanking]    
    updatedAtTimestamp : int
    
