#!/usr/bin/env python3
"""
市場情勢分析レポート生成スクリプト (analyze_market.py)
Gemini APIを使用してニュース記事を分析し、AI/IT市場の重要なファクトを抽出します。
このレポートはスライド・動画化の対象となります。
"""

import json
import os
from datetime import datetime
from google import genai

# Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# 新しいGoogle GenAI SDKのクライアントを作成
client = genai.Client(api_key=GEMINI_API_KEY)


def load_articles(input_file: str = "output/articles.json") -> dict:
    """記事データをJSONファイルから読み込みます。"""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Articles file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ai_insights(input_file: str = "data/ai_industry_insights.json") -> dict:
    """AI業界トレンド知識ベースをJSONファイルから読み込みます。"""
    if not os.path.exists(input_file):
        print(f"  AI insights file not found: {input_file}")
        return None

    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_market_analysis_prompt(articles: list, ai_insights: dict = None) -> str:
    """市場情勢分析用のプロンプトを生成します。"""

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

    # AI業界トレンド情報を整形
    ai_insights_text = ""
    if ai_insights:
        overview = ai_insights.get('industry_overview', {})
        watch_list = ai_insights.get('watch_list_companies', {})

        ai_insights_text = f"""
## AI業界トレンド分析の文脈

**業界の現状**:
- {overview.get('market_status', '')}

**重要な業界トレンド**:
"""
        for trend in overview.get('key_trends', []):
            ai_insights_text += f"- {trend}\n"

        ai_insights_text += "\n**注目すべき企業**:\n"
        for tier in ['tier_1_critical', 'tier_2_strategic']:
            if tier in watch_list:
                for company in watch_list[tier]:
                    ai_insights_text += f"- **{company['name']}**: {company['role']}\n"

    prompt = f"""
あなたはAI/IT業界の市場アナリストです。以下のニュース記事から、AI/IT業界の市場動向を分析してください。

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

## 出力フォーマット
以下のMarkdown形式でレポートを作成してください：

# AI/IT市場 日次情勢レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー
（3-5行で全体の要約。今日の市場の注目ポイントを簡潔に）

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

## 今日の注目ポイント
（今日のニュースで特に注目すべき点を2-3行で）

---
*このレポートはAI（Gemini）により自動生成されています。*
"""

    return prompt


def analyze_with_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Gemini APIを使用してテキストを分析します。"""
    try:
        print(f"Analyzing with {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        if not response.text:
            raise ValueError("Empty response from Gemini API")

        print("✓ Market analysis completed")
        return response.text

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise


def save_report(report: str, output_file: str = "output/market_report.md"):
    """レポートをMarkdownファイルに保存します。"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Market report saved to {output_file}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Market Analysis - Daily Report Generator")
    print("=" * 60)

    # 記事データを読み込む
    print("\nLoading articles...")
    data = load_articles()
    articles = data.get('articles', [])
    print(f"✓ Loaded {len(articles)} articles")

    # AI業界トレンドデータを読み込む
    print("\nLoading AI industry insights...")
    ai_insights = load_ai_insights()
    if ai_insights:
        print(f"✓ Loaded AI industry insights")
    else:
        print("  (AI industry insights not available)")

    if len(articles) == 0:
        print("\nNo articles found. Creating empty report...")
        empty_report = f"""# AI/IT市場 日次情勢レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー
過去24時間において、重要なニュースは検出されませんでした。

---
*このレポートはAI（Gemini）により自動生成されています。*
"""
        save_report(empty_report)
    else:
        # プロンプトを生成
        print("\nCreating market analysis prompt...")
        prompt = create_market_analysis_prompt(articles, ai_insights)

        # Gemini APIで分析
        report = analyze_with_gemini(prompt)

        # レポートを保存
        save_report(report)

    print("\n" + "=" * 60)
    print("Market analysis completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
