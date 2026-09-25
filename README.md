# 月影书房 · Hugo 静态博客主题

以《魔法使之夜》的蓝紫夜色为灵感，适配手机与桌面端的静态 Hugo 博客。首页使用用户提供的有珠壁纸；部署后请确认该图片适合公开发布，并替换为你拥有发布权的素材（如有需要）。

## 本地预览

安装 Hugo Extended 后，在本目录运行：

```sh
hugo server -D
```

打开终端显示的本地地址。编辑 `hugo.toml` 修改站名、简介、导航地址、头像等。修改 `baseURL` 为实际 GitHub Pages 地址后再发布。

## 写文章与卡片样式

```sh
hugo new content/posts/my-post.md
```

文章 Front Matter 可设置：

```yaml
cover: '/images/my-cover.webp'
cardStyle: standard # standard / wide / tall / feature / text
pinned: false
tags: ['魔法使之夜', '久远寺有珠']
categories: ['型月']
```

- `standard`：常规卡片，一列一行。
- `wide`：横跨两列。
- `tall`：纵向跨两行。
- `feature`：两列两行，适合重点文章。
- `text`：纯文字样式，无封面也能使用。

首页按日期倒序自动整理，`pinned: true` 的卡片通过徽标标识。首页「角色画廊」入口展示从 `data/gallery.yaml` 管理的插画；图片文件位于 `static/images/gallery/`，可在 YAML 中调整顺序和图片路径。卡片仅在桌面端采用不同尺寸；手机端自动改为单列以便阅读。

## GitHub Pages 自动部署

1. 创建名为 `用户名.github.io` 的公开 GitHub 仓库，把本目录文件推送到 `main` 分支。
2. 修改 `hugo.toml` 的 `baseURL`。个人站可用 `https://用户名.github.io/`；项目站用 `https://用户名.github.io/仓库名/`。
3. GitHub 仓库 Settings → Pages → Build and deployment，Source 选择 **GitHub Actions**。
4. 推送后，仓库内置的工作流会构建并发布。
