#!/usr/bin/env python3
"""
AI分析・レポート生成スクリプト (analyze_report.py)
Gemini APIを使用してニュース記事を分析し、重要なファクトを抽出します。
"""

import json
import os
from datetime import datetime
import google.generativeai as genai

# Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)


def load_articles(input_file: str = "output/articles.json") -> dict:
    """
    記事データをJSONファイルから読み込みます。

    Args:
        input_file: 入力ファイルパス

    Returns:
        記事データ
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Articles file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stock_prices(input_file: str = "output/stock_prices.json") -> dict:
    """
    株価データをJSONファイルから読み込みます。

    Args:
        input_file: 入力ファイルパス

    Returns:
        株価データ（ファイルが存在しない場合はNone）
    """
    if not os.path.exists(input_file):
        print(f"  Stock prices file not found: {input_file}")
        return None

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ai_insights(input_file: str = "data/ai_industry_insights.json") -> dict:
    """
    AI業界トレンド知識ベースをJSONファイルから読み込みます。

    Args:
        input_file: 入力ファイルパス

    Returns:
        AI業界トレンドデータ（ファイルが存在しない場合はNone）
    """
    if not os.path.exists(input_file):
        print(f"  AI insights file not found: {input_file}")
        return None

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_analysis_prompt(articles: list, stock_prices: dict = None, ai_insights: dict = None) -> str:
    """
    Gemini APIに送信するプロンプトを生成します。

    Args:
        articles: 記事のリスト
        stock_prices: 株価データ（オプション）
        ai_insights: AI業界トレンドデータ（オプション）

    Returns:
        プロンプト文字列
    """
    # 記事を整形
    articles_text = ""
    for idx, article in enumerate(articles, 1):
        articles_text += f"""
---
記事 {idx}:
情報源: {article['source']} ({article['category']})
タイトル: {article['title']}
リンク: {article['link']}
公開日: {article['published']}
概要: {article['summary']}
"""

    # 株価情報を整形
    portfolio_text = ""
    if stock_prices and stock_prices.get('stocks'):
        portfolio_summary = stock_prices.get('portfolio_summary', {})
        portfolio_text = f"""
## ポートフォリオ現在値（{datetime.now().strftime('%Y年%m月%d日')}時点）

**ポートフォリオサマリー**:
- 総評価額: {portfolio_summary.get('total_current_value', 0):,.2f}
- 総購入額: {portfolio_summary.get('total_purchase_value', 0):,.2f}
- 総損益: {portfolio_summary.get('total_gain_loss', 0):+,.2f} ({portfolio_summary.get('total_gain_loss_percent', 0):+.2f}%)

**保有銘柄**:
"""
        for stock in stock_prices['stocks']:
            portfolio_text += f"""
- **{stock['name']} ({stock['symbol']})**
  - 現在値: {stock['currency']} {stock['current_price']:,.2f} ({stock['change_percent']:+.2f}%)
  - 保有株数: {stock['shares']}株
  - 評価額: {stock['currency']} {stock['current_value']:,.2f}
  - 損益: {stock['currency']} {stock['gain_loss']:+,.2f} ({stock['gain_loss_percent']:+.2f}%)
"""

    # AI業界トレンド情報を整形
    ai_insights_text = ""
    if ai_insights:
        overview = ai_insights.get('industry_overview', {})
        key_concepts = ai_insights.get('key_concepts', {})
        watch_list = ai_insights.get('watch_list_companies', {})

        ai_insights_text = f"""
## AI業界トレンド分析の文脈

**業界の現状**:
- {overview.get('market_status', '')}

