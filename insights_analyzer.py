import json
import re
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

    trending = research_data.get("trending_snippets", []) if isinstance(research_data, dict) else []
    competitor = research_data.get("competitor_insights", []) if isinstance(research_data, dict) else []
    queries = research_data.get("search_queries", []) if isinstance(research_data, dict) else []
    all_snippets = [s for s in (trending + competitor) if isinstance(s, str)]
    research_summary = "\n".join(all_snippets)
    queries_summary = "、".join(queries[:8])

    prompt = f"""あなたはSNSマーケティングの専門家です。

アカウントコンセプト: 25歳理学療法士×看護師彼女×副業で人生が変わった
- BEFORE: PT1年目・副業前・手取り22万でお金に苦しかった頃
- AFTER: PT2年目から副業開始・手取り30万になって余裕が生まれた今
ターゲット: 22〜29歳、恋愛中・同棲・結婚を考えている収入に悩む男女
目的: スレッズで興味喚起 → InstagramのDM獲得
投稿テーマ: 恋愛×PT×お金（デート代・同棲・将来・記念日）×副業暗示

## 直近の投稿パフォーマンス
{posts_summary if posts_summary else "データなし（初回実行）"}

## 今回リサーチしたジャンル
{queries_summary if queries_summary else "データなし"}

## 市場リサーチ（トレンド・競合）
{research_summary if research_summary else "データなし"}

## 依頼
1. パフォーマンスの良かった投稿の特徴（なければスキップ）
2. 改善すべき点
3. 今日の投稿で使うべきキーワード・テーマ（3つ）
4. 次回投稿の具体的なシーン（高速・給料・ガソリン以外で。例：夜勤明けの彼女との電話、誕生日プレゼントを選ぶ場面、職場の休憩室、コンビニ、記念日など）
5. 次回投稿の方向性（1行）

JSON形式のみで返してください（他の文字は不要）:
{{
  "good_points": ["良かった点1", "良かった点2"],
  "improvements": ["改善点1", "改善点2"],
  "keywords": ["キーワード1", "キーワード2", "キーワード3"],
  "scene": "具体的なシーン（例: 夜勤明けの彼女に電話した夜、職場の休憩室で給与明細を見た瞬間）",
  "strategy": "今日の投稿方向性（例: 夜勤明けの彼女×手取り22万の不安を共感させる）"
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return {
        "good_points": [],
        "improvements": [],
        "keywords": ["遠距離恋愛", "手取り22万", "PT"],
        "scene": "職場の休憩室で給与明細を見た瞬間",
        "strategy": "遠距離恋愛×手取り22万PTの悩みを共感させる",
    }
