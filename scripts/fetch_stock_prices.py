#!/usr/bin/env python3
"""
株価取得スクリプト (fetch_stock_prices.py)
ポートフォリオの銘柄の株価情報を取得し、JSONファイルに保存します。
"""

import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List


def load_portfolio(portfolio_file: str = "data/portfolio.csv") -> pd.DataFrame:
    """
    ポートフォリオをCSVファイルから読み込みます。

    Args:
        portfolio_file: ポートフォリオファイルパス

    Returns:
        ポートフォリオのDataFrame
    """
    if not os.path.exists(portfolio_file):
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")

    df = pd.read_csv(portfolio_file)
    print(f"✓ Loaded {len(df)} stocks from portfolio")
    return df


def fetch_stock_price(symbol: str) -> Dict:
    """
    指定された銘柄の株価情報を取得します。

    Args:
        symbol: 銘柄コード

    Returns:
        株価情報の辞書
    """
    try:
        print(f"  Fetching {symbol}...")
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="5d")

        if hist.empty:
            print(f"    Warning: No price data available for {symbol}")
            return None

        latest_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else latest_price

        # 変動率を計算
        change = latest_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

        stock_data = {
            "symbol": symbol,
            "name": info.get("longName", info.get("shortName", "N/A")),
            "current_price": round(float(latest_price), 2),
            "previous_close": round(float(prev_close), 2),
            "change": round(float(change), 2),
            "change_percent": round(float(change_percent), 2),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap", "N/A"),
            "volume": info.get("volume", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
        }

        print(f"    ✓ {symbol}: {stock_data['currency']} {latest_price:.2f} ({change_percent:+.2f}%)")
        return stock_data

    except Exception as e:
        print(f"    Error fetching {symbol}: {str(e)}")
        return None


def fetch_all_portfolio_prices(portfolio: pd.DataFrame) -> List[Dict]:
    """
    ポートフォリオのすべての銘柄の株価を取得します。

    Args:
        portfolio: ポートフォリオのDataFrame

    Returns:
        株価情報のリスト
    """
    stock_prices = []

    for _, row in portfolio.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        purchase_price = row['purchase_price']

        stock_data = fetch_stock_price(symbol)

        if stock_data:
            # ポートフォリオ情報を追加
            stock_data['shares'] = int(shares)
            stock_data['purchase_price'] = round(float(purchase_price), 2)

            # 損益を計算
            current_value = stock_data['current_price'] * shares
            purchase_value = purchase_price * shares
            gain_loss = current_value - purchase_value
            gain_loss_percent = (gain_loss / purchase_value) * 100 if purchase_value != 0 else 0

            stock_data['current_value'] = round(float(current_value), 2)
            stock_data['purchase_value'] = round(float(purchase_value), 2)
            stock_data['gain_loss'] = round(float(gain_loss), 2)
            stock_data['gain_loss_percent'] = round(float(gain_loss_percent), 2)

            stock_prices.append(stock_data)

    return stock_prices


def save_stock_prices(stock_prices: List[Dict], output_file: str = "output/stock_prices.json"):
    """
    株価情報をJSONファイルに保存します。

    Args:
        stock_prices: 株価情報のリスト
        output_file: 出力ファイルパス
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # ポートフォリオ全体のサマリーを計算
    total_current_value = sum(s['current_value'] for s in stock_prices)
    total_purchase_value = sum(s['purchase_value'] for s in stock_prices)
    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percent = (total_gain_loss / total_purchase_value) * 100 if total_purchase_value != 0 else 0

    output_data = {
        "fetch_time": datetime.now().isoformat(),
        "portfolio_summary": {
            "total_stocks": len(stock_prices),
            "total_current_value": round(total_current_value, 2),
            "total_purchase_value": round(total_purchase_value, 2),
            "total_gain_loss": round(total_gain_loss, 2),
            "total_gain_loss_percent": round(total_gain_loss_percent, 2)
        },
        "stocks": stock_prices
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved stock prices to {output_file}")
    print(f"  Portfolio Value: {total_current_value:,.2f}")
    print(f"  Total Gain/Loss: {total_gain_loss:+,.2f} ({total_gain_loss_percent:+.2f}%)")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Stock Investment - Stock Price Fetcher")
    print("=" * 60)

    try:
        # ポートフォリオを読み込む
        print("\nLoading portfolio...")
        portfolio = load_portfolio()

        # 株価を取得
        print("\nFetching stock prices...")
        stock_prices = fetch_all_portfolio_prices(portfolio)

        if not stock_prices:
            print("\nWarning: No stock prices were fetched successfully")
            return

        # JSONファイルに保存
        save_stock_prices(stock_prices)

        print("\n" + "=" * 60)
        print("Fetch completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {str(e)}")
        raise


if __name__ == "__main__":
    main()
