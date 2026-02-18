#!/usr/bin/env python3
"""
YouTube自動アップロードスクリプト (upload_to_youtube.py)
YouTube Data API v3を使用して動画を自動アップロードします。
"""

import os
import sys
import re
import json
import argparse
import httplib2
from datetime import datetime
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# アップロード設定
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 動画のカテゴリID（22 = People & Blogs, 28 = Science & Technology）
CATEGORY_ID = "28"

# プライバシー設定
PRIVACY_STATUS = "public"  # "public", "private", "unlisted"


def get_authenticated_service():
    """
    YouTube APIの認証済みサービスを取得します。

    Returns:
        YouTube APIサービスオブジェクト
    """
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "環境変数が設定されていません: "
            "YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN"
        )

    # 認証情報を作成
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    # トークンをリフレッシュ
    credentials.refresh(Request())

    # YouTube APIサービスを構築
    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=credentials
    )


def find_playlist_by_name(youtube, playlist_name):
    """
    再生リスト名からプレイリストIDを検索します。

    Args:
        youtube: YouTube APIサービス
        playlist_name: 再生リスト名

    Returns:
        プレイリストID（見つからない場合はNone）
    """
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            if item["snippet"]["title"] == playlist_name:
                return item["id"]

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return None


def add_video_to_playlist(youtube, video_id, playlist_id):
    """
    動画を再生リストに追加します。

    Args:
        youtube: YouTube APIサービス
        video_id: 動画ID
        playlist_id: プレイリストID
    """
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    youtube.playlistItems().insert(
        part="snippet",
        body=body
    ).execute()
    print(f"✓ 再生リストに追加しました (playlist_id: {playlist_id})")


def extract_company_names_from_report(report_file):
    """
    マーケットレポートから企業名を抽出します。

    Args:
        report_file: レポートファイルのパス（Markdown）

    Returns:
        企業名のリスト
    """
    if not os.path.exists(report_file):
        print(f"レポートファイルが見つかりません: {report_file}")
        return []

    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    companies = set()

    # **太字** で囲まれた企業名・製品名を抽出
    bold_matches = re.findall(r'\*\*([^*]+)\*\*', content)
    for match in bold_matches:
        match = match.strip()
        # 短すぎるもの、長すぎるもの、日付、数値のみは除外
        if len(match) < 2 or len(match) > 30:
            continue
        if re.match(r'^[\d\.\,\%\+\-\s]+$', match):
            continue
        if re.match(r'^\d{4}年', match):
            continue
        companies.add(match)

    # 既知の主要企業・ティッカーのパターンマッチング
    known_companies = {
        'NVIDIA': ['NVIDIA', 'NVDA', 'エヌビディア'],
        'AMD': ['AMD', 'アドバンスト・マイクロ・デバイセズ'],
        'Broadcom': ['Broadcom', 'AVGO', 'ブロードコム'],
        'Google': ['Google', 'Alphabet', 'GOOG', 'GOOGL', 'グーグル', 'アルファベット'],
        'Tesla': ['Tesla', 'TSLA', 'テスラ'],
        'Intel': ['Intel', 'INTC', 'インテル'],
        'Qualcomm': ['Qualcomm', 'QCOM', 'クアルコム'],
        'Meta': ['Meta', 'META', 'メタ', 'Meta Platforms'],
        'Apple': ['Apple', 'AAPL', 'アップル'],
        'Microsoft': ['Microsoft', 'MSFT', 'マイクロソフト'],
        'Amazon': ['Amazon', 'AMZN', 'アマゾン'],
        'OpenAI': ['OpenAI'],
        'Anthropic': ['Anthropic', 'アンスロピック'],
        'xAI': ['xAI'],
        'Arm': ['Arm', 'ARM', 'アーム'],
        'Samsung': ['Samsung', 'サムスン'],
        'TSMC': ['TSMC', 'Taiwan Semiconductor', '台湾セミコンダクター'],
        'Oracle': ['Oracle', 'ORCL', 'オラクル'],
        'Palantir': ['Palantir', 'PLTR', 'パランティア'],
        'CrowdStrike': ['CrowdStrike', 'CRWD', 'クラウドストライク'],
        'Snowflake': ['Snowflake', 'SNOW', 'スノーフレーク'],
        'ServiceNow': ['ServiceNow', 'NOW'],
        'Salesforce': ['Salesforce', 'CRM', 'セールスフォース'],
        'Adobe': ['Adobe', 'ADBE', 'アドビ'],
        'Netflix': ['Netflix', 'NFLX', 'ネットフリックス'],
        'Sony': ['Sony', 'SONY', 'ソニー'],
        'Toyota': ['Toyota', 'トヨタ', 'TM'],
        'SoftBank': ['SoftBank', 'ソフトバンク', 'ソフトバンクグループ'],
        'SK Hynix': ['SK Hynix', 'SKハイニックス'],
        'Kioxia': ['Kioxia', 'キオクシア'],
        'LITALICO': ['LITALICO', 'リタリコ'],
        'Micron': ['Micron', 'MU', 'マイクロン'],
        'Marvell': ['Marvell', 'MRVL', 'マーベル'],
        'Super Micro': ['Super Micro', 'SMCI', 'スーパーマイクロ'],
        'Dell': ['Dell', 'DELL', 'デル'],
        'IBM': ['IBM', 'アイビーエム'],
        'Cisco': ['Cisco', 'CSCO', 'シスコ'],
    }

    for company_tag, aliases in known_companies.items():
        for alias in aliases:
            if alias in content:
                companies.add(company_tag)
                break

    # 除外すべき一般的な語句（企業名ではないもの）
    exclude_words = {
        'AI', 'IT', 'M&A', 'IPO', 'CEO', 'CTO', 'GPU', 'CPU', 'API',
        '上昇', '下落', '注目', '重要', '影響', '分析', '投資', '市場',
        '概要', 'サマリー', '免責事項', 'エグゼクティブサマリー',
        '本日', '今後', '新製品', '新技術', 'その他',
    }
    companies = companies - exclude_words

    return sorted(list(companies))


