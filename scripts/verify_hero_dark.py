# -*- coding: utf-8 -*-
"""一次性验证：用 localStorage 强制深色（不改服务端配置），输出 hero 状态 + 截图"""
import base64, json, subprocess, time, urllib.request
import websocket

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9339
proc = subprocess.Popen([EDGE, "--headless=new", "--disable-gpu",
    f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
    "--window-size=1440,900",
    "--user-data-dir=" + r"D:\Blog(CTF)\scripts\.edge-profile-vfy", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    ws_url = None
    for _ in range(60):
        try:
            targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
            ws_url = next(t for t in targets if t["type"] == "page")["webSocketDebuggerUrl"]
            break
        except Exception:
            time.sleep(0.5)
    ws = websocket.create_connection(ws_url, timeout=30)
    mid = [0]
    def send(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid[0]:
                return msg.get("result", {})

    send("Page.enable")
    # 页面加载前注入：强制深色
    send("Page.addScriptToEvaluateOnNewDocument",
         {"source": "localStorage.setItem('StackColorScheme','dark')"})
    send("Page.navigate", {"url": "http://127.0.0.1:1313/"})
    time.sleep(12)

    expr = """JSON.stringify({
        bodyLen: document.body.innerHTML.length,
        scheme: document.documentElement.getAttribute('data-scheme'),
        hasHero: !!document.querySelector('.hero-banner'),
        title: (document.querySelector('.hero-title')||{}).textContent,
        titleOpacity: document.querySelector('.hero-title') ? getComputedStyle(document.querySelector('.hero-title')).opacity : null,
        titleColor: document.querySelector('.hero-title') ? getComputedStyle(document.querySelector('.hero-title')).color : null,
        subColor: document.querySelector('.hero-subtitle') ? getComputedStyle(document.querySelector('.hero-subtitle')).color : null,
        contentOpacity: document.querySelector('.hero-content') ? getComputedStyle(document.querySelector('.hero-content')).opacity : null,
        bgImg: document.querySelector('.hero-banner') ? getComputedStyle(document.querySelector('.hero-banner')).backgroundImage.slice(0,50) : null
    })"""
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    print("DOM:", res["result"]["value"])

    shot = send("Page.captureScreenshot", {"format": "png"})
    with open("scripts/hero_dark_v3.png", "wb") as f:
        f.write(base64.b64decode(shot["data"]))
    print("saved: scripts/hero_dark_v3.png")
finally:
    proc.terminate()
