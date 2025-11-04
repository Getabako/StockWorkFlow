#!/usr/bin/env python3
"""
アクション提案スクリプト (generate_action.py)
Gemini APIを使用してポートフォリオを分析し、週次の売買アクションを提案します。
"""

import pandas as pd
import os
import json
from datetime import datetime
import google.generativeai as genai

# Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

# 生活費捻出のルール（カスタマイズ可能）
MONTHLY_LIVING_EXPENSE_TARGET = 200000  # 月次目標: 20万円
WEEKLY_TARGET = MONTHLY_LIVING_EXPENSE_TARGET / 4  # 週次目標: 5万円
MIN_PROFIT_THRESHOLD_PCT = 10.0  # 売却候補の最低利益率: 10%


def load_portfolio_summary(file_path: str = "output/portfolio_summary.csv") -> pd.DataFrame:
    """
    ポートフォリオサマリーをCSVファイルから読み込みます。

    Args:
        file_path: ポートフォリオサマリーファイルのパス

    Returns:
        ポートフォリオのDataFrame
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Portfolio summary file not found: {file_path}")

    df = pd.read_csv(file_path)
    print(f"✓ Loaded portfolio summary with {len(df)} holdings")
    return df


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


def create_action_prompt(portfolio_df: pd.DataFrame, ai_insights: dict = None) -> str:
    """
    Gemini APIに送信するプロンプトを生成します。

    Args:
        portfolio_df: ポートフォリオのDataFrame
        ai_insights: AI業界トレンドデータ（オプション）

    Returns:
        プロンプト文字列
    """
    # ポートフォリオの概要
    total_value = portfolio_df['current_value'].sum()
    total_pl = portfolio_df['profit_loss'].sum()
    total_pl_pct = (total_pl / portfolio_df['purchase_value'].sum()) * 100

    # 含み益のある銘柄を抽出
    profitable_df = portfolio_df[
        (portfolio_df['profit_loss'] > 0) &
        (portfolio_df['profit_loss_pct'] >= MIN_PROFIT_THRESHOLD_PCT)
    ].sort_values('profit_loss', ascending=False)

    # ポートフォリオの詳細
    portfolio_text = ""
    for idx, row in portfolio_df.iterrows():
        portfolio_text += f"""
{row['symbol']} ({row.get('name', 'N/A')}):
  - 保有株数: {row['shares']}株
  - 取得単価: ${row['purchase_price']:.2f}
  - 現在価格: ${row['current_price']:.2f}
  - 評価額: ${row['current_value']:,.2f}
  - 損益: ${row['profit_loss']:,.2f} ({row['profit_loss_pct']:+.2f}%)
"""

    # 含み益銘柄の詳細
    profitable_text = ""
    if len(profitable_df) > 0:
        for idx, row in profitable_df.iterrows():
            profitable_text += f"""
- {row['symbol']}: 損益 ${row['profit_loss']:,.2f} ({row['profit_loss_pct']:+.2f}%)
  評価額: ${row['current_value']:,.2f}, 保有株数: {row['shares']}株
"""
    else:
        profitable_text = "（利益率10%以上の含み益銘柄はありません）"

    # AI業界トレンド情報を整形
    ai_insights_text = ""
    if ai_insights:
        overview = ai_insights.get('industry_overview', {})
        investment_implications = ai_insights.get('investment_implications', {})
        recommended_actions = ai_insights.get('recommended_actions', {})
        watch_list = ai_insights.get('watch_list_companies', {})

        ai_insights_text = f"""
## AI業界トレンドに基づく投資戦略

**業界の現状**:
- {overview.get('market_status', '')}

**主要リスク**:
"""
        for risk in overview.get('key_risks', []):
            ai_insights_text += f"- {risk}\n"

        ai_insights_text += "\n**短期的な投資示唆**:\n"
        for implication in investment_implications.get('short_term', []):
            ai_insights_text += f"- {implication}\n"

        ai_insights_text += "\n**推奨アクション**:\n"
        for action in recommended_actions.get('portfolio_optimization', []):
            ai_insights_text += f"- {action}\n"

        ai_insights_text += "\n**リスク管理**:\n"
        for risk_action in recommended_actions.get('risk_management', []):
            ai_insights_text += f"- {risk_action}\n"

        # 現在保有している銘柄に関連する情報を抽出
        portfolio_symbols = portfolio_df['symbol'].tolist()
        ai_insights_text += "\n**保有銘柄に関する業界トレンド**:\n"
        for tier in ['tier_1_critical', 'tier_2_strategic']:
            if tier in watch_list:
                for company in watch_list[tier]:
                    symbol = company.get('symbol', '')
                    if symbol in portfolio_symbols or company.get('portfolio_status') == '保有中':
                        ai_insights_text += f"- **{company['name']} ({symbol})**: {company['role']}\n"
                        for point in company.get('key_points', [])[:2]:
                            ai_insights_text += f"  - {point}\n"

    prompt = f"""
