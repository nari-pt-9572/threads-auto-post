import json
import anthropic
from config import ANTHROPIC_API_KEY, POSTING_TOPIC


def analyze_pdca(posts_with_insights: list[dict], research_data: dict, topic: str) -> dict:
    """
    過去投稿のインサイト + リサーチデータをもとにPDCA分析
    → 次の投稿戦略を返す
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    posts_summary = ""
    for p in posts_with_insights:
        ins = p.get("insights", {})
        posts_summary += f"""
・投稿: {p.get('text', '')[:80]}
  閲覧: {ins.get('views', 0)} / いいね: {ins.get('likes', 0)} / リプライ: {ins.get('replies', 0)} / リポスト: {ins.get('reposts', 0)}
"""

    research_summary = "\n".join(
        p.get("trending_snippets", []) + p.get("competitor_insights", [])
        if isinstance(p, dict) else []
        for p in [research_data]
    )

    prompt = f"""あなたはSNSマーケティングの専門家です。
Threadsアカウントのジャンル: {topic}

## 直近の投稿パフォーマンス
{posts_summary if posts_summary else "データなし（初回実行）"}

## 市場リサーチ
{research_summary if research_summary else "データなし"}

## 依頼
1. パフォーマンスの良かった投稿の特徴（なければスキップ）
2. 改善すべき点
3. 今日の投稿で使うべきキーワード・テーマ（3つ）
4. 次回投稿の方向性（1行）

JSON形式のみで返してください:
{{
  "good_points": ["良かった点1", "良かった点2"],
  "improvements": ["改善点1", "改善点2"],
  "keywords": ["キーワード1", "キーワード2", "キーワード3"],
  "strategy": "今日の投稿方向性"
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return {
        "good_points": [],
        "improvements": [],
        "keywords": [topic],
        "strategy": f"{topic}に関する有益な情報を発信する",
    }
