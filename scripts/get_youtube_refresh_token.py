#!/usr/bin/env python3
"""
YouTube OAuth2 リフレッシュトークン取得スクリプト

このスクリプトを使用して、YouTube Data API v3のリフレッシュトークンを取得します。

使い方:
1. Google Cloud ConsoleでOAuth 2.0クライアントIDを作成
2. クライアントIDとシークレットを環境変数に設定
3. このスクリプトを実行してブラウザで認証
4. 取得したリフレッシュトークンをGitHub Secretsに設定
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def get_refresh_token(client_id, client_secret):
    """
    YouTube APIのリフレッシュトークンを取得します。

    Args:
        client_id: Google Cloud ConsoleのクライアントID
        client_secret: Google Cloud Consoleのクライアントシークレット

    Returns:
        リフレッシュトークン文字列
    """
    # OAuth2クライアント設定
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }

    # 認証フローを開始
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES
    )

    # ローカルサーバーを起動して認証
    print("\n" + "=" * 60)
    print("YouTube API 認証")
    print("=" * 60)
    print("\nブラウザが開きます。Googleアカウントでログインし、")
    print("アプリケーションに権限を付与してください。")
    print("\n")

    # ポート8080が使用中の場合に備えて、複数のポートを試す
    ports_to_try = [8080, 8888, 9090, 8000]
    credentials = None

    for port in ports_to_try:
        try:
            print(f"ポート {port} で認証を試みています...")
            credentials = flow.run_local_server(
                port=port,
                prompt='consent',
                success_message='認証が完了しました！このウィンドウを閉じてターミナルに戻ってください。'
            )
            break
        except OSError as e:
            if "10048" in str(e) or "address already in use" in str(e).lower():
                print(f"ポート {port} は使用中です。別のポートを試します...")
                continue
            else:
                raise

    if not credentials:
        raise Exception("利用可能なポートが見つかりませんでした。")

    return credentials.refresh_token


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='YouTube OAuth2 リフレッシュトークン取得ツール')
    parser.add_argument('--client-id', help='Google Cloud ConsoleのクライアントID')
    parser.add_argument('--client-secret', help='Google Cloud Consoleのクライアントシークレット')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("YouTube OAuth2 リフレッシュトークン取得ツール")
    print("=" * 60)
    print()

    # コマンドライン引数 → 環境変数 → 対話的入力の順で取得
    client_id = args.client_id or os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = args.client_secret or os.environ.get('YOUTUBE_CLIENT_SECRET')

    # 環境変数が設定されていない場合は対話的に入力
    if not client_id:
        print("YOUTUBE_CLIENT_ID環境変数が設定されていません。")
        try:
            client_id = input("Google Cloud ConsoleのクライアントIDを入力してください: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nエラー: 対話的な入力ができない環境です。")
            print("以下のいずれかの方法で実行してください:")
            print("1. コマンドライン引数で指定:")
            print("   python scripts/get_youtube_refresh_token.py --client-id YOUR_ID --client-secret YOUR_SECRET")
            print("2. 環境変数を設定:")
            print("   set YOUTUBE_CLIENT_ID=YOUR_ID")
            print("   set YOUTUBE_CLIENT_SECRET=YOUR_SECRET")
            sys.exit(1)

    if not client_secret:
        print("YOUTUBE_CLIENT_SECRET環境変数が設定されていません。")
        try:
            client_secret = input("Google Cloud Consoleのクライアントシークレットを入力してください: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nエラー: 対話的な入力ができない環境です。")
            print("コマンドライン引数で指定してください:")
            print("python scripts/get_youtube_refresh_token.py --client-id YOUR_ID --client-secret YOUR_SECRET")
            sys.exit(1)

    if not client_id or not client_secret:
        print("\nエラー: クライアントIDとシークレットが必要です。")
        print("\nGoogle Cloud Consoleでの設定手順:")
        print("1. https://console.cloud.google.com/ にアクセス")
        print("2. プロジェクトを選択または作成")
        print("3. 「APIとサービス」→「ライブラリ」から「YouTube Data API v3」を有効化")
        print("4. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」を選択")
        print("5. アプリケーションの種類を「デスクトップアプリ」として作成")
        print("6. クライアントIDとシークレットをコピー")
        sys.exit(1)

    try:
        # リフレッシュトークンを取得
        refresh_token = get_refresh_token(client_id, client_secret)

        if not refresh_token:
            print("\n❌ エラー: リフレッシュトークンの取得に失敗しました。")
            sys.exit(1)

        # 結果を表示
        print("\n" + "=" * 60)
        print("✓ リフレッシュトークンの取得に成功しました！")
        print("=" * 60)
        print("\n以下の情報をGitHub Secretsに設定してください:\n")
        print(f"YOUTUBE_CLIENT_ID={client_id}")
        print(f"YOUTUBE_CLIENT_SECRET={client_secret}")
        print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
        print("\n" + "=" * 60)
        print("\nGitHub Secretsの設定方法:")
        print("1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」")
        print("2. 「New repository secret」をクリック")
        print("3. 上記の3つのシークレットを追加")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\nトラブルシューティング:")
        print("- Google Cloud ConsoleでYouTube Data API v3が有効化されているか確認")
        print("- OAuth 2.0クライアントIDが「デスクトップアプリ」として作成されているか確認")
        print("- リダイレクトURIに http://localhost:8080/ が含まれているか確認")
        sys.exit(1)


if __name__ == "__main__":
    main()
