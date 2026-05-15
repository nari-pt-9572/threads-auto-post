import os
from groq import Groq
from config import GROQ_API_KEY, POSTING_TOPIC


def load_persona() -> str:
    persona_path = os.path.join(os.path.dirname(__file__), "persona.md")
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def generate_post(strategy: dict, topic: str, time_slot: str = "morning") -> str:
    client = Groq(api_key=GROQ_API_KEY)

    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")

    prompt = f"""以下の「良い投稿例」と全く同じ文体・構成・クオリティで投稿を1つ書いてください。

## 良い投稿例

例1（遠距離×交通費）:
彼女のSAで待ち合わせた夜、財布に6000円しか入ってなかった。
片道3時間、高速代だけで消えた。
彼女に「ご飯どうする？」って聞かれて、「なんでもいい」って返した。
本当は何でも良くなかった。
お金のこと、言えなかった。

例2（彼女のセリフ×情けない）:
「気にしないよ」って彼女が言うたびに、しんどくなってた。
割り勘にしてもらった帰り道、ずっと黙って運転してた。
手取り22万、遠距離の交通費、奨学金。
頭の中で計算するのがもう嫌だった。

例3（誕生日×リアルな葛藤）:
財布に4000円しかなかった頃。
彼女の誕生日プレゼントを買いに入った。
30分、同じ棚の前に立ってた。
これにした、と決めたのは4000円のやつだった。
包んでもらいながら、情けなかった。
彼女は「ありがとう」って笑った。
それが余計きつかった。

例4（今との対比）:
高速のSAで缶コーヒー買うの、昔は躊躇してた。
110円が惜しかった。
今はそれを気にしなくなった。
何かが変わったから。

## 投稿のルール
- 全体で130〜170文字
- 1文1行（改行必須）
- 1文は10〜30文字（短く、でも意味がある）
- 一人称は「僕」
- 絵文字なし・ハッシュタグなし
- 「同じような人いる？」などのCTAは入れない
- 副業・稼ぎ方の説明は絶対にしない（「何かが変わった」「動いた」程度ならOK）
- 売り込み感ゼロ
- 1行目は0.5秒でスクロールを止めるフック
  → 具体的な数字・場所・状況を1つだけ置く（例:「財布に4000円しかなかった頃。」）
  → 説明しすぎない（「遠距離恋愛でお金がなかった頃」はNG）
  → 語らなすぎない（「4000円。」だけでは何のことかわからない）
  → 読んだ人が「...どういうこと？」と思って次の行に進む一言
- 感情は説明せず、場面と行動で伝える
- ネガティブで終わっていい（余韻が大事）

## 今回のテーマ
{direction}
参考キーワード: {keywords}

投稿文だけ返してください（他は何も書かないこと）:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.88,
    )

    return response.choices[0].message.content.strip()
