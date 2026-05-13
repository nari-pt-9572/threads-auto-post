import os
from dotenv import load_dotenv

load_dotenv()

THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# 投稿ジャンル・テーマ（後で設定）
POSTING_TOPIC = os.getenv("POSTING_TOPIC", "")

# 競合アカウント（カンマ区切り）
COMPETITOR_ACCOUNTS = os.getenv("COMPETITOR_ACCOUNTS", "").split(",")

# 投稿スケジュール
POSTING_TIMES = ["06:00", "21:00"]
