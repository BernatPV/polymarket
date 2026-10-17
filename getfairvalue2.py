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
from getfairvalue import compute
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

#rellevant = ["liv","rma","fcb","mnc","psg","tot","new","cfc", "atm","int","spo","juv","bvb", "ata","lev","olm"]
teams = team_to_game.keys()


MIDPOINT_URL = "https://clob.polymarket.com/midpoint"

# Limit concurrent requests (avoid hammering the API / getting rate-limited)
CONCURRENCY = 30



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
    z1 = norm.ppf(prob_cum_lose)
    z2 = norm.ppf(prob_cum_draw_lose)
    sigma = 1.0 / (z2 - z1)
    mu = 0.5 - (z2 * sigma)

    return (mu,sigma)

qualify_prob = {
    "gal": 0.268,
    "juv": 0.732,

    "ben": 0.208,
    "rma": 0.792,

    "bvb": 0.467,
    "ata": 0.533,

    "asm": 0.119,
    "psg": 0.881,

    "qar": 0.074,
    "new": 0.926,

    "bog": 0.172,
    "int": 0.828,

    "bru": 0.217,
    "atm": 0.783,

    "oly": 0.442,
    "lev": 0.558,
}
order = ["gal","juv","ben","rma","bvb","ata","asm","psg","qar","new","bog","int","bru","atm","oly","lev"]
matches = [
    ("gal", "juv", 0.277, 0.285, 0.438),
    ("ben", "rma", 0.222, 0.274, 0.504),
    ("bvb", "ata", 0.451, 0.271, 0.278),
    ("asm", "psg", 0.163, 0.240, 0.597),
    ("qar", "new", 0.134, 0.197, 0.669),
    ("bog", "int", 0.198, 0.248, 0.554),
    ("bru", "atm", 0.240, 0.267, 0.493),
    ("oly", "lev", 0.419, 0.277, 0.304),
]
def goal_diff_sigma(p_win):
    p_lose = 1-p_win
    z2 = norm.ppf(p_lose)
    #mu = 0.5 - (z2 * (1.4+ abs(mu)/8))
    if(p_win>0.5):
        mu = (4 - 11.2*z2) / (8 + z2)
    else:
        mu = (4 - 11.2*z2) / (8 - z2)
    return (mu,(1.4+ mu/8))
def get_fp():

   for i in range(8):
        print("---- Match:", matches[i][0], "vs", matches[i][1],"----")
        win = matches[i][2]/(matches[i][2]+matches[i][4])
        lose = matches[i][4]/(matches[i][2]+matches[i][4])
        logit = np.log(win/lose)/T-HOME_ADVANTAGE_LOGIT

        print(logit, strength[matches[i][0]]-strength[matches[i][1]])
        p_win1 = 1 / (1 + np.exp(- (logit + HOME_ADVANTAGE_LOGIT) * T))
        p_win2 = 1 / (1 + np.exp(- (logit - HOME_ADVANTAGE_LOGIT) * T))
        print(matches[i][0], matches[i][1], p_win1, p_win2)
        mu1,sigma1 = goal_diff_sigma(p_win1)
        mu2,sigma2 = goal_diff_sigma(p_win2)
        print(mu1,mu2,sigma1,sigma2)
        winprob = 0
        for k in range(1000):
            gd1 = np.random.normal(loc=mu1, scale=sigma1)
            gd2 = np.random.normal(loc=mu2, scale=sigma2)
            if(gd1+gd2>0):
                winprob+=1/1000
        print("Fair price:", winprob)
        print("Fair price3:", 1 / (1 + np.exp(- (strength[matches[i][0]]-strength[matches[i][1]]) * T)))
        print("Fairprice2:", qualify_prob[matches[i][0]])


if __name__ == "__main__":
    get_fp()