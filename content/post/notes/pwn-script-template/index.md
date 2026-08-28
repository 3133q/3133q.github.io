---
title: "脚本模板"
description: "PWN 入门常用的 pwntools 完整脚本模板，涵盖本地与远程连接及基础交互流程。"
date: 2026-08-13T20:46:54+08:00
slug: "pwn-script-template"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - PWN
    - 脚本工具
    - pwntools
    - ELF
---

## 完整脚本模板

```python
from pwn import *
context.arch="amd64" # amd64(64位) i386(32位)
context.os="linux"
context.log_level="debug" #开启 debug 模式
elf=ELF("./lottery_debug")
libc=ELF("./libc.so.6") #如果有
def conn():
    if args.REMOTE:
       host=""
       port=
       return remote(host,port)
    else:
       return process("")
def exploit(io):
    io.recvuntil(b"")
    line=io.recvline().decode().split()
    payload=
    io.sendline(payload)
    io.interactive()
if __name__=='__main__':
    io=conn()
    exploit(io)
```
