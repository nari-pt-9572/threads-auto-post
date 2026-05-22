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
1年目の頃、彼女をご飯に誘う前に
毎回Googleマップで値段を確認してた。
「このくらいなら大丈夫」と判断してから、提案してた。
彼女は知らなかったと思う。
何が食べたいかより先に、いくらかかるかを考えてた。
その順番が、ずっと当たり前だった。

---
1年目の冬、ふたりで温泉旅行の宿を調べてた。
気になったところを開いて、値段を確認して、閉じた。
また別のを開いて、確認して、閉じた。
3回くらい繰り返して、少し安いところに決めた。
最初に開いた宿の方が、本当は良かった。
でも、もう閉じてた。"""


AFTER_EXAMPLES = """---
旅行の宿を選ぶとき、値段より先に場所を決めるようになった。
前は逆だった。予算を先に決めて、その中で探してた。
いつから変わったか、正確には覚えていない。
気づいたら、そうなってた。

---
スーパーで彼女が欲しそうにしてたものを、深く考えずにカゴに入れた。
昔の自分なら、一瞬迷ってた。
今日は迷わなかった。
それだけのことなのに、何かが変わった気がした。"""


BEFORE_RULES = """・時系列は「理学療法士1年目・副業を始める前・手取り22万だった頃」の話のみ
・2年目・3年目・副業・収入が上がった話は絶対に出さない。「今は〜」「最近は〜」も絶対に出さない
・手取り22万でも普通に生活はできている。「口座が空」「会いに行けない」「お金がなくて〇〇できない」などの極端な貧困描写はNG
・節約を「少し意識している」程度の描写にする。「数百円のために〇〇した」「数十円安いために遠くへ走った」など非現実的な極端節約はNG
・デートや外食を「完全に断る・行けない」ではなく「少し安い方を選ぶ・ワンランク下を選ぶ」程度の描写にする
・物語・日記形式で書く。詩的な表現や抽象的な締めはNG
・時間軸を明示する（「付き合い始めの頃」「月末」「〇ヶ月目」など）
・自分の思い込みを先に提示し、現実との衝突で展開する
・心理・本音を直接書く（「本当は〜だった」「〜だと思ってた」）
・「〜た」で統一。「〜だんだ」「〜たんだ」は使わない
・最後は余韻を残す一行で終わる（抽象的な哲学ではなく、感情の着地）"""

AFTER_RULES = """・時系列は「理学療法士2年目以降・副業を始めた頃〜今」の話のみ
・1年目・手取り22万の頃の話は絶対に出さない。before/afterを混ぜない
・収入の変化理由は絶対に説明しない
・「生活が180°変わった」「余裕ができた」という大げさな変化はNG。あくまで「ほんの少し贅沢できる」「節約を気にしなくなった」「生活がラクになった」程度のささやかな変化として描写する
・具体的な金額を出す場合は現実的な範囲で。「数十万円の〇〇を即決した」など極端な大きな支出の描写はNG
・物語・日記形式で書く。詩的な表現や抽象的な締めはNG
・昔との対比を自然に入れる（「前だったら〜してた。今日は〜した。」）
・彼女の反応で変化を示す。理由・手段の説明は絶対にしない
・「〜た」で統一。「〜だんだ」「〜たんだ」は使わない
・同棲・引っ越し・部屋探しのシーンは使わない
・最後は余韻を残す一行で終わる（抽象的な哲学ではなく、感情の着地）"""


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

    # 直近投稿で使われたシーン・場所（重複防止）
    scene_keywords = ["ショッピングモール", "海", "レストラン", "旅行", "プレゼント", "誕生日", "記念日",
                      "給料日", "明細", "口座", "高速", "下道", "電話", "LINE", "デート", "割り勘",
                      "外食", "カフェ", "ドライブ", "宿", "ホテル", "砂浜", "花火", "コンビニ",
                      "同棲", "ガソリン", "SA", "サービスエリア", "財布", "給油"]
    recent_all_text = " ".join([p.get("text", "") for p in recent_posts[-15:]])
    used_scenes = [kw for kw in scene_keywords if kw in recent_all_text]
    if used_scenes:
        scene_warning = "\n\n【直近で使ったシーン・場所は使わないこと】\n" + "\n".join(f"・{s}" for s in used_scenes)
    else:
        scene_warning = ""

    # 直近3件に金額（円）が含まれているか確認
    recent_3_text = " ".join([p.get("text", "") for p in recent_posts[-3:]])
    has_recent_money = "円" in recent_3_text or "万" in recent_3_text
    money_rule = "・具体的な金額（〇〇円・〇万円）は入れない。金額ではなく行動・心理で描写する" if has_recent_money else "・具体的な金額を入れる場合は現実的な範囲で1回まで。毎回必ず入れなくてよい"

    # 使用頻度が制限されるイベント（チェック範囲 = 直近N件）
    rare_events = {
        ("年1回", 60):      ["誕生日", "記念日", "クリスマス", "バレンタイン", "昇給"],
        ("月1〜2回", 40):   ["給料日", "給与明細"],
        ("3ヶ月に1回程度", 20): ["同棲", "ガソリン", "SA", "サービスエリア"],
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
{scene_warning}

【例文】
{examples}

【絶対に守るルール】
・1文1行で改行する
・一人称は「僕」。「〜です」「〜ました」などの丁寧語は使わない
・全体で160〜220文字（改行を除いてカウント）
・絵文字・ハッシュタグ・「同じような人いる？」などのCTAなし
・現在は遠距離恋愛中。移動手段は車のみ（電車・バス・徒歩はNG）。片道3時間、往復6〜8時間
・同棲・結婚はどちらも現在の話ではなく「将来どうする？」と話し合っている段階として描写する。同棲中・既婚の描写はNG
・セリフ・会話は入れない。内面の独白スタイルで書く
・彼女は登場してもよいが、セリフは不要。行動・様子の描写にとどめる
・話の流れに矛盾がないこと。登場する場面・状況が最初から最後まで一貫している
・最後の一行は具体の場面から導き出した「一言の気づき・抽象」で締める（例：「好きな人に、我慢を気づかれていた。」「変わったのは収入だけじゃなかった。」）
・現実の頻度で起きないことは使わない（誕生日は年1回、引っ越しは社会人になってからほぼしない、プロポーズは一生に1回など）
・整形外科クリニック勤務のため夜勤はない。「夜勤明け」「夜勤」のシーンは絶対に使わない
・同じ表現を繰り返さない
{money_rule}
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

    for attempt in range(3):
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
        if char_count < 160:
            issues.append(f"文字数が{char_count}文字で少なすぎます。必ず160〜220文字で書いてください。")
        elif char_count > 220:
            issues.append(f"文字数が{char_count}文字で多すぎます。必ず160〜220文字で書いてください。")

        # 文字数OKなら品質チェック（haiku使用でコスト削減）
        if not issues:
            check_prompt = f"""以下のThreads投稿を読んで、品質チェックをしてください。

