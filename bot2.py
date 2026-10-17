import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
from market_orders import API_CONCURRENCY, try_spread, try_spread_flat, make_order_buy, make_order_sell
import time
from getfairvalue2 import get_fp



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
#client.set_api_creds(client.create_or_derive_api_creds())
creds = auth_client.create_or_derive_api_creds()
auth_client.set_api_creds(creds)
balance = auth_client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))

print(int(balance['balance']) / 1e6)
juvkey = "6861183220591909492602735865618977161343792558093832256743373816660943808121"
ord = auth_client.create_and_post_order(
    OrderArgs(
            token_id=juvkey,
            price=0.5,
            size=5,
            side=BUY
        )
)

usdc_balance = int(balance['balance']) / 1e6
print(f"USDC Balance: ${usdc_balance:.2f}")



from eth_account import Account

acct = Account.from_key(PRIVATE_KEY)
print("derived:", acct.address)
print("funder: ", FUNDER)


client = ClobClient(CLOB_API)

done = ["ars","slp", "bay","vil", "kai","fra"]
async def mn():
    print("Starting mn()")
    await asyncio.to_thread(auth_client.cancel_all)
    p = qualify_prob
    sem = asyncio.Semaphore(API_CONCURRENCY)
    tasks = []
    for team in p:
        yes_token_id, no_token_id = team_to_id[team][0], team_to_id[team][1]
        print(team, yes_token_id)
        tasks.append(asyncio.create_task(
            try_spread_flat(auth_client, yes_token_id, no_token_id, p[team], 0.4, sem, debug=team)
        ))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print("ERROR:", repr(r))

PERIOD = 60
async def runner():
    while True:
        start = time.monotonic()
        try:
            await mn()
        except Exception as e:
            print("mn() crashed:", repr(e))

        elapsed = time.monotonic() - start
        sleep_time = max(0.0, PERIOD - elapsed)
        return
        await asyncio.sleep(sleep_time)
if __name__ == "__main__":
    asyncio.run(runner())