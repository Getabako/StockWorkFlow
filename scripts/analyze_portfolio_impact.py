#!/usr/bin/env python3
"""
ポートフォリオ影響分析レポート生成スクリプト (analyze_portfolio_impact.py)
日々の市場情勢がポートフォリオに与える影響と売買示唆を分析します。
"""

import json
import os
import csv
from datetime import datetime
import google.generativeai as genai

# Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)


def load_articles(input_file: str = "output/articles.json") -> dict:
    """記事データをJSONファイルから読み込みます。"""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Articles file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stock_prices(input_file: str = "output/stock_prices.json") -> dict:
    """株価データをJSONファイルから読み込みます。"""
    if not os.path.exists(input_file):
        print(f"  Stock prices file not found: {input_file}")
        return None

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_account_info(input_file: str = "portfolio/account.json") -> dict:
    """口座情報（買付余力など）をJSONファイルから読み込みます。"""
    if not os.path.exists(input_file):
        print(f"  Account info file not found: {input_file}")
        return None

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_transaction_history(input_file: str = "portfolio/history.csv") -> list:
    """取引履歴をCSVファイルから読み込みます。"""
    if not os.path.exists(input_file):
        print(f"  Transaction history file not found: {input_file}")
        return []

    transactions = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(row)

    return transactions


def load_market_report(input_file: str = "output/market_report.md") -> str:
    """市場情勢レポートを読み込みます。"""
    if not os.path.exists(input_file):
        print(f"  Market report file not found: {input_file}")
        return ""

    with open(input_file, 'r', encoding='utf-8') as f:
        return f.read()


def create_portfolio_impact_prompt(
    articles: list,
    stock_prices: dict,
    account_info: dict,
    transactions: list,
    market_report: str
) -> str:
    """ポートフォリオ影響分析用のプロンプトを生成します。"""

    # 株価情報を整形
    portfolio_text = ""
    if stock_prices and stock_prices.get('stocks'):
        portfolio_summary = stock_prices.get('portfolio_summary', {})
        portfolio_text = f"""
## 現在のポートフォリオ状況

**ポートフォリオサマリー**:
- 総評価額: ¥{portfolio_summary.get('total_current_value', 0):,.0f}
- 総購入額: ¥{portfolio_summary.get('total_purchase_value', 0):,.0f}
- 総損益: ¥{portfolio_summary.get('total_gain_loss', 0):+,.0f} ({portfolio_summary.get('total_gain_loss_percent', 0):+.2f}%)

**保有銘柄**:
"""
        for stock in stock_prices['stocks']:
            portfolio_text += f"""
- **{stock['name']} ({stock['symbol']})**
  - 現在値: {stock['currency']} {stock['current_price']:,.2f} ({stock['change_percent']:+.2f}%)
  - 保有株数: {stock['shares']}株
  - 評価額: ¥{stock['current_value']:,.0f}
  - 損益: ¥{stock['gain_loss']:+,.0f} ({stock['gain_loss_percent']:+.2f}%)
"""

    # 口座情報を整形
    account_text = ""
    if account_info:
        account_text = f"""
## 口座情報
- 買付余力: ¥{account_info.get('buying_power', 0):,}
- 最終更新: {account_info.get('last_updated', 'N/A')}
"""

    # 取引履歴を整形（最新10件）
    history_text = ""
    if transactions:
        history_text = "\n## 直近の取引履歴\n"
        for tx in transactions[-10:]:
            action_emoji = "🟢" if tx['action'] == 'BUY' else "🔴"
            history_text += f"- {action_emoji} {tx['date']}: {tx['action']} {tx['symbol']} {tx['shares']}株 @ ¥{tx['price_per_share']} (理由: {tx['reason']})\n"

    # 記事の要約（主要なものだけ）
    articles_summary = ""
    for idx, article in enumerate(articles[:10], 1):
        articles_summary += f"- {article['title']} ({article['source']})\n"

    prompt = f"""
あなたはAI/IT関連の株式投資アドバイザーです。今日の市場情勢分析と現在のポートフォリオ状況を基に、具体的な売買示唆を提供してください。

{portfolio_text}
{account_text}
{history_text}

## 今日の主要ニュース
{articles_summary}

## 今日の市場情勢分析
{market_report}

## 出力フォーマット
以下のMarkdown形式でレポートを作成してください：

# ポートフォリオ影響分析レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## サマリー
（今日の市場情勢がポートフォリオに与える影響を3-5行で要約）

## ポートフォリオ現況
{portfolio_text if portfolio_text else "（ポートフォリオ情報が利用できません）"}

## 保有銘柄への影響分析
（各保有銘柄について、今日のニュースがどのような影響を与えるか分析）

### 買い増し検討銘柄
（保有銘柄の中で、今日のニュースを受けて買い増しを検討すべきもの）

### 利益確定検討銘柄
（保有銘柄の中で、利益確定を検討すべきもの）

### ホールド推奨銘柄
（現状維持が適切な銘柄）

## 新規購入候補
（ポートフォリオにない銘柄で、今日のニュースを受けて購入を検討すべきもの）
- 買付余力: ¥{account_info.get('buying_power', 0):,}を考慮

## 売却検討銘柄
（保有銘柄の中で、売却を検討すべきもの）

## 本日のアクション提案
（具体的な行動提案を優先度順に3-5個）

1. **[優先度: 高/中/低]** アクション内容
   - 銘柄:
   - 株数:
   - 理由:

## 明日以降の注目点
（今後注視すべきポイント）

---
*このレポートはAI（Gemini）により自動生成されています。投資判断は必ずご自身で行ってください。*
"""

    return prompt


