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
from datetime import datetime
from pathlib import Path

from config import POSTING_TOPIC, COMPETITOR_ACCOUNTS
from threads_api import post_text, get_recent_posts, get_post_insights
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
    draft_path = DATA_DIR / "draft_post.txt"
    if draft_path.exists():
        with open(draft_path, "r", encoding="utf-8") as f:
            post_text_content = f.read().strip()
        draft_path.unlink()  # 使ったら削除
        post_type = "draft"
        print(f"\n--- 下書きを使用 ---\n{post_text_content}\n{'---'*10}\n")
    else:
        existing_log = load_json(POSTS_LOG)
        if not isinstance(existing_log, list):
            existing_log = []
        post_type = decide_post_type(existing_log)
        # 直近10件のテキストをAIに渡して同じネタを避ける
        recent_posts = existing_log[-10:]
        print(f"\n投稿文生成中... [タイプ: {post_type}]")
        post_text_content = generate_post(strategy, POSTING_TOPIC, slot, post_type, recent_posts)
        print(f"\n--- 生成された投稿 ({post_type}) ---\n{post_text_content}\n{'---'*10}\n")

    # ⑤ 投稿
    print("Threadsに投稿中...")
    post_id = post_text(post_text_content)
    print(f"✅ 投稿完了！ post_id={post_id}")

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
    parser.add_argument("--slot", choices=["morning", "evening"], default="morning")
    args = parser.parse_args()
    run(args.slot)
