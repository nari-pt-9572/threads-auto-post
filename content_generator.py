import os
import random
import anthropic
from config import ANTHROPIC_API_KEY, POSTING_TOPIC


def load_persona() -> str:
    persona_path = os.path.join(os.path.dirname(__file__), "persona.md")
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


BEFORE_EXAMPLES = """---
割り勘にしてもらった帰り道。
高速に乗る前に、口座の残高をスマホで確認した。
今月の残高、奨学金の引き落とし、来月の高速代。
頭の中で計算しながら、アクセルを踏んだ。
彼女は助手席で眠っていた。
起こさないように、音楽を消した。
別れ際、彼女が「無理しなくていいよ」と言った。
その言葉の意味が、ずっと頭に残った。

---
3年目の昇給通知が来た日。
明細を開いて、2000円という数字を3回確認した。
3年間、毎日22単位こなしてきた結果がこれだった。
ロッカーの前で5分、動けなかった。
その夜、彼女に電話した。
声を聞いたら、何も言えなくなった。
しばらく黙ってたら、「ちゃんと食べてる？」って聞かれた。
食べてる、とだけ答えた。

---
彼女から「今週末来れる？」ってLINEが来た。
既読だけつけて、3時間返信できなかった。
高速代と今月の残高を、頭の中で何度も計算してた。
結局「ちょっと確認する」って返した。
翌日、彼女から「私といると、しんどい？」と来た。
違う、と思った。
でも、うまく説明できなかった。"""


AFTER_EXAMPLES = """---
高速のSAで、缶コーヒーを何も考えずに買った。
昔は130円を握りしめて、棚の前で5分迷ってた。
今日は財布を出すのに1秒もかからなかった。
彼女がそれを見ていた。
「最近、別人みたい」って言われた。
そうかもしれない、と思った。
何が変わったか、うまく説明できなかった。

---
彼女の誕生日、デパートに入った。
値段を見ずに、似合うかどうかだけ考えた。
去年は4000円のやつで30分迷ってた。
今日は何も迷わなかった。
レジで支払いながら、少し不思議な気持ちになった。
「なんでこれにしたの？」って聞かれた。
「似合うと思って」って答えた。

---
彼女と外でご飯を食べた。
メニューを開いて、値段じゃなくて食べたいものを選んだ。
昔は右側の数字ばかり目で追ってた。
今日は何も計算しなかった。
会計を済ませて駐車場に向かったとき、彼女が「前と全然違う」と言った。
どのへんが、と聞いたら「なんか堂々としてる」と言った。
自分ではわからなかった。"""


BEFORE_RULES = """・時系列は「理学療法士1年目・副業前・手取り22万だった頃」の話のみ。「今は〜」「最近は〜」は絶対に出さない
・お金がなくて苦しかった場面を、行動と具体描写で見せる"""

AFTER_RULES = """・時系列は「理学療法士2年目以降・副業を始めてから・手取り30万で余裕がある今」の話のみ。before/afterを混ぜない
・余裕ができたことを、行動と彼女の反応で見せる。副業の説明・宣伝は絶対にしない"""


def generate_post(strategy: dict, topic: str, time_slot: str = "morning", post_type: str = "before", recent_posts: list = []) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")
    scene = strategy.get("scene", "")

    examples = AFTER_EXAMPLES if post_type == "after" else BEFORE_EXAMPLES
    type_rules = AFTER_RULES if post_type == "after" else BEFORE_RULES

    # 直近投稿の書き出し一覧（重複防止）
    recent_hooks = ""
    if recent_posts:
        hooks = [p.get("text", "").split("\n")[0] for p in recent_posts[-10:] if p.get("text")]
        if hooks:
            recent_hooks = "\n\n【以下と同じ書き出し・同じ場面は使わないこと】\n" + "\n".join(f"・{h}" for h in hooks)

    prompt = f"""以下の例文と全く同じ文体・トーン・構成で、新しい投稿を1つ書いてください。

【例文】
{examples}

【絶対に守るルール】
・1文1行で改行する
・一人称は「僕」。「〜です」「〜ました」などの丁寧語は使わない
・全体で150〜180文字（改行を除いてカウント）
・絵文字・ハッシュタグ・「同じような人いる？」などのCTAなし
・移動手段は車のみ（電車・バス・徒歩はNG）。片道3時間、往復6〜8時間
・彼女の一言を後半に1つ入れる（「〜って聞かれた」「〜って言われた」）
・彼女の一言は「僕の行動・状況・表情への自然な反応」にする。彼女が僕に何かをしてあげようとする内容はNG
・セリフは全体で最大2つまで。会話のやりとり（AがBに言って、BがAに返す）はNG
・話の流れに矛盾がないこと。登場する場面・状況が最初から最後まで一貫している
・同じ表現を繰り返さない
{type_rules}
{recent_hooks}

【今回のテーマ】
{direction}（参考キーワード: {keywords}）
【今回の舞台・シーン】
{scene}

投稿文だけ返してください（説明・タイトル不要）:"""

    for attempt in range(3):
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text.strip()
        char_count = len(result.replace("\n", ""))
        if 150 <= char_count <= 180:
            return result
        # 短すぎる場合はプロンプトに追記して再試行
        if char_count < 150:
            prompt += f"\n\n※前回の生成は{char_count}文字でした。必ず150文字以上180文字以内で書いてください。"
        else:
            prompt += f"\n\n※前回の生成は{char_count}文字でした。必ず180文字以内で書いてください。"

    return result  # 3回試してもダメなら最後の結果を返す


def decide_post_type(posts_log: list) -> str:
    """
    before/afterの比率を60:40で制御。
    beforeが5連続したら強制的にafter。
    """
    recent_types = [p.get("post_type", "before") for p in posts_log[-5:]]

    if len(recent_types) >= 5 and all(t == "before" for t in recent_types):
        return "after"

    return "after" if random.random() < 0.40 else "before"
