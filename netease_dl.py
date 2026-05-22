#!/usr/bin/env python3
"""NetEase Cloud Music Downloader."""

import json
import os
import re
import subprocess
import sys
import urllib.parse

from _ncm import NCM

BASE = os.path.dirname(os.path.abspath(__file__))
SESSION = os.path.join(BASE, "session.json")
UA = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36"


def curl(url, data=None, cookie=""):
    cmd = [
        "curl",
        "-s",
        "-4",
        "--connect-timeout",
        "5",
        "--max-time",
        "15",
        "-H",
        f"User-Agent: {UA}",
        "-H",
        "Referer: https://music.163.com/",
    ]
    if cookie:
        cmd += ["-H", f"Cookie: {cookie}"]
    if data:
        cmd += ["-d", data]
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout


ncm = NCM()

# ── Session ───────────────────────────────────────────────────────────

if os.path.exists(SESSION):
    cd = json.load(open(SESSION))
    if cd.get("MUSIC_U"):
        ncm.set_cookie({"MUSIC_U": cd["MUSIC_U"]})
        print(f"Session loaded (phone={cd.get('phone', '?')})")
    else:
        cd = None
else:
    cd = None

if not cd:
    print("=" * 50 + "\n  Login via SMS\n" + "=" * 50)
    phone = input("Phone (+86): ").strip()
    if not phone:
        sys.exit()
    print(f"Sending SMS to +86 {phone}...")
    resp = curl(
        "https://music.163.com/api/sms/captcha/sent", f"cellphone={phone}&ctcode=86"
    )
    try:
        rj = json.loads(resp)
        if rj.get("code") != 200:
            msg = rj.get("message", "Unknown error")
            print(f"SMS failed: {msg}")
            sys.exit(1)
    except json.JSONDecodeError:
        print(f"SMS failed (invalid response): {resp[:200]}")
        sys.exit(1)
    code = input("SMS code: ").strip()
    if not code:
        sys.exit()

    r = ncm.login_cellphone(phone=phone, captcha=code)
    if r.status != 200 or not r.body or r.body.get("code") != 200:
        msg = (r.body or {}).get("message", "") or (r.body or {}).get("msg", "")
        print(f"Login failed: {msg or f'status={r.status}'}")
        sys.exit(1)

    b = r.body
    token = b.get("token", "")
    ncm.set_cookie({"MUSIC_U": token})
    csrf = ""
    for p in b.get("cookie", "").split(";;"):
        for kv in p.split(";"):
            kv = kv.strip()
            if kv.startswith("__csrf="):
                csrf = kv.split("=", 1)[1]
    with open(SESSION, "w") as f:
        json.dump({"MUSIC_U": token, "__csrf": csrf, "phone": phone}, f)
    print(f"Login OK (UID={b.get('account', {}).get('id', '?')})")

# ── Search ────────────────────────────────────────────────────────────

kw = input("Keyword: ").strip()
if not kw:
    sys.exit()

data = urllib.parse.urlencode(
    {"s": kw, "type": "1", "limit": "10", "total": "true", "offset": "0"}
)
r = curl("http://music.163.com/api/search/get", data)
songs = json.loads(r).get("result", {}).get("songs", [])
if not songs:
    print("No results.")
    sys.exit()

# Check actual availability (one batch API call)
ids = ",".join(str(s["id"]) for s in songs)
r = ncm.song_url_v1(id=ids, level="standard")
available = set()
if r.status == 200 and r.body:
    for d in r.body.get("data", []):
        if d.get("url"):
            available.add(d["id"])

for i, s in enumerate(songs):
    ok = s["id"] in available
    arts = "/".join(a["name"] for a in s.get("ar", []))
    print(f"  [{i}] {'YES' if ok else ' NO'}  {s['name'][:50]} — {arts[:40]}")

while True:
    c = input(f"\nPick [0-{len(songs) - 1}]: ").strip()
    try:
        if 0 <= int(c) < len(songs):
            chosen = songs[int(c)]
            break
    except ValueError:
        pass

arts = "/".join(a["name"] for a in chosen.get("ar", []))
print(f"\n→ {chosen['name']} — {arts}")

# ── Get URL ───────────────────────────────────────────────────────────

for lv in ["exhigh", "higher", "standard"]:
    r = ncm.song_url_v1(id=str(chosen["id"]), level=lv)
    if r.status != 200 or not r.body:
        continue
    d = r.body.get("data", [])
    if d and d[0].get("url"):
        sd = d[0]
        print(
            f"  {sd.get('type')} @ {sd.get('br')}bps, {sd.get('size', 0) / 1024 / 1024:.1f}MB"
        )
        break
else:
    print("No playable URL (VIP-only or geo-locked).")
    sys.exit()  # noqa: E702

# ── Download ──────────────────────────────────────────────────────────

ext = sd.get("type", "mp3")
name = re.sub(r'[<>:"/\\|?*]', "_", f"{chosen['name']} - {arts}").strip()
path = os.path.join(os.getcwd(), f"{name}.{ext}")
print(f"Downloading → {path}")
subprocess.run(
    [
        "curl",
        "-s",
        "-4",
        "-L",
        "--connect-timeout",
        "10",
        "--max-time",
        "300",
        "-H",
        "User-Agent: Mozilla/5.0",
        "-o",
        path,
        sd["url"],
    ],
    check=True,
    timeout=310,
)
print(f"Done: {os.path.getsize(path) / 1024 / 1024:.1f} MB")

subprocess.run(
    [
        "ffprobe",
        "-hide_banner",
        "-show_entries",
        "format=duration,bit_rate",
        "-of",
        "default=noprint_wrappers=1",
        path,
    ],
    timeout=10,
)
print(f"Ready: {path}")
