import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests


ARSHA_BASE = "https://api.arsha.io"


@dataclass
class ItemMarketRow:
    id: int
    stock: int
    total_trades: int
    base_price: int


@dataclass
class OrderLevel:
    price: int
    buyers: int
    sellers: int


class ArshaClient:
    def __init__(self, region: str = "eu", session: Optional[requests.Session] = None, timeout: float = 8.0):
        self.region = region
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{ARSHA_BASE}{path}"
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json_body: Optional[dict | list] = None, params: Optional[dict] = None) -> dict:
        url = f"{ARSHA_BASE}{path}"
        r = self.session.post(url, json=json_body, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def market(self) -> List[ItemMarketRow]:
        # GET /v1/:region/market -> resultMsg: "id-stock-totalTrades-basePrice|..."
        data = self._get(f"/v1/{self.region}/market")
        msg = data.get("resultMsg", "")
        items: List[ItemMarketRow] = []
        if not msg:
            return items
        parts = [p for p in msg.split("|") if p]
        for p in parts:
            try:
                id_str, stock_str, trades_str, base_str = p.split("-")
                items.append(
                    ItemMarketRow(
                        id=int(id_str),
                        stock=int(stock_str),
                        total_trades=int(trades_str),
                        base_price=int(base_str),
                    )
                )
            except Exception:
                continue
        return items

    def orders_batch(self, ids: List[int], sid: int = 0) -> Dict[Tuple[int, int], List[OrderLevel]]:
        # POST /v2/:region/GetBiddingInfoList returns either object (single) or array (multi)
        body = [{"id": i, "sid": sid} for i in ids]
        try:
            data = self._post(f"/v2/{self.region}/GetBiddingInfoList", json_body=body, params={"lang": "en"})
        except requests.HTTPError as e:
            # Fallback to v1 for single requests if batch fails
            result: Dict[Tuple[int, int], List[OrderLevel]] = {}
            for i in ids:
                obj = self._get(f"/v1/{self.region}/orders", params={"id": i, "sid": sid})
                levels = self._parse_v1_orders(obj.get("resultMsg", ""))
                result[(i, sid)] = levels
            return result

        def normalize(obj: dict) -> Tuple[Tuple[int, int], List[OrderLevel]]:
            iid = int(obj.get("id"))
            sid_val = int(obj.get("sid", sid))
            raw_orders = obj.get("orders", [])
            levels: List[OrderLevel] = []
            for o in raw_orders:
                try:
                    levels.append(OrderLevel(price=int(o["price"]), buyers=int(o["buyers"]), sellers=int(o["sellers"])) )
                except Exception:
                    continue
            return (iid, sid_val), levels

        result: Dict[Tuple[int, int], List[OrderLevel]] = {}
        if isinstance(data, list):
            for obj in data:
                k, v = normalize(obj)
                result[k] = v
        elif isinstance(data, dict) and "orders" in data:
            k, v = normalize(data)
            result[k] = v
        else:
            # Unexpected shape; fallback to v1 per id
            for i in ids:
                obj = self._get(f"/v1/{self.region}/orders", params={"id": i, "sid": sid})
                levels = self._parse_v1_orders(obj.get("resultMsg", ""))
                result[(i, sid)] = levels
        return result

    @staticmethod
    def _parse_v1_orders(result_msg: str) -> List[OrderLevel]:
        levels: List[OrderLevel] = []
        for chunk in [c for c in result_msg.split("|") if c]:
            try:
                price_str, sellers_str, buyers_str = chunk.split("-")
                # v1: price - sellCount - buyCount (per docs)
                levels.append(OrderLevel(price=int(price_str), buyers=int(buyers_str), sellers=int(sellers_str)))
            except Exception:
                continue
        return levels


def compute_flip(levels: List[OrderLevel], tax: float) -> Optional[Tuple[int, int, float, float]]:
    # Find lowest sell ask (sellers > 0) and highest buy bid (buyers > 0)
    lowest_sell = None
    highest_buy = None
    for lv in levels:
        if lv.sellers > 0:
            if lowest_sell is None or lv.price < lowest_sell:
                lowest_sell = lv.price
        if lv.buyers > 0:
            if highest_buy is None or lv.price > highest_buy:
                highest_buy = lv.price
    if lowest_sell is None or highest_buy is None:
        return None
    profit = highest_buy * (1.0 - tax) - lowest_sell
    roi = profit / lowest_sell if lowest_sell > 0 else 0.0
    return lowest_sell, highest_buy, profit, roi


def load_config(path: Optional[str]) -> dict:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Suggest profitable flips on BDO EU Central Market (via api.arsha.io)")
    parser.add_argument("--region", default="eu", help="Region code (default: eu)")
    parser.add_argument("--tax", type=float, default=0.35, help="Seller tax rate (e.g., 0.35 for 35%)")
    parser.add_argument("--min-roi", type=float, default=0.05, help="Minimum ROI threshold (e.g., 0.05 for 5%)")
    parser.add_argument("--max-items", type=int, default=150, help="Max items to analyze (by trades/stock)")
    parser.add_argument("--export-json", default=None, help="Path to export candidates as JSON")
    parser.add_argument("--config", default=None, help="Path to config JSON (overridden by CLI args)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    region = str(cfg.get("region", args.region)).lower()
    tax = float(cfg.get("tax", args.tax))
    min_roi = float(cfg.get("min_roi", args.min_roi))
    max_items = int(cfg.get("max_items", args.max_items))

    client = ArshaClient(region=region)

    try:
        market_rows = client.market()
    except Exception as e:
        print(f"Failed to fetch market list: {e}", file=sys.stderr)
        sys.exit(1)

    # Prioritize by total trades and current stock
    market_rows.sort(key=lambda r: (r.total_trades, r.stock), reverse=True)
    selected = [r for r in market_rows if r.stock >= 0][:max_items]

    # Batch orders in chunks to be respectful
    candidates = []
    CHUNK = 25
    for i in range(0, len(selected), CHUNK):
        chunk = selected[i : i + CHUNK]
        ids = [r.id for r in chunk]
        try:
            obatch = client.orders_batch(ids)
        except Exception as e:
            # backoff and continue
            time.sleep(0.5)
            continue
        for r in chunk:
            levels = obatch.get((r.id, 0), [])
            if not levels:
                continue
            res = compute_flip(levels, tax)
            if not res:
                continue
            buy_at, sell_at, profit, roi = res
            if profit > 0 and roi >= min_roi:
                candidates.append(
                    {
                        "id": r.id,
                        "buy_at": buy_at,
                        "sell_at": sell_at,
                        "profit": profit,
                        "roi": roi,
                        "base_price": r.base_price,
                        "stock": r.stock,
                        "trades": r.total_trades,
                    }
                )
        time.sleep(0.2)

    # Rank and print
    candidates.sort(key=lambda c: (c["roi"], c["profit"]), reverse=True)
    top = candidates[:20]

    if not top:
        print("No candidates found. Consider lowering --min-roi or increasing --max-items.")
    else:
        print(f"Top {len(top)} flip candidates (region={region}, tax={tax:.2f}, min_roi={min_roi:.2f}):")
        print("id    buy_at    sell_at    profit      roi     stock   trades")
        for c in top:
            print(
                f"{c['id']:<6}{c['buy_at']:<10}{c['sell_at']:<11}{int(c['profit']):<11}{c['roi']*100:>5.1f}%   {c['stock']:<7}{c['trades']}"
            )

    if args.export_json:
        try:
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(top, f, indent=2)
            print(f"Exported {len(top)} candidates to {args.export_json}")
        except Exception as e:
            print(f"Failed to export JSON: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
