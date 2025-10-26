import json
import os
import sys
from typing import Dict

import requests


URL = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketList"


def load_auth_config(config_path: str) -> Dict[str, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ("cookie", "user_agent", "request_verification_token"):
        if not data.get(key):
            raise SystemExit(f"Missing '{key}' in {config_path}")
    return data


def main() -> None:
    config_path = os.path.join("config", "trader_auth.json")
    auth = load_auth_config(config_path)

    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": auth["user_agent"],
        "cookie": auth["cookie"],
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://eu-trade.naeu.playblackdesert.com",
        "referer": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-1",
    }

    payload = {
        "__RequestVerificationToken": auth["request_verification_token"],
        "mainCategory": 55,
        "subCategory": 1,
    }

    try:
        resp = requests.post(URL, headers=headers, data=payload, timeout=15)
        status = resp.status_code
        ok = False
        try:
            js = resp.json()
            ok = isinstance(js, dict) and "marketList" in js
            item_count = len(js.get("marketList", [])) if ok else 0
        except Exception:
            item_count = 0
        print(f"status={status} ok_marketList={ok} items={item_count}")
        if status == 401 or status == 403:
            print("auth_error=true token_or_cookie_invalid=true")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"request_exception={type(e).__name__} detail={e}")
        sys.exit(2)


if __name__ == "__main__":
    main()



