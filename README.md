# AI/IT株式投資 管理ワークフロー

GitHub Actionsを使用した、AI/IT関連株式投資の自動分析・レポートシステムです。

## 概要

このワークフローは以下の機能を提供します：

### 日次レポート（毎日早朝6:00 JST）
- AI/IT関連の重要ニュース（M&A、IR情報など）をRSSフィードから自動収集
- Gemini AIによる分析・要約
- リッチなHTML/PDFレポートの自動生成
- Discordへの自動通知

### 週次アクションレポート（毎週金曜20:00 JST）
- ポートフォリオの評価（株価取得・損益計算）
- 生活費捻出のための利確提案
- 定期買い付けのリマインド
- リッチなHTML/PDFレポートの自動生成
- Discordへの自動通知

## セットアップ手順

### 1. 必要なAPIキーの取得

以下のAPIキーを取得してください：

#### a) Google Gemini API Key
1. [Google AI Studio](https://ai.google.dev/aistudio) にアクセス
2. "Get API key" をクリックしてAPIキーを取得
3. 取得したキーを控えておく

#### b) Alpha Vantage API Key（株価取得用）
1. [Alpha Vantage](https://www.alphavantage.co/support/#api-key) にアクセス
2. 無料APIキーを取得
3. 取得したキーを控えておく

#### c) Discord Webhook URL
1. Discordで通知を受け取りたいチャンネルを開く
2. チャンネル設定 → 連携サービス → ウェブフック → 新しいウェブフック
3. ウェブフックURLをコピー

### 2. GitHub Secretsの設定

GitHubリポジトリの `Settings` → `Secrets and variables` → `Actions` に以下を追加：

| Secret名 | 説明 | 必須 |
|---------|------|------|
| `GEMINI_API_KEY` | Google Gemini APIキー | ✓ |
| `STOCK_API_KEY` | Alpha Vantage APIキー | ✓ |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | ✓ |
| `TDNET_RSS_URL` | 日本市場開示情報のRSS URL（オプション） | - |

### 3. ポートフォリオの設定

`data/portfolio.csv` を編集して、あなたの保有銘柄を入力してください：

```csv
symbol,name,shares,purchase_price
NVDA,NVIDIA Corporation,10,450.00
MSFT,Microsoft Corporation,15,350.00
```

**列の説明：**
- `symbol`: 株式シンボル（例: NVDA, MSFT, 7203.T）
- `name`: 企業名
- `shares`: 保有株数
- `purchase_price`: 取得単価（ドル）

### 4. ワークフローの有効化

1. リポジトリの `Actions` タブを開く
2. ワークフローを有効化
3. 初回は手動実行で動作確認を推奨：
   - `Daily AI/IT Stock News Report` を選択 → `Run workflow`
   - `Weekly Portfolio Action Plan` を選択 → `Run workflow`

### 5. レポートの閲覧・ダウンロード

**方法1: GitHubリポジトリから最新のHTMLレポートを閲覧**

最新のHTMLレポートは `report/` ディレクトリに自動保存されます：
- [report/daily_report.html](report/daily_report.html) - 最新の日次レポート
- [report/weekly_action_report.html](report/weekly_action_report.html) - 最新の週次レポート

ファイルをクリックして「Raw」ボタンからダウンロード後、ブラウザで開いてください。

**方法2: GitHub Actionsの成果物からダウンロード（PDF含む）**

1. `Actions` タブを開く
2. 実行されたワークフローを選択
3. `Artifacts` セクションから以下をダウンロード：
   - **日次レポート**: `daily-report-XXX` (MD, HTML, PDF含む、30日間保持)
   - **週次レポート**: `weekly-action-XXX` (MD, HTML, PDF, CSV含む、90日間保持)

ZIPファイルをダウンロード後、解凍してHTMLファイルをブラウザで開くか、PDFファイルを直接開いてください。

## レポート形式

レポートは **3つの形式** で生成されます：

### 📄 Markdown形式（.md）
- プレーンテキストベースの読みやすい形式
- Discordへの通知に使用

### 🎨 HTML形式（.html）
- リッチなデザインのWebページ形式
- グラデーション、シャドウ、カスタムフォント使用
- ブラウザで直接表示可能
- GitHub Actionsの成果物としてダウンロード可能

### 📑 PDF形式（.pdf）
- 印刷・共有に最適な形式
- HTMLと同じデザインを保持
- GitHub Actionsの成果物としてダウンロード可能

詳細は [HTML/PDF機能ドキュメント](docs/HTML_PDF_REPORTS.md) を参照してください。

## ディレクトリ構造

```
StockWorkFlow/
├── .github/
│   └── workflows/
│       ├── daily_report.yml           # 日次レポートワークフロー
│       └── weekly_action.yml          # 週次アクションワークフロー
├── scripts/
│   ├── fetch_data.py                  # ニュース収集スクリプト
│   ├── analyze_report.py              # AI分析スクリプト
│   ├── update_portfolio.py            # ポートフォリオ評価スクリプト
│   ├── generate_action.py             # アクション提案スクリプト
│   ├── send_to_discord.py             # Discord通知スクリプト
│   └── convert_report_to_html.py      # HTML/PDF変換スクリプト
├── data/
│   └── portfolio.csv                  # ポートフォリオデータ
├── docs/
│   └── HTML_PDF_REPORTS.md            # HTML/PDF機能ドキュメント
├── output/                            # 生成されたレポート（自動生成）
│   ├── daily_report.md                # 日次レポート（Markdown）
│   ├── daily_report.html              # 日次レポート（HTML）
│   ├── daily_report.pdf               # 日次レポート（PDF）
│   ├── weekly_action_report.md        # 週次レポート（Markdown）
│   ├── weekly_action_report.html      # 週次レポート（HTML）
│   └── weekly_action_report.pdf       # 週次レポート（PDF）
├── requirements.txt                   # Python依存関係
└── README.md                          # このファイル
```

## カスタマイズ

### 実行スケジュールの変更

ワークフローファイル（`.github/workflows/*.yml`）の `cron` 設定を編集してください：

```yaml
schedule:
  - cron: '0 21 * * *'  # 毎日 UTC 21:00 (JST 6:00)
```

[cron式の参考](https://crontab.guru/)

### 生活費捻出目標の変更

`scripts/generate_action.py` の以下の値を編集：

```python
MONTHLY_LIVING_EXPENSE_TARGET = 200000  # 月次目標（円）
MIN_PROFIT_THRESHOLD_PCT = 10.0         # 最低利益率（%）
```

### ニュースソースの追加

`scripts/fetch_data.py` の `RSS_FEEDS` 辞書に追加：

```python
{
    "name": "企業名",
    "url": "https://example.com/rss",
    "category": "カテゴリ"
}
```

## トラブルシューティング

### ワークフローが失敗する場合

1. GitHub Actionsの `Actions` タブでログを確認
2. Secretsが正しく設定されているか確認
3. APIキーの有効期限・利用制限を確認

### Alpha Vantage APIのレート制限

無料版は1分に5リクエストまでです。`update_portfolio.py` では自動的に待機時間を設けています。

保有銘柄が多い場合は、有料プランの検討または代替API（yfinanceなど）への切り替えをご検討ください。

### Discordに通知が届かない場合

1. Webhook URLが正しいか確認
2. Discord側でWebhookが削除されていないか確認
3. GitHub Actionsのログでエラーメッセージを確認

## 注意事項

- このシステムは投資判断の参考情報を提供するものであり、投資助言ではありません
- 最終的な投資判断はご自身の責任で行ってください
- APIの利用規約を遵守してください
- 個人情報・機密情報をリポジトリにコミットしないでください

## ライセンス

MIT License

## 免責事項

本ソフトウェアの使用により生じたいかなる損害についても、作者は責任を負いません。投資は自己責任で行ってください.
