# find-xin 的个人博客 (Hugo Magazine Theme)

本项目是基于 **Hugo Extended** 构建的高性能静态博客，融合了优雅的杂志排版（Magazine Style）、日夜间双重模式平滑切换、全站沉浸式相册、微光生活日记、Giscus 社区留言板及客户端全文检索。

博客通过 GitHub Actions 自动化持续集成（CI/CD），一旦将修改推送到 `main` 分支，即会自动构建并部署到 [find-xin.github.io](https://find-xin.github.io/)。

---

## 目录索引

- [0. 🌟 极简推荐：桌面可视化控制台（告别终端，全图形化操作）](#0--极简推荐桌面可视化控制台告别终端全图形化操作)
- [1. 网站核心目录架构](#1-网站核心目录架构)
- [2. 发布内容指南](#2-发布内容指南)
  - [2.1 撰写长篇博文（Markdown 文章）](#21-撰写长篇博文markdown-文章)
  - [2.2 记录随想与微光日记（Diary）](#22-记录随想与微光日记diary)
  - [2.3 插入图片与撰写「带图 Markdown」](#23-插入图片与撰写带图-markdown)
  - [2.4 上传与嵌入 PDF 文档](#24-上传与嵌入-pdf-文档)
  - [2.5 管理多分区相册（摄影 / 日常 / 动漫）](#25-管理多分区相册摄影--日常--动漫)
  - [2.6 从 Obsidian 发布文章与日记（带 attachments 附件）](#26-从-obsidian-发布文章与日记带-attachments-附件)
  - [2.7 发布 Jupyter Notebook（.ipynb 文件）](#27-发布-jupyter-notebookipynb-文件)
- [3. 本地调试与上传 GitHub 操作流程（必读命令）](#3-本地调试与上传-github-操作流程必读命令)
- [4. 常见问题与避坑提示](#4-常见问题与避坑提示)

---

## 0. 🌟 极简推荐：桌面可视化控制台（告别终端，全图形化操作）

如果你觉得每次打开终端输入 Python 脚本、Hugo 命令和 Git 提交太繁琐，本项目已为你内置了**零依赖、纯原生运行的桌面级可视化管理后台 2.0**！

### 0.1 环境与依赖说明（依赖包放哪里了？）
- **零外部 pip 依赖**：脚本全部基于 Python 3 标准库（`http.server`、`json`、`subprocess`、`shutil`、`pathlib`）开发，**不需要建立 Python 虚拟环境，不需要运行 `pip install` 安装任何第三方包**，不会污染你的系统环境。
- **图像与系统能力**：
  - 调用 macOS 系统底层自带的图像引擎 **`sips`** 自动计算图片实际物理宽高与长宽比（Ratio）；
  - 调用系统级 **`AppleScript (osascript)`** 调起 macOS 原生访达文件选择框；
  - 图片压缩优先调用 Homebrew 安装的 **`cwebp`**，若无则自动安全回退；
- **博客渲染引擎**：Hugo 位于系统全局（通过 Homebrew 安装在 `/opt/homebrew/bin/hugo`）。

---

### 0.2 如何启动控制台？
- **方式一（最推荐）**：在访达（Finder）中直接双击根目录下的 **`启动博客控制台.command`** 文件，控制台将自动启动并在默认浏览器中弹出。
- **方式二（命令行启动）**：
  ```bash
  python3 scripts/dashboard.py
  ```
- 打开后即可访问：`http://localhost:2026/`

---

### 0.3 控制台四大核心功能模块

#### 1. ✍️ 发布文章 / 笔记（支持 Obsidian 笔记与 Jupyter Notebook）
- **📂 系统原生文件选择器**：点击「📂 浏览电脑文件...」按钮，直接弹出 macOS 访达文件选择窗口选择笔记，也可选中文件后按 `⌥ + ⌘ + C` 复制路径直接粘贴。
- **自动格式转换与附件抽取**：
  - 自动识别正文中的 `![[附件图片]]` 与 Markdown 图片，统一转换为高质量 `.webp` 格式并自动压缩。
  - 针对 Jupyter Notebook，自动提取 Python 代码块、文字输出、Pandas 表格及 Matplotlib/Seaborn 高清绘图（自动转 WebP）。
  - 自动注入 KaTeX 数学公式支持与防重叠封面参数。
- **元数据定制**：选择板块（博文/日记）、快捷点击常用分类与标签、指定别名 Slug 或勾选草稿。点击 **「🚀 立即转换并发布」** 即可。

#### 2. 🖼️ 光影相册管理（Gallery Studio · 告别手动算比例与改 YAML）
- **📸 一键添加新照片**：
  - 点击「📂 选择图片文件...」选取任意本地 PNG/JPG/WebP 照片；
  - 选择相册分类：`🎨 动漫插画` / `📷 摄影大片` / `☕ 生活日常`；
  - 输入作品标题（Caption）与标签（Tags）；
  - 点击 **「✨ 自动测量宽高、转码并加入相册」**：后台将**自动提取真实长宽比（Ratio）**、**转码压缩为 WebP**、**自动按序递增全局编号**（如 `photo-07.webp`），并**自动安全更新 `data/gallery.yaml`**！
- **🖼️ 全站相册图墙一览**：
  - 实时瀑布流网格展示相册内所有 40+ 张照片的真实缩略图、分类徽标、编号、长宽比和标签；
  - 支持按分类即时筛选（全部 / 动漫 / 摄影 / 日常）；
  - 支持 **一键移除**：带确认弹窗，自动从 `data/gallery.yaml` 抹除记录并安全清理磁盘图片。

#### 3. 📚 全站文章管理（检索、下架、删除）
- **实时统计与过滤检索**：顶部显示博文、日记与草稿总数，输入文章关键词即时过滤。
- **快捷操作**：
  - **`👁️ 预览`**：点击直接在浏览器中打开该文章的本地预览页面。
  - **`🟡 下架 / 🟢 上架`**：单键将文章设为草稿（`draft: true`）或恢复公开，无需手动打开 md 文件编辑。
  - **`🗑️ 删除`**：彻底删除文章及其专属 `attachments/` 附件，防误删带二次确认。

#### 4. 🚀 部署到 GitHub
- **Git 状态实时监测**：清晰展示当前分支名称、工作区是否干净或待提交的文件数量。
- **免敲命令一键提交**：快捷选择或输入提交说明（Commit Message），点击 **「🚀 提交并推送到 GitHub」**，后台自动执行 `git add .`、`git commit` 与 `git push origin main` 并实时打印终端日志。
- 推送完成后 GitHub Actions 自动构建，约 1 分钟即可同步到线上。

#### 5. ⚡ Hugo 本地预览服务控制
- 页面顶部实时显示 Hugo 服务运行状态（端口 1314）。
- 点击 **「▶️ 启动 Hugo」** 或 **「⏹️ 停止服务」** 即可在后台启停，无需单独开终端窗口。
- 点击 **「🌐 本地预览」** 快速跳转 `http://localhost:1314/`。

---

## 1. 网站核心目录架构

了解各个文件夹的职责，有助于快速定位要修改和存放的文件：

```text
youshu-night/
├── content/                     # 内容源文件（全部采用 Markdown 撰写）
│   ├── posts/                   # 深度博文、技术笔记、长文
│   ├── diary/                   # 生活微光、短篇日记、随笔
│   ├── gallery/                 # 相册页面元数据
│   ├── friends/                 # 友链页面
│   └── guestbook/               # 留言板页面
├── static/                      # 静态资源根目录（编译时会被完整复制到网站根目录 /）
│   ├── docs/                    # 存放 PDF 文档、报告等文件
│   └── images/                  # 存放全站图片
│       ├── posts/               # 文章封面及正文插图
│       ├── photography/         # 摄影大片
│       ├── daily/               # 日常生活记录照片
│       └── gallery/             # 动漫/插画/收藏图库
├── data/
│   └── gallery.yaml             # 相册数据库（在此登记照片信息、长宽比、标签与分类）
├── layouts/                     # Hugo 页面模板（HTML）
├── assets/                      # 前端样式与脚本（CSS / JS）
├── hugo.toml                    # 博客全局配置文件
└── .github/workflows/pages.yml  # GitHub Actions 自动构建与部署脚本
```

---

## 2. 发布内容指南

### 2.1 撰写长篇博文（Markdown 文章）

博文存放在 `content/posts/` 目录下。

#### 步骤 1：新建文章文件
在项目根目录下通过终端生成，或者直接在编辑器中手动创建 `.md` 文件：

```bash
# 自动生成（文件名建议使用英文小写和中划线）
hugo new content/posts/my-new-article.md
```

#### 步骤 2：编辑文章头部参数（Front Matter）
打开新建的文件，顶部在两行 `---` 之间填写元数据：

```yaml
---
title: '如何构建优雅的静态博客'
date: 2026-10-02T14:00:00+08:00
draft: false                          # false 表示正式发布；true 为本地草稿（线上不显示）
summary: '本文记录了博客的设计思考与架构迁移全过程。' # 首页杂志卡片与搜索的摘要
cover: '/images/posts/my-cover.webp'   # 封面图路径（留空则显示优雅的纯文字卡片）
pinned: false                         # 设置为 true 会在首页卡片显示“置顶”星标
categories: ['技术']                  # 分类（支持单个或多个）
tags: ['Hugo', '前端', 'Web']          # 标签（用于全站标签归档和搜索）
---
```

#### 步骤 3：编写正文
在 Front Matter 之后正常使用 Markdown 语法书写。
- **目录生成**：只要正文中使用 `## 二级标题`、`### 三级标题`，文章页面左侧便会自动生成悬浮可折叠的目录导航。
- **代码高亮**：使用 ```` ```python ```` 或 ```` ```js ```` 包裹代码块即可自动美化。

---

### 2.2 记录随想与微光日记（Diary）

日记存放在 `content/diary/` 目录下，适合短篇生活记录、心情杂谈、随手拍碎片。

#### 步骤 1：创建日记文件
例如创建 `content/diary/2026-autumn-walk.md`：

```yaml
---
title: '秋日傍晚的滨江漫步'
date: 2026-10-02T19:00:00+08:00
draft: false
mood: '惬意'                           # 心情标签（可选，如：惬意 / 晴朗 / 沉思）
location: '徐汇滨江'                   # 地理位置（可选）
cover: '/images/daily/autumn-walk.webp'# 可选封面配图
tags: ['散步', '秋天', '日常生活']
likes: 6                              # 初始点赞数
---

正文记录今天的心情与生活切片……
```

日记会自动同步在首页下方的「生活微光 · 近期手记」时间轴展示，并汇入全站搜索。

---

### 2.3 插入图片与撰写「带图 Markdown」

#### 1. 图片格式与命名规范
- **推荐格式**：首选 **`.webp`**（体积小、加载迅速、画质无损），也支持 `.png`、`.jpg`、`.jpeg`、`.gif`、`.svg`。
- **命名规范**：文件名全部使用**小写英文字母、数字和减号 `-`**，例如 `tokyo-tower-night.webp`。禁止使用中文字符或空格，防止在网络传输或生成 URL 时被特殊字符转义导致无法显示。
- **压缩建议**：建议将图片尺寸宽度控制在 `1200px ~ 2400px` 之间，单张体积控制在 `500KB` 以内（推荐使用 [squoosh.app](https://squoosh.app) 或 `cwebp` 工具转换）。

#### 2. 图片存放在哪里？
根据用途存放至 `static/` 下的对应子目录中：
- 文章配图与封面：存放至 `static/images/posts/`
- 摄影作品原图：存放至 `static/images/photography/`
- 日常随手拍：存放至 `static/images/daily/`
- 动漫/收藏插画：存放至 `static/images/gallery/`

#### 3. 关键路径规则（绝对路径以 `/` 开头）
> ⚠️ **重要规则**：`static` 文件夹是 Hugo 的映射根目录。引用时**切勿加上 `static`**！
> - 实际电脑中的物理路径：`static/images/posts/my-illustration.webp`
> - 在 Markdown 或配置文件中的路径：`/images/posts/my-illustration.webp`

#### 4. 在 Markdown 中引用图片的几种方式

##### 方式一：标准 Markdown 语法（推荐）
```markdown
![这里填写图片描述说明文字](/images/posts/my-illustration.webp)
```

##### 方式二：带标题的图片语法（悬停显示标题）
```markdown
![秋日晨光](/images/posts/autumn-morning.webp "摄于世纪公园")
```

##### 方式三：HTML 优雅居中卡片（带自适应阴影与图注说明）
如果想对图片排版做更精细的控制，可以直接混入 HTML 代码：
```html
<figure style="text-align: center; margin: 2rem 0;">
  <img src="/images/posts/autumn-morning.webp" alt="秋日晨光" style="max-width: 90%; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
  <figcaption style="font-size: 0.88rem; color: var(--color-meta); margin-top: 8px;">图：秋日晨光穿透林间树隙</figcaption>
</figure>
```

---

### 2.4 上传与嵌入 PDF 文档

如果需要分享论文、设计方案、简历、报告等 PDF 文档：

#### 步骤 1：放置 PDF 文件
将你的 PDF 文件放置到：
```text
static/docs/your-document-name.pdf
```
（例如：`static/docs/hugo-architecture-guide.pdf`）

#### 步骤 2：在文章中引用 PDF

##### 方式 A：普通下载 / 跳转链接
```markdown
👉 [点击在线阅读或下载《Hugo 架构指南》(PDF)](/docs/hugo-architecture-guide.pdf)
```

##### 方式 B：精美胶囊按钮（新标签页打开）
```html
<p style="text-align: center; margin: 1.5rem 0;">
  <a href="/docs/hugo-architecture-guide.pdf" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; background: var(--color-accent); color: #ffffff; border-radius: 999px; text-decoration: none; font-size: 0.95rem; font-weight: 500; transition: transform 0.2s;">
    📄 在新标签页阅读《Hugo 架构指南》(PDF)
  </a>
</p>
```

##### 方式 C：正文中直接内嵌 PDF 阅读器窗口
用户无需跳出网页，即可在文章内滚动查阅 PDF 内容：
```html
<div style="margin: 2rem 0; width: 100%;">
  <iframe src="/docs/hugo-architecture-guide.pdf" width="100%" height="650px" style="border: 1px solid var(--color-border); border-radius: 8px; background: #fff;">
    <p>您的浏览器暂不支持内嵌预览，请 <a href="/docs/hugo-architecture-guide.pdf">点击此处下载 PDF</a> 查看。</p>
  </iframe>
</div>
```

---

### 2.5 管理多分区相册（摄影 / 日常 / 动漫）

全站相册页面（`/gallery/`）分为三大板块：
1. **摄影 (`photography`)**
2. **日常 (`daily`)**
3. **动漫 (`anime`)**

每个板块均自带标签筛选器、全屏放大灯箱（支持手机左右滑动切图）、原图查看等功能。

#### 添加一张新照片到相册：
1. 将照片文件放置在对应文件夹：
   - 摄影：`static/images/photography/photo-name.webp`
   - 日常：`static/images/daily/life-snap.webp`
   - 动漫：`static/images/gallery/illustration.webp`
2. 打开 `data/gallery.yaml`，在末尾新增一条记录：

```yaml
- image: /images/photography/shanghai-tower.webp   # 图片访问路径（以 / 开头）
  category: photography                          # 分区：photography（摄影）| daily（日常）| anime（动漫）
  ratio: 1.5                                     # 图片宽高比（宽 ÷ 高）。横屏通常为 1.5 (3:2) 或 1.7778 (16:9)；竖屏通常为 0.6667 (2:3) 或 0.75 (3:4)；正方形写 1.0
  number: "44"                                   # 唯一序号（保持连续递增，用双引号包裹）
  caption: '上海中心 · 暮色云端'                 # 图片标题或描述说明
  tags: ['城市', '建筑', '夜景']                  # 检索与筛选标签列表
  original: /images/photography/shanghai-tower.webp # 可选，高清原图路径
```

保存后，相册页面及首页下方的「光影切片」都会自动加载该照片并支持标签筛选！

---

### 2.6 从 Obsidian 发布文章与日记（带 attachments 附件）

在 Obsidian 中写文章通常会将图片与 PDF 等文件放在同级目录下的 `attachments/` 文件夹中。Hugo 提供了 **页面包（Page Bundle）** 架构，每个文章或日记都可以作为一个独立的文件夹，完美契合 Obsidian 的组织形式：

```text
content/posts/my-note/
├── index.md           # 笔记正文
└── attachments/       # 该文章引用的图片、PDF 文档等附件
    ├── image-1.png
    └── document.pdf
```

当浏览器访问 `/posts/my-note/` 时，正文中的相对路径 `attachments/image-1.png` 以及封面 `cover: 'attachments/image-1.png'` 均可自动解析并正常显示。

为了避免手动修改双链语法、手动重命名空格文件名和搬运文件的繁琐工作，本项目已内置**全自动发布脚本**：

#### 方案一：使用内置一键自动化脚本（强烈推荐 🌟）

项目根目录下提供了专属脚本 `scripts/publish_obsidian.py`，无需安装任何额外 Python 依赖包即可直接运行：

##### 1. 发布为长篇博文（Post）
```bash
python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/你的笔记.md"
```

##### 2. 发布为生活日记（Diary）
```bash
python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/今日随笔.md" --type diary
```

##### 3. 自定义别名、分类与标签
```bash
python3 scripts/publish_obsidian.py "/path/to/note.md" \
  --slug deep-learning \
  --category "技术" \
  --tags "AI,PyTorch,深度学习"
```

##### 4. 下架、重新上架、删除与管理已有文章
脚本不仅支持发布，还支持全站文章的一键维护：
```bash
# 查看全站所有博文与日记的发布状态（🟢 正常 / 🟡 已下架草稿）
python3 scripts/publish_obsidian.py --list

# 下架指定文章（转为草稿 draft: true，支持按标题或文件夹别名匹配）
python3 scripts/publish_obsidian.py --unpublish "久远寺有珠"

# 重新上架指定文章（恢复 draft: false）
python3 scripts/publish_obsidian.py --publish "久远寺有珠"

# 彻底删除指定文章及其关联附件目录
python3 scripts/publish_obsidian.py --delete "久远寺有珠"
```

##### 脚本自动为你完成的工作：
- 🖼️ **图片自动转换为 WebP**：自动调用系统 `cwebp` 工具将引用的 `.png`、`.jpg`、`.jpeg` 图片统一转换为体积小、画质高、加载极速的 `.webp` 格式，并自动更新 Markdown 中的引用链接与封面图路径。
- 🔍 **双链语法自动转换**：
  - 将 Obsidian 图片双链 `![[Pasted image.png]]` 或 `![[attachments/photo.png]]` 自动转换为 Hugo 标准语法 `![说明](attachments/photo.webp)`。
  - 将文档双链 `![[attachments/paper.pdf]]` 自动转换为 `[📄 查看文档 paper.pdf](attachments/paper.pdf)`。
  - 自动剥离 `[[内部笔记|别名]]` 为纯文本。
- 🛡️ **文件名安全净化**：自动将含空格或特殊符号的附件文件名（如 `Pasted image 20261002.png`）转为安全的 Web 文件名，防止网络 404。
- 📐 **排版与公式保障**：自动检测数学公式并开启 KaTeX 支持；开启 `hardWraps: true` 保证 Obsidian 换行与博客完全一致；添加 `hideCover: true` 避免正文图片与文章顶部 Banner 封面重复展示。
- 📦 **附件精准提取与复制**：仅复制本篇笔记实际引用的图片与 PDF 到对应的 `attachments/` 目录中。
- 📝 **智能 Front Matter 生成**：自动提取首行 `# 标题` 作为 `title`，提取修改时间作为 `date`，设置 `draft: false`，并将第一张照片自动设为文章封面。

---

#### 方案二：纯手动整理方式（零脚本）

如果你习惯手动整理文件：

1. **调整 Obsidian 设置（生成标准 Markdown 链接）**：
   - 打开 Obsidian「设置」→「文件与链接 (Files & links)」：
     - 将「使用 [[WikiLinks]]」开关 **关闭**。
     - 将「内部链接类型」更改为 **相对于当前文件的相对路径**。
   - 这样 Obsidian 插入图片时就会自动生成标准的 `![描述](attachments/xxx.png)` 语法。
2. **复制到博客目录**：
   - 在 `content/posts/` 或 `content/diary/` 下新建一个英文文件夹（例如 `content/posts/autumn-walk/`）。
   - 将笔记重命名为 `index.md` 放入该文件夹。
   - 将该笔记对应的 `attachments/` 文件夹整体复制到该文件夹中。
3. **补充 Front Matter**：
   - 在 `index.md` 顶部加上两行 `---`，配置 `title`、`date`、`draft: false` 等参数。
   - 封面可直接填写：`cover: 'attachments/your-cover.png'`。

---

### 2.7 发布 Jupyter Notebook（.ipynb 文件）

博客现已**原生完整支持 Jupyter Notebook（`.ipynb`）文件的一键解析与发布**，无需在本地安装 `jupyter`、`nbconvert` 或任何复杂外部依赖！

#### 使用方法：

##### 1. 一键发布 Notebook
```bash
# 直接指定 .ipynb 路径即可发布为博客文章
python3 scripts/publish_obsidian.py "/Users/xin/Documents/Lab/数据分析实战.ipynb"

# 自定义文件夹别名、分类与标签
python3 scripts/publish_obsidian.py "/path/to/deep_learning.ipynb" \
  --slug deep-learning-lab \
  --category "机器学习" \
  --tags "PyTorch,深度学习,Python"
```

##### 2. 转换特性一览：
- 🐍 **代码单元格高亮**：所有 Python 代码单元格均自动转换为语法高亮的代码块，支持一键复制代码。
- 📊 **图表自动提取与转 WebP**：Matplotlib、Seaborn、Plotly 等绘制的图表（Base64 图片）会自动提取并**通过 `cwebp` 转换为高清 `.webp` 格式**保存在文章的 `attachments/` 目录中。
- 🎨 **自动设置封面**：Notebook 中生成的第一张数据可视化图表会自动提取作为博客首页的杂志封面卡片。
- 🧮 **LaTeX 数学公式**：Markdown 单元格中使用的公式（如 `$\text{MSE} = ...$`）会自动被 KaTeX 渲染。
- 📋 **Pandas DataFrame 表格渲染**：表格与数据框输出自适应横向滚动，带有优雅的斑马纹交替底色。
- 💻 **控制台输出与报错**：`print(...)` 的标准输出和错误 Traceback 均会自动包装在优雅的终端输出框内展示。

---

## 3. 本地调试与上传 GitHub 操作流程（必读命令）

日常写博客、添加照片或修改页面的标准闭环工作流：

### 步骤 1：本地启动预览（实时热重载）
在终端中进入项目目录，运行以下命令启动本地服务：

```bash
hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender
```

- 浏览器打开：**`http://localhost:1314/`**
- 说明：`-D` 参数表示允许展示处于 `draft: true` 状态的草稿文章，保存文件时浏览器会自动刷新同步。

### 步骤 2：发布前检查
在确认内容无误准备正式发布前：
1. 将要发布的 Markdown 文件头部中的 `draft: true` 改为 `draft: false`。
2. 在终端执行一次预编译，确保没有语法冲突或路径错误：
   ```bash
   hugo --minify
   ```
   如果看到输出 `Total in XX ms` 且无报错提示，即代表编译完全正常。

### 步骤 3：提交修改到 Git
运行以下命令暂存并提交所有更改：

```bash
# 1. 查看当前哪些文件发生了改动或新增
git status

# 2. 将所有新增文件与修改暂存到 Git 暂存区
git add .

# 3. 提交并附带简要清晰的说明信息
git commit -m "feat: 发布新文章《构建优雅的静态博客》并更新相册"
```

### 步骤 4：推送到 GitHub 并触发自动化部署
运行以下命令将代码推送到 GitHub 远程仓库：

```bash
git push origin main
```

### 步骤 5：验证线上发布
1. 打开你的 GitHub 仓库主页：[https://github.com/find-xin/find-xin.github.io](https://github.com/find-xin/find-xin.github.io)
2. 点击顶部的 **Actions** 标签页，你会看到名为 `Deploy Hugo site to Pages` 的工作流正在自动运行（通常在 30 秒至 1 分钟内完成）。
3. 工作流运行成功打上绿色勾号后，访问线上博客：**[https://find-xin.github.io/](https://find-xin.github.io/)** 查看更新。

> 💡 **提示**：如果线上页面没有立即显示新内容，是因为浏览器缓存。请按下快捷键：
> - Windows: `Ctrl + F5` 强制刷新
> - macOS: `Cmd + Shift + R` 强制刷新

---

## 4. 常见问题与避坑提示

1. **为什么图片无法显示，提示 404？**
   - 检查引用路径中是否多写了 `static/`。切记：电脑里的 `static/images/a.webp`，在 Markdown 里面一定要写成 `/images/a.webp`。
   - 检查文件名的大小写是否完全一致（Linux 服务器对大小写严格敏感）。
2. **为什么我写的文章本地看得到，但是推送到 GitHub 后线上找不到？**
   - 检查文章 Front Matter 开头的 `draft:` 字段，发布前必须将其改为 `draft: false`。
3. **相册中新加的照片比例失真怎么办？**
   - 在 `data/gallery.yaml` 中，`ratio` 参数必须准确对应图片的「宽度 ÷ 高度」。例如宽 1920 高 1080 的照片，`ratio` 应写为 `1.7778`；宽 1080 高 1620 的竖图，`ratio` 应写为 `0.6667`。
4. **更换网站全局配置**：
   - 网站标题、副标题、导航菜单、头像（`avatar`）、首页大图（`heroImage`）、ICP 备案号等信息统一在 `hugo.toml` 中修改。
