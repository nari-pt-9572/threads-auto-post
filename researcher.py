import requests
import random
import re
import json
import anthropic
from config import SERPER_API_KEY, ANTHROPIC_API_KEY


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


def generate_search_queries() -> list[str]:
    """
    Groqが毎回異なる検索クエリを自動生成。
    恋愛全般（遠距離・同棲・結婚・将来・デート・記念日など）を幅広くカバー。
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = """以下のアカウントコンセプトに合った、SNS投稿ネタのリサーチ用検索クエリを8つ生成してください。

アカウントコンセプト:
- 25歳理学療法士（手取り22万）× 彼女は看護師 × お金の不安 × 副業で人生が変わった
- ターゲット: 22〜29歳の恋愛中・同棲中・結婚を考えている男女

検索クエリの条件:
- 恋愛全般を幅広くカバーする（遠距離・同棲・結婚・将来の話・デート・記念日・喧嘩・プロポーズ・価値観の違い・お金の話など）
- 毎回違うジャンルを選ぶ（高速・給料・ガソリンに偏らない）
- SNSでバズりやすい共感系ネタを狙う
- 「あるある」「エピソード」「本音」「共感」などをキーワードに含める

8つのクエリをJSON配列で返してください（説明不要）:
["クエリ1", "クエリ2", ...]"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            queries = json.loads(match.group())
            return queries[:8]
        except Exception:
            pass

    # フォールバック（生成失敗時）
    return [
        "同棲 彼女 お金 本音 SNS",
        "結婚 彼女 将来 不安 あるある",
        "看護師 彼女 夜勤 彼氏 エピソード",
        "理学療法士 手取り 低い リアル",
        "彼女 記念日 プレゼント お金ない",
        "同棲 生活費 分担 揉める あるある",
        "プロポーズ お金 タイミング 本音",
        "遠距離恋愛 終わり 同棲 決断 エピソード",
    ]


def get_trending_snippets(queries: list[str]) -> list[str]:
    """検索クエリで検索してスニペットを収集"""
    snippets = []
    for q in queries:
        results = search_google(q, num=3)
        for r in results:
            if r.get("snippet"):
                snippets.append(r["snippet"])
    return snippets[:16]


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
    print("検索クエリ自動生成中...")
    queries = generate_search_queries()
    print(f"  生成されたクエリ: {queries[:3]}...")

    print("トレンドリサーチ中...")
    trending = get_trending_snippets(queries)

    print("競合リサーチ中...")
    competitors = research_competitors(competitor_accounts)

    return {
        "search_queries": queries,
        "trending_snippets": trending,
        "competitor_insights": competitors,
    }
