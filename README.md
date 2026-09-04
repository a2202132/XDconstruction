# 鄉民首贏一站式銷售網站

## 直接啟動
Windows 電腦已安裝 Python 的話：

```bat
python server.py
```

瀏覽器開啟：`http://127.0.0.1:8080`

## 預約單會存在哪裡？
每一筆預約會同時寫入：
- `data/reservations.csv`（可直接用 Excel 開）
- `data/reservations.sqlite3`（正式資料庫）

## 上正式網站
這個專案沒有外部 Python 套件，可直接部署到任何能長期執行 Python 的主機/VPS。
請使用 HTTPS，並確保 `data/` 目錄有持久化磁碟與備份。

### 即時通知業務 / 串 Google Sheet / LINE CRM
設定環境變數 `RESERVATION_WEBHOOK_URL` 後，每一筆新預約都會以 JSON POST 到你的 webhook。
可接：Google Apps Script、Make、Zapier、n8n、公司 CRM 等。

Windows PowerShell 範例：
```powershell
$env:RESERVATION_WEBHOOK_URL="https://你的-webhook-url"
python server.py
```

## 注意
本網站的「送出預約單」屬賞屋／購屋意向，不等同正式不動產買賣契約或付款。若要做到線上刷卡訂金、電子簽約，需要再串金流與電子簽章，並依實際銷售流程及法務規範設定。


版本：PHONE_FINAL_20260904b
聯絡電話：0916882564 王小姐


版本：EXPERIMENTAL_SCHOOL_FEATURE_20260904
新增：新竹實驗附小大型專區＋親子天下報導連結


2026-09-05 更新：第一頁 Hero 背景改為較乾淨的建築外觀圖（hero-clean-v3.png），保留最新電話 0916882564 王小姐。
