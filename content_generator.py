import os
from groq import Groq
from config import GROQ_API_KEY, POSTING_TOPIC


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
    client = Groq(api_key=GROQ_API_KEY)

    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")

    prompt = f"""以下の「良い投稿例」のトーン・文体・構成を完全に真似して、新しい投稿を1つ書いてください。

## 発信者のプロフィール
- 25歳、理学療法士3年目、手取り22万、昇給2000円
- 車で片道3時間の遠距離恋愛中（往復6時間、高速代往復6000円、ガソリン代月2万）
- 彼女は看護師（手取りは自分より上）
- 副業で月8〜10万稼いでいる（副業の内容は絶対に言わない）
- 目的：共感を得て「この人何してるんだろ」と思わせる

## 良い投稿例（このトーンで書く）

例1：
高速のSA、財布開いて「あ、やばい」ってなったことある。
片道3時間、往復6時間かけて彼女に会いに行く途中。
当時手取り22万のPTで、高速代の6000円がマジでキツかった。
今はそれが気にならなくなったけど、あの頃の自分に何か言えるとしたら「もっと早く動けよ」って思う。

例2：
彼女の誕生日プレゼント、3000円のやつ買おうか悩んでた時期があった。
「高いと思われたくない」じゃなくて、純粋に3000円が限界だった。
手取り22万、遠距離の交通費に月2万消えて、奨学金も引かれたら残るのは...
今はちゃんとしたもの買えるけど、あの時の感覚は忘れたくないな。

例3：
看護師の彼女が「気にしないよ」って言ってくれるほど、しんどかった。
手取り22万のPTで、彼女より収入低いのが正直きつかった。
割り勘にしてもらった日、帰り道ずっと「なんか情けないな」ってなってた。
今は違う選択してよかったと思ってる。同じような気持ちだった人いる？

## 今回の投稿テーマ
{direction}
キーワード: {keywords}

## ルール
- 140〜170文字
- 一人称は「僕」
- ハッシュタグなし
- 絵文字は使わないか最大1個
- 副業の内容は絶対に言わない（「違う選択した」「動いた」程度の暗示のみ）
- 数字の誇張禁止（往復は必ず6時間以内）
- 説教・上から目線NG
- ネガティブで終わらない（でも無理やり希望で締めなくていい、余韻でもOK）

投稿文だけ返してください:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.85,
    )

    post_text = response.choices[0].message.content.strip()

    # 文字数チェック
    if len(post_text) > 180:
        post_text = post_text[:170].rsplit("\n", 1)[0]

    return post_text
