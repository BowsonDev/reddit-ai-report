# 🦊 Reddit AI 日報自動化系統

每天自動從 Reddit 的 AI 板塊抓取高互動文章，產生精美網頁報告，推送 Telegram 通知。

## 專案結構

```
reddit-ai-report/
├── .github/workflows/
│   └── daily_report.yml     ← GitHub Actions 排程設定
├── docs/
│   └── index.html           ← 報告網頁（GitHub Pages 會讀這個）
├── output/                   ← 程式產出的 JSON 資料
├── reddit_report.py          ← 主程式：抓 Reddit 資料
├── generate_html.py          ← 把資料變成精美網頁
├── notify_telegram.py        ← 發 Telegram 通知
├── requirements.txt          ← Python 套件清單
└── README.md                 ← 你正在看的這份
```

---

## 設定教學（照著做就好）

### ① 建立 Telegram 機器人（5 分鐘）

1. 打開 Telegram，搜尋 **@BotFather**（有藍勾勾的那個）
2. 發送 `/newbot`
3. 它會問你機器人的名字，輸入：`Reddit AI 日報`
4. 它會問你機器人的帳號，輸入：`redditai_你的名字_bot`（要以 `_bot` 結尾）
5. 建好後 BotFather 會給你一串金鑰，長這樣：
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   **這就是你的 TELEGRAM_BOT_TOKEN，先複製存起來**

6. 接下來要拿你的 Chat ID。搜尋 **@userinfobot** 並發送任意訊息
7. 它會回覆你的資訊，裡面有 `Id: 123456789`
   **這就是你的 TELEGRAM_CHAT_ID，也存起來**

8. 最後，去你剛建的機器人的對話框，發送 `/start`
   （這一步很重要，不做的話機器人沒辦法發訊息給你）

### ② 把專案推到 GitHub

打開終端機（Terminal），一行一行輸入：

```bash
# 如果你還沒有這個專案的資料夾，先下載
# 如果已經有了，跳到 cd 那一行

cd ~/reddit-ai-report

# 初始化 Git
git init
git add .
git commit -m "🚀 初始化 Reddit AI 日報系統"

# 在 GitHub 上建一個新的 repository
# 去 https://github.com/new
# Repository name 填：reddit-ai-report
# 選 Public（才能用免費的 GitHub Pages）
# 不要勾任何初始化選項
# 按 Create repository

# 然後把程式碼推上去（把下面的 YOUR_USERNAME 換成你的 GitHub 帳號）
git remote add origin https://github.com/YOUR_USERNAME/reddit-ai-report.git
git branch -M main
git push -u origin main
```

### ③ 設定 GitHub Secrets（存放金鑰）

1. 去你的 GitHub 專案頁面
2. 點 **Settings**（設定）→ 左邊選 **Secrets and variables** → **Actions**
3. 點 **New repository secret**，依序加入以下三個：

| Name（名稱） | Value（值） | 說明 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAHxxxxx...` | 步驟 ① 拿到的機器人金鑰 |
| `TELEGRAM_CHAT_ID` | `123456789` | 步驟 ① 拿到的聊天 ID |
| `REPORT_URL` | `https://YOUR_USERNAME.github.io/reddit-ai-report/` | 你的報告網址（把 YOUR_USERNAME 換成你的 GitHub 帳號） |

（選填，有的話速率限制比較寬：）

| Name | Value | 說明 |
|---|---|---|
| `REDDIT_CLIENT_ID` | 你的 Reddit App ID | 去 reddit.com/prefs/apps 申請 |
| `REDDIT_CLIENT_SECRET` | 你的 Reddit App Secret | 同上 |

### ④ 啟用 GitHub Pages

1. 在你的 GitHub 專案頁面，點 **Settings**
2. 左邊選 **Pages**
3. Source 選 **Deploy from a branch**
4. Branch 選 **main**，資料夾選 **/docs**
5. 按 **Save**

等幾分鐘後，你就可以在 `https://YOUR_USERNAME.github.io/reddit-ai-report/` 看到網頁了。

### ⑤ 測試（手動觸發一次）

1. 去你的 GitHub 專案頁面，點 **Actions** 頁籤
2. 左邊選 **Reddit AI Daily Report**
3. 右邊點 **Run workflow** → **Run workflow**
4. 等 2-3 分鐘，看看是不是全部綠勾勾 ✅
5. 檢查你的 Telegram 有沒有收到通知
6. 打開你的 GitHub Pages 網址看看報告

全部通過的話，之後每天早上 8 點（台灣時間）就會自動跑了！

---

## 在自己電腦上跑（本地測試）

```bash
# 安裝套件
pip3 install -r requirements.txt

# 跑日報
python3 reddit_report.py --mode daily

# 產生 HTML
python3 generate_html.py ./output/latest.json ./docs/index.html

# 測試 Telegram 通知（需要先設定環境變數）
export TELEGRAM_BOT_TOKEN="你的金鑰"
export TELEGRAM_CHAT_ID="你的ID"
python3 notify_telegram.py ./output/latest.json
```

---

## 客製化

### 改監測的板塊
打開 `reddit_report.py`，找到 `DEFAULT_SUBREDDITS`，加或刪板塊名稱。

### 改篩選門檻
同一個檔案裡的 `DAILY_MIN_UPVOTES`、`DAILY_MIN_COMMENTS` 等數字。

### 改排程時間
打開 `.github/workflows/daily_report.yml`，找到 `cron: '0 0 * * *'`。
格式是 `分 時 日 月 星期`，用 UTC 時間。台灣時間 -8 就是 UTC。
例如台灣下午 6 點 = UTC 10 點 = `0 10 * * *`

### 加週報
在 `daily_report.yml` 的 `schedule` 裡加一行：
```yaml
schedule:
  - cron: '0 0 * * *'      # 日報：每天 08:00 台灣
  - cron: '0 0 * * 0'      # 週報：每週日 08:00 台灣
```
然後把步驟四的 `--mode daily` 改成根據星期判斷。

---

## 開發路線圖

- [x] Reddit 資料抓取
- [x] HTML 精美報告
- [x] GitHub Actions 自動排程
- [x] GitHub Pages 網站
- [x] Telegram 通知
- [ ] 接 Claude API 自動分析（中文標題改寫、工具提取、爆紅原因）
- [ ] 帳號結構分析功能
- [ ] 模仿機器人
- [ ] Threads / X / IG 監測
