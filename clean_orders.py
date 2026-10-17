import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
from market_orders import try_spread, make_order_buy, make_order_sell
import time
from getfairvalue import get_fp
from pprint import pprint
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
teams = team_to_game.keys()

with open("team_to_id.json", "r") as f:
    team_to_id = json.load(f)

HOST = CLOB_API
CHAIN_ID = 137
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FUNDER = os.getenv("FUNDER2")

auth_client = ClobClient(
    HOST,
    key=PRIVATE_KEY,
    chain_id=CHAIN_ID,
    signature_type=1,
    funder=FUNDER
)
creds = auth_client.derive_api_key()
auth_client.set_api_creds(creds)
# Cancel all orders
result = auth_client.cancel_all()
print("All orders cancelled!")


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
print("Fibonacci of 10:", fibonacci(10))

n = int(os.getenv("FIB_N", "10"))
for i in range(10):
    print(f"Fibonacci of {n+i}: {fibonacci(n+i)}")