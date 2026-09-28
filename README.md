# find-xin 的博客

这是一个使用 Hugo Extended 构建的静态博客，页面样式移植自 [Magzine Hexo 主题](https://github.com/forever218/hexo-theme-magzine)。仓库的 `main` 分支通过 GitHub Actions 部署到 [find-xin.github.io](https://find-xin.github.io/)。

## 开始写一篇文章

在项目根目录运行：

```sh
hugo new content/posts/my-post.md
```

将 `my-post` 改成文章的英文文件名。新文章位于 `content/posts/`，默认 `draft: true`，可以先在本地预览而不进入正式构建。编辑文件时，保留开头两行 `---` 之间的 Front Matter，例如：

```yaml
---
title: '文章标题'
date: 2026-09-28T20:00:00+08:00
draft: true
summary: '一句话介绍文章内容。'
cover: '/images/posts/my-post-cover.webp'
pinned: false
tags: ['Hugo', '笔记']
categories: ['技术']
---
```

`title` 是文章标题；`date` 控制首页和归档排序；`summary` 可用于摘要；`tags` 和 `categories` 会生成对应的标签、分类页。`pinned: true` 只显示置顶标记，不改变排序。`cover` 可留空，留空时首页使用纯文字卡片。旧文章中的 `cardStyle` 字段已经不起作用，新文章无需填写。

在 Front Matter 之后用 Markdown 写正文。使用 `##`、`###` 等小标题会自动生成文章左侧目录；没有小标题时目录不显示。例如：

```md
## 第一部分

正文内容。

### 一个小节

更多内容。
```

当前 `content/posts/` 中的三篇文章是示例，正式发布自己的文章前可以修改或删除它们。

## 准备图片

把文章封面及正文图片放到 `static/images/posts/`，建议使用 `.webp`，文件名使用英文、数字和短横线。路径从 `static/` 后开始写，前面加 `/`：

```text
磁盘文件：static/images/posts/my-post-cover.webp
封面路径：/images/posts/my-post-cover.webp
```

正文插图用 Markdown 引用，并写有意义的替代文字：

```md
![图片内容说明](/images/posts/my-post-detail.webp)
```

封面会用于首页卡片、归档条目和文章顶部，不同位置会裁切图片。选图后请在电脑和手机预览中检查人物、文字等重要内容是否被裁掉。首页顶部大图由 `hugo.toml` 中的 `heroImage` 指定，头像由 `avatar` 指定；更换图片时同时修改对应路径。

画廊图片放在 `static/images/gallery/`，并在 `data/gallery.yaml` 的 `images` 列表中添加一项：

```yaml
- image: /images/gallery/collection-32.webp
  ratio: 1.7778
  number: "32"
  caption: '图片说明'
```

`ratio` 是图片宽度除以高度；`number` 保留引号。若另有原图，可增加 `original: /images/gallery/原图文件名.png`，画廊会提供查看原图的入口。

## 本地预览与发布

需要安装 **Hugo Extended**。写作时运行：

```sh
hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender
```

打开 <http://localhost:1314/>。`-D` 会把草稿也显示出来。准备发布时，把要发布文章的 `draft` 改为 `false`，然后运行与 GitHub Actions 相同的构建命令：

```sh
hugo --minify
```

检查首页、文章页、标签、分类、归档和图片都正常后，提交并推送：

```sh
git add content/posts static/images/posts data/gallery.yaml static/images/gallery
git commit -m "Publish new post"
git push origin main
```

只需暂存这次实际修改过的文件；如果同时修改了 `hugo.toml`、布局或样式，也把它们加入提交。推送 `main` 后，`.github/workflows/pages.yml` 会自动构建并部署。首次部署需在 GitHub 仓库的 **Settings → Pages → Build and deployment** 中把 Source 设为 **GitHub Actions**；此仓库的 `baseURL` 已设置为 `https://find-xin.github.io/`。

## 主题文件

- `assets/css/magzine-original.css`：Magzine 原始样式。
- `assets/css/magzine-hugo.css`：本站的 Hugo 与响应式适配。
- `layouts/`：Hugo 页面模板。
- `LICENSE.magzine`：移植的主题文件所附许可证。
