import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType,PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY, SELL
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType

from urllib.parse import urlparse
import requests
import json
import numpy as np
import aiohttp

GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"
HOST = CLOB_API
CHAIN_ID = 137
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FUNDER = os.getenv("FUNDER2")



def logit(p):
    if p<=0.001:
        p=0.001
    if p>=0.999:
        p=0.999
    return np.log(p / (1 - p))

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def quote(p, delta, POS=0):
    delta1 = delta 
    delta2 = delta
    ld = 1.15
    if(POS>3):
        delta1*=ld
        delta2/=ld
    if(POS>8):
        delta1*=ld
        delta2/=ld
    if(POS>13):
        delta1*=ld*ld
        delta2/=ld*ld
    if(POS>18):
        delta1*=ld*ld
        delta2/=ld*ld
    if(POS<-3):
        delta1/=ld
        delta2*=ld
    if(POS<-8):
        delta1/=ld
        delta2*=ld
    if(POS<-13):
        delta1/=ld*ld
        delta2*=ld*ld
    if(POS<-18):
        delta2*=ld*ld
        delta1/=ld*ld
    l = logit(p)
    bid = sigmoid(l - delta1)
    ask = sigmoid(l + delta2)
    return bid, ask

# Tune these
API_CONCURRENCY = 30

async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)

async def make_order_buy(auth_client, yes_token_id, no_token_id, price, size,sem: asyncio.Semaphore):
    async with sem:
        limit_buy = OrderArgs(
            token_id=yes_token_id,
            price=price,
            size=size,
            side=BUY
        )
        signed_order = auth_client.create_order(limit_buy, PartialCreateOrderOptions(
    neg_risk=False
))

        # Execute market order
        response = auth_client.post_order(signed_order, OrderType.GTC)
        print("Market order executed!")
        print(response)

async def make_order_sell(auth_client, yes_token_id, no_token_id, price, size,sem: asyncio.Semaphore):
    async with sem:
        limit_buy = OrderArgs(
            token_id=no_token_id,
            price=1.0-price,
            size=size,
            side=BUY
        )
        signed_order = auth_client.create_order(limit_buy, PartialCreateOrderOptions(
    neg_risk=False
))

        # Execute market order
        response = auth_client.post_order(signed_order, OrderType.GTC)
        print("Market order executed!")
        print(response)

async def get_position_size(session: aiohttp.ClientSession, wallet: str, token_id: str) -> float:
    url = f"https://data-api.polymarket.com/positions?user={wallet}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()

    for pos in data:
        if pos["asset"] == token_id:
            return float(pos["size"])
    return 0.0

def get_token_position(client, token_id: str) -> float:
    res = client.get_balance_allowance(
        BalanceAllowanceParams(
            asset_type=AssetType.CONDITIONAL,
            token_id=token_id
        )
    )
    return float(res['balance'])/1e6
async def get_best_bid_ask(
    session: aiohttp.ClientSession,
    token_id: str
):
    url = f"{CLOB_API}/book"
    params = {"token_id": token_id}  

    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        book = await resp.json()

    bids = book.get("bids", [])
    asks = book.get("asks", [])

    # docs show bids/asks as arrays of levels with "price" and "size" strings :contentReference[oaicite:2]{index=2}
    best_bid = max(bids, key=lambda x: float(x["price"])) if bids else None
    best_ask = min(asks, key=lambda x: float(x["price"])) if asks else None

    best_bid_price = float(best_bid["price"]) if best_bid else None
    best_bid_size  = float(best_bid["size"])  if best_bid else None
    best_ask_price = float(best_ask["price"]) if best_ask else None
    best_ask_size  = float(best_ask["size"])  if best_ask else None

    return best_bid_price, best_bid_size, best_ask_price, best_ask_size

def quote_flat(p, delta, POS=0):
    bid = p - delta/2 + delta*(POS/100)
    ask = p + delta/2 + delta*(POS/100)
    if bid>p or ask<p:
        bid = p-delta
        ask = p+delta
        print("WEIRD POSITION ADJUSTMENT")
    return bid, ask
async def try_spread_flat(auth_client, yes_token_id, no_token_id, fairvalue, spread, sem: asyncio.Semaphore, debug=None):
    #print("attempting to place order...")



    pyes = get_token_position(auth_client, yes_token_id)
    pno = get_token_position(auth_client, no_token_id)
    print(debug, pyes, pno)
    POS = pyes - pno
    async with aiohttp.ClientSession() as session:
        bestbid, bestbidsz, bestask, bestasksz = await get_best_bid_ask(
            session, yes_token_id)

    if abs(POS)>31:
        print(f"Position too large: {POS}, SOMETHING VERY WRONG")
        return
    
    buy_price, sell_price = quote_flat(fairvalue, spread,POS)
    buy_price = round(buy_price,2)
    sell_price = round(sell_price,2)
    sz = 5
    print(debug, sell_price, buy_price, sz,  fairvalue, POS)

    tasks = []
    if POS < 20 and 0.05 <= buy_price <= 0.95:
        tasks.append(asyncio.create_task(
            make_order_buy(auth_client, yes_token_id, no_token_id, buy_price, sz, sem)
        ))

    if POS > -20 and 0.05 <= sell_price <= 0.95:
        tasks.append(asyncio.create_task(
            make_order_sell(auth_client, yes_token_id, no_token_id, sell_price, sz, sem)
        ))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        print(r)


async def try_spread(auth_client, yes_token_id, no_token_id, fairvalue, logspread, sem: asyncio.Semaphore):
    #print("attempting to place order...")

    #posyes = await get_position_size(FUNDER, yes_token_id)
    #posno = await get_position_size(FUNDER, no_token_id)
    async with aiohttp.ClientSession() as session:
        t_yes = asyncio.create_task(get_position_size(session, FUNDER, yes_token_id))
        t_no  = asyncio.create_task(get_position_size(session, FUNDER, no_token_id))

        async def midpoint_task():
            async with sem:
                return await _to_thread(auth_client.get_prices, yes_token_id)

        prices = asyncio.create_task(midpoint_task())

        posyes, posno, mid = await asyncio.gather(t_yes, t_no, prices)
    POS = posyes-posno
    print(POS)
    print(prices)

    if POS>31 or POS<-31:
        print(f"Position too large: {POS}, SOMETHING VERY WRONG")
        return
    
    buy_price, sell_price = quote(fairvalue, logspread,POS)

    
    sz1 = 5
    if buy_price<=0.2:
        sz1 = 5
    sz2 = 5
    if sell_price>=0.8:
        sz2 = 5
    print(sell_price, buy_price, sz1,sz2, fairvalue, POS)
    
    #if(POS <20 and buy_price >= 0.05 and buy_price <=0.99):
    #    await make_order_buy(auth_client, yes_token_id, no_token_id, buy_price, sz1,sem)
    #if(POS > -20 and sell_price <=0.95 and sell_price >=0.01):
    #    await make_order_sell(auth_client, yes_token_id, no_token_id, sell_price, sz2,sem)
    tasks = []
    if POS < 20 and 0.05 <= buy_price <= 0.99:
        tasks.append(asyncio.create_task(
            make_order_buy(auth_client, yes_token_id, no_token_id, buy_price, sz1, sem)
        ))

    if POS > -20 and 0.01 <= sell_price <= 0.95:
        tasks.append(asyncio.create_task(
            make_order_sell(auth_client, yes_token_id, no_token_id, sell_price, sz2, sem)
        ))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)