【投稿文】
{result}

【チェック項目】
1. 夜勤・当直・引っ越し・プロポーズなど禁止シーンが含まれていないか（整形外科クリニック勤務のため夜勤は存在しない）
2. セリフ・会話が含まれていないか（内面の独白スタイルが守られているか）
3. 最後の一文が意味として明確に伝わるか（読んで「？」にならないか）
4. 全体の話の流れに矛盾・唐突な展開がないか
5. 読んだ人が「あるある」「わかる」と感じられるリアルな描写か
6. 「口座が空で会いに行けない」「数百円のために〇〇した」など手取り22万の若者が実際にはしない極端な行動や貧困描写が含まれていないか
7. ビフォー投稿の場合：「節約を少し意識する程度」になっているか（完全に断る・行けない・できないなどの極端描写はNG）
8. アフター投稿の場合：「ほんの少し余裕ができた」程度の描写になっているか（生活が180°変わった・大金を気前よく使うなどの過度な変化はNG）

すべてOKなら「OK」とだけ返してください。
問題があれば「NG: （理由を1行で）」と返してください。"""

            check = client.messages.create(
                model="claude-haiku-4-5",
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
    直近5件にfukugyoがなければ強制的にfukugyoを入れる。
    直近15件にreportがなければreportを入れる。
    beforeが5連続したら強制的にafter。
    """
    recent_types = [p.get("post_type", "before") for p in posts_log[-3:]]
    recent_15_types = [p.get("post_type", "before") for p in posts_log[-15:]]

    # 直近3件にfukugyoがなければ強制
    if len(posts_log) >= 3 and "fukugyo" not in recent_types:
        return "fukugyo"

    # 直近15件にreportがなければ強制
    if len(posts_log) >= 15 and "report" not in recent_15_types:
        return "report"

    # beforeが3連続したら強制after
    if len(recent_types) >= 3 and all(t == "before" for t in recent_types):
        return "after"

    return "after" if random.random() < 0.50 else "before"


