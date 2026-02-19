#!/usr/bin/env python3
"""
YouTubeリフレッシュトークン取得スクリプト

OAuthフローを実行し、YouTube Data API v3用のリフレッシュトークンを取得します。
取得したトークンをGitHub SecretsのYOUTUBE_REFRESH_TOKENに設定してください。

使い方:
    python3 scripts/youtube_get_refresh_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET

必要なスコープ:
    - https://www.googleapis.com/auth/youtube（フルアクセス：アップロード＋再生リスト操作）
"""

import argparse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
from urllib.request import urlopen, Request

SCOPES = ["https://www.googleapis.com/auth/youtube"]
REDIRECT_URI = "http://localhost:8090"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuthコールバックを受け取るハンドラ"""

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            self.server.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body><h1>認証成功！</h1>"
                "<p>このタブを閉じてターミナルに戻ってください。</p>"
                "</body></html>".encode("utf-8")
            )
        else:
            error = query.get("error", ["unknown"])[0]
            self.server.auth_code = None
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>認証エラー: {error}</h1></body></html>".encode("utf-8")
            )

    def log_message(self, format, *args):
        pass  # ログを抑制


def get_auth_code(client_id):
    """ブラウザでOAuth認証を行い、認証コードを取得"""
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print(f"\nブラウザで認証ページを開きます...")
    print(f"自動で開かない場合は以下のURLをブラウザに貼り付けてください:\n")
    print(f"  {auth_url}\n")
    webbrowser.open(auth_url)

    print("認証完了を待機中（localhost:8090）...")
    server = HTTPServer(("localhost", 8090), OAuthCallbackHandler)
    server.auth_code = None
    server.handle_request()

    return server.auth_code


def exchange_code_for_tokens(client_id, client_secret, auth_code):
    """認証コードをリフレッシュトークンに交換"""
    data = urlencode({
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = Request(TOKEN_URL, data=data, method="POST")
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description="YouTubeリフレッシュトークンを取得します"
    )
    parser.add_argument("--client-id", required=True, help="OAuth Client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth Client Secret")
    args = parser.parse_args()

    # 1. 認証コード取得
    auth_code = get_auth_code(args.client_id)
    if not auth_code:
        print("エラー: 認証コードの取得に失敗しました")
        return

    print("✓ 認証コード取得成功")

    # 2. トークン交換
    print("トークンを取得中...")
    tokens = exchange_code_for_tokens(args.client_id, args.client_secret, auth_code)

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("エラー: リフレッシュトークンが取得できませんでした")
        print(f"レスポンス: {json.dumps(tokens, indent=2)}")
        return

    print("\n" + "=" * 60)
    print("✓ リフレッシュトークン取得成功!")
    print("=" * 60)
    print(f"\nREFRESH_TOKEN:\n{refresh_token}")
    print(f"\n付与されたスコープ:\n{tokens.get('scope', 'N/A')}")
    print("\n" + "=" * 60)
    print("次のステップ:")
    print("  1. GitHub リポジトリの Settings > Secrets > Actions を開く")
    print("  2. YOUTUBE_REFRESH_TOKEN を上記の値で更新する")
    print("=" * 60)


if __name__ == "__main__":
    main()
