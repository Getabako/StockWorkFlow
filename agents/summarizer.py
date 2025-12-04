"""
SummarizerAgent（まとめ役）
日々の情勢をまとめ、レポートに仕立て上げるエージェント
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent


class SummarizerAgent(BaseAgent):
    """情報をまとめてレポートを作成するエージェント"""

    def __init__(self):
        super().__init__(
            name="SummarizerAgent",
            description="まとめ役 - 日々の情勢をまとめ、レポートに仕立て上げる"
        )
        self.skills = ["text_summarization", "report_generation", "analysis"]

    def load_ai_insights(self) -> Optional[Dict]:
        """AI業界トレンド知識ベースを読み込む"""
        try:
            return self.load_input("../data/ai_industry_insights.json")
        except FileNotFoundError:
            self.log("AI insights file not found", "WARNING")
            return None

    def create_analysis_prompt(self, articles: List[Dict], stock_prices: Optional[Dict] = None) -> str:
        """
        分析プロンプトを生成

        Args:
            articles: 記事のリスト
            stock_prices: 株価データ（オプション）

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

        prompt = f"""
あなたはAI/IT関連の株式投資アナリストです。以下のニュース記事とポートフォリオ情報から、投資判断に重要な「ファクト（事実）」を抽出・分析してください。

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

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - articles: 記事のリスト（ResearcherAgentからの出力）
                - stock_prices: 株価データ（オプション）

        Returns:
            実行結果
                - report: 生成されたレポート（Markdown形式）
                - report_date: レポート作成日時
        """
        self.log("Starting summarization...")

        articles = context.get("articles", [])
        stock_prices = context.get("stock_prices")

        if not articles:
            self.log("No articles to summarize", "WARNING")
            report = f"""# AI/IT株式投資 日次レポート
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## エグゼクティブサマリー
過去24時間において、重要なニュースは検出されませんでした。

---
*このレポートはAI（Gemini）により自動生成されています。*
"""
        else:
            # プロンプトを生成
            prompt = self.create_analysis_prompt(articles, stock_prices)

            # AIで分析
            self.log(f"Analyzing {len(articles)} articles...")
            report = self.generate(prompt)

        result = {
            "report": report,
            "report_date": datetime.now().isoformat(),
            "articles_count": len(articles)
        }

        # レポートを保存
        self.save_output(report, "daily_report.md", as_json=False)

        self.log("Summarization completed.")
        return result
