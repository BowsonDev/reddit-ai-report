"""
Reddit AI 板塊日報 / 週報產生器
=================================
自動從 Reddit 抓取 AI 相關板塊的高互動文章，
篩選、排序後產出 JSON 原始資料和 Markdown 報告。

可搭配 generate_html.py 產出精美 HTML 報告，
搭配 notify_telegram.py 發送 Telegram 通知。
"""

import requests
import json
import time
import os
import argparse
from datetime import datetime, timezone

# ============================================================
# 設定區（你可以依需求修改這些數字）
# ============================================================

# 預設監測的板塊清單
DEFAULT_SUBREDDITS = [
    "artificial",
    "LocalLLaMA",
    "ChatGPT",
    "ArtificialInteligence",
    "MachineLearning",
]

# 篩選門檻
DAILY_MIN_UPVOTES = 50       # 日報：最低按讚數
DAILY_MIN_COMMENTS = 10      # 日報：最低留言數
WEEKLY_MIN_UPVOTES = 200     # 週報：最低按讚數
WEEKLY_MIN_COMMENTS = 30     # 週報：最低留言數
MAX_POSTS_PER_SUB = 15       # 每個板塊最多抓幾篇
REPORT_TOP_N = 10            # 報告只取前 N 篇

# User-Agent（Reddit 要求每個程式要自報身份）
USER_AGENT = "RedditAIReport/1.0 (by FoxMindPeace)"


# ============================================================
# Reddit 資料抓取
# ============================================================

def get_reddit_session():
    """建立 Reddit 連線。有 API Key 就用 OAuth，沒有就用公開端點。"""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

    if client_id and client_secret:
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        data = {"grant_type": "client_credentials"}
        res = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=data,
            headers={"User-Agent": USER_AGENT},
        )
        token = res.json().get("access_token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
            session.base_url = "https://oauth.reddit.com"
            print("✅ 使用 OAuth 模式")
            return session

    session.base_url = "https://www.reddit.com"
    print("ℹ️  使用公開模式（不需要 API Key）")
    return session


def fetch_posts(session, subreddit, sort="hot", time_filter="day", limit=25):
    """從指定板塊抓取文章。"""
    base = getattr(session, "base_url", "https://www.reddit.com")
    url = f"{base}/r/{subreddit}/{sort}.json"
    params = {"limit": limit}
    if sort == "top":
        params["t"] = time_filter

    try:
        res = session.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            p = child.get("data", {})
            posts.append({
                "id": p.get("id"),
                "subreddit": p.get("subreddit"),
                "title": p.get("title"),
                "author": p.get("author"),
                "upvotes": p.get("ups", 0),
                "score": p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "created_utc": p.get("created_utc"),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "selftext": p.get("selftext", "")[:2000],
                "link_flair_text": p.get("link_flair_text"),
                "is_self": p.get("is_self", False),
                "domain": p.get("domain"),
                "upvote_ratio": p.get("upvote_ratio", 0),
            })
        return posts

    except Exception as e:
        print(f"  ⚠️  抓取 r/{subreddit} 失敗：{e}")
        return []


def calculate_metrics(post):
    """計算讚留比、熱度分數等衍生指標。"""
    upvotes = post.get("upvotes", 0)
    comments = post.get("num_comments", 0)

    post["engagement_ratio"] = round(upvotes / max(comments, 1), 1)
    post["heat_score"] = round(upvotes * 0.6 + comments * 0.4, 1)

    created = post.get("created_utc", 0)
    if created:
        dt = datetime.fromtimestamp(created, tz=timezone.utc)
        post["created_readable"] = dt.strftime("%Y-%m-%d %H:%M UTC")
        hours_ago = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        post["hours_ago"] = round(hours_ago, 1)

    return post


def filter_and_rank(all_posts, mode="daily"):
    """篩選並按熱度分數排序。"""
    min_up = DAILY_MIN_UPVOTES if mode == "daily" else WEEKLY_MIN_UPVOTES
    min_com = DAILY_MIN_COMMENTS if mode == "daily" else WEEKLY_MIN_COMMENTS

    filtered = [
        p for p in all_posts
        if p.get("upvotes", 0) >= min_up and p.get("num_comments", 0) >= min_com
    ]
    filtered.sort(key=lambda x: x.get("heat_score", 0), reverse=True)
    return filtered[:REPORT_TOP_N]


# ============================================================
# 主程式
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Reddit AI 板塊日報 / 週報產生器")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily",
                        help="報告模式：daily（日報）或 weekly（週報）")
    parser.add_argument("--subreddit", type=str, default=None,
                        help="要監測的板塊，用逗號分隔")
    parser.add_argument("--output", type=str, default="./output",
                        help="報告輸出目錄")
    args = parser.parse_args()

    subreddits = ([s.strip() for s in args.subreddit.split(",")]
                  if args.subreddit else DEFAULT_SUBREDDITS)

    mode_label = "日報" if args.mode == "daily" else "週報"
    print(f"\n{'='*50}")
    print(f"  Reddit AI {mode_label}產生器")
    print(f"  監測板塊：{', '.join(f'r/{s}' for s in subreddits)}")
    print(f"{'='*50}\n")

    session = get_reddit_session()

    all_posts = []
    for sub in subreddits:
        print(f"  📡 抓取 r/{sub}...")
        if args.mode == "daily":
            posts = fetch_posts(session, sub, sort="hot", limit=MAX_POSTS_PER_SUB)
        else:
            posts = fetch_posts(session, sub, sort="top", time_filter="week", limit=MAX_POSTS_PER_SUB)

        posts = [calculate_metrics(p) for p in posts]
        all_posts.extend(posts)
        print(f"     ✅ 取得 {len(posts)} 篇")
        time.sleep(2)

    print(f"\n  共抓取 {len(all_posts)} 篇文章")

    top_posts = filter_and_rank(all_posts, mode=args.mode)
    print(f"  篩選後精選 {len(top_posts)} 篇\n")

    if not top_posts:
        print("  ⚠️  沒有文章通過篩選門檻。")
        # 就算沒文章也產出空的 JSON，避免後續流程出錯
        top_posts = []

    os.makedirs(args.output, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")

    # 產出 JSON
    json_path = os.path.join(args.output, f"reddit_{args.mode}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(top_posts, f, ensure_ascii=False, indent=2)
    print(f"  💾 JSON：{json_path}")

    # 同時產出一份 latest.json（固定檔名，方便後續程式讀取）
    latest_path = os.path.join(args.output, "latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": args.mode,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "total_posts": len(top_posts),
            "total_upvotes": sum(p.get("upvotes", 0) for p in top_posts),
            "total_comments": sum(p.get("num_comments", 0) for p in top_posts),
            "subreddits": list(set(p.get("subreddit", "") for p in top_posts)),
            "posts": top_posts,
        }, f, ensure_ascii=False, indent=2)
    print(f"  💾 Latest：{latest_path}")

    print(f"\n  ✅ 資料抓取完成！\n")
    return latest_path


if __name__ == "__main__":
    main()
