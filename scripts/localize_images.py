# -*- coding: utf-8 -*-
"""把文章里的远程图片下载到本地 bundle，并改写 Markdown 引用"""
import os
import re
import time
import urllib.request
import urllib.error

ROOT = "content/post"
IMG_RE = re.compile(r'!\[([^\]]*)\]\((https?://[^)\s]+)\)')

# jsd.onmicrosoft.cn / gcore.jsdelivr.net 都是 jsdelivr 镜像，统一到可用的主站
HOST_REWRITE = {
    "jsd.onmicrosoft.cn": "cdn.jsdelivr.net",
    "gcore.jsdelivr.net": "cdn.jsdelivr.net",
}

# 各图床的防盗链 Referer（CSDN 必须带自家 Referer）
def headers_for(host):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if "csdnimg.cn" in host:
        h["Referer"] = "https://blog.csdn.net/"
    elif "cnblogs.com" in host:
        h["Referer"] = "https://www.cnblogs.com/"
    return h

ok, fail = 0, []

for dirpath, dirnames, filenames in os.walk(ROOT):
    if "index.md" not in filenames:
        continue
    md_path = os.path.join(dirpath, "index.md")
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    urls = IMG_RE.findall(content)
    if not urls:
        continue

    changed = False
    for alt, url in urls:
        # 生成本地文件名
        fname = url.split("?")[0].rstrip("/").split("/")[-1]
        if "." not in fname:
            fname += ".png"
        local_path = os.path.join(dirpath, fname)

        if not os.path.exists(local_path):
            # 下载（必要时改写域名）
            host = re.search(r'https?://([^/]+)', url).group(1)
            candidates = [url]
            if host in HOST_REWRITE:
                candidates.insert(0, url.replace(host, HOST_REWRITE[host], 1))

            data = None
            for cand in candidates:
                cand_host = re.search(r'https?://([^/]+)', cand).group(1)
                try:
                    req = urllib.request.Request(cand, headers=headers_for(cand_host))
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        data = resp.read()
                    break
                except Exception:
                    continue
            if data is None or len(data) < 500:
                fail.append((md_path, url))
                continue
            with open(local_path, "wb") as f:
                f.write(data)
            ok += 1
            time.sleep(0.2)

        # 改写引用为本地文件
        content = content.replace(f"]({url})", f"]({fname})")
        changed = True

    if changed:
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"[updated] {md_path}")

print(f"\n下载成功 {ok} 张，失败 {len(fail)} 张")
for p, u in fail:
    print("  FAIL:", p, "->", u)
