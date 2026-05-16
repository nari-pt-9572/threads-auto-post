"""
メイン実行スクリプト
GitHub Actionsから呼び出される

Usage:
  python pdca_runner.py --slot morning
  python pdca_runner.py --slot evening
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from config import POSTING_TOPIC, COMPETITOR_ACCOUNTS
from threads_api import post_text, post_reply, get_recent_posts, get_post_insights
from researcher import run_research
from insights_analyzer import analyze_pdca
from content_generator import generate_post, decide_post_type

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

POSTS_LOG = DATA_DIR / "posts_log.json"
PDCA_LOG = DATA_DIR / "pdca_log.json"


def load_json(path: Path) -> list | dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_insights_for_recent_posts() -> list[dict]:
    """直近投稿のインサイトを収集"""
    print("直近投稿のインサイト取得中...")
    recent = get_recent_posts(limit=5)
    posts_with_insights = []
    for post in recent:
        insights = get_post_insights(post["id"])
        posts_with_insights.append({
            "id": post["id"],
            "text": post.get("text", ""),
            "timestamp": post.get("timestamp", ""),
            "insights": insights,
        })
        print(f"  [{post['id']}] 閲覧:{insights.get('views',0)} いいね:{insights.get('likes',0)}")
    return posts_with_insights


def run(slot: str):
    print(f"\n{'='*50}")
    print(f"  Threads自動投稿 [{slot}] {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  テーマ: {POSTING_TOPIC}")
    print(f"{'='*50}\n")

    if not POSTING_TOPIC:
        print("ERROR: POSTING_TOPIC が設定されていません")
        sys.exit(1)

    # ① インサイト収集
    posts_with_insights = collect_insights_for_recent_posts()

    # ② リサーチ
    print("\nリサーチ実行中...")
    research_data = run_research(POSTING_TOPIC, COMPETITOR_ACCOUNTS)

    # ③ PDCA分析
    print("\nPDCA分析中...")
    strategy = analyze_pdca(posts_with_insights, research_data, POSTING_TOPIC)
    print(f"  戦略: {strategy.get('strategy')}")
    print(f"  キーワード: {strategy.get('keywords')}")

    # ④ 投稿文生成（下書きがあればそちらを優先）
    # draft_post.txt → draft_post2.txt の順で確認
    draft_path = DATA_DIR / "draft_post.txt"
    if not draft_path.exists():
        alt = DATA_DIR / "draft_post2.txt"
        if alt.exists():
            alt.rename(draft_path)
    if draft_path.exists():
        with open(draft_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        draft_path.unlink()  # 使ったら削除
        # 1行目が "TYPE:after" or "TYPE:before" なら種別を読み取る
        lines = content.splitlines()
        if lines[0].startswith("TYPE:"):
            post_type = lines[0].replace("TYPE:", "").strip()
            post_text_content = "\n".join(lines[1:]).strip()
        else:
            post_type = "before"
            post_text_content = content
        print(f"\n--- 下書きを使用 [{post_type}] ---\n{post_text_content}\n{'---'*10}\n")
    else:
        existing_log = load_json(POSTS_LOG)
        if not isinstance(existing_log, list):
            existing_log = []
        post_type = decide_post_type(existing_log)
        recent_posts = existing_log[-20:]
        print(f"\n投稿文生成中... [タイプ: {post_type}]")
        if post_type == "report":
            from content_generator import generate_report_post
            post_text_content = generate_report_post()
        elif post_type == "fukugyo":
            from content_generator import generate_fukugyo_post
            post_text_content = generate_fukugyo_post()
        else:
            post_text_content = generate_post(strategy, POSTING_TOPIC, slot, post_type, recent_posts)
        print(f"\n--- 生成された投稿 ({post_type}) ---\n{post_text_content}\n{'---'*10}\n")

    # ⑤ 投稿（タイトル → 本文の2段構成）
    print("Threadsに投稿中...")

    # タイトルをAIが本文に合わせて生成
    import anthropic as _anthropic
    from config import ANTHROPIC_API_KEY as _API_KEY
    _client = _anthropic.Anthropic(api_key=_API_KEY)

    if post_type == "report":
        _title_prompt = f"""以下の近況報告投稿に合うタイトルを1つ生成してください。

【投稿本文】
{post_text_content}

【タイトルのルール】
・読んだ人が「どういうこと？」と続きを読みたくなる逆説・カウンター表現
・例：「変わったのに、気づかなかった。」「お金じゃない何かが増えた。」「1年前の自分に言えない。」「少しだけ、楽になった話。」「副業より先に変わったこと。」
・毎回違うバリエーションにする
・20文字以内。句読点で終わる。タイトルのみ返す（説明不要）"""
    elif post_type == "fukugyo":
        _title_prompt = f"""以下の副業に関する投稿に合うタイトルを1つ生成してください。

【投稿本文】
{post_text_content}

【タイトルのルール】
・読んだ人が「どういうこと？」と続きを読みたくなる逆説・カウンター表現
・例：「動いてから気づいたこと。」「PTが副業を始めた理由。」「怖かったけど動いた話。」「職場には言ってない。」
・毎回違うバリエーションにする
・20文字以内。句読点で終わる。タイトルのみ返す（説明不要）"""
    else:
        _time_label = "手取り22万だった頃" if post_type == "before" else "手取り30万になった今"
        _title_prompt = f"""以下のThreads投稿の内容を読んで、タイトルを1つ生成してください。

【投稿本文】
{post_text_content}

【タイトルのルール】
・「{_time_label}、彼女に言われた一言。」という形を基本としつつ、本文のテーマに合わせて逆説・カウンター表現にしてもよい
・例1（基本）：「手取り22万だった頃、彼女に言われた一言。」
・例2（逆説）：「『会いに行く』が、二人を壊しかけてた。」
・例3（逆説）：「好きだから我慢する、が一番危なかった。」
・20文字以内。句読点で終わる。タイトルのみ返す（説明不要）"""

    _title_msg = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=50,
        messages=[{"role": "user", "content": _title_prompt}],
    )
    title = _title_msg.content[0].text.strip()
    print(f"  タイトル: {title}")

    # タイトル投稿
    title_post_id = post_text(title)
    print(f"✅ タイトル投稿完了！ post_id={title_post_id}")

    # 本文を返信として投稿
    time.sleep(3)
    post_id = post_reply(post_text_content, title_post_id)
    print(f"✅ 本文投稿完了！ post_id={post_id}")

    # ⑥ ログ保存
    log = load_json(POSTS_LOG)
    if not isinstance(log, list):
        log = []
    log.append({
        "post_id": post_id,
        "text": post_text_content,
        "slot": slot,
        "post_type": post_type,
        "timestamp": datetime.now().isoformat(),
        "strategy": strategy,
        "insights": {},  # 翌日取得
    })
    save_json(POSTS_LOG, log)

    # PDCAログ
    pdca_log = load_json(PDCA_LOG)
    if not isinstance(pdca_log, list):
        pdca_log = []
    pdca_log.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "slot": slot,
        "strategy": strategy,
        "research": research_data,
        "post_insights_sample": posts_with_insights[:2],
    })
    save_json(PDCA_LOG, pdca_log[-30:])  # 直近30件だけ保持

    print("\n✅ 全処理完了")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["morning", "evening", "night1", "night2", "night3", "midnight"], default="morning")
    args = parser.parse_args()
    run(args.slot)
