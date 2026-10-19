---
title: "漏洞函数汇总"
description: "汇总 PWN 中常见的漏洞函数：read、gets、scanf、printf 系列、strcpy 等，梳理其原型、底层逻辑与漏洞触发点。"
date: 2026-10-19T17:41:53+08:00
slug: "vuln-functions"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - PWN
    - 漏洞函数
---

## read/fread

### 原型

ssize_t read(int fd, void *buf, size_t count)

### 逻辑

从指定的文件描述符 `fd`（标准输入通常为 0）读取最多 `count` 字节的数据到 `buf` 中。它是系统调用封装，完全不关心数据内容：不补 `\x00`，也不将 `\n` 视作终止符。

### 漏洞存在点：

- 显式缓冲区溢出： 若 `count > sizeof(buf)`，直接导致栈/堆溢出。
- 整型溢出/无符号转换（Integer Overflow/Signedness）： `count` 常为无符号类型（`size_t`），若外部校验代码使用有符号整型（如 `int len`）校验且未过滤负数，传入 `-1` 时可通过 `len < MAX` 检查，但在传递给 `read` 时被解释为超大正数 `0xFFFFFFFF`，造成巨量溢出。
- 未截断导致信息泄露（Leak）： 因 `read` 不会自动在末尾填充 `\x00`，若紧接着使用 `puts` 或 `printf("%s")` 打印该缓冲区，会顺带泄露缓冲区后未初始化的内存（如 canary、栈地址或 libc 地址）。
- Off-by-One： 如 `read(0, buf, sizeof(buf) + 1)`，刚好覆盖相邻变量或栈帧的 saved RBP 最低字节。

---

## gets/getline

### 原型

char *gets(char *s)

### 逻辑

从标准输入不断读取字符并存入 `s`，直到遇到换行符 `\n` 或 `EOF` 为止，最后把换行符替换为 `\0`

### 漏洞存在点

绝对无界溢出： `gets` 完全没有长度上限限制，输入多长就写多长，是 PWN 中最经典的无条件栈溢出函数

---

## fgets

### 原型

char *fgets(char *s, int size, FILE *stream)

### 逻辑

最多读取 `size - 1` 个字符，或读到换行符 `\n` 为止，并在末尾**强制追加 `\0`**

### 漏洞存在点

参数大小传错： 若程序员误将 `sizeof(pointer)`（8字节）当作缓冲区大小，或者误将结构体总大小当成了单一字段的大小（如 `fgets(s->name, sizeof(*s), stdin)`）。

Off-by-One 边界误判： 虽然本身安全，但若搭配错误的索引逻辑（如程序员以为读了 `size` 字节而手动在 `s[size]` 赋值），仍会溢出。

---

## scanf/__iso99_scanf/fscanf

### 原型

int scanf(const char *format, ...)

### 逻辑

根据格式化字符串解析标准输入。遇到空白字符（空格、Tab、换行）通常作为分割符。

### 漏洞存在点：

- `%s` 无界溢出： 若直接使用 `scanf("%s", buf)`，行为与 `gets` 等价，读入任意长度字符直至遇到空白字符。*(安全写法应为 `%31s`)*。
- 类型不匹配截断： 用 `%d` 读入整数存入 `short` 或 `char` 变量，多余字节直接覆盖相邻变量。
- 跳过输入利用： 当使用 `%d` 但用户输入 `+` 或非数字字符时，`scanf` 会匹配失败，对应变量不会被赋值且保持原值，可用来绕过逻辑检测或保留栈上残留值。

---

## printf/sprintf/snprintf/dprintf

### 原型

int printf(const char *format, ...)

### 逻辑

解析 `format` 中的占位符（如 `%d`, `%s`, `%p` 等）。遇到占位符时，依次从寄存器（x86-64 依调用约定为 RSI, RDX, RCX, R8, R9）以及栈顶读取参数并格式化输出

### 漏洞存在点

直接以用户输入作为 format： 如 `printf(buf);` 而不是 `printf("%s", buf);`。

任意地址读（Leak）：

- `%p` / `%x`：泄露寄存器与栈数据（Canary、PIE基址、Libc基址）。
- `%s`：将指定栈参数视作指针，解引用读取该地址处的字符串，实现跨空间任意读。
- Positional 语法：如 `%7$p` 可直接定位读取第 7 个参数。

任意地址写：

