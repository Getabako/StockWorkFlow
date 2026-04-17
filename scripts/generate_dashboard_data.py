#!/usr/bin/env python3
"""
ダッシュボード用データ集約スクリプト (generate_dashboard_data.py)
既存データソースを読み込み、dashboard/dashboard_data.json に集約出力する。
標準ライブラリのみ使用。
"""

import json
import csv
import os
from datetime import datetime

# プロジェクトルート（スクリプトの親ディレクトリ）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 入力ファイルパス
STOCK_PRICES_FILE = os.path.join(BASE_DIR, "output", "stock_prices.json")
PORTFOLIO_CSV = os.path.join(BASE_DIR, "data", "portfolio.csv")
ACCOUNT_FILE = os.path.join(BASE_DIR, "portfolio", "account.json")
ACTION_LOG_FILE = os.path.join(BASE_DIR, "data", "action_log.json")
INSIGHTS_FILE = os.path.join(BASE_DIR, "data", "ai_industry_insights.json")
HISTORY_CSV = os.path.join(BASE_DIR, "portfolio", "history.csv")

# 出力ファイルパス
OUTPUT_FILE = os.path.join(BASE_DIR, "dashboard", "dashboard_data.json")

# 固定為替レート (USD/JPY)
USD_JPY_RATE = 150.0

# セクター分類マッピング（portfolio.csvの sector 列が優先。ここはフォールバック）
SECTOR_MAP = {
    "NVDA": "AI半導体",
    "AVGO": "AI半導体",
    "INTC": "AI半導体",
    "QCOM": "AI半導体",
    "AMD": "AI半導体",
    "GOOG": "クラウド/広告",
    "TSLA": "EV/自動運転",
    "7366.T": "教育テック",
    "6006821": "新興国株式投信",
    "6006846": "米国成長株投信",
    "6006884": "テーマ型投信",
    "6016884": "テーマ型投信",
}


def load_json(filepath, default=None):
    """JSONファイルを読み込む。ファイル不在時はデフォルト値を返す。"""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        print(f"  [SKIP] {os.path.basename(filepath)} not found, using default")
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  [OK] {os.path.basename(filepath)}")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"  [ERROR] {os.path.basename(filepath)}: {e}")
        return default


def load_csv(filepath):
    """CSVファイルをリストの辞書として読み込む。ファイル不在時は空リスト。"""
    if not os.path.exists(filepath):
        print(f"  [SKIP] {os.path.basename(filepath)} not found")
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"  [OK] {os.path.basename(filepath)} ({len(rows)} rows)")
        return rows
    except IOError as e:
        print(f"  [ERROR] {os.path.basename(filepath)}: {e}")
        return []


def build_stocks_data(stock_prices, portfolio_csv):
    """
    株価データとポートフォリオCSVから銘柄情報を構築する。
    stock_prices.json が存在する場合はそちらを優先し、
    存在しない場合は portfolio.csv からフォールバック。
    """
    stocks = []

    if stock_prices and "stocks" in stock_prices:
        for s in stock_prices["stocks"]:
            sector = SECTOR_MAP.get(s.get("symbol", ""), "その他")
            stocks.append({
                "symbol": s.get("symbol", ""),
                "name": s.get("name", ""),
                "shares": s.get("shares", 0),
                "purchase_price": s.get("purchase_price", 0),
                "current_price": s.get("current_price", 0),
                "currency": s.get("currency", "USD"),
                "current_value": s.get("current_value", 0),
                "purchase_value": s.get("purchase_value", 0),
                "gain_loss": s.get("gain_loss", 0),
                "gain_loss_percent": s.get("gain_loss_percent", 0),
                "change": s.get("change", 0),
                "change_percent": s.get("change_percent", 0),
                "sector": sector,
            })
    elif portfolio_csv:
        # portfolio.csv から読み込み（スナップショット形式に対応）
        # 新形式: purchase_value_jpy, current_value_jpy, sector, account, category を持つ
        # 旧形式: purchase_price のみ（現在価格は不明）
        for row in portfolio_csv:
            symbol = row.get("symbol", "")
            shares = float(row.get("shares", 0) or 0)
            currency = row.get("currency", "JPY")
            sector = row.get("sector") or SECTOR_MAP.get(symbol, "その他")
            account = row.get("account", "")
            category = row.get("category", "")

            # 新形式（評価額が既知）
            if row.get("current_value_jpy"):
                purchase_value = float(row.get("purchase_value_jpy", 0) or 0)
                current_value = float(row.get("current_value_jpy", 0) or 0)
                purchase_price = purchase_value / shares if shares else 0
                current_price = current_value / shares if shares else 0
                gain_loss = current_value - purchase_value
                gain_loss_percent = (
                    (gain_loss / purchase_value * 100) if purchase_value else 0
                )
            else:
                # 旧形式フォールバック
                purchase_price = float(row.get("purchase_price", 0) or 0)
                purchase_value = shares * purchase_price
                current_price = purchase_price
                current_value = purchase_value
                gain_loss = 0
                gain_loss_percent = 0

            stocks.append({
                "symbol": symbol,
                "name": row.get("name", ""),
                "shares": int(shares),
                "purchase_price": round(purchase_price, 2),
                "current_price": round(current_price, 2),
                "currency": currency,
                "current_value": round(current_value, 2),
                "purchase_value": round(purchase_value, 2),
                "gain_loss": round(gain_loss),
                "gain_loss_percent": round(gain_loss_percent, 2),
                "change": 0,
                "change_percent": 0,
                "sector": sector,
                "account": account,
                "category": category,
            })

    return stocks


