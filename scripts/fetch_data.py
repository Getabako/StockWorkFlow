#!/usr/bin/env python3
"""
情報収集スクリプト (fetch_data.py)
AI/IT関連の重要ニュースをRSSフィードから収集し、JSONファイルに保存します。
"""

import feedparser
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# RSS フィードのリスト
RSS_FEEDS = {
    "主要企業IR (英語)": [
        {
            "name": "NVIDIA",
            "url": "https://nvidianews.nvidia.com/releases/rss",
            "category": "GPU/AI Hardware"
        },
        {
            "name": "Microsoft",
            "url": "https://news.microsoft.com/feed/",
            "category": "Cloud/AI Platform"
        },
        {
            "name": "Google/Alphabet",
            "url": "https://blog.google/rss/",
            "category": "AI Research/Cloud"
        },
        {
            "name": "AMD",
            "url": "https://ir.amd.com/rss/news-releases/default.aspx",
            "category": "GPU/CPU"
        },
        {
            "name": "Oracle",
            "url": "https://www.oracle.com/news/rss/",
            "category": "Cloud/Database"
        },
        {
            "name": "Intel",
            "url": "https://www.intc.com/news-events/press-releases/rss",
            "category": "CPU/AI Chips"
        },
        {
            "name": "Qualcomm",
            "url": "https://www.qualcomm.com/news/rss",
            "category": "Mobile/AI Chips"
        },
        {
            "name": "Broadcom",
            "url": "https://investors.broadcom.com/news-releases/rss",
            "category": "Semiconductors/Custom Chips"
        },
        {
            "name": "Arm",
            "url": "https://newsroom.arm.com/rss",
            "category": "CPU Architecture/IoT"
        },
        {
            "name": "Texas Instruments",
            "url": "https://news.ti.com/rss",
            "category": "Semiconductors/Analog"
        }
    ],
    "日本企業IR": [
        {
            "name": "SoftBank Group",
            "url": "https://group.softbank/news/rss",
            "category": "AI/Robotics Investment"
        },
        {
            "name": "ROHM Semiconductor",
            "url": "https://www.rohm.co.jp/news/rss",
            "category": "Semiconductors/Components"
        }
    ],
    "大手経済ニュース": [
        {
            "name": "Bloomberg Technology",
            "url": "https://feeds.bloomberg.com/technology/news.rss",
            "category": "Tech News"
        },
        {
            "name": "Reuters Technology",
            "url": "https://www.reuters.com/technology",
            "category": "Tech News",
            "note": "RSSフィードが変更される可能性があります"
        }
    ]
}

# オプション: 環境変数からカスタムRSSフィードを追加
TDNET_RSS_URL = os.getenv("TDNET_RSS_URL", "")


def fetch_rss_feed(url: str, name: str, category: str, hours_ago: int = 24) -> List[Dict]:
    """
    RSSフィードを取得し、指定時間内の記事を抽出します。

    Args:
        url: RSSフィードのURL
        name: フィードの名前
        category: カテゴリ
        hours_ago: 何時間前までの記事を取得するか（デフォルト: 24時間）

    Returns:
        記事のリスト
    """
    articles = []
    try:
        print(f"Fetching: {name} ({url})")
        feed = feedparser.parse(url)

        # フィード取得の成功確認
        if feed.bozo:
            print(f"  Warning: Feed may have parsing issues - {name}")

        cutoff_time = datetime.now() - timedelta(hours=hours_ago)

        for entry in feed.entries:
            # 公開日時の取得（複数のフォーマットに対応）
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # 指定期間内の記事のみ抽出
            if pub_date and pub_date >= cutoff_time:
                article = {
                    "source": name,
                    "category": category,
                    "title": entry.get('title', 'No Title'),
                    "link": entry.get('link', ''),
                    "published": pub_date.isoformat() if pub_date else '',
                    "summary": entry.get('summary', entry.get('description', ''))[:500]
                }
                articles.append(article)

        print(f"  Found {len(articles)} recent articles from {name}")

    except Exception as e:
        print(f"  Error fetching {name}: {str(e)}")

    return articles


def fetch_all_feeds(hours_ago: int = 24) -> List[Dict]:
    """
    すべてのRSSフィードから記事を取得します。

    Args:
        hours_ago: 何時間前までの記事を取得するか

    Returns:
        すべての記事のリスト
    """
    all_articles = []

    # 定義されたRSSフィードを処理
    for category_name, feeds in RSS_FEEDS.items():
        print(f"\n=== {category_name} ===")
        for feed_info in feeds:
            articles = fetch_rss_feed(
                url=feed_info["url"],
                name=feed_info["name"],
                category=feed_info["category"],
                hours_ago=hours_ago
            )
            all_articles.extend(articles)

    # TDnet RSSがある場合は追加
    if TDNET_RSS_URL:
        print(f"\n=== 日本市場 開示情報 ===")
        articles = fetch_rss_feed(
            url=TDNET_RSS_URL,
            name="TDnet/EDINET",
            category="Japanese Market Disclosure",
            hours_ago=hours_ago
        )
        all_articles.extend(articles)

    return all_articles


def save_articles(articles: List[Dict], output_file: str = "output/articles.json"):
    """
    記事をJSONファイルに保存します。

    Args:
        articles: 記事のリスト
        output_file: 出力ファイルパス
    """
    # 出力ディレクトリの作成
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    output_data = {
        "fetch_time": datetime.now().isoformat(),
        "total_articles": len(articles),
        "articles": articles
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved {len(articles)} articles to {output_file}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("AI/IT Stock Investment - News Fetcher")
    print("=" * 60)

    # 記事を取得（過去24時間）
    articles = fetch_all_feeds(hours_ago=24)

    # JSONファイルに保存
    save_articles(articles)

    print("\n" + "=" * 60)
    print("Fetch completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
