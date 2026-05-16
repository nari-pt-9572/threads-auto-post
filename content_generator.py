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
・余裕ができたことを、行動と彼女の反応で見せる。副業の説明・宣伝は絶対にしない
・同棲・引っ越し・部屋探しのシーンは使わない"""


def generate_post(strategy: dict, topic: str, time_slot: str = "morning", post_type: str = "before", recent_posts: list = []) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    keywords = "、".join(strategy.get("keywords", []))
    direction = strategy.get("strategy", "")
    scene = strategy.get("scene", "")

    examples = AFTER_EXAMPLES if post_type == "after" else BEFORE_EXAMPLES
    type_rules = AFTER_RULES if post_type == "after" else BEFORE_RULES

    # 直近投稿の書き出し＋テーマ一覧（重複防止）
    recent_hooks = ""
    if recent_posts:
        hooks = [p.get("text", "").split("\n")[0] for p in recent_posts[-10:] if p.get("text")]
        if hooks:
            recent_hooks = "\n\n【以下と同じ書き出し・同じ場面は使わないこと】\n" + "\n".join(f"・{h}" for h in hooks)

    # 使用頻度が制限されるイベント（現実の発生頻度で管理）
    rare_events = {
        "年1回": ["誕生日", "記念日", "クリスマス", "バレンタイン", "昇給"],
        "月1回": ["給料日", "給与明細"],
        "一生に数回": ["プロポーズ", "引っ越し", "結婚式"],
    }
    recent_texts_20 = " ".join([p.get("text", "") for p in recent_posts[-20:]])
    recent_texts_100 = " ".join([p.get("text", "") for p in recent_posts[-100:]])

    overused = []
    for freq, keywords in rare_events.items():
        target = recent_texts_100 if freq == "一生に数回" else recent_texts_20
        for kw in keywords:
            if kw in target:
                overused.append(f"{kw}（{freq}のイベントのため使用済み）")

    annual_event_warning = ""
    if overused:
        annual_event_warning = "\n\n【現実の頻度を考慮して今回は使わないこと】\n" + "\n".join(f"・{e}" for e in overused)

    prompt = f"""以下の例文と全く同じ文体・トーン・構成で、新しい投稿を1つ書いてください。

【例文】
{examples}

【絶対に守るルール】
・1文1行で改行する
・一人称は「僕」。「〜です」「〜ました」などの丁寧語は使わない
・全体で150〜180文字（改行を除いてカウント）
・絵文字・ハッシュタグ・「同じような人いる？」などのCTAなし
・現在は遠距離恋愛中。移動手段は車のみ（電車・バス・徒歩はNG）。片道3時間、往復6〜8時間
・同棲・結婚はどちらも現在の話ではなく「将来どうする？」と話し合っている段階として描写する。同棲中・既婚の描写はNG
・彼女の一言を後半に1つ入れる（「〜って聞かれた」「〜って言われた」）
・彼女の一言は「僕の行動・状況・表情への自然な反応」にする。彼女が僕に何かをしてあげようとする内容はNG
・セリフは全体で最大2つまで。会話のやりとり（AがBに言って、BがAに返す）はNG
・話の流れに矛盾がないこと。登場する場面・状況が最初から最後まで一貫している
・現実の頻度で起きないことは使わない（誕生日は年1回、引っ越しは社会人になってからほぼしない、プロポーズは一生に1回など）
・整形外科クリニック勤務のため夜勤はない。「夜勤明け」「夜勤」のシーンは絶対に使わない
・同じ表現を繰り返さない
{type_rules}
{recent_hooks}
{annual_event_warning}

【今回のテーマ】
{direction}（参考キーワード: {keywords}）
【今回の舞台・シーン】
{scene}

投稿文だけ返してください（説明・タイトル不要）:"""

    current_prompt = prompt
    last_result = ""

    for attempt in range(5):
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": current_prompt}],
        )
        result = message.content[0].text.strip()
        last_result = result
        char_count = len(result.replace("\n", ""))

        issues = []

        # 文字数チェック
        if char_count < 150:
            issues.append(f"文字数が{char_count}文字で少なすぎます。必ず150〜180文字で書いてください。")
        elif char_count > 180:
            issues.append(f"文字数が{char_count}文字で多すぎます。必ず150〜180文字で書いてください。")

        # 文字数OKなら品質チェック
        if not issues:
            check_prompt = f"""以下のThreads投稿を読んで、品質チェックをしてください。

【投稿文】
{result}

【チェック項目】
1. 誕生日・夜勤・引っ越し・プロポーズなど禁止シーンが含まれていないか
2. 彼女の一言が「僕の行動・状況・表情への自然な反応」になっているか（彼女が何かしてあげようとする内容はNG）
3. 最後の一文が意味として明確に伝わるか（読んで「？」にならないか）
4. 全体の話の流れに矛盾・唐突な展開がないか
5. 読んだ人が「あるある」「わかる」と感じられるリアルな描写か

すべてOKなら「OK」とだけ返してください。
問題があれば「NG: （理由を1行で）」と返してください。"""

            check = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=100,
                messages=[{"role": "user", "content": check_prompt}],
            )
            check_result = check.content[0].text.strip()

            if check_result.startswith("OK"):
                return result
            else:
                issues.append(check_result)

        # 問題点をまとめてフィードバック
        feedback = "\n".join(f"・{i}" for i in issues)
        current_prompt = prompt + f"\n\n※前回の生成に問題がありました。修正して書き直してください:\n{feedback}"

    return last_result  # 5回試してもダメなら最後の結果を返す


def decide_post_type(posts_log: list) -> str:
    """
    before/afterの比率を60:40で制御。
    beforeが5連続したら強制的にafter。
    """
    recent_types = [p.get("post_type", "before") for p in posts_log[-5:]]

    if len(recent_types) >= 5 and all(t == "before" for t in recent_types):
        return "after"

    return "after" if random.random() < 0.40 else "before"
