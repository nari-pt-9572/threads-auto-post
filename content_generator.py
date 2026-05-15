import os
import random
from groq import Groq
from config import GROQ_API_KEY, POSTING_TOPIC


def load_persona() -> str:
    persona_path = os.path.join(os.path.dirname(__file__), "persona.md")
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


BEFORE_EXAMPLES = """例1（割り勘×帰り道）:
割り勘にしてもらった帰り道。
ずっと黙って運転してた。
「疲れてる？」って彼女が聞いてきた。
違う、と思ったけど、うなずいた。
信号待ちのたびに、口座の残高を思い出してた。
彼女は助手席で音楽をかけた。
僕はずっと前を見てた。

例2（昇給×絶望）:
3年目の昇給、2000円だった。
明細を見てすぐ、折りたたんだ。
3年間、毎日22単位こなしてきた。
その夜、彼女に電話した。
声を聞いたら、何も言えなくなった。
天気の話だけして、切った。

例3（彼女のLINE×返信できない）:
彼女から「今週末来れる？」ってLINEが来た。
既読だけつけて、3時間返信できなかった。
高速代と、今月の残高を頭の中で計算してた。
「行けそう」って打って、送れなかった。
結局「ちょっと確認する」って返した。

例4（誕生日×リアルな葛藤）:
彼女の誕生日プレゼントを買いに入った。
30分、同じ棚の前に立ってた。
これにした、と決めたのは4000円のやつだった。
包んでもらいながら、情けなかった。
彼女は「ありがとう」って笑った。
それが余計きつかった。"""


AFTER_EXAMPLES = """例1（SAで缶コーヒー×変化）:
SAで缶コーヒーを買った。
何も考えずに、手に取った。
昔は5分迷ってた。
彼女が「最近なんか変わった？」って聞いてきた。
気づいてたんだ、と思った。
何も言わなかった。
ただ、コーヒーを飲んだ。

例2（誕生日プレゼント×after）:
彼女の誕生日、デパートに入った。
値段を見ずに選んだ。
去年は4000円のやつを30分迷ってた。
「なんでこれにしたの？」って聞かれた。
「似合うと思って」って答えた。
本当のことだった。

例3（割り勘→奢る）:
「今日は僕が出すよ」って言えるようになった。
彼女は少し驚いた顔をした。
ずっと割り勘にしてもらってた。
帰り道、何も計算しなかった。
ただ運転してた。
それだけで、だいぶ違った。

例4（給料日×変化）:
給料日の夜、彼女に電話した。
前は出られなかった夜だった。
「なんか声明るいね」って言われた。
そうかもしれない、と思った。
何が変わったか、まだうまく説明できない。
でも、変わった。"""


BEFORE_RULES = """- 手取り22万・遠距離・お金の不安がリアルに伝わる場面を描く
- ネガティブで終わっていい（余韻が大事）
- 「情けない」「きつい」「言えなかった」のような感情は説明せず場面で伝える"""

AFTER_RULES = """- 「何かが変わった」ことを、彼女のセリフや自分の行動の変化で伝える
- 副業・稼ぎ方の説明は絶対にしない（「変わった」「動いた」程度でOK）
- 自慢にならない・売り込み感ゼロ
- before時代との対比を場面で自然に入れる"""


def generate_post(strategy: dict, topic: str, time_slot: str = "morning", post_type: str = "before", recent_posts: list = []) -> str:
    client = Groq(api_key=GROQ_API_KEY)

    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")

    if post_type == "after":
        examples = AFTER_EXAMPLES
        type_rules = AFTER_RULES
    else:
        examples = BEFORE_EXAMPLES
        type_rules = BEFORE_RULES

    # 直近投稿のネタ一覧（同じ場面を避けるため）
    recent_texts = ""
    if recent_posts:
        recent_texts = "\n\n## 直近の投稿（これらと同じ場面・ネタは絶対に使わないこと）\n"
        for p in recent_posts:
            recent_texts += f"---\n{p.get('text', '')[:80]}\n"

    prompt = f"""以下の「良い投稿例」と全く同じ文体・構成・クオリティで投稿を1つ書いてください。

## 良い投稿例

{examples}

## 投稿のルール（全共通）
- 全体で120〜170文字
- 1文1行（改行必須）
- 1文は10〜30文字（短く、でも意味がある）
- 一人称は「僕」
- 絵文字なし・ハッシュタグなし
- 「同じような人いる？」などのCTAは入れない
- 売り込み感ゼロ

【読んで映像が浮かぶか？ が最重要】
- 全ての文が「誰が・どこで・何をしたか」を明確に描写していること
- 読んだ人が頭の中で場面を映像として想像できること
- 「え、どういう状況？」となる曖昧な描写はNG
- 主語が誰か、場所はどこか、行動は何か、を明確に書く

【1行目のフック】
- 毎回違うパターンで始める（場所・行動・セリフ・日時・金額など）
- 「財布に〇〇円しか」で始めるのは禁止（使いすぎ）
- 読んだ人が「続きを読みたい」と思う具体的な一言

【因果関係・ストーリーの一貫性】
- 前後の流れが論理的につながっていること
- セリフはその場面の感情を深めるものだけ使う（唐突なセリフNG）
- 感情は説明せず行動で見せる（「返信できなかった」「黙って運転してた」）

【設定・リアリティ】
- 遠距離（片道3時間・車移動）の設定を守る
- 「今夜会いに行く」など近距離前提の表現はNG
- 金額は社会人としてリアルな範囲で（数百円・1000円台はNG）
- 往復は6時間以内

## このタイプの追加ルール
{type_rules}

## 今回のテーマ
{direction}
参考キーワード: {keywords}
{recent_texts}
投稿文だけ返してください（他は何も書かないこと）:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.88,
    )

    return response.choices[0].message.content.strip()


def decide_post_type(posts_log: list) -> str:
    """
    直近の投稿履歴を見てbefore/afterを決める。
    - after連続OK
    - before/afterどちらでも新しいネタを優先
    - after比率は約40%
    - beforeが5連続したら強制的にafter
    """
    recent_types = [p.get("post_type", "before") for p in posts_log[-5:]]

    # beforeが5連続したらafterを強制
    if len(recent_types) >= 5 and all(t == "before" for t in recent_types):
        return "after"

    # 通常は60% before / 40% after
    return "after" if random.random() < 0.40 else "before"
