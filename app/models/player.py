from pydantic import BaseModel

class Country(BaseModel):
    alpha2 : str | None = None
    alpha3 : str | None = None
    name : str | None = None
    # IOC-style lowercase three-letter code, e.g. "sui", "ned", "gre".
    # Kept separate from alpha3 on purpose: IOC codes are not ISO 3166 alpha-3
    # ("ned" vs "nld"). Only populated by the optional livetennisapi provider.
    ioc : str | None = None

class Team(BaseModel):
    id : int
    name : str
    country : Country

class PlayerRanking(BaseModel):
    ranking : int
    # points and previousRanking are optional because a source may legitimately
    # not have them: a player entering the table for the first time has no
    # previous rank. The default provider always supplies both, so its
    # responses are unchanged.
    points : int | None = None
    previousRanking : int | None = None
    rowName: str
    team : Team

class RankingsResponse(BaseModel):
    rankings : list[PlayerRanking]    
    updatedAtTimestamp : int
    
