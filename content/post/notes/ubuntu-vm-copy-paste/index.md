---
title: "解决Ubuntu16.04主机与虚拟机无法复制粘贴的问题"
description: "open-vm-tools 正常安装却失效，通过排查 VMX 配置与 vmtoolsd 进程解决主机与 Ubuntu16.04 虚拟机之间无法复制粘贴的问题。"
date: 2026-10-01T13:30:00+08:00
slug: "ubuntu-vm-copy-paste"
image: ""
math: false
categories:
    - 学习笔记
tags:
    - Ubuntu
    - VMware
    - 虚拟机
---

## 按照正常的解决办法

![image-20260919170742405](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20260919170742405.png)

装一个open-vm-tools

```python
sudo apt update
sudo apt install open-vm-tools open-vm-tools-desktop
```

然后重启一下

```python
sudo reboot
```

就可以解决粘贴问题了

但实测之后发现无法成功，还是没能解决问题

## 解决

### 排查过程

1. **确认包安装**：`dpkg -l | grep vm-tools` → `open-vm-tools` 和 `open-vm-tools-desktop` 均已安装
2. **确认进程**：`ps aux | grep vmtoolsd` → 系统服务和用户会话 (vmusr) 都在跑
3. **确认 vmblock fuse**：`mount | grep vmblock` → 已挂载
4. **检查 VMX 配置**：发现缺少 isolation 配置行，且 `guestOS` 类型不匹配（写的 `ubuntu-64`，实际是 32-bit）

### 修复步骤

1.**安装桌面版工具包**

```bash
sudo apt update
sudo apt install open-vm-tools-desktop -y
```

2.**修改 VMX 文件（关机状态下编辑）**

```python
guestOS = "ubuntu"
isolation.tools.copy.disable = "FALSE"
isolation.tools.paste.disable = "FALSE"
```

**3. 重启虚拟机后，杀掉 vmtoolsd 并重新启动**

```python
sudo pkill -9 vmtoolsd
sudo systemctl start open-vm-tools
/usr/bin/vmtoolsd -n vmusr &
```

![image-20260919171241560](https://cdn.jsdelivr.net/gh/3133q/blog-pictures@main/image-20260919171241560.png)

成功解决！！
