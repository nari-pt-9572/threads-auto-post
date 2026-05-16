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
        # 遠距離恋愛ネタ
        "遠距離恋愛 あるある SNS バズ",
        "遠距離恋愛 お金 しんどい 共感",
        # 看護師彼女ネタ
        "看護師 彼女 あるある Threads",
        "看護師 彼氏 夜勤 遠距離",
        # 理学療法士ネタ
        "理学療法士 給料 リアル あるある",
        "PT 手取り 低い 本音",
        # 恋愛×お金ネタ
        "彼女に言われた一言 お金 共感 バズ",
        "手取り 低い 彼女 遠距離 Threads",
    ]
    snippets = []
    for q in queries:
        results = search_google(q, num=3)
        for r in results:
            if r.get("snippet"):
                snippets.append(r["snippet"])
    return snippets[:12]


def get_scene_ideas() -> list[str]:
    """バズりやすいシーン・ネタを検索して取得"""
    queries = [
        "遠距離恋愛 彼女 会いに行く エピソード",
        "看護師 彼女 夜勤明け 彼氏 エピソード",
        "理学療法士 職場 あるある エピソード",
        "手取り低い 彼女 記念日 プレゼント エピソード",
        "社会人 遠距離 お金ない リアル",
        "彼女に言われた 忘れられない 一言",
    ]
    scenes = []
    for q in queries:
        results = search_google(q, num=3)
        for r in results:
            if r.get("snippet"):
                scenes.append(r["snippet"])
    return scenes[:10]


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

    print("シーンネタリサーチ中...")
    scenes = get_scene_ideas()

    print("競合リサーチ中...")
    competitors = research_competitors(competitor_accounts)

    return {
        "trending_snippets": trending,
        "scene_ideas": scenes,
        "competitor_insights": competitors,
    }
