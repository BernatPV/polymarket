import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json


GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

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
creds = auth_client.derive_api_key()
auth_client.set_api_creds(creds)
balance = auth_client.get_balance_allowance(BalanceAllowanceParams(asset_type=AssetType.COLLATERAL))
usdc_balance = int(balance['balance']) / 1e6
print(f"USDC Balance: ${usdc_balance:.2f}")

def get_user_positions(wallet_address):
    """Get a user's current positions."""
    url = f"{DATA_API}/positions"
    params = {"user": wallet_address}
    response = requests.get(url, params=params)
    return response.json()

def f(s):
    if s=='YES':
        return 1
    elif s=='NO':
        return -1
    raise ValueError("Unknown outcome")

import aiohttp


address = FUNDER
positions = get_user_positions(address)
print(len(positions))
for p in positions:
    if(p["eventId"]!= '45936'):
        continue
    print(p['size'], p['avgPrice'], p['conditionId'], p['outcome'], p['mergeable'])
print(positions[0].keys())