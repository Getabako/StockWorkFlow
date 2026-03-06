#!/usr/bin/env python3
"""
既存のYouTube動画を再生リストに追加するスクリプト
チャンネル内の動画をタイトルで検索して再生リストに追加します。
"""

import os
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 追加対象の動画タイトル（2/16〜2/20）
# daily_report.yml のアップロードタイトル形式: "AI/IT株式日次レポート YYYY_MM_DD"
TARGET_TITLES = [
    "AI/IT株式日次レポート 2026_02_16",
    "AI/IT株式日次レポート 2026_02_17",
    "AI/IT株式日次レポート 2026_02_18",
    "AI/IT株式日次レポート 2026_02_19",
    "AI/IT株式日次レポート 2026_02_20",
]

PLAYLIST_NAME = "デイリー株式投資分析"


def get_authenticated_service():
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "環境変数が未設定: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN"
        )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    credentials.refresh(Request())
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def find_playlist_by_name(youtube, playlist_name):
    next_page_token = None
    while True:
        response = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response.get("items", []):
            if item["snippet"]["title"] == playlist_name:
                return item["id"]

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return None


def get_videos_already_in_playlist(youtube, playlist_id):
    """再生リストに既に入っている動画IDのセットを返す"""
    video_ids = set()
    next_page_token = None
    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response.get("items", []):
            video_ids.add(item["snippet"]["resourceId"]["videoId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return video_ids


def search_my_videos_by_title(youtube, title):
    """自分のチャンネルからタイトルが完全一致する動画を検索"""
    response = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        q=title,
        maxResults=10
    ).execute()

    for item in response.get("items", []):
        if item["snippet"]["title"] == title:
            return item["id"]["videoId"]
    return None


def add_video_to_playlist(youtube, video_id, playlist_id):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()


def main():
    print("YouTube APIに接続中...")
    youtube = get_authenticated_service()
    print("認証成功")

    print(f"\n再生リストを検索中: {PLAYLIST_NAME}")
    playlist_id = find_playlist_by_name(youtube, PLAYLIST_NAME)
    if not playlist_id:
        print(f"エラー: 再生リスト '{PLAYLIST_NAME}' が見つかりません")
        print("YouTubeで先に再生リストを作成してください")
        sys.exit(1)
    print(f"再生リストID: {playlist_id}")

    already_in_playlist = get_videos_already_in_playlist(youtube, playlist_id)
    print(f"再生リスト内の既存動画数: {len(already_in_playlist)}")

    print(f"\n対象動画 ({len(TARGET_TITLES)}本) を処理します...")
    success = 0
    skipped = 0
    not_found = 0

    for title in TARGET_TITLES:
        print(f"\n  検索中: {title}")
        video_id = search_my_videos_by_title(youtube, title)

        if not video_id:
            print(f"  見つかりません (スキップ): {title}")
            not_found += 1
            continue

        if video_id in already_in_playlist:
            print(f"  既に再生リスト内 (スキップ): {title} ({video_id})")
            skipped += 1
            continue

        try:
            add_video_to_playlist(youtube, video_id, playlist_id)
            print(f"  追加完了: {title} ({video_id})")
            success += 1
        except HttpError as e:
            print(f"  追加失敗: {title} - {e}")

    print(f"\n{'='*50}")
    print(f"処理完了")
    print(f"  追加成功: {success}本")
    print(f"  既に追加済み: {skipped}本")
    print(f"  動画未発見: {not_found}本")


if __name__ == "__main__":
    main()
