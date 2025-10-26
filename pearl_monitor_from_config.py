import os
import time
import json
import argparse
from typing import Dict, Any, List

import requests


URL = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketList"


PEARL_ITEM_CATEGORIES: List[Dict[str, Any]] = [
    {"mainCategory": 55, "subCategory": 1, "name": "Männliche Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 2, "name": "Weibliche Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 3, "name": "Männliche Outfits (Einzel)"},
    {"mainCategory": 55, "subCategory": 4, "name": "Weibliche Outfits (Einzel)"},
    {"mainCategory": 55, "subCategory": 5, "name": "Klassen-Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 6, "name": "Funktional (Tiere, Elixiere etc.)"},
    {"mainCategory": 55, "subCategory": 7, "name": "Reittiere (Pferdeausrüstung)"},
    {"mainCategory": 55, "subCategory": 8, "name": "Begleiter (Pets)"},
]


def load_auth_config(config_path: str) -> Dict[str, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    required = ["cookie", "user_agent", "request_verification_token"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"Missing '{key}' in {config_path}")
    return {
        "cookie": data["cookie"],
        "user_agent": data["user_agent"],
        "request_verification_token": data["request_verification_token"],
    }


def build_headers(user_agent: str, cookie: str) -> Dict[str, str]:
    return {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": user_agent,
        "cookie": cookie,
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://eu-trade.naeu.playblackdesert.com",
        "referer": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-1",
    }


def check_market_once(headers: Dict[str, str], token: str) -> None:
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- {now_str} Starte Marktabfrage ---")

    for category in PEARL_ITEM_CATEGORIES:
        payload = {
            "__RequestVerificationToken": token,
            "mainCategory": category["mainCategory"],
            "subCategory": category["subCategory"],
        }
        try:
            response = requests.post(URL, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"\n!!! KRITISCHER FEHLER in {category['name']} !!!")
            print(f"Fehlerdetails: {e}")
            print(
                ">>> Der '__RequestVerificationToken' oder der 'Cookie' ist abgelaufen. Bitte erneuern Sie die Daten."
            )
            return
        except json.JSONDecodeError:
            print(f"Antwort ist kein JSON für Kategorie: {category['name']}")
            return

        items_found = 0
        market_list = data.get("marketList") if isinstance(data, dict) else None
        if isinstance(market_list, list):
            for item in market_list:
                sum_count = 0 if not isinstance(item, dict) else int(item.get("sumCount", 0))
                if sum_count >= 1:
                    print("====================================")
                    print("🚨🚨🚨 ARTIKEL GEFUNDEN! 🚨🚨🚨")
                    print(f"Kategorie: {category['name']}")
                    print(f"Name: {item.get('name', 'Unbekannt')}")
                    print(f"Verfügbarkeit: {sum_count}")
                    print(f"Item-ID (mainKey): {item.get('mainKey')}")
                    print("====================================")
                    items_found += 1

        if items_found == 0:
            print(f"  [OK] {category['name']} (keine neuen Einträge)")


def main() -> None:
    parser = argparse.ArgumentParser(description="BDO Pearl-Kategorien überwachen")
    parser.add_argument(
        "--config",
        default=os.path.join("config", "trader_auth.json"),
        help="Pfad zur Auth-Konfigurationsdatei",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("POLL_INTERVAL", "0.5")),
        help="Abfrageintervall in Sekunden (Standard 0.5)",
    )
    args = parser.parse_args()

    auth = load_auth_config(args.config)
    headers = build_headers(auth["user_agent"], auth["cookie"])
    token = auth["request_verification_token"]

    interval = max(0.1, float(args.interval))

    while True:
        check_market_once(headers, token)
        time.sleep(interval)


if __name__ == "__main__":
    main()



