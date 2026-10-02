# find-xin 的个人博客 (Hugo Magazine & Dark Night Theme)

本项目是基于 **Hugo Extended** 构建的高性能个人静态博客，融合了优雅的杂志排版（Magazine Style）、日夜间双重模式平滑切换、全屏沉浸式光影相册、微光生活日记、知识资料库、Giscus 社区留言板及客户端实时全文检索。

博客通过 **GitHub Actions** 自动化持续集成（CI/CD），一旦将修改推送到 `main` 分支，即会自动编译并部署到 **[find-xin.github.io](https://find-xin.github.io/)**。

---

## 目录索引

- [0. 🌟 核心推荐：本地可视化控制台与管理服务](#0--核心推荐本地可视化控制台与管理服务)
  - [0.1 环境与依赖说明（零外部 pip 依赖）](#01-环境与依赖说明零外部-pip-依赖)
  - [0.2 如何启动控制台与服务？（三种便捷方式）](#02-如何启动控制台与服务三种便捷方式)
  - [0.3 控制台六大核心功能模块一览](#03-控制台六大核心功能模块一览)
- [1. 网站核心目录架构](#1-网站核心目录架构)
- [2. 发布内容指南](#2-发布内容指南)
  - [2.1 撰写长篇博文（Markdown 文章）](#21-撰写长篇博文markdown-文章)
  - [2.2 记录随想与微光日记（Diary）](#22-记录随想与微光日记diary)
  - [2.3 插入图片与撰写「带图 Markdown」](#23-插入图片与撰写带图-markdown)
  - [2.4 PDF 文档处理（博文展示型 vs 资料库型）](#24-pdf-文档处理博文展示型-vs-资料库型)
  - [2.5 管理多分区相册（摄影 / 日常 / 动漫 · 含拍摄日期）](#25-管理多分区相册摄影--日常--动漫--含拍摄日期)
  - [2.6 从 Obsidian 发布笔记（带 attachments 附件与 WebP 转码）](#26-从-obsidian-发布笔记带-attachments-附件与-webp-转码)
  - [2.7 发布 Jupyter Notebook（.ipynb 原生解析）](#27-发布-jupyter-notebookipynb-原生解析)
- [3. 全站归档与分类体系](#3-全站归档与分类体系)
- [4. 本地调试与上传 GitHub 操作流程（必读命令）](#4-本地调试与上传-github-操作流程必读命令)
- [5. 常见问题与避坑提示（含 Slug 命名规范）](#5-常见问题与避坑提示含-slug-命名规范)

---

## 0. 🌟 核心推荐：本地可视化控制台与管理服务

为了告别繁琐的终端命令和手动计算图片比例的烦恼，本项目内置了**零依赖、纯原生运行的桌面级可视化管理后台 2.0** 与全功能服务脚本。

### 0.1 环境与依赖说明（零外部 pip 依赖）
- **零外部 pip 依赖**：后台脚本全部基于 Python 3 标准库（`http.server`、`json`、`subprocess`、`shutil`、`pathlib`）开发，**不需要建立 Python 虚拟环境，不需要运行 `pip install` 安装任何第三方包**，绝对不会污染你的系统环境。
- **图像与系统能力**：
  - 调用 macOS 系统底层自带的图像引擎 **`sips`** 自动计算图片物理尺寸与长宽比（Ratio）；
  - 调用系统级 **`AppleScript (osascript)`** 调起 macOS 原生访达文件选择框；
  - 图片压缩优先调用 Homebrew 安装的 **`cwebp`**（若无则自动安全回退保持原图）；
- **博客渲染引擎**：Hugo 位于系统全局（通过 Homebrew 安装在 `/opt/homebrew/bin/hugo`）。

---

### 0.2 如何启动控制台与服务？（三种便捷方式）

#### 方式一：macOS 桌面快捷启动（最推荐 ⭐️）
在访达（Finder）中直接双击根目录下的 **`启动博客控制台.command`**，会自动启动后台服务并拉起默认浏览器访问控制台。

#### 方式二：终端全能服务管理脚本（`start.sh`）
根目录内置了功能完备的 `start.sh` 服务控制脚本：
```bash
./start.sh          # 默认启动全套服务（Hugo 预览端口 1314 + 控制台端口 2026）
./start.sh hugo     # 仅启动 Hugo 本地预览服务 (http://localhost:1314/)
./start.sh dash     # 仅启动博客管理控制台 (http://localhost:2026/)
./start.sh status   # 实时查看 Hugo 与控制台的运行状态及端口
./start.sh stop     # 一键安全停止所有博客相关后台进程
./start.sh restart  # 重启全套服务
```

#### 方式三：原生 Python 直接启动
```bash
python3 scripts/dashboard.py
```
启动后在浏览器打开：`http://localhost:2026/`

---

### 0.3 控制台六大核心功能模块一览

#### 1. ✍️ 一键发布文章 / 日记（支持 Markdown、Obsidian 笔记与 Jupyter Notebook）
- **系统原生文件选择**：点击「📂 浏览电脑文件...」直接弹出 macOS 访达选择窗口，或按 `⌥ + ⌘ + C` 复制路径粘贴。
- **格式全自动转码**：
  - 自动识别正文与 `attachments/` 中的图片，统一转码为高质量 `.webp` 格式并压缩；
  - 自动转换 Obsidian 双链语法（`![[图片]]`、`[[链接]]`）；
  - 自动将 Jupyter Notebook（`.ipynb`）解析为 Markdown、代码块、终端输出、Pandas 斑马纹表格，并将绘图自动提取为 WebP 保存；
  - 智能注入 KaTeX 数学公式支持，防封面与正文重复显示。
- **发布定制**：自由选择板块（博文 / 日记）、分类、标签、自定义 URL 标识（Slug）或设为草稿。

#### 2. 📚 文章与日记管理（快速编辑、Slug 平滑重命名、草稿上下架）
- **即时检索与状态统计**：实时显示文章与日记总数、草稿数，支持关键词模糊检索。
- **⚡ 快速编辑与 Slug 重定向**：
  - 无需打开源文件，点击「快速编辑」即可直接修改标题、分类、标签、摘要及 **URL 标识（Slug）**；
  - **修改 Slug 零风险**：后台不仅自动重命名文件/目录，还会在文章 Front Matter 中自动写入 Hugo 的 `aliases` 别名重定向，**即便访客或搜索引擎访问旧链接也不会 404**！
  - **更新时间保护**：仅微调标签或分类时，不会破坏正文真实的最后更新时间。
- **草稿上下架与删除**：一键切换公开 / 草稿状态；安全级彻底删除（连带专属附件清理，带二次确认）。

#### 3. 🖼️ 光影相册管理（Gallery Studio · 自动比例与拍摄日期）
- **📸 零门槛添加相片**：
  - 选取本地任意图片，选择分区（🎨 动漫插画 / 📷 摄影大片 / ☕ 生活日常）；
  - 填写作品标题、拍摄日期（自动读取文件元数据或手动填写）及标签；
  - 点击「✨ 自动测量宽高、转码并加入相册」：后台通过 macOS `sips` 自动测量长宽比、转码为 WebP、递增全局编号，并安全写入 `data/gallery.yaml`。
- **图墙瀑布流维护**：一览相册所有作品缩略图与元信息，支持按分类筛选及一键移除。

#### 4. 📂 知识资料库管理（Resources Library）
- **文件与资料归档**：在控制台直接查阅和管理供读者下载的 PDF 报告、学术论文、代码压缩包等资料。
- 自动生成对应下载卡片与阅读链接，保障网站静态资产井井有条。

#### 5. 🚀 Git 部署一键直达
- **Git 状态实时监测**：清晰展示当前分支名称、未提交变更文件清单。
- **免敲命令一键提交**：输入提交说明（Commit Message），点击「🚀 提交并推送到 GitHub」，后台自动执行 `git add .`、`git commit` 与 `git push origin main` 并实时显示终端输出。

#### 6. ⚡ Hugo 本地预览服务控制
- 页面顶部实时显示 Hugo 服务运行状态（端口 1314）。
- 点击「▶️ 启动 Hugo」或「⏹️ 停止服务」即可在后台启停，无需打开多余终端窗口。
- 点击「🌐 本地预览」快速跳转 `http://localhost:1314/`。

---

## 1. 网站核心目录架构

了解各个文件夹的职责，有助于快速定位要修改和存放的文件：

```text
youshu-night/
├── content/                     # 内容源文件（全部采用 Markdown 撰写）
│   ├── posts/                   # 深度博文、技术笔记、长文
│   ├── diary/                   # 生活微光、短篇日记、随笔
│   ├── diary-archive/           # 日记归档与分类页面元数据
│   ├── resources/               # 资料库页面（PDF、报告、代码包等）
│   ├── gallery/                 # 相册页面元数据
│   ├── friends/                 # 友链页面
│   └── guestbook/               # 留言板页面
├── static/                      # 静态资源根目录（编译时会被完整复制到网站根目录 /）
│   ├── docs/                    # 存放公开下载的 PDF 文档、报告、资料
│   └── images/                  # 存放全站图片
│       ├── posts/               # 文章封面及正文插图
│       ├── photography/         # 摄影大片原图与 WebP
│       ├── daily/               # 日常生活记录照片
│       └── gallery/             # 动漫/插画/收藏图库
├── data/
│   └── gallery.yaml             # 相册数据库（在此登记照片信息、长宽比、标签、拍摄日期与分类）
├── layouts/                     # Hugo 页面模板（HTML）
│   ├── _default/                # 默认文章与列表模板（含底栏爱心与淡雅更新时间）
│   ├── diary/                   # 日记列表与单页模板
│   ├── gallery/                 # 相册展示模板
│   └── partials/                # 公共模块（导航、灯箱 Lightbox、留言板等）
├── assets/                      # 前端样式与脚本（CSS / JS）
│   ├── css/                     # 杂志风格样式 (magzine-hugo.css, diary.css 等)
│   └── js/                      # 相册交互 (gallery.js)、主题切换、搜索等
├── scripts/                     # 本地自动化与控制台脚本
│   ├── dashboard.py             # 博客桌面管理控制台后端
│   └── publish_obsidian.py      # Obsidian / Jupyter Notebook / Markdown 一键转换发布脚本
├── hugo.toml                    # 博客全局配置文件
├── start.sh                     # 服务管理 Shell 脚本
├── 启动博客控制台.command         # macOS 桌面双击启动文件
└── .github/workflows/pages.yml  # GitHub Actions 自动构建与部署脚本
```

---

## 2. 发布内容指南

### 2.1 撰写长篇博文（Markdown 文章）

博文存放在 `content/posts/` 目录下。

#### 步骤 1：新建文章文件
可以在编辑器中创建文件，或通过终端快速创建：
```bash
hugo new content/posts/my-new-article.md
```

#### 步骤 2：编辑文章头部参数（Front Matter）
打开新建的文件，顶部在两行 `---` 之间填写元数据：

```yaml
---
title: '如何构建优雅的静态博客'
date: 2026-10-02T14:00:00+08:00
lastmod: 2026-10-02T18:30:00+08:00     # 最后更新时间（可选，会自动显示在文末右侧）
draft: false                          # false 正式发布；true 为本地草稿
summary: '本文记录了博客的设计思考与架构迁移全过程。' # 首页卡片与搜索摘要
cover: '/images/posts/my-cover.webp'   # 封面图路径（留空则显示极简纯文字卡片）
pinned: false                         # 设置为 true 会在首页卡片显示“置顶”星标
categories: ['技术']                  # 分类
tags: ['Hugo', '前端', 'Web']          # 标签
slug: 'building-elegant-static-blog'  # URL 路径标识（建议全小写英文与短横线）
---
```

#### 步骤 3：编写正文
- **自动目录**：正文中使用 `## 二级标题`、`### 三级标题`，页面左侧会自动生成悬浮可折叠的目录导航。
- **时间与排版**：文章头部会自动展示精确到小时的发布时间；文末呈现居中的点赞爱心与靠右对齐的淡雅更新时间。

---

### 2.2 记录随想与微光日记（Diary）

日记存放在 `content/diary/` 目录下，适合短篇生活记录、碎片随感。

```yaml
---
title: '秋日傍晚的滨江漫步'
date: 2026-10-02T19:30:00+08:00
draft: false
category: '日常生活'                  # 日记专属分类
mood: '惬意'                          # 心情标签（可选，如：惬意 / 晴朗 / 沉思）
location: '徐汇滨江'                  # 地理位置（可选）
cover: '/images/daily/autumn-walk.webp'
tags: ['散步', '秋天', '日常生活']
likes: 6                             # 初始点赞数
---

正文记录今天的心情与生活切片……
```

日记会自动汇总至首页下方的「生活微光」时间轴、日记归档列表页及全站搜索中。

---

### 2.3 插入图片与撰写「带图 Markdown」

#### 1. 规范与存放位置
- **推荐格式**：首选 **`.webp`**（体积小、加载迅速、画质无损），也支持 `.png`、`.jpg` 等。
- **命名规范**：使用小写英文字母、数字和减号 `-`（如 `tokyo-night.webp`），禁止空格和特殊符号。
- **物理路径与引用路径区别**：
  - 存放物理路径：`static/images/posts/my-pic.webp`
  - Markdown 中引用：`/images/posts/my-pic.webp`（**切勿带有 `static` 前缀**）。

#### 2. Markdown 引用语法
```markdown
<!-- 标准语法 -->
![图片描述](/images/posts/my-pic.webp)

<!-- 带标题说明 -->
![秋日晨光](/images/posts/my-pic.webp "摄于世纪公园")
```

---

### 2.4 PDF 文档处理（博文展示型 vs 资料库型）

根据使用场景，博客对 PDF 提供了两种清晰的展示方案：

#### 场景 A：博文展示型 PDF（仅作为文章正文展示，不进资料库）
如果你写了一篇博文，其核心内容就是一份 PDF（如一份调研报告或演讲 PPT），希望读者直接在博文页面内阅读并提供下载：
- **放置路径**：放在该文章的 `attachments/` 目录或 `static/docs/` 下。
- **在博文正文中内嵌预览**：
  ```html
  <div style="margin: 2rem 0; width: 100%;">
    <iframe src="/docs/my-report.pdf" width="100%" height="680px" style="border: 1px solid var(--color-border); border-radius: 8px; background: #fff;">
      <p>您的浏览器暂不支持内嵌预览，请 <a href="/docs/my-report.pdf">点击此处下载 PDF</a> 查看。</p>
    </iframe>
  </div>
  ```
- **提供精美胶囊下载链接**：
  ```markdown
  👉 [📄 点击下载/阅读《完整报告》(PDF)](/docs/my-report.pdf)
  ```

#### 场景 B：公共资料库型 PDF（面向全站公开资料分享）
如果是公共参考资料、开源书籍、课程讲义，希望归档在博客的「资料库」栏目供所有人检索下载：
- 将文件放入 `static/docs/`；
- 在资料库管理面板登记或在 `content/resources/` 中归类，即可自动展示在全站资料库清单中。

---

### 2.5 管理多分区相册（摄影 / 日常 / 动漫 · 含拍摄日期）

全站相册页面（`/gallery/`）与首页「光影切片」共享数据源 `data/gallery.yaml`：
- **首页光影切片**：点击任意照片**直接在当前页面原地唤起全屏大图灯箱（Lightbox）**，支持键盘左右键切图与 Esc 退出，无需跳转页面。
- **相册三大分区**：`photography`（摄影）/ `daily`（日常）/ `anime`（动漫）。

#### 手动在 `data/gallery.yaml` 添加照片记录：
```yaml
- image: /images/photography/shanghai-tower.webp   # 图片访问路径
  category: photography                          # 分区：photography | daily | anime
  ratio: 1.5                                     # 图片长宽比（宽 ÷ 高），如 3:2 为 1.5
  number: "44"                                   # 唯一递增编号（双引号包裹）
  caption: '上海中心 · 暮色云端'                 # 图片标题
  date: "2026-10-02"                             # 拍摄日期（YYYY-MM-DD）
  tags: ['城市', '建筑', '夜景']                  # 标签列表
  original: /images/photography/shanghai-tower.webp # 原图访问路径
```

> 💡 **提示**：推荐使用控制台的「光影相册管理」，点选图片即可自动由系统完成比例测量、转码与 YAML 写入，免去手动操作。

---

### 2.6 从 Obsidian 发布笔记（带 attachments 附件与 WebP 转码）

Obsidian 习惯使用 `attachments/` 文件夹管理图片，博客通过 **Page Bundle** 架构完美无缝兼容：

#### 自动化发布脚本：
```bash
# 发布为长篇博文（Post）
python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/我的笔记.md"

# 发布为生活日记（Diary）
python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/今日随笔.md" --type diary

# 自定义 Slug、分类与标签
python3 scripts/publish_obsidian.py "/path/to/note.md" \
  --slug deep-learning-notes \
  --category "技术" \
  --tags "AI,深度学习,Python"
```

#### 脚本自动完成的优化工作：
1. **自动 WebP 转码**：自动调用系统 `cwebp` 将 `.png` / `.jpg` 转码为 `.webp` 并压缩，减小体积。
2. **语法智能转换**：将 `![[Pasted image.png]]` 转换为标准 Markdown，将 PDF 嵌入转换为阅读卡片，自动去除多余的双链语法。
3. **文件名防乱码**：含空格或中文的附件文件名自动净化为安全的 Web 文件名。
4. **公式与换行**：自动识别数学公式开启 KaTeX 支持，开启 `hardWraps: true` 保证排版与 Obsidian 完全一致。

---

### 2.7 发布 Jupyter Notebook（.ipynb 原生解析）

无需安装任何第三方大型依赖，直接原生支持将 Jupyter Notebook 发布为博客文章：

```bash
python3 scripts/publish_obsidian.py "/path/to/data_analysis.ipynb" \
  --slug data-analysis-lab \
  --category "数据科学" \
  --tags "Python,Pandas,Matplotlib"
```

- **代码与高亮**：提取 Python 代码单元格，支持高亮与一键复制；
- **绘图自动转码**：Matplotlib / Seaborn 渲染的 Base64 图表自动保存为 WebP 并提取为文章封面；
- **表格与终端**：Pandas DataFrame 自动转化为斑马纹表格，标准输出包装为终端样式；
- **数学公式**：LaTeX 数学符号自动通过 KaTeX 极速渲染。

---

## 3. 全站归档与分类体系

博客具备层级清晰的归档与检索导航系统（可在导航栏「归档」中直接访问）：

| 归档板块 | 访问路径 | 涵盖内容与作用 |
| :--- | :--- | :--- |
| **博文归档** | `/posts/` | 按年份时间轴清晰列出全站所有长篇技术博文与文章 |
| **博文分类** | `/categories/` | 按技术、读书、随笔等主题分类汇总文章 |
| **日记归档** | `/diary-archive/` | 专属于日记的优雅时间轴，沉淀生活的微光碎片 |
| **日记分类** | `/diary-categories/` | 日记专属分类聚合（日常生活、代码夜谈、咖啡漫步等） |
| **全站标签** | `/tags/` | 汇聚博文与日记的所有标签云，支持快速交叉检索 |

---

## 4. 本地调试与上传 GitHub 操作流程（必读命令）

日常写博客、调试样式或部署更新的标准工作流程：

### 步骤 1：本地启动预览（实时热重载）
```bash
./start.sh hugo
# 或者手动执行：
hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender
```
浏览器打开：**`http://localhost:1314/`**，修改并保存文件时浏览器会自动刷新同步。

### 步骤 2：发布前编译检查
在确认内容无误准备正式上线前，在终端执行一次编译验证：
```bash
hugo --minify
```
若输出 `Total in XX ms` 且无任何红色 Error，说明语法和路径完全正确。

### 步骤 3：提交修改并推送到 GitHub
```bash
# 1. 查看改动的文件
git status

# 2. 暂存所有变更
git add .

# 3. 提交说明
git commit -m "feat: 发布新博文与更新相册"

# 4. 推送到远程主分支
git push origin main
```
> 💡 也可直接在控制台的「🚀 部署到 GitHub」面板中单键完成上述 Git 流程。

### 步骤 4：验证线上发布
1. 访问 GitHub 仓库主页：[https://github.com/find-xin/find-xin.github.io](https://github.com/find-xin/find-xin.github.io)
2. 点击顶部的 **Actions** 标签页，查看 `Deploy Hugo site to Pages` 工作流运行状态（约 30 秒至 1 分钟）。
3. 部署成功后，访问线上博客：**[https://find-xin.github.io/](https://find-xin.github.io/)**。
   - 若未及时显示，请按 `Cmd + Shift + R` (Mac) 或 `Ctrl + F5` (Windows) 强制清除浏览器缓存刷新。

---

## 5. 常见问题与避坑提示（含 Slug 命名规范）

### 1. 关于文章 Slug（URL 路径标识）的规则与建议
Slug 是文章在网址中的“唯一英文代号”（如 `https://域名/posts/my-slug/`）：
- **禁止字符**：严禁包含 `/ \ : * ? " < > | # %` 等特殊符号及空格，禁止以点 `.` 开头；
- **同一板块内唯一**：同在文章分类下的 Slug 不能重复，防止文件冲突；
- **强烈不建议使用中文 Slug**：虽然支持中文，但分享到微信、QQ 或外部平台时，中文会被编码成很长的 `%E5%8C%97%E4%BA%AC...` 乱码；
- **最佳推荐格式**：**全小写英文字母 + 数字 + 中划线 `-`**（如 `hugo-theme-guide`、`autumn-walk-2026`）；
- **改了 Slug 会 404 吗？**：在控制台快速编辑修改 Slug 时，系统会自动写入 Hugo 的 `aliases` 别名配置，访问旧链接会自动跳转到新链接，旧链接绝不失效！

### 2. 为什么图片无法显示，提示 404？
- 检查 Markdown 中的路径是否误写了 `static/` 前缀。电脑里的 `static/images/a.webp`，在 Markdown 里面一定要写成 `/images/a.webp`；
- Linux 服务器对字母大小写严格敏感，确保路径中的大小写与实际文件名一致。

### 3. 为什么本地看得到文章，推送到 GitHub 线上却找不到？
- 检查文章 Front Matter 开头的 `draft:` 字段。处于草稿状态（`draft: true`）的文章线上会自动隐藏，发布前需改为 `draft: false`。

### 4. 如何修改网站全局信息（标题、头像、介绍等）？
- 博客全站全局参数集中在项目根目录的 **`hugo.toml`** 文件中。包括网站标题（`title`）、作者名称、头像（`avatar`）、导航菜单项、留言板 Giscus 配置等均可在此直接修改。
