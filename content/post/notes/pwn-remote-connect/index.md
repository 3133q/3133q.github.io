---
title: "连接远端"
description: "记录 PWN 远程连接时通过端口转发与防火墙规则打通本地调试环境的方法。"
date: 2026-08-13T20:46:19+08:00
slug: "pwn-remote-connect"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - PWN
    - 端口转发
    - 脚本工具
---

**1. 添加端口转发规则：**

```python
netsh interface portproxy add v4tov4 listenport=54854 listenaddress=0.0.0.0 connectport=54854 connectaddress=127.0.0.1
```

**2. 添加入站防火墙规则（防止被 Windows 防火墙拦截）：**

```python
netsh advfirewall firewall add rule name="CTF-WSRX-54854" dir=in action=allow protocol=TCP localport=54854
```

pwninit 修复文件

---

*以上内容如有理解不到位或表述不当的地方，还请各位师傅不吝赐教。*