- `%n` / `%hn` / `%hhn`：将目前已经打印的字符总数写入对应指针指向的内存地址。配合格式化字符串构造，可以向 GOT 表、Hook 指针、返回地址等写入目标值。

​     `snprintf` 的逻辑截断陷阱： `snprintf(buf, size, ...)` 返回的是完全格式化所需字符数，而非实际写入的字符数；若后续使用其返回值做偏移累加，可能导致堆/栈上的越界写。

---

## puts

### 原型

int puts(const char *s)

### 逻辑

从 `s` 指向的地址开始遍历打印字符，直到遇到第一个 `\0` 为止，并在末尾自动追加换行符 `\n`

### 漏洞存在点

内存泄露（Leak）： 如果前序输入函数（如 `read`）填满了缓冲区而没有保留 `\0`，`puts` 会接着往下读，直到内存中出现 `\0`，从而泄露栈上的敏感数据（如 Canary、Saved RBP、返回地址 libc 等）。

ROP Chain 常用 Gadget： 经常被用来在 ROP 阶段构造泄露，例如 `pop rdi; ret` 加载 GOT 表项地址后 `call puts`。

---

## write

### 原型

ssize_t write(int fd, const void *buf, size_t count)

### 逻辑

从 `buf` 开始向 `fd` 精确输出 `count` 个字节。不依赖 `\0` 截断

### 漏洞存在点：

- 未初始化/越界泄露： 若 `count` 大于有效数据长度，会忠实地把内存中紧随其后的内容原封不动吐出来，适合用来精准泄露任意长度的内存块（包括中间含有 `\0` 的指针）。

---

## strcpy/strcat

### 原型

char *strcpy(char *dest, const char *src)

### 逻辑

依次复制字节直至遇到 `src` 中的 `\0`，连同 `\0` 一并写入 `dest`

### 漏洞存在点：

- 缺乏边界检查： 若 `strlen(src) >= sizeof(dest)`，发生经典栈/堆溢出。

---

## strncpy/strncat

### 原型

char *strncpy(char *dest, const char *src, size_t n)

char *strncat(char *dest, const char *src, size_t n)

### 逻辑

`strncpy`：最多复制 `n` 个字节。**关键特性**：如果 `src` 长度 $\ge n$，复制完 `n` 字节后**不会在末尾补 `\0`**。

`strncat`：在 `dest` 原有末尾追加最多 `n` 个字符，**并且始终会额外追加一个 `\0`**

### 漏洞存在点

**`strncpy` 丢失 `\0`：** 紧随其后的字符串操作（如 `strlen`, `strcpy`, `puts`）会越界继续向后找 `\0`，导致信息泄露或溢出。

**`strncat` Off-by-One：** 开发者常写错：`strncat(dest, src, sizeof(dest) - strlen(dest))`，因为其额外追加的 `\0` 会写到 `dest[sizeof(dest)]`，刚好造成 1 字节越界覆盖。

---

## strlen

### 原型

size_t strlen(const char *s)

### 逻辑

顺序遍历字符，计算直到遇到 `\0` 前的字符个数

### 漏洞存在点

**截断绕过：** 若用 `read` 读取输入后紧接着 `strlen(buf)` 做长度校验，若输入开头或中间塞入 `\x00`，`strlen` 会被提前截断返回极小的值，从而绕过后续长度过滤。

---

## 堆部分函数

| 函数                     | 底层行为机制                                                 | 漏洞触发场景                                                 |
| :----------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| **`free(ptr)`**          | 释放内存块，将其链接到 tcache / fastbin / unsorted bin 等链表中。**默认不清空指针**。 | 产生 **Use-After-Free (UAF)**（指针未置 NULL 仍可读写）或 **Double Free**（连续释放同一 chunk 导致 bin 链成环）。 |
| **`malloc(size)`**       | 分配指定字节大小的 chunk。                                   | 传入极端参数（如 `size = 0` 或 `size = -1` 整数溢出）引发异常行为，或与堆越界结合伪造 chunk 发生 overlap。 |
| **`realloc(ptr, size)`** | 根据新 `size` 调整内存块大小；若扩大且原地不足则在别处分配并释放原块。 | 若 `realloc` 失败返回 `NULL` 易造成悬挂指针；若缩小尺寸但未更新外层代码记录的 `len`，可导致堆越界读写。 |
