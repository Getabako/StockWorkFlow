#!/usr/bin/env python3
"""
ポートフォリオ評価スクリプト (update_portfolio.py)
Alpha Vantage APIを使用して株価を取得し、ポートフォリオの損益を計算します。
"""

import pandas as pd
import requests
import os
import time
from datetime import datetime

# Alpha Vantage APIの設定
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
if not STOCK_API_KEY:
    raise ValueError("STOCK_API_KEY environment variable is not set")

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def load_portfolio(file_path: str = "data/portfolio.csv") -> pd.DataFrame:
    """
    ポートフォリオデータをCSVファイルから読み込みます。

    Args:
        file_path: ポートフォリオファイルのパス

    Returns:
        ポートフォリオのDataFrame
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Portfolio file not found: {file_path}")

    df = pd.read_csv(file_path)
    print(f"✓ Loaded portfolio with {len(df)} holdings")
    return df


def get_stock_price(symbol: str, api_key: str) -> float:
    """
    Alpha Vantage APIを使用して株価を取得します。

    Args:
        symbol: 株式シンボル（例: NVDA, MSFT, 7203.T）
        api_key: Alpha Vantage APIキー

    Returns:
        最新の株価（取得失敗時はNone）
    """
    try:
        # APIリクエスト（GLOBAL_QUOTE）
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }

        response = requests.get(ALPHA_VANTAGE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # レスポンスの確認
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price = float(data["Global Quote"]["05. price"])
            print(f"  {symbol}: ${price:.2f}")
            return price
        elif "Note" in data:
            # API制限に達した場合
            print(f"  {symbol}: API rate limit reached")
            return None
        else:
            print(f"  {symbol}: No data available")
            return None

    except Exception as e:
        print(f"  {symbol}: Error - {str(e)}")
        return None


def update_portfolio_prices(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    ポートフォリオの全銘柄の株価を更新します。

    Args:
        portfolio_df: ポートフォリオのDataFrame

    Returns:
        更新されたDataFrame
    """
    print("\nFetching stock prices...")

    current_prices = []

    for idx, row in portfolio_df.iterrows():
        symbol = row['symbol']
        price = get_stock_price(symbol, STOCK_API_KEY)
        current_prices.append(price)

        # APIレート制限対策（無料版は1分に5リクエストまで）
        if idx < len(portfolio_df) - 1:
            time.sleep(12)  # 安全のため12秒待機

    portfolio_df['current_price'] = current_prices
    return portfolio_df


def calculate_portfolio_summary(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """
    ポートフォリオの損益を計算します。
    purchase_priceは平均取得単価（USD/JPY）として扱います。

    Args:
        portfolio_df: ポートフォリオのDataFrame

    Returns:
        損益計算済みのDataFrame
    """
    # 必要な列が存在するか確認
    required_columns = ['symbol', 'shares', 'purchase_price', 'current_price']
    for col in required_columns:
        if col not in portfolio_df.columns:
            raise ValueError(f"Required column '{col}' not found in portfolio")

    # currency列がない場合はUSDをデフォルトとする
    if 'currency' not in portfolio_df.columns:
        portfolio_df['currency'] = 'USD'

    # 損益計算（purchase_priceは平均取得単価）
    portfolio_df['purchase_value'] = portfolio_df['shares'] * portfolio_df['purchase_price']
    portfolio_df['current_value'] = portfolio_df['shares'] * portfolio_df['current_price']
    portfolio_df['profit_loss'] = portfolio_df['current_value'] - portfolio_df['purchase_value']
    portfolio_df['profit_loss_pct'] = (portfolio_df['profit_loss'] / portfolio_df['purchase_value']) * 100

    # NaN値の処理
    portfolio_df['current_value'].fillna(portfolio_df['purchase_value'], inplace=True)
    portfolio_df['profit_loss'].fillna(0, inplace=True)
    portfolio_df['profit_loss_pct'].fillna(0, inplace=True)

    return portfolio_df


def save_portfolio_summary(portfolio_df: pd.DataFrame, output_file: str = "output/portfolio_summary.csv"):
    """
    ポートフォリオサマリーをCSVファイルに保存します。

    Args:
        portfolio_df: ポートフォリオのDataFrame
        output_file: 出力ファイルパス
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    portfolio_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✓ Portfolio summary saved to {output_file}")


def print_summary_stats(portfolio_df: pd.DataFrame):
    """
    ポートフォリオの統計情報を表示します。

    Args:
        portfolio_df: ポートフォリオのDataFrame
    """
    total_purchase = portfolio_df['purchase_value'].sum()
    total_current = portfolio_df['current_value'].sum()
    total_pl = portfolio_df['profit_loss'].sum()
    total_pl_pct = (total_pl / total_purchase) * 100 if total_purchase > 0 else 0

    print("\n" + "=" * 60)
    print("Portfolio Summary")
    print("=" * 60)
    print(f"Total Purchase Value: ${total_purchase:,.2f}")
    print(f"Total Current Value:  ${total_current:,.2f}")
    print(f"Total P/L:            ${total_pl:,.2f} ({total_pl_pct:+.2f}%)")
    print("=" * 60)

    # 個別銘柄のトップ/ワースト
    sorted_df = portfolio_df.sort_values('profit_loss', ascending=False)

    print("\nTop 3 Gainers:")
    for idx, row in sorted_df.head(3).iterrows():
        print(f"  {row['symbol']}: ${row['profit_loss']:,.2f} ({row['profit_loss_pct']:+.2f}%)")

    if len(sorted_df) > 3:
        print("\nTop 3 Losers:")
        for idx, row in sorted_df.tail(3).iterrows():
            print(f"  {row['symbol']}: ${row['profit_loss']:,.2f} ({row['profit_loss_pct']:+.2f}%)")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Stock Investment - Portfolio Evaluator")
    print("=" * 60)

    # ポートフォリオを読み込む
    portfolio_df = load_portfolio()

    # 株価を更新
    portfolio_df = update_portfolio_prices(portfolio_df)

    # 損益を計算
    portfolio_df = calculate_portfolio_summary(portfolio_df)

    # サマリーを保存
    save_portfolio_summary(portfolio_df)

    # 統計情報を表示
    print_summary_stats(portfolio_df)

    print("\n" + "=" * 60)
    print("Portfolio evaluation completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