def calculate_summary(stocks, account):
    """
    サマリーカードのデータを計算する。
    JPY株はそのまま、USD株はUSD_JPY_RATEで換算して合計。
    """
    total_value_jpy = 0
    total_purchase_jpy = 0

    for s in stocks:
        if s["currency"] == "JPY":
            total_value_jpy += s["current_value"]
            total_purchase_jpy += s["purchase_value"]
        else:
            total_value_jpy += s["current_value"] * USD_JPY_RATE
            total_purchase_jpy += s["purchase_value"] * USD_JPY_RATE

    total_gain_loss_jpy = total_value_jpy - total_purchase_jpy
    total_gain_loss_pct = (
        (total_gain_loss_jpy / total_purchase_jpy * 100)
        if total_purchase_jpy != 0
        else 0
    )

    buying_power = account.get("buying_power", 0)

    return {
        "total_value_jpy": round(total_value_jpy),
        "total_purchase_jpy": round(total_purchase_jpy),
        "total_gain_loss_jpy": round(total_gain_loss_jpy),
        "total_gain_loss_pct": round(total_gain_loss_pct, 2),
        "buying_power": buying_power,
        "buying_power_currency": account.get("currency", "JPY"),
        "total_stocks": len(stocks),
        "usd_jpy_rate": USD_JPY_RATE,
    }


def build_sector_allocation(stocks):
    """セクター別配分を計算する（JPY換算）。"""
    sector_values = {}
    for s in stocks:
        sector = s["sector"]
        value = s["current_value"]
        if s["currency"] != "JPY":
            value *= USD_JPY_RATE
        sector_values[sector] = sector_values.get(sector, 0) + value

    total = sum(sector_values.values())
    allocation = []
    for sector, value in sorted(sector_values.items(), key=lambda x: -x[1]):
        allocation.append({
            "sector": sector,
            "value_jpy": round(value),
            "percentage": round(value / total * 100, 1) if total > 0 else 0,
        })

    return allocation


def build_actions(action_log, insights):
    """アクション推奨データを構築する。"""
    actions = []

    # action_log から pending_actions を取得
    for action in action_log.get("pending_actions", []):
        actions.append({
            "type": action.get("action", "HOLD"),
            "symbol": action.get("symbol", ""),
            "name": action.get("name", ""),
            "reason": action.get("reason", ""),
            "trigger": action.get("trigger", ""),
        })

    # insights の recommended_actions からも生成
    if not actions and insights:
        rec = insights.get("recommended_actions", {})
        for item in rec.get("portfolio_optimization", []):
            # テキストから簡易的にアクション種別を推定
            action_type = "HOLD"
            if "検討" in item or "追加" in item:
                action_type = "BUY"
            elif "売却" in item or "利確" in item:
                action_type = "SELL"
            actions.append({
                "type": action_type,
                "symbol": "",
                "name": "",
                "reason": item,
                "trigger": "",
            })

    return actions