**主要リスク**:
"""
        for risk in overview.get('key_risks', []):
            ai_insights_text += f"- {risk}\n"

        ai_insights_text += "\n**重要な業界トレンド**:\n"
        for trend in overview.get('key_trends', []):
            ai_insights_text += f"- {trend}\n"

        ai_insights_text += "\n**注目すべき企業と理由**:\n"
        for tier in ['tier_1_critical', 'tier_2_strategic']:
            if tier in watch_list:
                for company in watch_list[tier]:
                    ai_insights_text += f"- **{company['name']} ({company.get('symbol', 'N/A')})**: {company['role']}\n"

        ai_insights_text += "\n**特に注意すべき概念**:\n"
        if 'cross_sell_economy' in key_concepts:
            cse = key_concepts['cross_sell_economy']
            ai_insights_text += f"- **クロスセル経済圏**: {cse['description']} (リスクレベル: {cse['risk_level']})\n"
        if 'semiconductor_geopolitics' in key_concepts:
            sg = key_concepts['semiconductor_geopolitics']
            ai_insights_text += f"- **半導体地政学リスク**: {sg['description']}\n"

    prompt = f"""
あなたはAI/IT関連の株式投資アナリストです。以下のニュース記事とポートフォリオ情報から、投資判断に重要な「ファクト（事実）」を抽出・分析してください。

{ai_insights_text if ai_insights_text else ""}

特に以下の情報を重点的に探してください：
1. **M&A（企業買収・合併）**: 企業の統合や買収の発表
2. **戦略的提携・パートナーシップ**: 企業間の重要な協業
3. **大型契約**: 大規模な受注や契約の締結
4. **新製品・新技術の発表**: 市場に影響を与える革新的な製品やサービス
5. **業績発表**: 四半期決算や業績予想の修正
6. **規制・政策変更**: 業界に影響を与える法規制の変更
7. **人事**: 重要なCレベルの人事異動

## 入力記事（過去24時間）
{articles_text}
{portfolio_text}

## 出力フォーマット
以下のMarkdown形式でレポートを作成してください：

# AI/IT株式投資 日次レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー
（3-5行で全体の要約。ポートフォリオの状況にも簡単に言及）

## ポートフォリオ状況
{portfolio_text if portfolio_text else "（ポートフォリオ情報が利用できません）"}

## 重要ファクト
### M&A・企業買収
（該当する情報がある場合のみ記載）

### 戦略的提携・パートナーシップ
（該当する情報がある場合のみ記載）

### 大型契約・受注
（該当する情報がある場合のみ記載）

### 新製品・新技術
（該当する情報がある場合のみ記載）

### 業績・財務情報
（該当する情報がある場合のみ記載）

### その他の重要情報
（該当する情報がある場合のみ記載）

## 投資への示唆
（今回のニュースが投資判断にどう影響するか、2-3行で簡潔に）

---
*このレポートはAI（Gemini）により自動生成されています。投資判断は必ずご自身で行ってください。*
"""

    return prompt


def analyze_with_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Gemini APIを使用してテキストを分析します。

    Args:
        prompt: 分析プロンプト
        model_name: 使用するGeminiモデル

    Returns:
        分析結果
    """
    try:
        print(f"Analyzing with {model_name}...")
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(prompt)

        if not response.text:
            raise ValueError("Empty response from Gemini API")

        print("✓ Analysis completed")
        return response.text

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise


def save_report(report: str, output_file: str = "output/daily_report.md"):
    """
    レポートをMarkdownファイルに保存します。

    Args:
        report: レポート内容
        output_file: 出力ファイルパス
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Report saved to {output_file}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Stock Investment - Analysis & Report Generator")
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

    # AI業界トレンドデータを読み込む
    print("\nLoading AI industry insights...")
    ai_insights = load_ai_insights()
    if ai_insights:
        print(f"✓ Loaded AI industry insights (last updated: {ai_insights.get('last_updated', 'N/A')})")
    else:
        print("  (AI industry insights not available)")

    if len(articles) == 0:
        print("\nNo articles found. Creating empty report...")
        empty_report = f"""# AI/IT株式投資 日次レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー
過去24時間において、重要なニュースは検出されませんでした。

---
*このレポートはAI（Gemini）により自動生成されています。*
"""
        save_report(empty_report)
    else:
        # プロンプトを生成
        print("\nCreating analysis prompt...")
        prompt = create_analysis_prompt(articles, stock_prices, ai_insights)

        # Gemini APIで分析
        report = analyze_with_gemini(prompt)

        # レポートを保存
        save_report(report)

    print("\n" + "=" * 60)
    print("Analysis completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
