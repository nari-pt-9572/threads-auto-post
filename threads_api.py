import time
import requests
from config import THREADS_ACCESS_TOKEN, THREADS_USER_ID

BASE_URL = "https://graph.threads.net/v1.0"


def create_text_container(text: str) -> str:
    """テキスト投稿コンテナを作成"""
    r = requests.post(
        f"{BASE_URL}/{THREADS_USER_ID}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=30,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"コンテナ作成エラー: {data['error']['message']}")
    return data["id"]


def publish_container(container_id: str) -> str:
    """コンテナを公開（投稿）"""
    time.sleep(5)
    r = requests.post(
        f"{BASE_URL}/{THREADS_USER_ID}/threads_publish",
        params={
            "creation_id": container_id,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=30,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"投稿エラー: {data['error']['message']}")
    return data["id"]


def post_text(text: str) -> str:
    """テキストをThreadsに投稿"""
    container_id = create_text_container(text)
    post_id = publish_container(container_id)
    return post_id


def create_reply_container(text: str, reply_to_id: str) -> str:
    """返信用コンテナを作成"""
    r = requests.post(
        f"{BASE_URL}/{THREADS_USER_ID}/threads",
        params={
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": reply_to_id,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=30,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"返信コンテナ作成エラー: {data['error']['message']}")
    return data["id"]


def post_reply(text: str, reply_to_id: str) -> str:
    """既存投稿への返信を投稿"""
    container_id = create_reply_container(text, reply_to_id)
    post_id = publish_container(container_id)
    return post_id


def get_post_insights(post_id: str) -> dict:
    """投稿のインサイト（いいね・閲覧・リプライ等）を取得"""
    r = requests.get(
        f"{BASE_URL}/{post_id}/insights",
        params={
            "metric": "views,likes,replies,reposts,quotes",
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=15,
    )
    data = r.json()
    if "error" in data:
        return {}
    insights = {}
    for item in data.get("data", []):
        val = item.get("values", [{}])[0].get("value", 0) if item.get("values") else item.get("total_value", {}).get("value", 0)
        insights[item["name"]] = val
    return insights


def get_recent_posts(limit: int = 5) -> list:
    """最近の投稿一覧を取得"""
    r = requests.get(
        f"{BASE_URL}/{THREADS_USER_ID}/threads",
        params={
            "fields": "id,text,timestamp",
            "limit": limit,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=15,
    )
    data = r.json()
    return data.get("data", [])
