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

# 投資方針設定（カスタマイズ可能）
INVESTMENT_BUDGET_JPY = 3000000  # 追加投資予算: 300万円
INVESTMENT_BUDGET_USD = 20000  # 追加投資予算（USD換算、1ドル=150円想定）
FOCUS_ON_BUYING = True  # 買い推奨をメインにする
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
あなたはAI/IT株式投資の教育的アドバイザーです。投資初心者が自分で考えて判断できるよう、詳細な分析と理由を提供してください。

{ai_insights_text if ai_insights_text else ""}

## 投資方針と現状
1. **投資ステージ**: ポートフォリオ構築期（買い増し段階）
2. **追加投資予算**: 約¥{INVESTMENT_BUDGET_JPY:,}（約${INVESTMENT_BUDGET_USD:,}）
3. **投資目標**:
   - 有望な AI/IT 銘柄を選定し、分散投資でポートフォリオを構築
   - 各銘柄の選定理由と懸念点を理解した上で投資判断
   - 投資を通じて株式投資スキルを向上させる
4. **基本方針**:
   - 長期保有を前提とした成長株投資
   - まずは買い増しを優先し、利確は後回し
   - 分散投資でリスクを管理
   - 予算を考慮し、現実的な投資額と株数を提案

## 現在のポートフォリオ概要
- 総評価額: ${total_value:,.2f}
- 総損益: ${total_pl:,.2f} ({total_pl_pct:+.2f}%)
- 保有銘柄数: {len(portfolio_df)}

## 全銘柄の詳細
{portfolio_text}

## 出力フォーマット
以下のMarkdown形式で、**教育的で詳細な**週次アクションレポートを作成してください：

# AI/IT株式投資 週次アクションレポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## 📊 ポートフォリオサマリー
（現在の資産状況を2-3行で要約）

## 🎯 今週の投資推奨銘柄

### 推奨度 A（今週特に注目すべき銘柄）

#### 1. [銘柄名] ([シンボル])
**現在価格**: $XXX.XX
**推奨投資額**: $X,XXX - $X,XXX（予算¥3,000,000 = 約$20,000の範囲内で現実的な金額）
**推奨株数**: XX-XX株

**📈 選定ポイント（買うべき理由）**:
1. （具体的な成長要因やビジネスの強み）
2. （財務状況や業績の良さ）
3. （AI/IT業界でのポジション）
4. （最近のニュースやイベント）

**⚠️ 懸念点（リスク）**:
1. （考えられるリスク要因）
2. （競合や市場環境の懸念）
3. （株価の割高感など）

**💡 推奨される買い方**:
- **戦略**: （例：一括購入 / 分割購入）
- **理由**: （なぜその買い方が良いのか）
- **具体例**: （例：今週$2,000で5株、来週$3,000で7株など、予算内で分散）
- **エントリーポイント**: （理想的な買い場のタイミング）

**重要**: 追加投資予算は約$20,000（¥3,000,000）です。複数銘柄への分散投資を考慮し、1銘柄あたりの推奨投資額は$2,000〜$8,000程度の現実的な範囲で提案してください。

---

#### 2. [2番目の推奨銘柄...]
（同様の形式で記載）

---

### 推奨度 B（検討の価値がある銘柄）

#### 1. [銘柄名] ([シンボル])
（同様の形式で簡潔に記載）

---

## 🔍 保有銘柄の状況分析

### [保有銘柄シンボル1]
**現在の状況**: （損益、保有株数など）
**今週のアクション**:
- ホールド推奨 / 追加購入検討 / 一部利確検討
- **理由**: （なぜそのアクションが良いのか）

（保有銘柄すべてについて記載）

---

## 📚 今週の投資スキル向上ポイント

### 学習テーマ: [今週学ぶべきこと]
（例：「セクター分析の重要性」「PER/PBRの読み方」など）

**解説**:
（投資判断に役立つ知識を1-2段落で説明）

**今週のレポートへの適用**:
（上記の推奨銘柄のどこでこの知識が使われているか）

---

## 📅 来週の注目イベント
- （決算発表予定の銘柄）
- （重要な経済指標発表）
- （業界イベントなど）

---

## 💭 投資判断のためのチェックリスト

今週の推奨銘柄を検討する際、以下の点を自分で考えてみましょう：

□ この銘柄の事業内容を理解できているか？
□ なぜ今この銘柄が成長すると考えるか？
□ 懸念点を受け入れられるか？
□ 自分のポートフォリオに必要な銘柄か？
□ 投資額は自分のリスク許容度に合っているか？

---

*このレポートは教育目的で詳細な分析を提供していますが、最終的な投資判断は必ずご自身で行ってください。*
*推奨内容を鵜呑みにせず、自分で考えて判断することが投資スキル向上への第一歩です。*
"""

    return prompt


def generate_action_with_gemini(prompt: str, model_name: str = "gemini-2.5-pro") -> str:
    """
    Gemini APIを使用してアクション提案を生成します。

    教育的で詳細な分析が必要なため、Pro モデルを使用します。

    Args:
        prompt: プロンプト
        model_name: 使用するGeminiモデル（デフォルト: gemini-2.5-pro）

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
