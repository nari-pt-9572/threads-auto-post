import requests
import json
from config import SERPER_API_KEY, POSTING_TOPIC


def search_google(query: str, num: int = 5) -> list[dict]:
    """Serper APIでGoogle検索"""
    if not SERPER_API_KEY:
        return []
    r = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "gl": "jp", "hl": "ja", "num": num},
        timeout=15,
    )
    results = r.json()
    return results.get("organic", [])


def get_trending_topics(topic: str) -> list[str]:
    """ジャンル内のトレンドキーワードを取得"""
    queries = [
        f"{topic} トレンド 2025",
        f"{topic} 話題",
        f"{topic} Threads 人気",
    ]
    snippets = []
    for q in queries:
        results = search_google(q, num=3)
        for r in results:
            if r.get("snippet"):
                snippets.append(r["snippet"])
    return snippets[:6]


def research_competitors(accounts: list[str]) -> list[str]:
    """競合アカウントの投稿傾向を調査"""
    insights = []
    for account in accounts:
        if not account.strip():
            continue
        results = search_google(f"Threads {account} 投稿 人気", num=3)
        for r in results:
            if r.get("snippet"):
                insights.append(f"[{account}] {r['snippet']}")
    return insights[:5]


def run_research(topic: str, competitor_accounts: list[str]) -> dict:
    """総合リサーチ実行"""
    print("トレンドリサーチ中...")
    trending = get_trending_topics(topic)

    print("競合リサーチ中...")
    competitors = research_competitors(competitor_accounts)

    return {
        "trending_snippets": trending,
        "competitor_insights": competitors,
    }
