# 有珠之夜 · 博客项目全景总结与 AI 协作提示词

> **文档用途**：本文档旨在全面梳理博客的技术架构、功能模块、设计哲学与开发规范。在开启新对话时，**直接复制最下方的提示词发送给新 AI**，即可让其零门槛无缝接管本博客的后续迭代开发。

---

## 目录
1. [项目概况与线上地址](#1-项目概况与线上地址)
2. [技术栈与环境架构](#2-技术栈与环境架构)
3. [全站核心功能板块详解](#3-全站核心功能板块详解)
4. [本地自动化生态与管理控制台](#4-本地自动化生态与管理控制台)
5. [样式系统与排版设计规范](#5-样式系统与排版设计规范)
6. [核心技术红线与开发约定](#6-核心技术红线与开发约定)
7. [新对话 AI 专属交接提示词（直接复制即可）](#7-新对话-ai-专属交接提示词直接复制即可)

---

## 1. 项目概况与线上地址

- **博客名称**：find-xin 的个人博客 (有珠之夜 · Type-Moon 杂志风静态博客)
- **线上站点**：[https://find-xin.github.io/](https://find-xin.github.io/)
- **GitHub 仓库**：`find-xin/find-xin.github.io`
- **本地工作区**：`/Users/xin/Desktop/youshu-night`
- **CI/CD 部署**：基于 GitHub Actions 自动化工作流（`.github/workflows/pages.yml`），向 `main` 分支执行 `git push origin main` 后约 30 秒自动完成编译并更新线上。

---

## 2. 技术栈与环境架构

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **静态博客引擎** | Hugo Extended (v0.166.0+) | 基于 Go 模板，全站生成仅耗时约 30~60 毫秒 |
| **本地服务与控制台** | Python 3 标准库（零 pip 依赖） | 纯原生 `http.server`、`json`、`subprocess`、`pathlib`，无任何外部环境依赖 |
| **系统底层支持** | macOS `sips` + `osascript` + `cwebp` | `sips` 测量物理长宽比；`osascript` 唤起原生访达；`cwebp` 转换压缩 WebP |
| **前端样式与脚本** | Hugo Pipes 管道打包 | `magzine-original.css` + `magzine-hugo.css` 合并指纹；`diary.css` 独立手记样式 |
| **数学公式与评论** | KaTeX + Giscus (GitHub Discussions) | 极速数学公式支持；基于 GitHub Discussions 的无审核评论系统 |

---

## 3. 全站核心功能板块详解

### 3.1 导航栏架构与页面划分
导航栏采用水平排版，包含 8 个核心入口：
**首页 ｜ 文章 ｜ 日记 ｜ 归档 ｜ 相册 ｜ 资料库 ｜ 友链 ｜ 留言**

### 3.2 各功能页面设计规范
1. **首页 (`/`) (`layouts/index.html`)**：
   - **英雄名片 (Hero Card)**：全屏星空动态粒子背景、久远寺有珠立绘、作者头像、社交与 RSS 链接；
   - **最新文章**：杂志排版卡片流，直通 `/posts/` 文章专页；
   - **生活微光**：日记卡片，直通 `/diary/` 日记专页；
   - **光影切片**：**原地呼出全屏 Lightbox（灯箱）大图**，可查看拍摄日期、分类、标签与配文，无需跳转页面。
2. **专属文章专页 (`/posts/`) (`layouts/posts/list.html`)**：
   - 专属头部：`ARTICLES · 深度博文`、文章总数徽章、时间轴归档直达链接；
   - **分类即时筛选工具栏**：支持 `✨ 全部` 及各分类标签，纯前端零重载即时切换；
   - **杂志质感卡片流**：高清封面（悬停微缩放）、分类文字、置顶徽标、摘要、字数/阅读时长、统一格式发布时间。
3. **专属日记专页 (`/diary/`) (`layouts/diary/list.html`)**：
   - 专属生活手记流，支持标签过滤、小红书双列/三列瀑布流排版、心情/天气徽标、初始点赞爱心交互。
4. **全站归档体系 (`/archive/`) (`layouts/_default/list.html`)**：
   - 顶部 5 大维度 Tab 切换：
     - **文章归档 (`/archive/`)**：按年份时间轴沉淀长篇博文；
     - **日记归档 (`/diary-archive/`)**：按年份时间轴沉淀生活碎片；
     - **文章分类 (`/categories/`)**：博文主题分类网格；
     - **日记分类 (`/diary_categories/`)**：日记专属分类网格；
     - **全站标签 (`/tags/`)**：文章与日记标签云聚合。
   - **分类文字排版**：日记归档与文章归档的分类全部统一为 **黑色/深色纯文本样式**（无胶囊背景、无边框、无红字），悬停优雅下划线。
5. **光影相册 (`/gallery/`) (`layouts/gallery/list.html`, `data/gallery.yaml`)**：
   - 三大分类：动漫插画 (`anime`)、摄影大片 (`photography`)、生活日常 (`daily`)；
   - 每张照片均包含：图片路径、拍摄日期 (`date`)、全局序号 (`number`)、精确长宽比 (`ratio`)、配文与标签；
   - 全屏沉浸式灯箱：支持键盘左右翻页、Esc 退出、触控手势及原图入口。
6. **知识资料库 (`/resources/`)**：
   - 集中展示与管理供读者下载的 PDF 报告、学术论文、代码压缩包，修复了顶部标题对齐遮挡问题。
7. **单篇阅读页通用能力**：
   - 悬浮可折叠目录导航（TOC）；
   - 正文内嵌 PDF 阅读器与胶囊下载按钮（`pdf: "..."`）；
   - **文末尾栏**：点赞爱心居中，最后更新时间淡雅右对齐（极简现代风，省空间）；
   - 作者名片、延伸阅读推荐、相邻文章导航、Giscus 留言板。

---

## 4. 本地自动化生态与管理控制台

本项目内置完整的本地管理与发布系统，日常管理无需依赖复杂命令：

### 4.1 启动方式
1. **macOS 桌面双击（最推荐）**：双击根目录下的 **`启动博客控制台.command`**，自动拉起服务并在默认浏览器打开后台。
2. **终端服务脚本 (`start.sh`)**：
   - `./start.sh`：全套启动（Hugo 本地预览端口 1314 + 管理控制台端口 2026）
   - `./start.sh hugo` / `./start.sh dash`：单项启动
   - `./start.sh status`：查看服务运行状态与端口
   - `./start.sh stop`：一键清理停止所有相关后台进程
3. **原生命令行**：`python3 scripts/dashboard.py`（访问 `http://localhost:2026/`）。

### 4.2 控制台六大核心能力 (`scripts/dashboard.py`)
1. **文章与日记发布**：支持选择电脑 Markdown 笔记、Obsidian 笔记及 Jupyter Notebook（`.ipynb`）。
2. **文章管理与快速编辑**：
   - 支持在线快速修改分类、标签、摘要及 **URL 标识 (Slug)**；
   - **Slug 平滑重命名与防 404 保障**：修改 Slug 后后台自动重命名文件/目录，并**自动在 Front Matter 写入 `aliases: ['/posts/old-slug/']` 别名重定向**，旧链接绝不失效；
   - **时间保护**：仅修改标签时不篡改正文更新时间。
3. **光影相册 Studio**：上传本地图片，自动调用 macOS `sips` 计算长宽比、转码为 WebP、递增编号、写入拍摄日期与 `data/gallery.yaml`。
4. **资料库管理**：管理上传公开 PDF 与附件资产。
5. **一键 Git 部署**：状态检测，自定义 Commit Message，单键执行 `git add`、`commit` 与 `push origin main`。
6. **Hugo 服务启停**：后台一键启停 1314 预览服务。

### 4.3 笔记发布转换引擎 (`scripts/publish_obsidian.py`)
- **Obsidian 支持**：精准抽取 `attachments/` 附件，自动调用 `cwebp` 转换为高质量 WebP；自动剥离 `![[...]]` 双链转为标准 Markdown；自动适配 KaTeX 公式与硬换行。
- **Jupyter Notebook 原生支持**：无需安装 `jupyter` 或 `nbconvert`，原生解析代码块高亮、Pandas 斑马纹表格、Base64 绘图转 WebP 并提取为封面。

---

## 5. 样式系统与排版设计规范

### 5.1 统一时间字体规范（绝对红线）
全站所有日期与时间元素（包括文章发布时间、文末更新时间、日记卡片时间、相册拍摄日期、归档时间轴日期、搜索结果日期、资料库日期等），**全部统一使用系统标准无衬线字体**：
```css
time,
.post-date,
.article-date,
.archive-date,
.diary-card-date,
.home-diary-meta time,
.album-card-date,
.spotlight-item-date,
.res-date,
.related-card-date,
.posts-card-date,
.post-updated-notice,
.diary-lastmod-text {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif !important;
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
}
```
> ⚠️ **严禁**在任何日期元素上使用等宽代码字体（`monospace` / `var(--mono)`）或衬线字体。

### 5.2 归档分类链接样式规范
归档页面中的分类文字统一使用纯净文本链接（`.archive-cat-link`）：
- **深色模式/浅色模式自适应**：浅色模式下为深黑字，深色模式下为浅灰白字；
- **禁止使用胶囊背景**：`background: none; padding: 0; border: none; border-radius: 0;`；
- **禁止标红**：移除针对日记分类的红色高亮，二者完全统一。

---

## 6. 核心技术红线与开发约定

1. **Python 脚本零外部 pip 依赖**：所有后台扩展必须使用 Python 3 标准库（`http.server`、`json`、`subprocess`、`pathlib`）以及 macOS 系统级原生工具（`sips`、`osascript`、`cwebp`），严禁要求用户安装外部 pip 依赖或创建虚拟环境。
2. **路径规范**：电脑物理路径为 `static/images/...` 的文件，在 Markdown / 模板中引用时**绝对不能包含 `static`**，必须以绝对路径 `/images/...` 开头。
3. **Slug 命名规范**：推荐使用全小写英文字母、数字和短横线 `-`（如 `my-post-name`）。禁止包含特殊字符与空格，避免中文乱码。
4. **构建前自检**：任何改动后必须运行 `hugo --minify` 确保 0 报错，耗时保持在毫秒级。

---

## 7. 新对话 AI 专属交接提示词（直接复制即可）

```markdown
你现在是该静态博客项目的资深前端与系统维护工程师。请仔细阅读以下博客的完整架构与技术规范，在此基准上承接我接下来的开发和完善需求：

### 1. 项目基础信息
- 站点类型：基于 Hugo Extended 构建的高性能个人静态博客（杂志风 + 型月夜间美学）。
- 本地工作目录：/Users/xin/Desktop/youshu-night
- 线上部署：GitHub Pages (find-xin.github.io)，由 GitHub Actions 监听 main 分支自动编译发布。
- 本地环境：macOS，全局 Hugo，Python 3 原生标准库（零第三方 pip 依赖，无虚拟环境）。

### 2. 页面与架构布局
- 导航栏（8个入口）：首页 ｜ 文章 ｜ 日记 ｜ 归档 ｜ 相册 ｜ 资料库 ｜ 友链 ｜ 留言
- 首页 (/)：英雄名片卡、最新文章流、生活微光日记、光影切片（原地唤起全屏灯箱，无需跳转）。
- 文章专页 (/posts/)：专属长篇博文列表，具备纯前端分类即时过滤栏、阅读统计、杂志质感卡片。
- 日记专页 (/diary/)：专属生活手记，标签过滤、小红书瀑布流排版、心情徽标、点赞互动。
- 归档体系 (/archive/)：包含文章归档时间轴、日记归档时间轴 (/diary-archive/)、文章分类、日记分类及全站标签云。分类排版均为纯文本链接（深色/浅色自适应，无胶囊无背景）。
- 相册专页 (/gallery/)：摄影/日常/动漫三分区，YAML 驱动，带拍摄日期、长宽比、全屏灯箱。
- 资料库 (/resources/)：公开 PDF 与学术资料下载预览。

### 3. 本地管理与自动化生态
- 启动入口：根目录双击「启动博客控制台.command」或终端执行「./start.sh」（支持 hugo / dash / status / stop / restart）。
- 控制台系统 (scripts/dashboard.py)：端口 2026，原生 Python 实现，支持文章/日记全生命周期管理、快速编辑（修改 Slug 会自动平滑重命名并向 Front Matter 写入 aliases 别名重定向防 404）、相册 Studio（macOS sips 自动算长宽比、cwebp 转码并安全写入 YAML）、资料库管理与 Git 一键推送。
- 发布转换脚本 (scripts/publish_obsidian.py)：原生支持 Obsidian 笔记（附件抽取、WebP 转码、双链转换、KaTeX 公式）及 Jupyter Notebook (.ipynb 原生解析代码、输出、表格与 Base64 绘图转码)。

### 4. 样式与工程红线
- 统一时间字体：全站所有日期与时间元素（文章发布/更新时间、日记卡片时间、相册拍摄日期、归档时间轴、搜索等），统一使用系统无衬线字体（-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif），严格禁止在日期上滥用等宽代码字体 (monospace) 或衬线体。
- 归档分类样式：日记与文章分类在归档中保持一致的纯文本无胶囊样式。
- 零 pip 依赖：所有 Python 脚本保持仅依赖 Python 3 标准库，不增加系统负担。
- 静态资源路径：static/ 目录下的文件在 Markdown 中引用一律以 / 开头，不得带有 static/ 前缀。

请确认你已完全掌握上述架构、文件分布与代码规范。确认后请简短回应，我将向你下达具体的修改需求。
```