FUKUGYO_SERIES = {
    0: """【シリーズ①：現実の危機感】
25歳理学療法士として、老後のお金の現実について書いてください。

ポイント：
・PTの給料で老後の計算をしたことがある
・年金は少子高齢化で確実に減る（2057年には月21万円台になる見通し）
・老後2000万問題どころか、増税・物価上昇・寿命の伸びを考えると5000〜6000万必要と言われてる
・その数字を見て、計算を途中でやめた
・だからこそ今から収入の作り方を変えないといけないと気づいた
・具体的な金額の数字は使ってよい（現実感のため）""",

    1: """【シリーズ②：共感（やりたいけど怖かった）】
副業に挑戦したかったけど一歩踏み出せなかった頃の気持ちを書いてください。

ポイント：
・やりたい気持ちはずっとあった
・でも最初の一歩が怖かった
・「怪しいものに手を出した」と思われることが怖かった
・SNSで「月収100万」「すぐ稼げる」を見るたびに逆に引いてた
・動けないまま時間だけ過ぎてた
・同じ気持ちの人はぼくだけじゃないと思う、という共感で締める""",

    2: """【シリーズ③：怪しいは正しい感覚（逆説）】
「副業は怪しい」という感覚について逆説的に書いてください。

ポイント：
・副業って怪しいよね、という気持ちはわかる（共感から入る）
・高級車・高級料理・大量の札束を見せて「月収100万！」と煽ってくる人が多い
・でも「怪しい」と感じる感覚は実はすごく正しい
・怪しいのは「副業」じゃなくて「案件を売りたいだけの人」
・見分け方：自分の収入・目標・生活を聞いてくるかどうか
・聞いてこない人は、こっちの状況に関係なく自分の商材を売りたいだけ""",

    3: """【シリーズ④：解決（自分に合ったやり方）】
自分の状況に合った方法を見つけて続けられてる話を書いてください。

ポイント：
・自分の収入・生活・目標・不安を全部話して、状況に合ったやり方を提案してもらった
・「これをやれば稼げる」じゃなく「あなたにはこれが合ってる」だった
・不安や迷いがなくなった
・自分のペースで続けられてる
・続けられるから少しずつ成果につながってる
・大げさな目標を持たなかったから続けられた、という締め""",

    4: """【シリーズ⑤：DM誘導】
同じ気持ちを持ってる人へ向けて、自然なDM誘導を書いてください。

ポイント：
・自分も同じ不安・疑いを持ってたからこそ話せることがある
・副業を聞かれたとき、まず相手の収入・目標・不安を聞く
・それを聞かずに勧めてくる人は信用しない
・同じことをやれば稼げるとは言えない。人によって合うやり方は違う
・気軽にDMで今の状況と目的を教えてほしい、という自然な流れで締める
・押しつけがましくならないトーンで""",
}


def get_fukugyo_series_position(posts_log: list) -> int:
    """副業投稿の現在のシリーズ位置（0〜4）を返す"""
    fukugyo_count = sum(1 for p in posts_log if p.get("post_type") == "fukugyo")
    return fukugyo_count % 5


def generate_fukugyo_post(posts_log: list = None) -> str:
    """副業投稿を5投稿1シリーズで生成"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    position = get_fukugyo_series_position(posts_log or [])
    series_instruction = FUKUGYO_SERIES[position]

    prompt = f"""25歳理学療法士（整形外科クリニック勤務・日勤のみ・夜勤なし）が副業について書いたThreads投稿を1つ生成してください。

{series_instruction}

【共通ルール】
・1文1行、一人称は「僕」、丁寧語NG
・副業の具体的な手法・プラットフォーム名（Amazon・メルカリ等）は言わない
・「月収100万」「すぐ稼げる」をうたう人間は案件屋であり詐欺まがい。そういう価値観とは距離を置く
・等身大で、地味に、自分のペースで続けられるというスタンス
・絵文字・ハッシュタグなし
・100〜180文字

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
