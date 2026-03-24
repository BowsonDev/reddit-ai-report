"""
Telegram 通知機器人
====================
讀取 latest.json，發送日報摘要通知到你的 Telegram。

需要兩個環境變數：
  TELEGRAM_BOT_TOKEN  ← 從 @BotFather 拿到的機器人金鑰
  TELEGRAM_CHAT_ID    ← 你的聊天 ID（從 @userinfobot 拿）
"""

import json
import os
import sys
import requests


def send_telegram(token, chat_id, message):
    """發送 Telegram 訊息。"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        print("  ✅ Telegram 通知已發送！")
    else:
        print(f"  ❌ 發送失敗：{res.status_code} {res.text}")


def format_message(data, report_url=None):
    """把日報資料格式化成 Telegram 訊息。"""
    mode = data.get("mode", "daily")
    mode_emoji = "📰" if mode == "daily" else "📊"
    mode_label = "日報" if mode == "daily" else "週報"
    date_str = data.get("date", "???")
    total_posts = data.get("total_posts", 0)
    total_up = data.get("total_upvotes", 0)
    total_com = data.get("total_comments", 0)
    posts = data.get("posts", [])

    lines = []
    lines.append(f"🦊 <b>Reddit AI {mode_label}已更新</b>")
    lines.append(f"📅 {date_str}")
    lines.append(f"📊 精選 {total_posts} 篇 ｜ 👍 {total_up:,} ｜ 💬 {total_com:,}")
    lines.append("")

    # 前三名文章摘要
    for i, post in enumerate(posts[:3], 1):
        medal = ["🥇", "🥈", "🥉"][i - 1]
        title = post.get("title", "無標題")
        if len(title) > 60:
            title = title[:57] + "..."
        up = post.get("upvotes", 0)
        com = post.get("num_comments", 0)
        sub = post.get("subreddit", "?")
        lines.append(f"{medal} <b>{title}</b>")
        lines.append(f"   r/{sub} ｜ 👍{up:,} 💬{com:,}")
        lines.append("")

    # 報告連結
    if report_url:
        lines.append(f"🔗 <a href=\"{report_url}\">查看完整報告</a>")
    else:
        lines.append("🔗 報告已更新至 GitHub Pages")

    return "\n".join(lines)


def main():
    # 讀取環境變數
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    report_url = os.environ.get("REPORT_URL", "")

    if not token or not chat_id:
        print("  ❌ 缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 環境變數")
        print("  請參考 README 的設定教學。")
        sys.exit(1)

    # 讀取資料
    json_path = sys.argv[1] if len(sys.argv) > 1 else "./output/latest.json"
    if not os.path.exists(json_path):
        print(f"  ❌ 找不到 {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 格式化並發送
    message = format_message(data, report_url)
    send_telegram(token, chat_id, message)


if __name__ == "__main__":
    main()
