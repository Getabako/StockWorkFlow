"""
ResearcherAgent（日々の情勢調べ役）
AI関係の企業の動向や世界情勢を調べるエージェント
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """日々の情勢を調査するエージェント"""

    # RSSフィードの設定
    RSS_FEEDS = {
        "主要企業IR (英語)": [
            {"name": "NVIDIA", "url": "https://nvidianews.nvidia.com/releases/rss", "category": "GPU/AI Hardware"},
            {"name": "Microsoft", "url": "https://news.microsoft.com/feed/", "category": "Cloud/AI Platform"},
            {"name": "Google/Alphabet", "url": "https://blog.google/rss/", "category": "AI Research/Cloud"},
            {"name": "AMD", "url": "https://ir.amd.com/rss/news-releases/default.aspx", "category": "GPU/CPU"},
            {"name": "Oracle", "url": "https://www.oracle.com/news/rss/", "category": "Cloud/Database"},
            {"name": "Intel", "url": "https://www.intc.com/news-events/press-releases/rss", "category": "CPU/AI Chips"},
            {"name": "Qualcomm", "url": "https://www.qualcomm.com/news/rss", "category": "Mobile/AI Chips"},
            {"name": "Broadcom", "url": "https://investors.broadcom.com/news-releases/rss", "category": "Semiconductors"},
            {"name": "Arm", "url": "https://newsroom.arm.com/rss", "category": "CPU Architecture/IoT"},
        ],
        "日本企業IR": [
            {"name": "SoftBank Group", "url": "https://group.softbank/news/rss", "category": "AI/Robotics Investment"},
        ],
        "大手経済ニュース": [
            {"name": "Bloomberg Technology", "url": "https://feeds.bloomberg.com/technology/news.rss", "category": "Tech News"},
        ]
    }

    def __init__(self):
        super().__init__(
            name="ResearcherAgent",
            description="日々の情勢調べ役 - AI関係の企業の動向や世界情勢を調べる"
        )
        self.skills = ["rss_fetch", "web_search", "news_analysis"]

    def fetch_rss_feed(self, url: str, name: str, category: str, hours_ago: int = 24) -> List[Dict]:
        """
        RSSフィードを取得し、指定時間内の記事を抽出

        Args:
            url: RSSフィードのURL
            name: フィード名
            category: カテゴリ
            hours_ago: 何時間前までの記事を取得するか

        Returns:
            記事のリスト
        """
        articles = []
        try:
            self.log(f"Fetching: {name} ({url})")
            feed = feedparser.parse(url)

            if feed.bozo:
                self.log(f"Feed may have parsing issues - {name}", "WARNING")

            cutoff_time = datetime.now() - timedelta(hours=hours_ago)

            for entry in feed.entries:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

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

            self.log(f"Found {len(articles)} recent articles from {name}")

        except Exception as e:
            self.log(f"Error fetching {name}: {str(e)}", "ERROR")

        return articles

    def fetch_all_feeds(self, hours_ago: int = 24) -> List[Dict]:
        """
        すべてのRSSフィードから記事を取得

        Args:
            hours_ago: 何時間前までの記事を取得するか

        Returns:
            すべての記事のリスト
        """
        all_articles = []

        for category_name, feeds in self.RSS_FEEDS.items():
            self.log(f"=== {category_name} ===")
            for feed_info in feeds:
                articles = self.fetch_rss_feed(
                    url=feed_info["url"],
                    name=feed_info["name"],
                    category=feed_info["category"],
                    hours_ago=hours_ago
                )
                all_articles.extend(articles)

        return all_articles

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト
                - hours_ago: 何時間前までの記事を取得するか（デフォルト: 24）

        Returns:
            実行結果
                - articles: 収集した記事のリスト
                - fetch_time: 取得日時
                - total_articles: 記事の総数
        """
        self.log("Starting research...")

        hours_ago = context.get("hours_ago", 24)
        articles = self.fetch_all_feeds(hours_ago=hours_ago)

        result = {
            "fetch_time": datetime.now().isoformat(),
            "total_articles": len(articles),
            "articles": articles
        }

        # 結果を保存
        self.save_output(result, "articles.json")

        self.log(f"Research completed. Found {len(articles)} articles.")
        return result
