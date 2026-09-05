#!/usr/bin/env python3
"""鄉民首贏 - 零相依預約網站伺服器
Run: python server.py
Env:
  PORT=8080
  HOST=0.0.0.0
  RESERVATION_WEBHOOK_URL=https://...   # optional: forward each lead to Make/Zapier/Apps Script/CRM
  LINE_CHANNEL_ACCESS_TOKEN=...          # optional: LINE Messaging API long-lived token
  LINE_USER_ID=U...                      # optional: recipient's LINE user ID
"""
from __future__ import annotations
import csv, json, os, re, secrets, sqlite3, threading
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB = DATA / "reservations.sqlite3"
CSV = DATA / "reservations.csv"
LOCK = threading.Lock()
FIELDS = ["reservation_id","created_at","name","phone","unit","preferred_date","preferred_time","purpose","note","source","page","ip","user_agent"]

def init_db():
    DATA.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS reservations (
            reservation_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, name TEXT NOT NULL,
            phone TEXT NOT NULL, unit TEXT NOT NULL, preferred_date TEXT, preferred_time TEXT,
            purpose TEXT, note TEXT, source TEXT, page TEXT, ip TEXT, user_agent TEXT
        )""")
    if not CSV.exists():
        with CSV.open("w", newline="", encoding="utf-8-sig") as f: csv.DictWriter(f, fieldnames=FIELDS).writeheader()

def clean(v, n=500): return str(v or "").strip()[:n]
def valid_phone(p): return bool(re.fullmatch(r"[0-9+()\-\s]{8,20}", p))
def make_id(): return "SY-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2).upper()

def forward_webhook(row):
    url = os.environ.get("RESERVATION_WEBHOOK_URL", "").strip()
    if not url: return False
    payload = dict(row)
    payload["webhook_secret"] = os.environ.get("RESERVATION_WEBHOOK_SECRET", "")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type":"application/json"}, method="POST")
    result = json.loads(urlopen(req, timeout=12).read(4096).decode("utf-8"))
    if result.get("ok") is not True: raise RuntimeError(result.get("error") or "Google Sheet 寫入失敗")
    return True

def notify_line(row):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    user_id = os.environ.get("LINE_USER_ID", "").strip()
    if not token or not user_id: return False
    appointment = " ".join(filter(None, [row.get("preferred_date"), row.get("preferred_time")])) or "未填寫"
    message = "\n".join([
        "新預約通知",
        f"姓名：{row['name']}",
        f"電話：{row['phone']}",
        f"預計預約時間：{appointment}",
    ])
    body = json.dumps({
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }, ensure_ascii=False).encode("utf-8")
    req = Request(
        "https://api.line.me/v2/bot/message/push",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=12) as response:
        if response.status != 200: raise RuntimeError(f"LINE API 回傳 HTTP {response.status}")
    return True

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT), **kwargs)
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()
    def do_GET(self):
        if self.path == "/api/health": return self.json_response(200,{"ok":True})
        return super().do_GET()
    def do_POST(self):
        if self.path != "/api/reservations": return self.json_response(404,{"error":"Not found"})
        try:
            length = int(self.headers.get("Content-Length","0"))
            if length <= 0 or length > 20000: return self.json_response(400,{"error":"資料格式不正確"})
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception: return self.json_response(400,{"error":"資料格式不正確"})
        name, phone, unit = clean(data.get("name"),40), clean(data.get("phone"),20), clean(data.get("unit"),80)
        if not name: return self.json_response(400,{"error":"請填寫姓名"})
        if not valid_phone(phone): return self.json_response(400,{"error":"請填寫正確手機號碼"})
        if not unit: return self.json_response(400,{"error":"請選擇想看的房型"})
        if data.get("consent") is not True: return self.json_response(400,{"error":"請勾選個資聯繫同意"})
        rid = make_id(); now = datetime.now(ZoneInfo("Asia/Taipei")).isoformat(timespec="seconds")
        row = {
            "reservation_id":rid,"created_at":now,"name":name,"phone":phone,"unit":unit,
            "preferred_date":clean(data.get("preferred_date"),20),"preferred_time":clean(data.get("preferred_time"),40),
            "purpose":clean(data.get("purpose"),40),"note":clean(data.get("note"),500),"source":clean(data.get("source"),100),
            "page":clean(data.get("page"),500),"ip":clean(self.client_address[0],80),"user_agent":clean(self.headers.get("User-Agent"),300)
        }
        try:
            forwarded = forward_webhook(row)
        except Exception as exc:
            print("[webhook error]", exc)
            return self.json_response(503,{"error":"預約資料暫時無法安全保存，請稍後再試或直接來電"})
        with LOCK:
            with sqlite3.connect(DB) as con:
                con.execute("INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [row[k] for k in FIELDS])
            with CSV.open("a", newline="", encoding="utf-8-sig") as f: csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
        if not forwarded: print("[storage warning] RESERVATION_WEBHOOK_URL is not configured; using ephemeral local storage only")
        try:
            if not notify_line(row): print("[notification warning] LINE notification is not configured")
        except Exception as exc:
            # The reservation is already safely stored, so a transient LINE error must not lose the lead.
            print("[LINE notification error]", exc)
        print(f"[NEW LEAD] {rid} {name} {phone} {unit}")
        return self.json_response(201,{"ok":True,"reservation_id":rid})
    def json_response(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)

if __name__ == "__main__":
    os.chdir(ROOT); init_db()
    host, port = os.environ.get("HOST","0.0.0.0"), int(os.environ.get("PORT","8080"))
    print(f"鄉民首贏網站：http://127.0.0.1:{port}")
    print(f"預約資料：{CSV}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()
