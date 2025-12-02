# YouTube API認証設定ガイド

このドキュメントでは、YouTube Data API v3の認証情報を設定する手順を説明します。

## 問題

以下のようなエラーが発生した場合、YouTubeのOAuth2リフレッシュトークンが期限切れになっています：

```
エラー: ('invalid_grant: Token has been expired or revoked.', {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})
```

## 解決手順

### 1. Google Cloud Consoleでの設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを選択（または新規作成）
3. 左側メニューから「APIとサービス」→「ライブラリ」を選択
4. 「YouTube Data API v3」を検索して有効化
5. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」を選択
6. アプリケーションの種類を「**デスクトップアプリ**」として作成
7. クライアントIDとクライアントシークレットをコピー

### 2. リフレッシュトークンの取得

プロジェクトのルートディレクトリで以下のコマンドを実行：

```bash
# 環境変数を設定（オプション）
export YOUTUBE_CLIENT_ID="your_client_id_here"
export YOUTUBE_CLIENT_SECRET="your_client_secret_here"

# リフレッシュトークン取得スクリプトを実行
python scripts/get_youtube_refresh_token.py
```

または、環境変数を設定せずに実行すると対話的に入力できます：

```bash
python scripts/get_youtube_refresh_token.py
```

スクリプトを実行すると：
1. ブラウザが自動的に開きます
2. Googleアカウントでログインします
3. アプリケーションに権限を付与します
4. 認証が完了すると、ターミナルにリフレッシュトークンが表示されます

### 3. GitHub Secretsの設定

1. GitHubリポジトリページにアクセス
2. 「Settings」→「Secrets and variables」→「Actions」を選択
3. 以下の3つのシークレットを追加/更新：

   - **YOUTUBE_CLIENT_ID**: Google Cloud Consoleで取得したクライアントID
   - **YOUTUBE_CLIENT_SECRET**: Google Cloud Consoleで取得したクライアントシークレット
   - **YOUTUBE_REFRESH_TOKEN**: スクリプトで取得したリフレッシュトークン

### 4. 動作確認

GitHub Actionsワークフローを再実行して、エラーが解消されたことを確認します。

## トラブルシューティング

### エラー: redirect_uri_mismatch

リダイレクトURIが一致しない場合、Google Cloud Consoleで以下を確認：
1. OAuth 2.0クライアントIDの設定を開く
2. 「承認済みのリダイレクト URI」に以下を追加：
   - `http://localhost:8080/`
   - `urn:ietf:wg:oauth:2.0:oob`

### エラー: Access blocked: This app's request is invalid

OAuth同意画面の設定が必要な場合：
1. Google Cloud Consoleで「OAuth同意画面」を設定
2. ユーザータイプを「外部」として作成
3. 必要な情報を入力して保存

### リフレッシュトークンが取得できない

1. YouTube Data API v3が有効化されているか確認
2. OAuth 2.0クライアントIDが「デスクトップアプリ」として作成されているか確認
3. ブラウザのキャッシュをクリアして再試行

## セキュリティ上の注意

- クライアントIDとシークレットは公開しないでください
- リフレッシュトークンは特に機密情報です
- GitHub Secretsは暗号化されて安全に保管されます
- ローカル環境では環境変数ファイル（.env）を使用し、Gitにコミットしないでください

## 参考リンク

- [YouTube Data API v3 ドキュメント](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 認証](https://developers.google.com/identity/protocols/oauth2)
- [GitHub Secrets の使用方法](https://docs.github.com/ja/actions/security-guides/encrypted-secrets)
