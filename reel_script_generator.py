"""
Threads高反応投稿 → Instagram Reelスクリプト生成
"""
import json
import os
from datetime import datetime
from pathlib import Path
from groq import Groq
from config import GROQ_API_KEY

DATA_DIR = Path("data")
POSTS_LOG = DATA_DIR / "posts_log.json"
SCRIPTS_DIR = DATA_DIR / "reel_scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# 固定イントロパターン
INTRO_BEFORE = "理学療法士で手取り22万だった僕が彼女に言われた一言。"
INTRO_AFTER  = "理学療法士で手取り30万になった僕が彼女に言われた一言。"


def get_top_posts(min_likes: int = 3, min_views: int = 100, limit: int = 5) -> list[dict]:
    """インサイトから高反応投稿を抽出"""
    if not POSTS_LOG.exists():
        return []
    with open(POSTS_LOG, "r", encoding="utf-8") as f:
        posts = json.load(f)

    top = []
    for p in posts:
        ins = p.get("insights", {})
        likes = ins.get("likes", 0)
        views = ins.get("views", 0)
        if likes >= min_likes or views >= min_views:
            top.append(p)

    # いいね順でソート
    top.sort(key=lambda x: x.get("insights", {}).get("likes", 0), reverse=True)
    return top[:limit]


def generate_reel_script(threads_post: str, intro_type: str = "before") -> str:
    """
    Threadsの投稿テキストをもとにReelスクリプトを生成
    intro_type: "before" or "after"
    """
    client = Groq(api_key=GROQ_API_KEY)

    intro = INTRO_BEFORE if intro_type == "before" else INTRO_AFTER

    prompt = f"""あなたは25歳の理学療法士(PT)のInstagramリール台本ライターです。

## 発信者プロフィール
- 25歳、理学療法士3年目、元手取り22万→副業で月8〜10万追加
- 車で片道3時間の遠距離恋愛（彼女は看護師、手取りは自分より上）
- 視聴者：22〜29歳、恋愛中・収入に悩む男女

## Threadsで反応が良かった投稿（このネタをReelに展開する）
{threads_post}

## 固定イントロ（必ずこれで始める）
「{intro}」

## Reelスクリプトの構成（30〜60秒想定）

【冒頭テキスト】（画面テロップ）
{intro}

【彼女のセリフ】（インパクトある一言、画面テロップ）
← Threadsのネタから自然につながる彼女の言葉を1つ考える
例：「またファミレス？」「高速代って高くない？」「プレゼントとか気にしないよ」

【本編ナレーション】（話し言葉、3〜5文）
← Threadsの内容を膨らませてリアルな場面描写
← 数字・感情・あるあるを入れる
← 「当時の自分」の気持ちを正直に話す

【転換】（1文）
← 「でも今は〜」「そこから動いて〜」（副業の内容は言わない）

【締め】（1〜2文）
← 視聴者への問いかけ or 余韻で終わる
← 「同じような経験ある人いる？」「コメントで教えて」など

## ルール
- 話し言葉・若者言葉でリアルに（「マジで」「やばかった」「キツかった」OK）
- 副業の内容・手法は絶対に言わない
- 彼女を悪者にしない（彼女は優しく描く）
- 説教NG・上から目線NG
- 数字の誇張NG（往復6時間以内）

台本のみ返してください（説明不要）:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.8,
    )

    return response.choices[0].message.content.strip()


def run_reel_pipeline():
    """高反応Threads投稿を自動でReel台本に変換"""
    print("=== Reel台本生成 ===")

    top_posts = get_top_posts(min_likes=3, min_views=50)

    if not top_posts:
        print("高反応投稿がまだありません（いいね3以上 or 閲覧50以上の投稿が対象）")
        # デモ用：ログから最新投稿を使う
        if POSTS_LOG.exists():
            with open(POSTS_LOG, "r", encoding="utf-8") as f:
                posts = json.load(f)
            if posts:
                top_posts = [posts[-1]]
                print(f"→ 最新投稿でデモ生成します")

    if not top_posts:
        print("投稿ログが空です。先にThreads投稿を実行してください。")
        return

    for post in top_posts:
        text = post.get("text", "")
        ins = post.get("insights", {})
        print(f"\n元ネタ: {text[:50]}...")
        print(f"いいね:{ins.get('likes',0)} 閲覧:{ins.get('views',0)}")

        # Before/Afterどちらのイントロか判断（キーワードで自動判定）
        intro_type = "after" if "今は" in text or "余裕" in text else "before"

        script = generate_reel_script(text, intro_type)

        # 保存
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        filename = SCRIPTS_DIR / f"reel_{date_str}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"元ネタ（Threads）:\n{text}\n\n")
            f.write(f"いいね:{ins.get('likes',0)} 閲覧:{ins.get('views',0)}\n\n")
            f.write("=" * 40 + "\n")
            f.write("Reel台本:\n\n")
            f.write(script)

        print(f"\n{'='*40}")
        print("【生成された台本】")
        print(script)
        print(f"{'='*40}")
        print(f"→ 保存: {filename}")


if __name__ == "__main__":
    run_reel_pipeline()
