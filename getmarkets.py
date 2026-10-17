import os
import asyncio
import pprint
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL
from urllib.parse import urlparse
import requests
import json
import time
import random


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

game_to_id = {}
team_to_game = {}

cnt = 1

# atm vs bog
link = "https://polymarket.com/event/ucl-atm-bog1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["atm"] = cnt
team_to_game["bog"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# ars vs kai
link = "https://polymarket.com/event/ucl-ars-kai1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["ars"] = cnt
team_to_game["kai"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# paf vs slp
link = "https://polymarket.com/event/ucl-paf-slp-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["paf"] = cnt
team_to_game["slp"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# bru vs olm
link = "https://polymarket.com/event/ucl-bru1-olm-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["bru"] = cnt
team_to_game["olm"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# fcb vs kob
link = "https://polymarket.com/event/ucl-fcb1-kob1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["fcb"] = cnt
team_to_game["kob"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# liv vs qar
link = "https://polymarket.com/event/ucl-liv1-qar1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["liv"] = cnt
team_to_game["qar"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# ben vs rma
link = "https://polymarket.com/event/ucl-ben1-rma1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["ben"] = cnt
team_to_game["rma"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# ath vs spo
link = "https://polymarket.com/event/ucl-ath1-spo1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["ath"] = cnt
team_to_game["spo"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# lev vs vil
link = "https://polymarket.com/event/ucl-lev2-vil1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["lev"] = cnt
team_to_game["vil"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# usg vs ata
link = "https://polymarket.com/event/ucl-usg1-ata1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["usg"] = cnt
team_to_game["ata"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# bvb vs int
link = "https://polymarket.com/event/ucl-bvb-int-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["bvb"] = cnt
team_to_game["int"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# aja vs oly
link = "https://polymarket.com/event/ucl-aja-oly-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["aja"] = cnt
team_to_game["oly"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# mnc vs gal
link = "https://polymarket.com/event/ucl-mnc-gal-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["mnc"] = cnt
team_to_game["gal"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# asm vs juv
link = "https://polymarket.com/event/ucl-asm-juv-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["asm"] = cnt
team_to_game["juv"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# nap vs cfc
link = "https://polymarket.com/event/ucl-nap1-cfc-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["nap"] = cnt
team_to_game["cfc"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# psv vs bay
link = "https://polymarket.com/event/ucl-psv1-bay-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["psv"] = cnt
team_to_game["bay"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# fra vs tot
link = "https://polymarket.com/event/ucl-fra1-tot-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["fra"] = cnt
team_to_game["tot"] = -cnt
game_to_id[cnt] = ids
cnt += 1

# psg vs new
link = "https://polymarket.com/event/ucl-psg1-new1-2026-01-28"
ids = get_token_ids_from_polymarket_link(link)
team_to_game["psg"] = cnt
team_to_game["new"] = -cnt
game_to_id[cnt] = ids
cnt += 1


#rellevant = ["liv","rma","fcb","mnc","psg","tot","new","cfc", "atm","int","spo","juv","bvb", "ata","lev","olm"]
teams = team_to_game.keys()

with open("team_data.json", "w") as f:
    json.dump(team_to_game, f)

with open("game_data.json", "w") as f:
    json.dump(game_to_id, f)

champions_league_points = {
    "atm": 13,   # Atlético Madrid
    "bog": 6,   # Bodo Glimt
    "ars": 21,   # Arsenal
    "kai": 1,    # Kairat Almaty
    "paf": 6,    # Pafos
    "slp": 3,    # Slavia Prague
    "bru": 7,    # Club Brugge
    "olm": 8,    # Marsella
    "fcb": 13,   # Barcelona
    "kob": 8,    # Copenhagen
    "liv": 15,   # Liverpool
    "qar": 10,   # Qarabag
    "ben": 6,    # Benfica
    "rma": 15,   # Real Madrid
    "ath": 8,    # Athletic Club
    "spo": 13,   # Sporting CP
    "lev": 9,    # Bayer Leverkusen
    "vil": 1,    # Villarreal
    "usg": 6,    # Union Saint-Gilloise
    "ata": 13,   # Atalanta
    "bvb": 11,   # Borussia Dortmund
    "int": 12,   # Inter
    "aja": 6,    # Ajax
    "oly": 8,    # Olympiacos
    "mnc": 13,   # Manchester City
    "gal": 10,   # Galatasaray
    "asm": 9,    # Monaco
    "juv": 12,   # Juventus
    "nap": 8,    # Napoli
    "cfc": 13,   # Chelsea
    "psv": 8,    # PSV
    "bay": 18,   # Bayern Munich
    "fra": 4,    # Eintracht Frankfurt
    "tot": 14,   # Tottenham
    "psg": 13,   # PSG
    "new": 13    # Newcastle
}
from pprint import pprint
pprint(sorted(champions_league_points.items(), key=lambda x: x[1], reverse=True))
champions_league_goal_diff = {
    "ars": +18,
    "bay": +13,
    "rma": +11,
    "liv":  +6,
    "tot":  +8,
    "psg": +10,
    "new": +10,
    "cfc":  +6,
    "fcb":  +5,
    "spo":  +5,
    "mnc":  +4,
    "atm":  +3,
    "ata":  +1,
    "int":  +6,
    "juv":  +4,
    "bvb":  +4,
    "gal":   0,
    "qar":  -2,   # Qarabağ
    "lev":  -4,   # Bayer Leverkusen
    "asm":  -6,   # Monaco
    "psv":  +1,
    "ath":  -4,   # Athletic Bilbao
    "oly":  -5,   # Olympiacos
    "nap":  -5,   # Napoli
    "kob":  -6,   # Copenhagen
    "bru":  -5,   # Club Brugge
    "bog":  -2,   # Bodø/Glimt
    "ben":  -4,
    "paf":  -6,
    "usg": -10,   # Union Saint-Gilloise
    "aja": -12,
    "fra":  -9,   # Eintracht Frankfurt
    "slp": -11,   # Slavia Prague
    "vil": -10,
    "kai": -14,
    "olm": 0      # Marsellella
}
for team in champions_league_points:
    champions_league_points[team] += champions_league_goal_diff[team] * 0.01
with open("team_points.json", "w") as f:
    json.dump(champions_league_points, f)
