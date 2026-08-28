---
title: "Linux二进制程序保护机制"
description: "介绍 Linux 二进制程序的常见保护机制，包括 ASLR、NX、PIE、Canary 和 RELRO 的原理与作用。"
date: 2026-07-21T08:41:03+08:00
slug: "linux-binary-protection"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - PWN
    - 保护机制
    - ELF
---

## 1.ASLR

ASLR是操作系统的功能选项，作用于executable（ELF）装入内存运行时，因而只能随机化stack，heap，libraries的基址

### 作用

未开启：无作用
半开启：随机化 stack 和 libarys
全开启：随机化 stack、libarys 和 heap

### 开启关闭方式

```python
  ## 未开启：地址随机化关闭
  echo 0 > /proc/sys/kernel/randomize_va_space
  ## 半开启：随机化 stack 、librarys
  echo 1 > /proc/sys/kernel/randomize_va_space
  ## 全开启：随机化 stack 、librarys 、heap（默认选项）
  echo 2 > /proc/sys/kernel/randomize_va_space
```

## 2.NX

No-Execute（不可执行），NX的原理是将数据所在内存页标识为不可执行，当程序执行流被劫持到栈上时，程序会尝试在数据页面上执行指令，因为数据页被标记为不可知性，此时CPU就会抛出异常，而非去执行栈上数据

在程序的某个位置有控制程序是否可以执行的标志位（若为 6 不可执行 、7 不可执行），也可以用 execstack 工具查询和设置该标志位，该标志位在 51e5 7464 后边。

### 作用

**NX disabled：** 栈可以执行，栈上的数据也可以被当作代码执行。
**NX enabled：** 栈不可执行，栈上的数据程序只认为是数据，如果去执行的话会发生错误。即栈上的数据不可以被当作代码执行。

## 3.PIE

PIE（Position Independent Executables）是编译器功能选项，作用于编译过程，其随机化了ELF装载内存的基址（代码段，PLT，GOT，data等共同的基地址），效果为用objdump，IDA反汇编之后的地址是用偏移表示的而不是用绝对地址

### 作用

**No PIE：** 无作用
**PIE enabled：** 代码段、plt、got、data 等共同的基址会随机化。在编译后的程序中，只保留指令、数据等的偏移，而不是绝对地址的形式。

## 4.Canary

金丝雀保护，用来防护栈溢出的保护机制，原理是在函数入口处，先从fs/gs寄存器中取出一个4(eax)/8(rax)字节的cookie信息存到栈上，当函数结束返回的时候会验证cookie信息是否合法（与开始存的是否一致），如果不合法就停止程序运行，真正的cookie信息也会存到程序的某个位置。

### 作用

无 Canary 保护： 无任何作用
部分函数 Canary 保护： 在一些容易受到攻击的函数返回地址之前添加 cookie 。在函数返回时，检查该 cookie 与原本程序插入该位置的 cookie 是否一致，若一致则程序认为没有受到栈溢出攻击。
全部函数 Canary 保护： 所有的自定义函数在返回地址之前都会添加 cookie 。在函数返回时，检查该 cookie 与原本程序插入该位置的 cookie 是否一致，若一致则程序认为没有受到栈溢出攻击。

## 5.RELRO

设置符号重定位表格为只读或在程序启动时就解析并绑定所有动态符号，从而减少对GOT的攻击

### 作用

No RELRO： 在这种模式下关于重定位并不进行任何保护。
Partial RELRO： 在这种模式下，一些段 (包括.dynamic) 在初始化后将会被标识为只读。
Full RELRO： 在这种模式下，除了会开启部分保护外。惰性解析会被禁用（所有的导入符号将在开始时被解析，.got.plt 段会被完全初始化为目标函数的终地址，并被标记为只读）。此外，既然惰性解析被禁用，GOT[1] 与 GOT[2] 条目将不会被初始化为提到的值。但是Full RELRO会增加启动时间

### 添加方式

```python
  ## 关闭： No RELRO
  -z norelro
  ## 开启： Partial RELRO(默认选项)
  -z lazy
  ## 完全开启： Full RELRO
  -z now
```

---

*若文中有理解不深、表述欠妥之处，欢迎各路师傅指正交流。*