def upload_video(youtube, video_file, title, description, tags=None, category_id=CATEGORY_ID, privacy_status=PRIVACY_STATUS, company_names=None):
    """
    動画をYouTubeにアップロードします。

    Args:
        youtube: YouTube APIサービス
        video_file: 動画ファイルのパス
        title: 動画タイトル
        description: 動画の説明
        tags: タグのリスト
        category_id: カテゴリID
        privacy_status: プライバシー設定
        company_names: レポートから抽出した企業名リスト

    Returns:
        アップロードされた動画のID
    """
    if tags is None:
        tags = ["AI", "IT", "株式投資", "市場分析", "日次レポート", "if塾", "プログラミング教育", "完全自動化", "AI活用"]

    # 企業名をタグに追加
    if company_names:
        for name in company_names:
            if name not in tags:
                tags.append(name)

    # ハッシュタグを動的に生成
    base_hashtags = ["#AI", "#完全自動化", "#if塾", "#プログラミング教育", "#AIニュース", "#株式投資", "#AI株", "#IT株", "#米国株", "#半導体"]
    if company_names:
        company_hashtags = [f"#{name}" for name in company_names]
        all_hashtags = base_hashtags + company_hashtags
    else:
        all_hashtags = base_hashtags
    hashtag_str = " ".join(all_hashtags)

    # 概要欄のテンプレートを作成
    enhanced_description = f"""{description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 塾頭高崎の完全自動化への挑戦について
━━━━━━━━━━━━━━━━━━━━━━━━━━━

このコンテンツは、if塾塾頭による「ブログ・SNS完全自動化プロジェクト」の
実験的な取り組みとして、AIが自動生成したものです。

私たちは、AI技術を活用した情報発信の可能性を探求しており、
徐々に品質を向上させています。現在の記事内容と実際の活動に
大きなズレはありませんが、細部については異なる場合があります。

※現時点では事実と異なる内容が含まれる可能性があります
※最新の正確な情報については、お問い合わせください

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 無料AI教育・導入コンサルのご案内
━━━━━━━━━━━━━━━━━━━━━━━━━━━

if塾では、無料のAI教育やAI導入コンサルティングを
受け付けております。お気軽にお問い合わせください。

🔗 お問い合わせフォーム:
https://docs.google.com/forms/d/e/1FAIpQLSdu-w12JZxtiEMySp84T82JrguXhh8ZcADP5_4RKHLvv9cqSQ/viewform

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📣 チャンネル登録・高評価よろしくお願いします！
━━━━━━━━━━━━━━━━━━━━━━━━━━━

この技術的挑戦に共感していただけましたら、
ぜひチャンネル登録とグッドボタンをお願いします！

{hashtag_str}"""

    body = {
        "snippet": {
            "title": title,
            "description": enhanced_description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "ja",
            "defaultAudioLanguage": "ja"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # MediaFileUploadオブジェクトを作成
    media = MediaFileUpload(
        video_file,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024  # 1MB chunks
    )

    # アップロードリクエストを作成
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    # アップロードを実行
    print(f"アップロード中: {video_file}")
    response = None

    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  進捗: {progress}%")

    video_id = response["id"]
    print(f"✓ アップロード完了!")
    print(f"  動画ID: {video_id}")
    print(f"  URL: https://www.youtube.com/watch?v={video_id}")

    return video_id


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='YouTubeに動画をアップロードします'
    )
    parser.add_argument('video_file', help='アップロードする動画ファイルのパス')
    parser.add_argument('--title', '-t', required=True, help='動画タイトル')
    parser.add_argument('--description', '-d', default='', help='動画の説明')
    parser.add_argument('--tags', nargs='+', help='タグ（スペース区切り）')
    parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                       default='public', help='プライバシー設定')
    parser.add_argument('--category', default=CATEGORY_ID, help='カテゴリID')
    parser.add_argument('--playlist', help='追加先の再生リスト名')
    parser.add_argument('--report-file', help='企業名抽出用のマーケットレポートファイル（Markdown）')

    args = parser.parse_args()

    # ファイル存在確認
    if not os.path.exists(args.video_file):
        print(f"エラー: 動画ファイルが見つかりません: {args.video_file}")
        sys.exit(1)

    # レポートから企業名を抽出
    company_names = []
    if args.report_file:
        print(f"レポートから企業名を抽出中: {args.report_file}")
        company_names = extract_company_names_from_report(args.report_file)
        if company_names:
            print(f"✓ 抽出された企業名: {', '.join(company_names)}")
        else:
            print("  企業名は見つかりませんでした")

    try:
        # YouTube APIサービスを取得
        print("YouTube APIに接続中...")
        youtube = get_authenticated_service()
        print("✓ 認証成功")

        # 動画をアップロード
        video_id = upload_video(
            youtube,
            args.video_file,
            args.title,
            args.description,
            args.tags,
            args.category,
            args.privacy,
            company_names=company_names
        )

        # 再生リストに追加
        if args.playlist:
            print(f"再生リストを検索中: {args.playlist}")
            playlist_id = find_playlist_by_name(youtube, args.playlist)
            if playlist_id:
                add_video_to_playlist(youtube, video_id, playlist_id)
            else:
                print(f"⚠ 再生リストが見つかりません: {args.playlist}")

        # GitHub Actions用に出力
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"video_id={video_id}\n")
                f.write(f"video_url=https://www.youtube.com/watch?v={video_id}\n")

        print("\n" + "=" * 50)
        print("YouTubeアップロード完了!")
        print("=" * 50)

    except HttpError as e:
        print(f"YouTube APIエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