def analyze_with_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Gemini APIを使用してテキストを分析します。"""
    try:
        print(f"Analyzing portfolio impact with {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        if not response.text:
            raise ValueError("Empty response from Gemini API")

        print("✓ Portfolio impact analysis completed")
        return response.text

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise


def save_report(report: str, output_file: str = "output/portfolio_impact_report.md"):
    """レポートをMarkdownファイルに保存します。"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Portfolio impact report saved to {output_file}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("Portfolio Impact Analysis - Daily Report Generator")
    print("=" * 60)

    # 記事データを読み込む
    print("\nLoading articles...")
    data = load_articles()
    articles = data.get('articles', [])
    print(f"✓ Loaded {len(articles)} articles")

    # 株価データを読み込む
    print("\nLoading stock prices...")
    stock_prices = load_stock_prices()
    if stock_prices:
        print(f"✓ Loaded stock prices for {len(stock_prices.get('stocks', []))} stocks")
    else:
        print("  (Stock prices not available)")

    # 口座情報を読み込む
    print("\nLoading account info...")
    account_info = load_account_info()
    if account_info:
        print(f"✓ Loaded account info (buying power: ¥{account_info.get('buying_power', 0):,})")
    else:
        print("  (Account info not available)")
        account_info = {"buying_power": 0}

    # 取引履歴を読み込む
    print("\nLoading transaction history...")
    transactions = load_transaction_history()
    print(f"✓ Loaded {len(transactions)} transactions")

    # 市場情勢レポートを読み込む
    print("\nLoading market report...")
    market_report = load_market_report()
    if market_report:
        print("✓ Loaded market report")
    else:
        print("  (Market report not available)")

    if len(articles) == 0 and not stock_prices:
        print("\nNo data available. Creating empty report...")
        empty_report = f"""# ポートフォリオ影響分析レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## サマリー
データが不足しているため、分析を実行できませんでした。

---
*このレポートはAI（Gemini）により自動生成されています。*
"""
        save_report(empty_report)
    else:
        # プロンプトを生成
        print("\nCreating portfolio impact analysis prompt...")
        prompt = create_portfolio_impact_prompt(
            articles, stock_prices, account_info, transactions, market_report
        )

        # Gemini APIで分析
        report = analyze_with_gemini(prompt)

        # レポートを保存
        save_report(report)

    print("\n" + "=" * 60)
    print("Portfolio impact analysis completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
