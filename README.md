# Vortex's Blog

> CTF 萌新 · PWN 方向修行中

记录 CTF 比赛复盘、二进制 / Web 安全学习笔记的个人博客。

**在线地址**：https://3133q.github.io/

## 技术栈

- [Hugo](https://gohugo.io/) — 静态站点生成
- [hugo-theme-stack](https://github.com/CaiJimmy/hugo-theme-stack) — 主题
- [Giscus](https://giscus.app/) — 评论（基于 GitHub Discussions）
- GitHub Actions + GitHub Pages — 自动部署

## 本地运行

```bash
# 需要 Hugo Extended 0.165+
hugo server -D
```

访问 http://localhost:1313/

## 目录结构

```
.
├── content/          # 文章（post + page）
├── config/_default/  # 站点配置
├── layouts/          # 自定义模板（覆盖主题）
├── assets/           # 静态资源（SCSS / JS）
├── static/           # 直接复制到根目录的静态文件
├── scripts/          # 本地辅助脚本（封面图生成等）
└── .github/workflows # CI/CD
```

## 部署

`main` 分支 push 后，`.github/workflows/hugo.yml` 自动构建并发布到 GitHub Pages。

## 联系

- GitHub：[@3133q](https://github.com/3133q)
- 博客留言：使用页面底部的 Giscus 评论

## 许可

文章采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议。
