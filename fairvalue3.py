import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
import time
from functools import partial
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random
import numpy as np

GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


with open("game_data.json", "r") as f:
    game_to_id = json.load(f)
with open("team_data.json", "r") as f:
    team_to_game = json.load(f)

game_teams ={}
for team, game in team_to_game.items():
    if abs(game) not in game_teams:
        game_teams[abs(game)] = ['' for _ in range(2)]
    if game < 0:
        game_teams[abs(game)][1] = team
    else:
        game_teams[abs(game)][0] = team 

print(game_teams)
#rellevant = ["liv","rma","fcb","mnc","psg","tot","new","cfc", "atm","int","spo","juv","bvb", "ata","lev","olm"]
teams = team_to_game.keys()


MIDPOINT_URL = "https://clob.polymarket.com/midpoint"

# Limit concurrent requests (avoid hammering the API / getting rate-limited)
CONCURRENCY = 50


async def fetch_mid(session: aiohttp.ClientSession, token_id: str, sem: asyncio.Semaphore) -> float:
    """Fetch midpoint for one token_id."""
    async with sem:
        async with session.get(MIDPOINT_URL, params={"token_id": token_id}, timeout=aiohttp.ClientTimeout(total=10)) as r:
            r.raise_for_status()
            data = await r.json()
            return float(data["mid"])


async def fetch_team_prices(session: aiohttp.ClientSession, game: int, sem: asyncio.Semaphore):
    """
    Fetch win/draw/lose mids concurrently for one team.
    Assumes team_to_id[team][0][0] / [1][0] / [2][0] are token_ids.
    """
    win_id  = game_to_id[game][0][0]
    draw_id = game_to_id[game][1][0]
    lose_id = game_to_id[game][2][0]

    win_f  = fetch_mid(session, win_id, sem)
    draw_f = fetch_mid(session, draw_id, sem)
    lose_f = fetch_mid(session, lose_id, sem)

    win, draw, lose = await asyncio.gather(win_f, draw_f, lose_f)
    return game, win, draw, lose


with open("team_points.json", "r") as f:
    team_points = json.load(f)

pp = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
print("Current Points:")
for team, points in pp:
    print(team, points)


T = 6
HOME_ADVANTAGE_LOGIT = 0.606*T
strength = {
    "bay": 0.98, "rma": 0.97, "mnc": 0.96, "ars": 0.94, "liv": 0.93, "psg": 0.92,
    "int": 0.90, "juv": 0.88, "cfc": 0.87, "atm": 0.86, "bvb": 0.85, "fcb": 0.84,
    "lev": 0.82, "ata": 0.81, "tot": 0.80, "new": 0.78, "spo": 0.76, "ben": 0.74,
    "nap": 0.72, "psv": 0.70, "bru": 0.68, "gal": 0.66, "asm": 0.64, "fra": 0.62,
    "aja": 0.60, "oly": 0.58, "slp": 0.55, "kob": 0.53, "usg": 0.50, "vil": 0.48,
    "ath": 0.46, "olm": 0.44, "qar": 0.40, "bog": 0.38, "paf": 0.35, "kai": 0.25,
}
def headsup(team1, team2):
    s1 = strength.get(team1)
    s2 = strength.get(team2)
    diff = (s1 - s2)*T
    p = 1 / (1 + np.exp(-diff))
    return p



def compute(results):
    M = 2000
    success_by_team = {}
    for team in teams:
        success_by_team[team] = 0.0
    for k in range(M):
        
        points_by_team = team_points.copy()
        for r in results:
            game, win, draw, lose = r
            team1 = game_teams[int(game)][0]
            team2 = game_teams[int(game)][1]
            rnd = random.random()
            if rnd < win:
                points_by_team[team1] += 3
            elif rnd < win + draw:
                points_by_team[team1] += 1
                points_by_team[team2] += 1
            else:
                points_by_team[team2] += 3
        top_24 = sorted(points_by_team, key=points_by_team.get, reverse=True)[:24]
        top_8  = top_24[:8]
        second_8 = top_24[8:16]
        third_8 = top_24[16:24]
        for team in top_8:
            success_by_team[team] += 1.0/M
        for team in second_8:
            success_by_team[team] += 0.6/M
        for team in third_8:
            success_by_team[team] += 0.4/M
        
    for team in success_by_team:
        success_by_team[team] = round(success_by_team[team], 2)
    print(success_by_team)
    p = sorted(success_by_team, key=success_by_team.get, reverse=True)
    print("RANKINGS")
    for team in p:
        print(team, success_by_team[team])

async def track_price_async(duration_seconds=30, interval=1):
    print(f"Tracking price for {duration_seconds}s...\n")
    start_time = time.time()

    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration_seconds:
            timestamp = time.strftime("%H:%M:%S")
            print(timestamp)

            results = await asyncio.gather(
                *(fetch_team_prices(session, game, sem) for game in game_to_id.keys()),
                return_exceptions=True
            )

            for r in results:
                if isinstance(r, Exception):
                    print("ERROR:", repr(r))
                    continue
                game, win, draw, lose = r
                print(f"game {game_teams[int(game)][0]} {game_teams[int(game)][1]} win draw lose: {win} {draw} {lose}")
                p = headsup(game_teams[int(game)][0], game_teams[int(game)][1])
                p = round(p,2)
                #print(round(win+0.5*draw,2), round(lose+0.5*draw,2))
                #print(p,1-p)
            print("Time to compute odds")

            compute(results)

            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(track_price_async(duration_seconds=30, interval=20))