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
from scipy.stats import norm

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
CONCURRENCY = 30


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




T = 6
HOME_ADVANTAGE_LOGIT = 0.087

strength = {
    "mnc": 0.29,
    "ars": 0.278,
    "bay": 0.26,
    "psg": 0.225,
    "fcb": 0.207,
    "int": 0.196,
    "liv": 0.195,
    "cfc": 0.184,
    "rma": 0.158,
    "new": 0.146,
    "atm": 0.108,
    "juv": 0.101,
    "bvb": 0.087,
    "tot": 0.032,
    "nap": 0.031,
    "ata": 0.012,
    "spo": 0.008,
    "lev": 0.0,
    "olm": -0.001,
    "vil": -0.014,
    "psv": -0.04,
    "ben": -0.042,
    "gal": -0.067,
    "bog": -0.068,
    "asm": -0.07,
    "ath": -0.075,
    "oly": -0.083,
    "bru": -0.11,
    "fra": -0.133,
    "usg": -0.138,
    "kob": -0.175,
    "slp": -0.207,
    "aja": -0.232,
    "qar": -0.276,
    "paf": -0.345,
    "kai": -0.443,
}

def headsup_home(team1, team2):
    s1 = strength.get(team1) + HOME_ADVANTAGE_LOGIT
    s2 = strength.get(team2)
    diff = (s1 - s2) * T
    p = 1 / (1 + np.exp(-diff))
    return p
def headsup(team1, team2):
    s1 = strength.get(team1)
    s2 = strength.get(team2)
    diff = (s1 - s2) * T
    p = 1 / (1 + np.exp(-diff))
    return p
def approx_ppf(p):
    # valid for 0 < p < 1
    t = np.sqrt(-2.0 * np.log(p if p < 0.5 else 1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308

    x = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
    return -x if p < 0.5 else x

def get_goal_diff(p_win, p_draw, p_lose):
    # Draw boundaries: [-0.5, +0.5]
    p_lose = 1-p_win - p_draw
    prob_cum_lose = p_lose
    
    prob_cum_draw_lose = p_lose + p_draw
    z1 = approx_ppf(prob_cum_lose)
    z2 = approx_ppf(prob_cum_draw_lose)
    sigma = 1.0 / (z2 - z1)
    mu = 0.5 - (z2 * sigma)

    return (mu,sigma)


def compute(results):
    M = 1000
    success_by_team = {}
    for team in teams:
        success_by_team[team] = 0.0

    musigma = {}
    for r in results:
        musigma[r[0]] = get_goal_diff(r[1], r[2], r[3])
    for k in range(M):
        points_by_team = team_points.copy()
        for r in results:
            game, win, draw, lose = r
            team1 = game_teams[int(game)][0]
            team2 = game_teams[int(game)][1]
            mu,sigma = musigma[game]
            gd = np.random.normal(loc=mu, scale=sigma)
            if(gd<-0.5):
                points_by_team[team2] += 3
            elif(gd> 0.5):
                points_by_team[team1] += 3
            else:
                points_by_team[team1] += 1
                points_by_team[team2] += 1
            points_by_team[team1] += 0.01*gd
            points_by_team[team2] += 0.01*(-gd)
            """rnd = random.random()
            if rnd < win:
                points_by_team[team1] += 3
                np.random.normal(loc=0.0, scale=1.2)
            elif rnd < win + draw:
                points_by_team[team1] += 1
                points_by_team[team2] += 1
            else:
                points_by_team[team2] += 3
                """
        top_24 = sorted(points_by_team, key=points_by_team.get, reverse=True)[:24]
        top_8  = top_24[:8]
        second_8 = list(top_24[8:16])
        third_8 = list(top_24[16:24])
        random.shuffle(third_8)
        for team in top_8:
            success_by_team[team] += 1.0/M
        for i in range(8):
            p = headsup(second_8[i], third_8[i])
            success_by_team[second_8[i]] += p/M
            success_by_team[third_8[i]] += (1-p)/M
        #for team in second_8:
        #    success_by_team[team] += 0.6/M
        #for team in third_8:
        #    success_by_team[team] += 0.4/M
    
    # p = sorted(success_by_team, key=success_by_team.get, reverse=True)
    #print("RANKINGS")
    #for team in p:
    #    print(team, success_by_team[team])
    return success_by_team
   

async def get_fp():

    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:

        results = await asyncio.gather(
            *(fetch_team_prices(session, game, sem) for game in game_to_id.keys()),
            return_exceptions=True
        )
        #print("Time to compute odds")
        success_by_team = compute(results)
        return success_by_team


if __name__ == "__main__":
    asyncio.run(get_fp())