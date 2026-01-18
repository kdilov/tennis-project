import asyncio
from app.services.rankings import get_live_rankings

async def main():
    print("Fetching rankings...")
    data = await get_live_rankings()
    
    print(f"Got {len(data.rankings)} players")
    print(f"Last updated: {data.updatedAtTimestamp}")
    print()
    print("Top 5:")
    for player in data.rankings[:10]:
        print(f"  {player.ranking}. {player.rowName} - {player.points} pts")


asyncio.run(main())