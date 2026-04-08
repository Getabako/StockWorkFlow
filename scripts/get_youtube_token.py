#!/usr/bin/env python3
"""
YouTube OAuth2 リフレッシュトークン取得スクリプト

使い方:
  python3 scripts/get_youtube_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET

ブラウザが開き、Googleアカウントでの認証後にリフレッシュトークンが表示されます。
"""

import argparse
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]


def main():
    parser = argparse.ArgumentParser(description="YouTube OAuth2 リフレッシュトークンを取得します")
    parser.add_argument("--client-id", required=True, help="OAuth クライアントID")
    parser.add_argument("--client-secret", required=True, help="OAuth クライアントシークレット")
    args = parser.parse_args()

    client_config = {
        "installed": {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=8080)

    print("\n" + "=" * 60)
    print("認証成功! 以下の値を GitHub Secrets に設定してください:")
    print("=" * 60)
    print(f"\nYOUTUBE_CLIENT_ID:     {args.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET: {args.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN: {credentials.refresh_token}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
