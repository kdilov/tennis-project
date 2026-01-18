from app.models.player import PlayerRanking

def test_player_ranking_parses_correctly():

    sample_data = {
        "ranking": 1,
        "points": 12050,
        "previousRanking": 2,
        "rowName": "Test Player",
        "team": {
            "id": 12345,
            "name": "Test Player Full Name",
            "country": {
                "alpha2": "GB",
                "alpha3": "GBR",
                "name": "United Kingdom"
            }
        }
    }
     
    player = PlayerRanking.model_validate(sample_data)  

    assert player.ranking == 1, "ranking error"
    assert player.points == 12050, "points error"
    assert player.previousRanking == 2, "previousRanking error"
    assert player.team.name == "Test Player Full Name", "team name error"
    assert player.team.country.name == "United Kingdom", "team country name error"
