"""Tests for the optional Live Tennis API rankings provider.

Every response below is a stub shaped to the published OpenAPI specification
(https://docs.livetennisapi.com/openapi.yaml). No live call is made.
"""

import httpx
import pytest

from app.config import settings
from app.exceptions import RankingsAPIError
from app.services import livetennisapi
from app.services.livetennisapi import get_livetennisapi_rankings

BASE = "https://api.livetennisapi.com/api/public/v1"


def ranking_record(player_id, rank, points, previous_rank, observed_at):
    """A RankingRecord as the spec defines it."""
    return {
        "player_id": player_id,
        "system": "atp",
        "tour": "atp",
        "rank": rank,
        "points": points,
        "previous_rank": previous_rank,
        "rating": None,
        "effective_date": "2026-08-03",
        "observed_at": observed_at,
    }


def player(player_id, name, country):
    """A Player as the spec defines it."""
    return {
        "id": player_id,
        "name": name,
        "tour": "atp",
        "country": country,
        "ranking": None,
        "ranking_points": None,
        "ranking_movement": None,
        "hand": None,
        "backhand": None,
        "birthday": None,
        "is_doubles_team": False,
    }


@pytest.fixture
def use_livetennisapi(monkeypatch):
    monkeypatch.setattr(settings, "rankings_provider", "livetennisapi")
    monkeypatch.setattr(settings, "livetennisapi_key", "test-key")
    monkeypatch.setattr(settings, "livetennisapi_base_url", BASE)


@pytest.fixture
def stub_api(monkeypatch):
    """Install a MockTransport and record every request the provider makes."""
    calls = []
    real_client = httpx.AsyncClient

    def install(handler):
        def make_client(*args, **kwargs):
            def recording(request):
                calls.append(request)
                return handler(request)

            kwargs["transport"] = httpx.MockTransport(recording)
            return real_client(*args, **kwargs)

        monkeypatch.setattr(livetennisapi.httpx, "AsyncClient", make_client)
        return calls

    return install


def default_handler(request):
    if request.url.path.endswith("/rankings"):
        return httpx.Response(
            200,
            json={
                "data": [
                    ranking_record(101, 1, 11540, 2, "2026-08-03T06:00:00Z"),
                    ranking_record(102, 2, 9200, 1, "2026-08-03T05:00:00Z"),
                ],
                "meta": {"total": 2},
            },
        )
    if request.url.path == "/api/public/v1/players/101":
        return httpx.Response(200, json=player(101, "Player One", "sui"))
    if request.url.path == "/api/public/v1/players/102":
        return httpx.Response(200, json=player(102, "Player Two", "ned"))
    return httpx.Response(404, json={"error": "not_found"})


def test_default_provider_is_unchanged():
    """Absent configuration the existing provider is used, as before."""
    from app.config import Settings

    assert Settings.model_fields["rankings_provider"].default == "rapidapi"
    assert Settings.model_fields["livetennisapi_key"].default is None


async def test_maps_ranking_table_into_the_existing_response(
    use_livetennisapi, stub_api
):
    stub_api(default_handler)

    result = await get_livetennisapi_rankings()

    assert len(result.rankings) == 2
    first = result.rankings[0]
    assert first.ranking == 1
    assert first.points == 11540
    assert first.previousRanking == 2
    assert first.rowName == "Player One"
    assert first.team.id == 101
    assert first.team.name == "Player One"
    # IOC-style code, kept out of alpha3 because it is not ISO 3166 alpha-3.
    assert first.team.country.ioc == "sui"
    assert first.team.country.alpha3 is None
    # Newest observed_at, not the time we asked.
    assert result.updatedAtTimestamp == 1785736800


async def test_sends_the_documented_query_and_bearer_token(
    use_livetennisapi, stub_api
):
    calls = stub_api(default_handler)

    await get_livetennisapi_rankings()

    rankings_call = calls[0]
    assert rankings_call.url.path == "/api/public/v1/rankings"
    assert rankings_call.url.params["system"] == "atp"
    assert rankings_call.url.params["limit"] == "50"
    assert rankings_call.headers["authorization"] == "Bearer test-key"


async def test_orders_by_rank_and_drops_unranked_records(
    use_livetennisapi, stub_api
):
    def handler(request):
        if request.url.path.endswith("/rankings"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        ranking_record(102, 2, 9200, 1, "2026-08-03T05:00:00Z"),
                        # A UTR-style record: a rating, no rank. Not a table row.
                        ranking_record(103, None, None, None, "2026-08-03T05:00:00Z"),
                        ranking_record(101, 1, 11540, 2, "2026-08-03T06:00:00Z"),
                    ]
                },
            )
        return default_handler(request)

    stub_api(handler)

    result = await get_livetennisapi_rankings()

    assert [r.ranking for r in result.rankings] == [1, 2]


async def test_a_first_time_entrant_has_no_previous_rank(
    use_livetennisapi, stub_api
):
    def handler(request):
        if request.url.path.endswith("/rankings"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        ranking_record(101, 1, 11540, None, "2026-08-03T06:00:00Z")
                    ]
                },
            )
        return default_handler(request)

    stub_api(handler)

    result = await get_livetennisapi_rankings()

    assert result.rankings[0].previousRanking is None


async def test_skips_the_player_lookup_when_the_record_embeds_the_player(
    use_livetennisapi, stub_api
):
    """Additive changes ship within v1, so tolerate an embedded player object."""

    def handler(request):
        if request.url.path.endswith("/rankings"):
            record = ranking_record(101, 1, 11540, 2, "2026-08-03T06:00:00Z")
            record["player"] = {"id": 101, "name": "Player One", "country": "sui"}
            return httpx.Response(200, json={"data": [record]})
        raise AssertionError(f"unexpected extra request: {request.url}")

    calls = stub_api(handler)

    result = await get_livetennisapi_rankings()

    assert len(calls) == 1
    assert result.rankings[0].rowName == "Player One"
    assert result.rankings[0].team.country.ioc == "sui"


async def test_falls_back_to_effective_date_when_observed_at_is_absent(
    use_livetennisapi, stub_api
):
    def handler(request):
        if request.url.path.endswith("/rankings"):
            return httpx.Response(
                200,
                json={"data": [ranking_record(101, 1, 11540, 2, None)]},
            )
        return default_handler(request)

    stub_api(handler)

    result = await get_livetennisapi_rankings()

    # 2026-08-03T00:00:00Z
    assert result.updatedAtTimestamp == 1785715200


async def test_undateable_response_is_an_error_not_a_guess(
    use_livetennisapi, stub_api
):
    def handler(request):
        if request.url.path.endswith("/rankings"):
            record = ranking_record(101, 1, 11540, 2, None)
            record["effective_date"] = None
            return httpx.Response(200, json={"data": [record]})
        return default_handler(request)

    stub_api(handler)

    with pytest.raises(RankingsAPIError):
        await get_livetennisapi_rankings()


async def test_upstream_error_becomes_the_existing_exception(
    use_livetennisapi, stub_api
):
    def handler(request):
        return httpx.Response(403, json={"error": "upgrade_required"})

    stub_api(handler)

    with pytest.raises(RankingsAPIError):
        await get_livetennisapi_rankings()


async def test_missing_key_is_reported_clearly(monkeypatch, stub_api):
    monkeypatch.setattr(settings, "rankings_provider", "livetennisapi")
    monkeypatch.setattr(settings, "livetennisapi_key", None)
    stub_api(default_handler)

    with pytest.raises(RankingsAPIError, match="LIVETENNISAPI_KEY"):
        await get_livetennisapi_rankings()
