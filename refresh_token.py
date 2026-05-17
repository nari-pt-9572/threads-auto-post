"""
Threadsアクセストークン自動更新スクリプト
GitHub Actionsから呼び出される（50日ごと）
"""
import os
import sys
import requests
from base64 import b64encode
from nacl import encoding, public


def refresh_threads_token(current_token: str) -> str:
    """Threadsトークンを更新して新しいトークンを返す"""
    r = requests.get(
        "https://graph.threads.net/refresh_access_token",
        params={
            "grant_type": "th_refresh_token",
            "access_token": current_token,
        },
        timeout=15,
    )
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"トークン更新失敗: {data}")
    return data["access_token"]


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """GitHub API用にシークレットを暗号化"""
    pk = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    box = public.SealedBox(pk)
    encrypted = box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def update_github_secret(token: str, owner: str, repo: str, secret_name: str, secret_value: str):
    """GitHubのSecretsを更新"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # 公開鍵取得
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=15,
    )
    key_data = r.json()
    key_id = key_data["key_id"]
    public_key = key_data["key"]

    # 暗号化
    encrypted = encrypt_secret(public_key, secret_value)

    # 更新
    r = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted, "key_id": key_id},
        timeout=15,
    )
    if r.status_code not in (201, 204):
        raise RuntimeError(f"Secret更新失敗: {r.status_code} {r.text}")
    print(f"  ✅ {secret_name} を更新しました")


if __name__ == "__main__":
    current_token = os.environ.get("THREADS_ACCESS_TOKEN")
    gh_pat = os.environ.get("GH_PAT")
    owner = "nari-pt-9572"
    repo = "threads-auto-post"

    if not current_token or not gh_pat:
        print("ERROR: 環境変数が不足しています")
        sys.exit(1)

    print("Threadsトークンを更新中...")
    new_token = refresh_threads_token(current_token)
    print(f"  新しいトークン取得成功")

    print("GitHubのSecretsを更新中...")
    update_github_secret(gh_pat, owner, repo, "THREADS_ACCESS_TOKEN", new_token)

    print("\n✅ トークン更新完了")
