import os
import asyncio
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
import time


GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


def get_token_ids_from_polymarket_link(link: str) -> dict:
    path = urlparse(link).path.strip("/").split("/")
    kind, slug = path[0], path[1]          # kind = "market" or "event"
    print(kind,slug)
    if kind == "event":
        data = requests.get(f"{GAMMA_API}/events/slug/{slug}", timeout=15).json()

        out = []
        for m in data["markets"]:
            token_ids = m.get('clobTokenIds')
            token_ids = json.loads(token_ids)
            out.append(token_ids)
           # print(m.keys())
            print(m["question"],"   ", token_ids)
        return out

    raise ValueError(f"Unrecognized Polymarket link path: {urlparse(link).path}")

team_to_id = {}

link = "https://polymarket.com/event/ucl-atm-bog1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["atm"] = ids
team_to_id["bog"] = ids[::-1]

# ars vs kai1
link = "https://polymarket.com/event/ucl-ars-kai1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["ars"] = ids
team_to_id["kai"] = ids[::-1]

# paf vs slp
link = "https://polymarket.com/event/ucl-paf-slp-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["paf"] = ids
team_to_id["slp"] = ids[::-1]

# bru1 vs olm
link = "https://polymarket.com/event/ucl-bru1-olm-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["bru"] = ids
team_to_id["olm"] = ids[::-1]

# fcb1 vs kob1
link = "https://polymarket.com/event/ucl-fcb1-kob1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["fcb"] = ids
team_to_id["kob"] = ids[::-1]

# liv1 vs qar1
link = "https://polymarket.com/event/ucl-liv1-qar1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["liv"] = ids
team_to_id["qar"] = ids[::-1]

# ben1 vs rma1
link = "https://polymarket.com/event/ucl-ben1-rma1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["ben"] = ids
team_to_id["rma"] = ids[::-1]

# ath1 vs spo1
link = "https://polymarket.com/event/ucl-ath1-spo1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["ath"] = ids
team_to_id["spo"] = ids[::-1]

# lev2 vs vil1
link = "https://polymarket.com/event/ucl-lev2-vil1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["lev"] = ids
team_to_id["vil"] = ids[::-1]

# usg1 vs ata1
link = "https://polymarket.com/event/ucl-usg1-ata1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["usg"] = ids
team_to_id["ata"] = ids[::-1]

# bvb vs int
link = "https://polymarket.com/event/ucl-bvb-int-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["bvb"] = ids
team_to_id["int"] = ids[::-1]

# aja vs oly
link = "https://polymarket.com/event/ucl-aja-oly-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["aja"] = ids
team_to_id["oly"] = ids[::-1]

# mnc vs gal
link = "https://polymarket.com/event/ucl-mnc-gal-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["mnc"] = ids
team_to_id["gal"] = ids[::-1]

# asm vs juv
link = "https://polymarket.com/event/ucl-asm-juv-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["asm"] = ids
team_to_id["juv"] = ids[::-1]

# nap1 vs cfc
link = "https://polymarket.com/event/ucl-nap1-cfc-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["nap"] = ids
team_to_id["cfc"] = ids[::-1]

# psv1 vs bay
link = "https://polymarket.com/event/ucl-psv1-bay-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["psv"] = ids
team_to_id["bay"] = ids[::-1]

# fra1 vs tot
link = "https://polymarket.com/event/ucl-fra1-tot-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["fra"] = ids
team_to_id["tot"] = ids[::-1]

# psg1 vs new1
link = "https://polymarket.com/event/ucl-psg1-new1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_id["psg"] = ids
team_to_id["new"] = ids[::-1]

#rellevant = ["liv","rma","fcb","mnc","psg","tot","new","cfc", "atm","int","spo","juv","bvb", "ata","lev","olm"]
teams = team_to_id.keys()

client = ClobClient(CLOB_API)



def track_price(duration_seconds=30, interval=1):
    """Track price changes in real-time."""
    print(f"Tracking price for {duration_seconds}s...\n")

    client = ClobClient(CLOB_API)
    start_time = time.time()
    prices = []

    while time.time() - start_time < duration_seconds:
        timestamp = time.strftime("%H:%M:%S")
        print(timestamp)
        for team in teams:
            mid = client.get_midpoint(team_to_id[team][0][0])
            win = float(mid['mid'])
            mid = client.get_midpoint(team_to_id[team][1][0])
            draw = float(mid['mid'])
            mid = client.get_midpoint(team_to_id[team][2][0])
            lose = float(mid['mid'])
            print("team "+team+" win draw lose:", win, draw, lose)
        time.sleep(interval)
    return

track_price(duration_seconds=60, interval=1)