import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, POSTING_TOPIC


def generate_post(strategy: dict, topic: str, time_slot: str = "morning") -> str:
    """
    PDCA戦略をもとにThreads投稿文を生成
    time_slot: "morning"(朝6時) or "evening"(夜21時)
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    keywords = "、".join(strategy.get("keywords", [topic]))
    direction = strategy.get("strategy", f"{topic}に関する情報を発信する")

    time_context = "朝の時間帯（6時）に読まれる投稿" if time_slot == "morning" else "夜の時間帯（21時）に読まれる投稿"

    prompt = f"""あなたはThreadsのプロフェッショナルなコンテンツクリエイターです。

ジャンル: {topic}
今日のテーマ: {direction}
使うキーワード: {keywords}
時間帯: {time_context}

## Threads投稿文を1つ生成してください

ルール:
- 300文字以内
- 自然な日本語で話しかけるように
- 最後に行動を促す一言を入れる（「コメントで教えて」「保存して後で見て」など）
- ハッシュタグは2〜3個のみ
- 朝なら「おはよう」など時間帯に合わせた書き出し
- 共感・価値提供・気づき のどれかを意識する
- 改行を使って読みやすく

投稿文のみ返してください（説明不要）:"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()