あなたはAI/IT株式投資のアドバイザーです。以下のポートフォリオを分析し、週次の売買アクションを提案してください。

{ai_insights_text if ai_insights_text else ""}

## 投資方針
1. **長期資産増額**: 基本的には長期保有を前提とし、有望銘柄は保持する
2. **生活費捻出**: 週次で約${WEEKLY_TARGET:,.0f}（月次${MONTHLY_LIVING_EXPENSE_TARGET:,.0f}）の利確を目標とする
3. **利確ルール**:
   - 含み益が{MIN_PROFIT_THRESHOLD_PCT}%以上の銘柄から売却を検討
   - ただし、今後も成長が見込める銘柄は一部保持も検討
   - 複数銘柄から少しずつ利確することでリスク分散

## ポートフォリオ概要
- 総評価額: ${total_value:,.2f}
- 総損益: ${total_pl:,.2f} ({total_pl_pct:+.2f}%)
- 保有銘柄数: {len(portfolio_df)}

## 全銘柄の詳細
{portfolio_text}

## 含み益銘柄（利益率{MIN_PROFIT_THRESHOLD_PCT}%以上）
{profitable_text}

## 出力フォーマット
以下のMarkdown形式で週次アクションレポートを作成してください：

# AI/IT株式投資 週次アクションレポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## ポートフォリオサマリー
（現在の資産状況を2-3行で要約）

## 今週の推奨アクション

### 1. 生活費捻出のための利確提案
**目標金額**: ${WEEKLY_TARGET:,.0f}

（以下の形式で具体的な売却提案を記載）
- **[銘柄シンボル]**: X株売却 → 約$X,XXX の利確
  - 理由: （なぜこの銘柄を選んだか、一部保持する場合はその理由も）

**合計利確見込額**: $X,XXX

### 2. 定期買い付けリマインド
（定期的に積み立てるべき有望銘柄があれば提案）

### 3. ポートフォリオ最適化の提案
（リバランスや、注意すべき銘柄があれば記載）

## 来週の注意事項
（業績発表予定や、市場イベントで注意すべき点があれば記載）

---
*このレポートはAI（Gemini）により自動生成されています。最終的な投資判断はご自身で行ってください。*
"""

    return prompt


def generate_action_with_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Gemini APIを使用してアクション提案を生成します。

    Args:
        prompt: プロンプト
        model_name: 使用するGeminiモデル

    Returns:
        生成されたレポート
    """
    try:
        print(f"Generating action plan with {model_name}...")
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(prompt)

        if not response.text:
            raise ValueError("Empty response from Gemini API")

        print("✓ Action plan generated")
        return response.text

    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise


def save_action_report(report: str, output_file: str = "output/weekly_action_report.md"):
    """
    アクションレポートをMarkdownファイルに保存します。

    Args:
        report: レポート内容
        output_file: 出力ファイルパス
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Action report saved to {output_file}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Stock Investment - Action Plan Generator")
    print("=" * 60)

    # ポートフォリオサマリーを読み込む
    print("\nLoading portfolio summary...")
    portfolio_df = load_portfolio_summary()

    # AI業界トレンドデータを読み込む
    print("\nLoading AI industry insights...")
    ai_insights = load_ai_insights()
    if ai_insights:
        print(f"✓ Loaded AI industry insights (last updated: {ai_insights.get('last_updated', 'N/A')})")
    else:
        print("  (AI industry insights not available)")

    # プロンプトを生成
    print("\nCreating action prompt...")
    prompt = create_action_prompt(portfolio_df, ai_insights)

    # Gemini APIでアクション提案を生成
    report = generate_action_with_gemini(prompt)

    # レポートを保存
    save_action_report(report)

    print("\n" + "=" * 60)
    print("Action plan generation completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
