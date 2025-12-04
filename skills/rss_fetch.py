"""
RSSFetchSkill
RSSフィードから記事を取得するスキル
"""

import feedparser
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .base_skill import BaseSkill


class RSSFetchSkill(BaseSkill):
    """RSSフィードを取得するスキル"""

    def __init__(self):
        super().__init__(
            name="rss_fetch",
            description="RSSフィードから記事を取得する"
        )

    def fetch_feed(self, url: str, name: str, category: str, hours_ago: int = 24) -> List[Dict]:
        """
        単一のRSSフィードを取得

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
            self.log(f"Fetching: {name}")
            feed = feedparser.parse(url)

            if feed.bozo:
                self.log(f"Feed parsing warning: {name}", "WARNING")

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

            self.log(f"Found {len(articles)} articles from {name}")

        except Exception as e:
            self.log(f"Error fetching {name}: {str(e)}", "ERROR")

        return articles

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルを実行

        Args:
            params:
                - feeds: フィード情報のリスト [{url, name, category}, ...]
                - hours_ago: 何時間前までの記事を取得するか（デフォルト: 24）

        Returns:
            実行結果
                - articles: 記事のリスト
                - fetch_time: 取得日時
        """
        feeds = params.get("feeds", [])
        hours_ago = params.get("hours_ago", 24)

        if not feeds:
            self.log("No feeds provided", "WARNING")
            return {"articles": [], "fetch_time": datetime.now().isoformat()}

        all_articles = []
        for feed_info in feeds:
            articles = self.fetch_feed(
                url=feed_info.get("url", ""),
                name=feed_info.get("name", "Unknown"),
                category=feed_info.get("category", "General"),
                hours_ago=hours_ago
            )
            all_articles.extend(articles)

        return {
            "articles": all_articles,
            "total_count": len(all_articles),
            "fetch_time": datetime.now().isoformat()
        }
