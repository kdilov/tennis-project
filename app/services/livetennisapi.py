"""Optional alternative rankings provider: Live Tennis API.

This module is inert unless `RANKINGS_PROVIDER=livetennisapi` is set. The
default provider is unchanged.

It builds the same `RankingsResponse` the existing provider returns, from two
documented endpoints:

  GET /rankings?system=atp&limit=N   -> the published rank-ordered table (PRO)
  GET /players/{id}                  -> name and country for one player (FREE)

The ranking table is keyed by `player_id`; a ranking record carries rank,
points and previous rank but not the player's name, so names are resolved with
a bounded set of concurrent per-player lookups. If a future response already
embeds the player object, that lookup is skipped for those records.

Reference: https://docs.livetennisapi.com/openapi.yaml
"""

import asyncio
import logging
from datetime import date, datetime, timezone

import httpx
from httpx import HTTPStatusError

from app.config import settings
from app.exceptions import RankingsAPIError
from app.models.player import Country, PlayerRanking, RankingsResponse, Team

logger = logging.getLogger(__name__)

# Concurrency for the per-player name lookups. The published rate limits start
# at 30 requests/minute, so this stays deliberately modest.
_NAME_LOOKUP_CONCURRENCY = 5


def _auth_headers() -> dict[str, str]:
    if not settings.livetennisapi_key:
        raise RankingsAPIError(
            "RANKINGS_PROVIDER=livetennisapi but LIVETENNISAPI_KEY is not set"
        )
    return {"Authorization": f"Bearer {settings.livetennisapi_key}"}


def _embedded_name(record: dict) -> str | None:
    """Return the player name if the ranking record already carries one."""
    player = record.get("player")
    if isinstance(player, dict) and player.get("name"):
        return player["name"]
    return record.get("player_name")


def _embedded_country(record: dict) -> str | None:
    player = record.get("player")
    if isinstance(player, dict):
        return player.get("country")
    return None


def _updated_at(records: list[dict]) -> int:
    """Newest instant the source vouches for, as a Unix timestamp.

    Prefers `observed_at` (an exact instant). Falls back to `effective_date`,
    the publication week the record took effect, read as UTC midnight. The
    fetch time is deliberately not used: it would describe when we asked, not
    when the data changed.
    """
    newest: datetime | None = None
    for record in records:
        observed = record.get("observed_at")
        if not observed:
            continue
        try:
            parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if newest is None or parsed > newest:
            newest = parsed
    if newest is None:
        for record in records:
            effective = record.get("effective_date")
            if not effective:
                continue
            try:
                parsed_date = date.fromisoformat(effective)
            except (ValueError, TypeError):
                continue
            parsed = datetime.combine(parsed_date, datetime.min.time(), timezone.utc)
            if newest is None or parsed > newest:
                newest = parsed
    if newest is None:
        raise RankingsAPIError(
            "Ranking records carried neither observed_at nor effective_date, "
            "so the response cannot be dated"
        )
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=timezone.utc)
    return int(newest.timestamp())


async def _fetch_player(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    player_id: int,
) -> tuple[int, dict]:
    async with semaphore:
        response = await client.get(
            f"{settings.livetennisapi_base_url}/players/{player_id}",
            headers=_auth_headers(),
        )
        response.raise_for_status()
        return player_id, response.json()


async def get_livetennisapi_rankings() -> RankingsResponse:
    """Fetch the current published ranking table and shape it like the default."""
    system = settings.livetennisapi_system
    limit = settings.livetennisapi_limit

    logger.info("Fetching %s rankings (top %s) from Live Tennis API", system, limit)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.livetennisapi_base_url}/rankings",
                params={"system": system, "limit": limit},
                headers=_auth_headers(),
            )
            response.raise_for_status()
            payload = response.json()

            records = [
                record
                for record in payload.get("data", [])
                if record.get("rank") is not None
            ]
            records.sort(key=lambda record: record["rank"])

            # Names are not part of a ranking record, so resolve the ones we
            # do not already have.
            unresolved = [
                record["player_id"]
                for record in records
                if _embedded_name(record) is None and record.get("player_id")
            ]
            players: dict[int, dict] = {}
            if unresolved:
                semaphore = asyncio.Semaphore(_NAME_LOOKUP_CONCURRENCY)
                results = await asyncio.gather(
                    *(
                        _fetch_player(client, semaphore, player_id)
                        for player_id in unresolved
                    )
                )
                players = dict(results)

        rankings = []
        for record in records:
            player_id = record.get("player_id")
            player = players.get(player_id, {})
            name = _embedded_name(record) or player.get("name")
            if not name:
                # Without a name the row cannot be rendered. Skipping it is the
                # only honest option; inventing a placeholder is not.
                logger.warning(
                    "Skipping rank %s: no name available for player %s",
                    record.get("rank"),
                    player_id,
                )
                continue
            country_code = _embedded_country(record) or player.get("country")
            rankings.append(
                PlayerRanking(
                    ranking=record["rank"],
                    points=record.get("points"),
                    previousRanking=record.get("previous_rank"),
                    rowName=name,
                    team=Team(
                        id=player_id,
                        name=name,
                        country=Country(ioc=country_code),
                    ),
                )
            )

        logger.info("Successfully fetched %s players", len(rankings))
        return RankingsResponse(
            rankings=rankings,
            updatedAtTimestamp=_updated_at(records),
        )

    except RankingsAPIError:
        raise
    except HTTPStatusError as e:
        logger.error("Live Tennis API HTTP error: %s", e.response.status_code)
        raise RankingsAPIError(
            f"Live Tennis API returned error {e.response.status_code}"
        )
    except Exception as e:
        logger.error("Failed to fetch rankings: %s", str(e))
        raise RankingsAPIError(f"Failed to fetch rankings: {str(e)}")
