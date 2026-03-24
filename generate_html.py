"""
HTML 報告產生器
===============
讀取 reddit_report.py 產出的 latest.json，
產生精美的 HTML 日報頁面，放到 docs/ 給 GitHub Pages 用。
"""

import json
import os
import sys
from datetime import datetime


def load_data(json_path):
    """讀取 JSON 資料。"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_post_card(post, rank):
    """產生單篇文章的 HTML 卡片。"""
    ratio = post.get("engagement_ratio", 0)
    ratio_note = " 🔥 高討論度" if ratio < 4 else ""
    hours = post.get("hours_ago", "?")
    selftext = post.get("selftext", "").strip()
    preview = selftext[:300].replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ") if selftext else "（連結型貼文，無內文）"

    rank_label = "#1 本日最高互動" if rank == 1 else f"#{rank}"

    return f"""
    <div class="post-card">
      <div class="post-rank">{rank_label}</div>
      <div class="post-meta">
        <span class="post-subreddit">r/{post.get("subreddit", "?")}</span>
        <span class="post-time">約 {hours} 小時前發文</span>
      </div>
      <div class="post-title-en">{post.get("title", "無標題")}</div>

      <div class="metrics">
        <div class="metric">
          <span class="icon">▲</span>
          <span class="val">{post.get("upvotes", 0):,}</span>
          <span class="mlabel">按讚</span>
        </div>
        <div class="metric">
          <span class="icon">💬</span>
          <span class="val">{post.get("num_comments", 0):,}</span>
          <span class="mlabel">留言</span>
        </div>
        <div class="metric">
          <span class="icon">📊</span>
          <span class="val">{ratio}:1{ratio_note}</span>
          <span class="mlabel">讚留比</span>
        </div>
        <div class="metric">
          <span class="icon">🎯</span>
          <span class="val">{post.get("heat_score", 0):,.0f}</span>
          <span class="mlabel">熱度分數</span>
        </div>
      </div>

      <div class="section-label">📝 內文預覽</div>
      <p class="post-summary">{preview}</p>

      <a href="{post.get("url", "#")}" target="_blank" class="post-link">🔗 查看原文 →</a>
    </div>
    """


def generate_html(data, output_path):
    """產生完整的 HTML 報告頁面。"""
    posts = data.get("posts", [])
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    mode = data.get("mode", "daily")
    mode_label = "日報" if mode == "daily" else "週報"
    total_up = data.get("total_upvotes", 0)
    total_com = data.get("total_comments", 0)
    subs = data.get("subreddits", [])

    # 產生所有文章卡片
    cards_html = ""
    for i, post in enumerate(posts, 1):
        cards_html += generate_post_card(post, i)

    # 如果沒有文章
    if not posts:
        cards_html = """
        <div class="post-card" style="text-align: center; padding: 60px 32px;">
          <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
          <div style="font-size: 18px; color: var(--text-dim);">
            今天沒有文章通過篩選門檻<br>
            可能是休息日，或者門檻設太高了
          </div>
        </div>
        """

    subreddit_tags = "".join(f'<span>r/{s}</span>' for s in subs)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reddit AI {mode_label} — {date_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface-2: #1a1a26;
    --border: #2a2a3a;
    --text: #e8e8f0;
    --text-dim: #8888a0;
    --accent: #ff4500;
    --accent-glow: rgba(255, 69, 0, 0.15);
    --green: #00d68f;
    --blue: #4a9eff;
    --purple: #b44aff;
    --yellow: #ffb800;
    --font: 'Noto Sans TC', sans-serif;
    --mono: 'JetBrains Mono', monospace;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.7;
    min-height: 100vh;
  }}
  .noise {{
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none; z-index: 0;
  }}
  .container {{
    max-width: 860px; margin: 0 auto; padding: 40px 24px 80px;
    position: relative; z-index: 1;
  }}
  .header {{
    text-align: center; margin-bottom: 56px; padding-bottom: 40px;
    border-bottom: 1px solid var(--border);
  }}
  .header-tag {{
    display: inline-block; font-family: var(--mono); font-size: 11px;
    letter-spacing: 3px; text-transform: uppercase; color: var(--accent);
    background: var(--accent-glow); padding: 6px 16px; border-radius: 4px;
    margin-bottom: 20px;
  }}
  .header h1 {{
    font-size: 32px; font-weight: 900; line-height: 1.3; margin-bottom: 12px;
    background: linear-gradient(135deg, #fff 0%, #ccc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .header .date {{
    font-family: var(--mono); font-size: 13px; color: var(--text-dim);
  }}
  .header .subreddits {{
    display: flex; justify-content: center; gap: 10px; margin-top: 20px; flex-wrap: wrap;
  }}
  .header .subreddits span {{
    font-family: var(--mono); font-size: 12px; color: var(--blue);
    background: rgba(74, 158, 255, 0.08); padding: 4px 12px; border-radius: 20px;
    border: 1px solid rgba(74, 158, 255, 0.15);
  }}
  .summary-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 48px;
  }}
  .stat-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px 16px; text-align: center;
  }}
  .stat-card .num {{
    font-family: var(--mono); font-size: 28px; font-weight: 600; color: var(--accent);
  }}
  .stat-card .label {{ font-size: 12px; color: var(--text-dim); margin-top: 4px; }}
  .post-card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 32px; margin-bottom: 24px; position: relative; transition: border-color 0.3s;
  }}
  .post-card:hover {{ border-color: rgba(255, 69, 0, 0.3); }}
  .post-rank {{
    position: absolute; top: -14px; left: 28px; font-family: var(--mono);
    font-size: 12px; font-weight: 600; color: var(--bg); background: var(--accent);
    padding: 3px 14px; border-radius: 20px;
  }}
  .post-meta {{
    display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
  }}
  .post-subreddit {{
    font-family: var(--mono); font-size: 12px; color: var(--blue);
    background: rgba(74, 158, 255, 0.08); padding: 3px 10px; border-radius: 4px;
  }}
  .post-time {{ font-family: var(--mono); font-size: 11px; color: var(--text-dim); }}
  .post-title-en {{
    font-size: 18px; font-weight: 700; line-height: 1.5; margin-bottom: 16px; color: #fff;
  }}
  .metrics {{
    display: flex; gap: 20px; margin-bottom: 20px; padding: 14px 18px;
    background: var(--surface-2); border-radius: 8px; flex-wrap: wrap;
  }}
  .metric {{ display: flex; align-items: center; gap: 6px; }}
  .metric .icon {{ font-size: 14px; }}
  .metric .val {{ font-family: var(--mono); font-size: 14px; font-weight: 600; color: var(--green); }}
  .metric .mlabel {{ font-size: 12px; color: var(--text-dim); }}
  .section-label {{
    font-family: var(--mono); font-size: 11px; letter-spacing: 2px;
    text-transform: uppercase; color: var(--purple); margin-bottom: 8px; margin-top: 18px;
  }}
  .post-summary {{
    font-size: 14px; color: var(--text); line-height: 1.8; margin-bottom: 4px;
  }}
  .post-link {{
    display: inline-block; margin-top: 16px; font-family: var(--mono); font-size: 13px;
    color: var(--blue); text-decoration: none; padding: 8px 16px;
    border: 1px solid rgba(74, 158, 255, 0.3); border-radius: 6px;
    transition: all 0.2s;
  }}
  .post-link:hover {{ background: rgba(74, 158, 255, 0.1); border-color: var(--blue); }}
  .footer {{
    margin-top: 56px; padding-top: 32px; border-top: 1px solid var(--border);
    text-align: center; font-size: 12px; color: var(--text-dim); font-family: var(--mono);
  }}
  .updated-badge {{
    display: inline-block; margin-top: 12px; padding: 4px 12px; border-radius: 20px;
    background: rgba(0, 214, 143, 0.1); color: var(--green); font-size: 11px;
    border: 1px solid rgba(0, 214, 143, 0.2);
  }}
  @media (max-width: 600px) {{
    .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .header h1 {{ font-size: 24px; }}
    .post-card {{ padding: 24px 18px; }}
  }}
</style>
</head>
<body>
<div class="noise"></div>
<div class="container">

  <div class="header">
    <div class="header-tag">Reddit AI Intelligence Report</div>
    <h1>Reddit AI 板塊{mode_label}</h1>
    <div class="date">{date_str}｜{'過去 24 小時熱門文章' if mode == 'daily' else '過去 7 天最高互動文章'}</div>
    <div class="subreddits">{subreddit_tags}</div>
  </div>

  <div class="summary-grid">
    <div class="stat-card">
      <div class="num">{len(posts)}</div>
      <div class="label">精選文章</div>
    </div>
    <div class="stat-card">
      <div class="num">{total_up:,}</div>
      <div class="label">總按讚數</div>
    </div>
    <div class="stat-card">
      <div class="num">{total_com:,}</div>
      <div class="label">總留言數</div>
    </div>
    <div class="stat-card">
      <div class="num">{len(subs)}</div>
      <div class="label">涵蓋板塊</div>
    </div>
  </div>

  {cards_html}

  <div class="footer">
    <p>由 🦊 思維狐 社群情報系統自動產出</p>
    <p>篩選規則：按讚 &gt; 板塊門檻 且 留言 &gt; {'10' if mode == 'daily' else '30'}</p>
    <div class="updated-badge">最後更新：{datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</div>
  </div>

</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  🌐 HTML 報告：{output_path}")


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "./output/latest.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "./docs/index.html"

    if not os.path.exists(json_path):
        print(f"  ❌ 找不到 {json_path}，請先跑 reddit_report.py")
        sys.exit(1)

    data = load_data(json_path)
    generate_html(data, output_path)
    print("  ✅ HTML 報告產生完成！")


if __name__ == "__main__":
    main()
