# HTML/PDFレポート生成機能

## 概要
Markdownで生成されたレポートを、リッチなHTML/CSSデザインに変換し、PDF形式でもダウンロードできるようにする機能です。

## 機能
- ✅ MarkdownレポートをリッチなデザインのHTMLに変換
- ✅ グラデーション、シャドウ、カスタムフォントを使用した美しいデザイン
- ✅ PDFファイルの自動生成
- ✅ GitHub Actionsでの自動実行
- ✅ HTMLとPDFの両方をアーティファクトとしてダウンロード可能

## 生成されるファイル

### 日次レポート
- `output/daily_report.md` - Markdownレポート（既存）
- `output/daily_report.html` - HTMLレポート（新規）
- `output/daily_report.pdf` - PDFレポート（新規）

### 週次アクションレポート
- `output/weekly_action_report.md` - Markdownレポート（既存）
- `output/weekly_action_report.html` - HTMLレポート（新規）
- `output/weekly_action_report.pdf` - PDFレポート（新規）

## デザイン特徴

### カラースキーム
- **プライマリカラー**: 青系グラデーション（#2563eb → #0ea5e9）
- **成功色**: グリーン（#10b981）
- **警告色**: オレンジ（#f59e0b）
- **エラー色**: レッド（#ef4444）

### レイアウト
- グラデーション背景のヘッダー
- カード型のコンテンツエリア
- セクションごとのビジュアル区切り
- テーブル、リスト、引用の美しいスタイリング
- レスポンシブデザイン対応

### タイポグラフィ
- **日本語**: Noto Sans JP
- **英語**: Roboto
- 見出しサイズの階層化
- 読みやすい行間設定

## 使用方法

### 1. ローカルでの変換

#### 仮想環境のセットアップ
```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

#### 個別ファイルの変換
```bash
# 特定のMarkdownファイルを変換
python scripts/convert_report_to_html.py output/daily_report.md

# 出力先ディレクトリを指定
python scripts/convert_report_to_html.py output/daily_report.md output/
```

#### すべてのレポートを変換
```bash
# デフォルトレポートをすべて変換
python scripts/convert_report_to_html.py
```

### 2. GitHub Actionsでの自動実行

GitHub Actionsワークフローは自動的にHTML/PDF変換を実行します：

#### 日次レポート
- **トリガー**: 毎日 JST 6:00 (UTC 21:00)
- **手動実行**: Actions タブから "Daily AI/IT Stock News Report" を選択して実行
- **成果物**: Artifacts からHTML/PDFをダウンロード可能（30日間保持）

#### 週次アクションレポート
- **トリガー**: 毎週金曜日 JST 20:00 (UTC 11:00)
- **手動実行**: Actions タブから "Weekly Portfolio Action Plan" を選択して実行
- **成果物**: Artifacts からHTML/PDFをダウンロード可能（90日間保持）

### 3. GitHub Actionsの成果物のダウンロード

1. GitHubリポジトリの **Actions** タブを開く
2. 実行されたワークフローを選択
3. **Artifacts** セクションから以下をダウンロード：
   - `daily-report-XXX` - 日次レポート（MD、HTML、PDF含む）
   - `weekly-action-XXX` - 週次レポート（MD、HTML、PDF、CSV含む）

## 技術仕様

### 依存関係
```
markdown>=3.5.0      # Markdown → HTML変換
weasyprint>=60.0     # HTML → PDF変換
pygments>=2.17.0     # コードハイライト
```

### 変換スクリプト
- **ファイル**: `scripts/convert_report_to_html.py`
- **入力**: Markdownファイル (.md)
- **出力**: HTMLファイル (.html) + PDFファイル (.pdf)

### Markdown拡張機能
- `extra` - テーブル、脚注、属性リスト
- `codehilite` - コードブロックのシンタックスハイライト
- `toc` - 目次の自動生成
- `nl2br` - 改行を自動的に<br>タグに変換
- `sane_lists` - リスト処理の改善

## トラブルシューティング

### PDF生成エラー
WeasyPrintはシステムフォントに依存します。以下を確認してください：

**macOS**:
```bash
brew install pango cairo gdk-pixbuf libffi
```

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 \
    libharfbuzz0b libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**Windows**:
GTK+ for Windows をインストール:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

### フォント関連の警告
Google FontsのNoto Sans JPとRobotoを使用しています。オフライン環境ではデフォルトフォントにフォールバックされます。

## カスタマイズ

### デザインの変更
`scripts/convert_report_to_html.py` の `get_html_template()` 関数内のCSSを編集してください。

### カラースキームの変更
`:root` 内のCSS変数を変更：
```css
:root {
    --primary-color: #2563eb;      /* メインカラー */
    --secondary-color: #0ea5e9;    /* セカンダリカラー */
    --success-color: #10b981;      /* 成功色 */
    /* ... */
}
```

### レイアウトの調整
各セクションのCSSクラスを編集：
- `.header` - ヘッダー部分
- `.content` - メインコンテンツ
- `.footer` - フッター部分
- `h1`, `h2`, `h3` - 見出しスタイル

## ワークフローの統合

### 既存ワークフローの更新内容

#### `.github/workflows/daily_report.yml`
```yaml
- name: Convert report to HTML/PDF
  if: success()
  run: |
    python scripts/convert_report_to_html.py output/daily_report.md

- name: Upload report as artifact
  if: always()
  uses: actions/upload-artifact@v4
  with:
    path: |
      output/daily_report.md
      output/daily_report.html
      output/daily_report.pdf
```

#### `.github/workflows/weekly_action.yml`
```yaml
- name: Convert report to HTML/PDF
  if: success()
  run: |
    python scripts/convert_report_to_html.py output/weekly_action_report.md

- name: Upload reports as artifact
  if: always()
  uses: actions/upload-artifact@v4
  with:
    path: |
      output/weekly_action_report.md
      output/weekly_action_report.html
      output/weekly_action_report.pdf
```

## 今後の拡張案

- [ ] インタラクティブなチャート（Chart.js）の追加
- [ ] ダークモード対応
- [ ] 複数テーマの選択機能
- [ ] メール配信機能（HTML添付）
- [ ] Webホスティング（GitHub Pages）
- [ ] カスタムロゴの追加
- [ ] 署名/電子印鑑機能

## サンプル

サンプルレポートが `output/sample_daily_report.md` として提供されています。
これを使用して変換をテストできます：

```bash
python scripts/convert_report_to_html.py output/sample_daily_report.md
```

生成されたHTML/PDFファイルを開いて、デザインを確認してください。
