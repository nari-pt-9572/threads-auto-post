import json
import os
import re
import anthropic
from config import ANTHROPIC_API_KEY, POSTING_TOPIC


def load_persona() -> str:
    """persona.mdを読み込む"""
    persona_path = os.path.join(os.path.dirname(__file__), "persona.md")
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def generate_post(strategy: dict, topic: str, time_slot: str = "morning") -> str:
    """
    PDCA戦略をもとにThreads投稿文を生成
    time_slot: "morning"(朝6時) or "evening"(夜21時)
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    persona = load_persona()
    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")
    improvements = strategy.get("improvements", "")

    time_context = "朝6時（通勤・起床時間帯）" if time_slot == "morning" else "夜21時（帰宅後・リラックス時間帯）"

    persona_section = f"\n## ペルソナ・運用ガイドライン\n{persona}\n" if persona else ""

    prompt = f"""あなたは25歳の理学療法士(PT)として、Threadsに投稿するコンテンツクリエイターです。
{persona_section}
## 今回の投稿指示

PDCAから得た戦略:
- 今日の方向性: {direction}
- 改善ポイント: {improvements}
- 使うキーワード: {keywords}
- 時間帯: {time_context}

## 投稿文を1つ生成してください

### 必須ルール
- **140〜170文字**（絶対に守る）
- 一人称は「僕」（「俺」は使わない）
- ハッシュタグは使わない
- 絵文字は1〜2個まで
- ネガティブで終わらない（必ず希望を見せる）
- 1投稿=1テーマ（複数トピック詰め込みNG）

### 構成パターン（以下のどれかを使う）
パターンA: 過去の悩み → 現在の変化 → 「同じ人いる?」
パターンB: 具体的な数字で現実を突きつける → 「でも今は違う」
パターンC: あるある描写 → 「その気持ちわかる」→ 希望

### 絶対NG
- PT技術・医療知識の話
- 副業の具体的な手法（暗示のみ）
- 彼女を悪者にする表現
- 「DM送って」などの押し付けがましい誘導
- ネガティブで終わる投稿

投稿文のみ返してください（説明・タイトル・注釈不要）:"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    post_text = message.content[0].text.strip()

    # 文字数チェック（170文字超えたらトリミング）
    if len(post_text) > 175:
        # 文末で切る
        post_text = post_text[:170].rsplit("\n", 1)[0]

    return post_text
