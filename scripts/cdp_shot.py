# -*- coding: utf-8 -*-
"""通过 CDP 截取页面真实渲染结果（真实时间等待，非虚拟时间）"""
import base64
import json
import subprocess
import sys
import time
import urllib.request

import websocket

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:1313/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "scripts/cdp_shot.png"
WAIT = float(sys.argv[3]) if len(sys.argv) > 3 else 6
CLICK = len(sys.argv) > 4 and sys.argv[4] == "click"

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9333

proc = subprocess.Popen([
    EDGE, "--headless=new", "--disable-gpu",
    f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*",
    "--window-size=1440,900",
    "--user-data-dir=" + r"D:\Blog(CTF)\scripts\.edge-profile",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    ws_url = None
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as r:
                targets = json.load(r)
            page = next(t for t in targets if t["type"] == "page")
            ws_url = page["webSocketDebuggerUrl"]
            break
        except Exception:
            time.sleep(0.3)
    if not ws_url:
        print("无法连接 CDP")
        sys.exit(1)

    ws = websocket.create_connection(ws_url, timeout=30)
    mid = 0

    def send(method, params=None):
        global mid
        mid += 1
        ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid:
                return msg.get("result", {})

    send("Page.enable")
    send("Page.navigate", {"url": URL})
    time.sleep(WAIT)

    if CLICK:
        # 模拟一次鼠标点击，验证点击爆裂效果
        send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 700, "y": 450, "button": "left", "clickCount": 1})
        send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 700, "y": 450, "button": "left", "clickCount": 1})
        time.sleep(0.35)

    shot = send("Page.captureScreenshot", {"format": "png"})
    with open(OUT, "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    print("saved:", OUT)
finally:
    proc.terminate()