def flatten_strategy(insights):
    """投資戦略セクションを平坦化する。"""
    if not insights:
        return {}

    overview = insights.get("industry_overview", {})
    implications = insights.get("investment_implications", {})
    monitoring = insights.get("monitoring_points", {})

    # 各フィールドが文字列の場合はリストに変換
    def ensure_list(val):
        if isinstance(val, str):
            return [val]
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            result = []
            for k, v in val.items():
                if isinstance(v, list):
                    result.extend(v)
                elif isinstance(v, str):
                    result.append(v)
            return result
        return []

    return {
        "market_status": overview.get("market_status", ""),
        "key_risks": ensure_list(overview.get("key_risks", [])),
        "key_trends": ensure_list(overview.get("key_trends", [])),
        "short_term": ensure_list(implications.get("short_term", [])),
        "medium_term": ensure_list(implications.get("medium_term", [])),
        "long_term": ensure_list(implications.get("long_term", [])),
        "bubble_indicators": ensure_list(monitoring.get("bubble_indicators", [])),
        "positive_signals": ensure_list(monitoring.get("positive_signals", [])),
        "risk_signals": ensure_list(monitoring.get("risk_signals", [])),
    }


def build_history(history_csv):
    """取引履歴をダッシュボード用フォーマットに変換する。"""
    history = []
    for row in history_csv:
        history.append({
            "date": row.get("date", ""),
            "action": row.get("action", ""),
            "symbol": row.get("symbol", ""),
            "name": row.get("name", ""),
            "shares": int(row.get("shares", 0)) if row.get("shares") else 0,
            "price_per_share": float(row.get("price_per_share", 0)) if row.get("price_per_share") else 0,
            "total_amount": float(row.get("total_amount", 0)) if row.get("total_amount") else 0,
            "reason": row.get("reason", ""),
        })
    # 新しい順にソート
    history.sort(key=lambda x: x["date"], reverse=True)
    return history


def main():
    print("=" * 60)
    print("Dashboard Data Generator")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Base dir: {BASE_DIR}\n")

    # 1. データソース読み込み
    print("Loading data sources...")
    stock_prices = load_json(STOCK_PRICES_FILE, {})
    portfolio_csv = load_csv(PORTFOLIO_CSV)
    account = load_json(ACCOUNT_FILE, {"buying_power": 0, "currency": "JPY"})
    action_log = load_json(ACTION_LOG_FILE, {"pending_actions": [], "completed_actions": []})
    insights = load_json(INSIGHTS_FILE, {})
    history_csv = load_csv(HISTORY_CSV)

    # 2. 銘柄データ構築
    print("\nBuilding stocks data...")
    stocks = build_stocks_data(stock_prices, portfolio_csv)
    print(f"  {len(stocks)} stocks processed")

    # 3. サマリー計算
    print("Calculating summary...")
    summary = calculate_summary(stocks, account)

    # 4. セクター配分
    print("Building sector allocation...")
    sector_allocation = build_sector_allocation(stocks)

    # 5. アクション推奨
    print("Building action recommendations...")
    actions = build_actions(action_log, insights)

    # 6. 投資戦略
    print("Flattening strategy data...")
    strategy = flatten_strategy(insights)

    # 7. 取引履歴
    print("Building trade history...")
    history = build_history(history_csv)

    # 8. fetch_time の取得
    fetch_time = stock_prices.get("fetch_time", "")

    # 9. 出力データ構築
    dashboard_data = {
        "generated_at": datetime.now().isoformat(),
        "data_fetch_time": fetch_time,
        "summary": summary,
        "stocks": stocks,
        "sector_allocation": sector_allocation,
        "actions": actions,
        "strategy": strategy,
        "history": history,
    }

    # 10. 出力
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Dashboard data saved to: {OUTPUT_FILE}")
    print(f"  Summary: {summary['total_stocks']} stocks, "
          f"Total: {summary['total_value_jpy']:,.0f} JPY, "
          f"P/L: {summary['total_gain_loss_jpy']:+,.0f} JPY ({summary['total_gain_loss_pct']:+.2f}%)")
    print(f"  Sectors: {len(sector_allocation)}")
    print(f"  Actions: {len(actions)}")
    print(f"  History: {len(history)} trades")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
