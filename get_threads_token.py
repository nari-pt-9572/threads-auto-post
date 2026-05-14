# -*- coding: utf-8 -*-
"""
Threads APIアクセストークン取得スクリプト
実行するとブラウザが開くので認証するだけでトークンが取得できます
"""
import sys
import os
import json
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

THREADS_APP_ID = "1300555821523665"
THREADS_APP_SECRET = "d57f7981b2b5d8cc3f878e09055dff5b"
REDIRECT_URI = "http://localhost:8080/"
SCOPES = "threads_basic,threads_content_publish,threads_manage_insights"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>OK! This window can be closed.</h1>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: no code")

    def log_message(self, format, *args):
        pass  # ログ非表示


def register_redirect_uri():
    """リダイレクトURIをAPIで登録"""
    r = requests.post(
        f"https://graph.threads.net/v1.0/{THREADS_APP_ID}/update_app_settings",
        params={
            "access_token": f"{THREADS_APP_ID}|{THREADS_APP_SECRET}",
            "redirect_uris": REDIRECT_URI,
        },
    )
    return r.json()


def get_short_lived_token(code: str) -> str:
    r = requests.post(
        "https://graph.threads.net/oauth/access_token",
        data={
            "client_id": THREADS_APP_ID,
            "client_secret": THREADS_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
    )
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"短期トークン取得失敗: {data}")
    return data["access_token"]


def get_long_lived_token(short_token: str) -> tuple[str, str]:
    r = requests.get(
        "https://graph.threads.net/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": THREADS_APP_SECRET,
            "access_token": short_token,
        },
    )
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"長期トークン取得失敗: {data}")
    return data["access_token"], str(data.get("expires_in", ""))


def get_threads_user_id(token: str) -> str:
    r = requests.get(
        "https://graph.threads.net/v1.0/me",
        params={"fields": "id,username", "access_token": token},
    )
    data = r.json()
    return data.get("id", ""), data.get("username", "")


def main():
    print("=" * 50)
    print("  Threads APIトークン取得")
    print("=" * 50)

    # リダイレクトURI登録を試みる
    print("\nリダイレクトURIを登録中...")
    result = register_redirect_uri()
    print(f"  結果: {result}")

    # 認証URL構築
    auth_url = (
        f"https://threads.net/oauth/authorize"
        f"?client_id={THREADS_APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&response_type=code"
    )

    print(f"\nブラウザを開いて認証してください...")
    print(f"URL: {auth_url}")
    webbrowser.open(auth_url)

    # ローカルサーバーでコールバック待機
    print("\n認証待機中... (ブラウザで許可してください)")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print("エラー: 認証コードが取得できませんでした")
        sys.exit(1)

    print(f"\n認証コード取得成功！")

    # 短期トークン取得
    print("短期トークンを取得中...")
    short_token = get_short_lived_token(auth_code)

    # 長期トークン取得
    print("長期トークンに変換中...")
    long_token, expires = get_long_lived_token(short_token)

    # ユーザーID取得
    print("ユーザーID取得中...")
    user_id, username = get_threads_user_id(long_token)

    print("\n" + "=" * 50)
    print("  取得完了！")
    print("=" * 50)
    print(f"ユーザー名: @{username}")
    print(f"ユーザーID: {user_id}")
    print(f"アクセストークン: {long_token}")
    print("=" * 50)

    # .envに保存
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"THREADS_ACCESS_TOKEN={long_token}\n")
        f.write(f"THREADS_USER_ID={user_id}\n")
        f.write(f"ANTHROPIC_API_KEY=\n")
        f.write(f"SERPER_API_KEY=\n")
        f.write(f"POSTING_TOPIC=\n")
        f.write(f"COMPETITOR_ACCOUNTS=\n")

    print(f"\n.envファイルに保存しました")
    print("次のステップ: GitHub Secretsに以下を登録してください")
    print(f"  THREADS_ACCESS_TOKEN = {long_token[:30]}...")
    print(f"  THREADS_USER_ID = {user_id}")

    input("\nEnterで閉じる...")


if __name__ == "__main__":
    main()
