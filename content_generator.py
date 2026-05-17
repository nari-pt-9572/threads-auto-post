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
コンビニで彼女への差し入れを選んでいた。
お菓子とジュースで1200円。
レジで電子マネーをかざす瞬間、残高不足の音がした。
月末まであと一週間なのに。
「無理しないでよ」って彼女は言った。
僕は自分の昼食代を削ることでプライドを守っていた。
愛情は、自分を粗末にした先には届かない。

---
SAの駐車場で仮眠から目を覚ました。
ガソリン代を浮かすために深夜割引を待っていた。
彼女に会いに行く往復6時間、月2回で2万円が消える。
「会えるだけで嬉しいよ」って言われた。
その言葉に甘えて、僕は自分の時間を安売りしていた。
正しさは時に、二人の可能性を狭くする。

---
彼女から「今週末来れる？」ってLINEが来た。
既読だけつけて、3時間返信できなかった。
高速代と今月の残高を、頭の中で何度も計算してた。
結局「ちょっと確認する」って返した。
翌日、彼女から「私といると、しんどい？」と来た。
違う、と思った。
でも、正直に言える言葉が見つからなかった。"""


AFTER_EXAMPLES = """---
車のダッシュボードから高速代を取り出した。
往復6000円、でも今は痛くない。
「最近、表情が明るいね」って彼女に言われた。
お金の余裕は、僕から我慢を演じる癖を奪っていた。
彼女の前で本当の自分でいられるようになっていた。
安心は、素直になるための土台だった。

---
高速のSAで、缶コーヒーを何も考えずに買った。
昔は130円を握りしめて、棚の前で5分迷ってた。
今日は財布を出すのに1秒もかからなかった。
彼女がそれを見ていた。
「最近、別人みたい」って言われた。
変わったのは収入だけじゃなかったんだと、そのとき気づいた。

---
彼女と外でご飯を食べた。
メニューを開いて、値段じゃなくて食べたいものを選んだ。
昔は右側の数字ばかり目で追ってた。
今日は何も計算しなかった。
会計を済ませて駐車場に向かったとき、彼女が「前と全然違う」と言った。
余裕ができると、表情まで変わるんだと思った。"""


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

    # 使用頻度が制限されるイベント（チェック範囲 = 直近N件）
    rare_events = {
        ("年1回", 60):      ["誕生日", "記念日", "クリスマス", "バレンタイン", "昇給"],
        ("月1〜2回", 40):   ["給料日", "給与明細"],
        ("一生に数回", 200): ["プロポーズ", "引っ越し", "結婚式"],
    }
    recent_texts_cache = {}

    overused = []
    for (freq, window), keywords in rare_events.items():
        target = " ".join([p.get("text", "") for p in recent_posts[-window:]])
        for kw in keywords:
            if kw in target:
                overused.append(f"{kw}（{freq}のネタのため使用済み）")

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
・最後の一行は具体の場面から導き出した「一言の気づき・抽象」で締める（例：「好きな人に、我慢を気づかれていた。」「変わったのは収入だけじゃなかった。」）
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
1. 夜勤・当直・引っ越し・プロポーズなど禁止シーンが含まれていないか（整形外科クリニック勤務のため夜勤は存在しない）
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
    before/afterの比率を50:50で制御。
    beforeが5連続したら強制的にafter。
    10投稿に1回はfukugyo、15投稿に1回はreportを返す。
    """
    count = len(posts_log)

    # 5投稿に1回、副業投稿を挟む（reportより優先）
    if count > 0 and count % 5 == 0:
        return "fukugyo"

    # 15投稿に1回、近況報告を挟む
    if count > 0 and count % 15 == 0:
        return "report"

    recent_types = [p.get("post_type", "before") for p in posts_log[-5:]]

    if len(recent_types) >= 5 and all(t == "before" for t in recent_types):
        return "after"

    return "after" if random.random() < 0.50 else "before"


def generate_fukugyo_post() -> str:
    """15投稿に1回挟む副業投稿を生成"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = """25歳理学療法士（整形外科クリニック勤務・日勤のみ・夜勤なし）が副業を始めた前後のリアルを1つ書いてください。副業は職場に内緒にしている。

【切り口（毎回ランダムに1つ選ぶ）】

A. 最初の一歩の怖さ
　ポイント：副業を始める前、一番怖かったのは失敗じゃなく「怪しいものに手を出した」と思われること。職場にも彼女にも言えず、ひとりで始めた。3ヶ月後に話したら「なんで早く言わなかったの」と言われた。怖かったのは自分の思い込みだけだった。

B. 勧誘への不信感
　ポイント：副業を始める前、何人かに声をかけられた。全員、僕の収入・目標・生活を聞いてこなかった。ただ誘いたいだけだった。その不信感が、逆に正しい選び方を教えてくれた。

C. 怪しいの解像度
　ポイント：「副業って怪しくない？」と聞かれたとき否定できなかった。怪しい人が多いのは本当だから。でも怪しい人を見分けられるようになったのも、副業を始めてからだった。詐欺を見抜く目は、近づいた人間にしか育たない。

D. 老後の計算
　ポイント：PTの給料で老後の計算をして、途中でやめた。答えを見たくなかった。副業を始めたのは稼ぎたかったからじゃなく、その計算の続きを見られるようになりたかったから。

E. 副業後に彼女との関係が変わった話
　ポイント：将来の話を避けなくなった。お金の話で黙らなくなった。彼女が気づいたのは収入じゃなく、そっちの変化だった。

F. 本業と副業を両立して気づいたこと
　ポイント：時間がないのは本当。でも「時間がないから無理」と言ってた頃の方が、時間を無駄にしてた。

G. 月収100万はいらない、という話
　ポイント：副業を始めた理由は、月収100万でも起業でもなかった。彼女との将来を、お金の不安なく考えたかっただけ。大げさな目標を持たなかったから、続けられた。

H. 職場・友人に言えない話
　ポイント：副業してることを言えない。「怪しいことしてる」と思われたくないから。でも黙って続けた結果、何かが変わった。それでよかったと思ってる。

I. 自分に合ったやり方で続けられた話
　ポイント：月収100万を目指す人の話は参考にならなかった。自分のペースで少しずつ動いた。それだけで、半年後の不安の量が違った。

【ルール】
・1文1行、一人称は「僕」、丁寧語NG
・副業の内容・手法・具体的な金額は言わない
・読者の不安・疑いを先に代弁し、自分の体験で静かに裏切る構成にする
・「月収100万」「起業」などの大げさな勧誘と距離を置き、等身大で語る
・最後の一行は抽象的な気づきで締める
・選んだ切り口のポイントはあくまで骨格。表現・順序・セリフは毎回変える
・100〜200文字
・絵文字・ハッシュタグなし

投稿文だけ返してください（説明不要）:"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=350,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_report_post() -> str:
    """10投稿に1回挟む近況報告投稿を生成"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = """25歳理学療法士が副業を始めてからの近況を、以下の例文スタイルで書いてください。

【例文】
副業始めて1年が経った。
手取りは変わってない。
でも毎月8万、別で入るようになった。
彼女に「最近変わったね」って言われる回数が増えた。
何が変わったか、うまく説明できない。
お金じゃない何かが、変わったんだと思う。

【ルール】
・1文1行、一人称は「僕」、丁寧語NG
・副業の内容・手法は言わない
・100〜130文字
・絵文字・ハッシュタグなし
・毎回少し違う切り口で書く（収入・彼女の反応・自分の変化・将来への気持ちなど）
・最後の一行は抽象的な気づきで締める

投稿文だけ返してください（説明不要）:"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
