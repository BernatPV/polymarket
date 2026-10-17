import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
import time
import asyncio
import time
from functools import partial
from concurrent.futures import ThreadPoolExecutor

GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"



with open("team_data.json", "r") as f:
    team_to_id = json.load(f)

#rellevant = ["liv","rma","fcb","mnc","psg","tot","new","cfc", "atm","int","spo","juv","bvb", "ata","lev","olm"]
teams = team_to_id.keys()

client = ClobClient(CLOB_API)

# How many concurrent HTTP calls you want at once
MAX_WORKERS = 50


def _get_mid_sync(client: ClobClient, token_id: str) -> float:
    """Blocking call (sync). Returns mid as float."""
    mid = client.get_midpoint(token_id)
    return float(mid["mid"])


async def fetch_team_prices(executor, client: ClobClient, team: str):
    """
    Fetch win/draw/lose mids concurrently for one team.
    Assumes team_to_id[team] is like:
      team_to_id[team][0][0] -> token_id for win
      team_to_id[team][1][0] -> token_id for draw
      team_to_id[team][2][0] -> token_id for lose
    """
    win_id  = team_to_id[team][0][0]
    draw_id = team_to_id[team][1][0]
    lose_id = team_to_id[team][2][0]

    loop = asyncio.get_running_loop()

    win_f  = loop.run_in_executor(executor, partial(_get_mid_sync, client, win_id))
    draw_f = loop.run_in_executor(executor, partial(_get_mid_sync, client, draw_id))
    lose_f = loop.run_in_executor(executor, partial(_get_mid_sync, client, lose_id))

    win, draw, lose = await asyncio.gather(win_f, draw_f, lose_f)
    return team, win, draw, lose


async def track_price_async(duration_seconds=60, interval=1):
    print(f"Tracking price for {duration_seconds}s...\n")

    client = ClobClient(CLOB_API)

    # Thread pool for concurrent blocking HTTP calls
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        start = time.time()

        while time.time() - start < duration_seconds:
            timestamp = time.strftime("%H:%M:%S")
            print(timestamp)

            # Run all teams concurrently (each team runs 3 calls concurrently too)
            results = await asyncio.gather(
                *(fetch_team_prices(executor, client, team) for team in teams),
                return_exceptions=True
            )

            for r in results:
                if isinstance(r, Exception):
                    print("ERROR:", repr(r))
                    continue
                team, win, draw, lose = r
                print(f"team {team} win draw lose: {win} {draw} {lose}")

            # non-blocking sleep
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(track_price_async(duration_seconds=60, interval=1))