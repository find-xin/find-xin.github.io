#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_obsidian.py - 一键管理与发布 Obsidian 笔记与附件到 Hugo 博客

功能：
1. 【自动发布】将 Obsidian 笔记转换为 Hugo 页面包（Page Bundle）架构：
   - 自动转换 Obsidian 双链语法（![[...]]）为标准 Markdown 链接。
   - 自动将所有引用的图片（PNG、JPG、JPEG 等）转换为高质量 .webp 格式并压缩。
   - 自动净化文件名（去除空格与特殊字符，杜绝网络 404）。
   - 智能生成 Front Matter，自动检测 KaTeX 数学公式（math: true），避免顶部裁切重复（hideCover: true）。
2. 【文章管理】支持快速下架（草稿）、重新上架、删除及查看全站文章列表：
   - --list                : 列出当前全站所有博文与日记的状态
   - --unpublish <关键词>  : 下架文章（转为草稿 draft: true）
   - --publish <关键词>    : 重新上架文章（draft: false）
   - --delete <关键词>     : 彻底删除指定文章及其关联附件目录

用法示例：
  # 发布博文
  python3 scripts/publish_obsidian.py "/Users/xin/Desktop/Notes/久远寺有珠.md"
  python3 scripts/publish_obsidian.py "/path/to/note.md" --slug kuonji-alice --category "型月" --tags "魔法使之夜,有珠"

  # 发布日记
  python3 scripts/publish_obsidian.py "/Users/xin/Desktop/Notes/随手记.md" --type diary

  # 管理文章
  python3 scripts/publish_obsidian.py --list
  python3 scripts/publish_obsidian.py --unpublish "久远寺有珠"
  python3 scripts/publish_obsidian.py --delete "note-202610021513"
"""

from __future__ import annotations
import os
import sys
import re
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# 支持的图片与文档扩展名
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.bmp', '.tiff'}
DOC_EXTENSIONS = {'.pdf', '.zip', '.tar', '.gz', '.mp4', '.mp3'}

BLOG_ROOT = Path(__file__).resolve().parent.parent

def sanitize_filename(name: str) -> str:
    """将含空格或特殊字符的文件名转为 Web 友好的名称"""
    clean = re.sub(r'[^\w\.\-\u4e00-\u9fa5]', '-', name.strip())
    clean = re.sub(r'-+', '-', clean)
    return clean

def sanitize_slug(text: str) -> str:
    """为文章目录生成干净的英文字符串"""
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '-', text.lower().strip())
    clean = re.sub(r'-+', '-', clean).strip('-')
    if not clean or len(clean) < 2:
        clean = f"note-{datetime.now().strftime('%Y%m%d%H%M')}"
    return clean

def parse_frontmatter(content: str):
    """解析文章头部的 Front Matter"""
    frontmatter_dict = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].lstrip('\n')
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    frontmatter_dict[key] = val
    return frontmatter_dict, body

def find_attachment_file(md_dir: Path, filename: str) -> Path | None:
    """在当前目录及其 attachments 搜索附件文件"""
    candidates = [
        md_dir / "attachments" / filename,
        md_dir / filename,
        md_dir.parent / "attachments" / filename,
    ]
    for c in candidates:
        if c.is_file():
            return c
    for folder in [md_dir / "attachments", md_dir, md_dir.parent / "attachments"]:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.name.lower() == filename.lower():
                    return item
    return None

def convert_to_webp_if_possible(src_file: Path, dest_dir: Path, base_clean_name: str) -> str:
    """
    尝试使用 cwebp 或系统工具将图片转换为 .webp 格式。
    若成功，返回目标 webp 文件名；若不支持，复制原格式并返回原文件名。
    """
    ext = src_file.suffix.lower()
    clean_stem = Path(base_clean_name).stem
    dest_webp_name = f"{clean_stem}.webp"
    dest_webp_path = dest_dir / dest_webp_name

    # 本身已经是 webp 或矢量 svg/动图 gif，直接拷贝
    if ext in {'.webp', '.svg', '.gif'}:
        final_dest = dest_dir / base_clean_name
        shutil.copy2(src_file, final_dest)
        return base_clean_name

    # 尝试使用 cwebp 转换
    cwebp_bin = shutil.which('cwebp')
    if cwebp_bin:
        try:
            res = subprocess.run(
                [cwebp_bin, '-q', '85', str(src_file), '-o', str(dest_webp_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if res.returncode == 0 and dest_webp_path.exists():
                return dest_webp_name
        except Exception:
            pass

    # 转换失败或无 cwebp，回退为普通拷贝
    fallback_dest = dest_dir / base_clean_name
    shutil.copy2(src_file, fallback_dest)
    return base_clean_name

def get_all_articles():
    """获取全站所有文章与日记结构化数据"""
    posts_dir = BLOG_ROOT / 'content' / 'posts'
    diaries_dir = BLOG_ROOT / 'content' / 'diary'

    entries = []
    for base_dir, type_key, type_label in [(posts_dir, 'post', '文章'), (diaries_dir, 'diary', '日记')]:
        if not base_dir.exists():
            continue
        for item in sorted(base_dir.iterdir(), reverse=True):
            if item.name.startswith(('.', '_')):
                continue
            md_path = item / 'index.md' if item.is_dir() else item
            if not md_path.exists() or md_path.suffix != '.md':
                continue
            
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            fm, _ = parse_frontmatter(content)
            title = fm.get('title', item.stem)
            draft = fm.get('draft', 'false').lower() == 'true'
            date = fm.get('date', '未知日期')[:10]
            cover = fm.get('cover', '')
            if cover and not cover.startswith('/') and not cover.startswith('http'):
                cover = f"/{'posts' if type_key == 'post' else 'diary'}/{item.stem}/{cover}"

            entries.append({
                'type': type_key,
                'type_label': type_label,
                'slug': item.stem,
                'title': title,
                'draft': draft,
                'date': date,
                'cover': cover,
                'url': f"/{'posts' if type_key == 'post' else 'diary'}/{item.stem}/",
                'path': str(item.relative_to(BLOG_ROOT))
            })
    return entries

def list_all_articles():
    """列出全站所有文章与日记状态"""
    entries = get_all_articles()
    print("\n📚 全站内容管理列表：")
    print(f"{'类型':<6} {'状态':<8} {'日期':<12} {'Slug / 标识':<22} {'标题'}")
    print("-" * 75)
    for e in entries:
        status_tag = "🟡 已下架" if e['draft'] else "🟢 正常"
        print(f"{e['type_label']:<6} {status_tag:<8} {e['date']:<12} {e['slug']:<22} {e['title']}")
    print(f"\n共找到 {len(entries)} 篇文章/日记。\n")

def find_target_item(keyword: str):
    """根据关键词在 content/posts 和 content/diary 中查找匹配的文章"""
    keyword_clean = keyword.strip().lower()
    posts_dir = BLOG_ROOT / 'content' / 'posts'
    diaries_dir = BLOG_ROOT / 'content' / 'diary'

    for base_dir in [posts_dir, diaries_dir]:
        if not base_dir.exists():
            continue
        for item in base_dir.iterdir():
            if item.name.startswith(('.', '_')):
                continue
            md_path = item / 'index.md' if item.is_dir() else item
            if not md_path.exists() or md_path.suffix != '.md':
                continue
            
            # 匹配 slug
            if keyword_clean in item.name.lower():
                return item, md_path
            
            # 匹配 title
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                fm, _ = parse_frontmatter(content)
                if keyword_clean in fm.get('title', '').lower():
                    return item, md_path
            except Exception:
                pass
    return None, None

def set_draft_status(keyword: str, set_draft: bool):
    """下架（设为草稿）或重新上架文章"""
    target_item, md_path = find_target_item(keyword)
    if not target_item or not md_path:
        print(f"❌ 未找到匹配文章：'{keyword}'。你可以使用 python3 scripts/publish_obsidian.py --list 查看所有文章。")
        return False

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    action_label = "下架（转为草稿）" if set_draft else "重新上架"
    draft_val = "true" if set_draft else "false"

    if 'draft:' in content:
        new_content = re.sub(r'draft:\s*(true|false)', f'draft: {draft_val}', content)
    else:
        new_content = content.replace('---\n', f'---\ndraft: {draft_val}\n', 1)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✅ 成功{action_label}：{target_item.name}")
    print(f"📄 文件路径：{md_path.relative_to(BLOG_ROOT)}")
    print(f"👉 记得提交并推送到 GitHub 线上生效：")
    print(f"   git add {target_item.relative_to(BLOG_ROOT)}")
    print(f"   git commit -m \"chore: {action_label}文章 {target_item.name}\"")
    print(f"   git push origin main\n")
    return True

def delete_article(keyword: str):
    """彻底删除文章及其附件文件夹"""
    target_item, md_path = find_target_item(keyword)
    if not target_item:
        print(f"❌ 未找到匹配文章：'{keyword}'。你可以使用 python3 scripts/publish_obsidian.py --list 查看所有文章。")
        return False

    rel_path = target_item.relative_to(BLOG_ROOT)
    if target_item.is_dir():
        shutil.rmtree(target_item)
    else:
        target_item.unlink()

    print(f"\n🗑️ 成功删除文章：{target_item.name}")
    print(f"📁 已清理路径：{rel_path}")
    print(f"👉 记得同步删除到 GitHub 仓库：")
    print(f"   git add -A")
    print(f"   git commit -m \"chore: 删除文章 {target_item.name}\"")
    print(f"   git push origin main\n")
    return True

CALLOUT_ICONS = {
    'note': ('📌', 'Note', 'callout-note'),
    'info': ('ℹ️', 'Info', 'callout-info'),
    'tip': ('💡', 'Tip', 'callout-tip'),
    'hint': ('💡', 'Hint', 'callout-tip'),
    'important': ('✨', 'Important', 'callout-important'),
    'warning': ('⚠️', 'Warning', 'callout-warning'),
    'caution': ('⚠️', 'Caution', 'callout-warning'),
    'danger': ('🚨', 'Danger', 'callout-danger'),
    'error': ('🚨', 'Error', 'callout-danger'),
    'quote': ('💬', 'Quote', 'callout-quote'),
    'cite': ('💬', 'Cite', 'callout-quote'),
    'example': ('🔮', 'Example', 'callout-example'),
    'question': ('❓', 'Question', 'callout-question'),
    'faq': ('❓', 'FAQ', 'callout-question'),
    'todo': ('📝', 'Todo', 'callout-todo'),
    'summary': ('📋', 'Summary', 'callout-summary'),
    'abstract': ('📋', 'Abstract', 'callout-summary'),
}

def convert_obsidian_callouts(text: str) -> str:
    """将 Obsidian > [!note] Callout 语法转换为语义化 HTML 卡片"""
    lines = text.split('\n')
    result = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        m = re.match(r'^>\s*\[!([a-zA-Z0-9_-]+)\]([+-]?)(?:\s+(.*))?$', line)
        if m:
            c_type = m.group(1).lower()
            c_collapse = m.group(2)
            c_title = (m.group(3) or '').strip()
            icon, default_title, c_class = CALLOUT_ICONS.get(c_type, ('📌', c_type.capitalize(), 'callout-note'))
            final_title = c_title if c_title else default_title

            body_lines = []
            i += 1
            while i < n and (lines[i].startswith('>') or lines[i].strip() == ''):
                if re.match(r'^>\s*\[!([a-zA-Z0-9_-]+)\]', lines[i]):
                    break
                clean_l = re.sub(r'^>\s?', '', lines[i])
                body_lines.append(clean_l)
                i += 1

            callout_body = '\n'.join(body_lines).strip()

            if c_collapse == '-':
                callout_html = (
                    f'<details class="obsidian-callout {c_class}">\n'
                    f'  <summary class="callout-header"><span class="callout-icon">{icon}</span><span class="callout-title">{final_title}</span></summary>\n'
                    f'  <div class="callout-body">\n\n{callout_body}\n\n  </div>\n'
                    f'</details>'
                )
            else:
                callout_html = (
                    f'<div class="obsidian-callout {c_class}">\n'
                    f'  <div class="callout-header"><span class="callout-icon">{icon}</span><span class="callout-title">{final_title}</span></div>\n'
                    f'  <div class="callout-body">\n\n{callout_body}\n\n  </div>\n'
                    f'</div>'
                )
            result.append(callout_html)
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)

def process_obsidian_note(md_path: Path, note_type: str, custom_slug: str | None, tags: list[str], category: str | None, draft: bool):
    if not md_path.exists():
        print(f"❌ 错误：找不到文件 {md_path}")
        return False

    with open(md_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    md_dir = md_path.parent
    base_name = md_path.stem

    fm, body = parse_frontmatter(raw_content)

    # 1. 确定标题
    title = fm.get('title')
    if not title:
        h1_match = re.search(r'^#\s+(.+)$', body, flags=re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
            body = re.sub(r'^#\s+.+\n?', '', body, count=1, flags=re.MULTILINE)
        else:
            title = base_name

    # 2. 确定日期
    date_str = fm.get('date')
    if not date_str:
        mtime = datetime.fromtimestamp(md_path.stat().st_mtime)
        date_str = mtime.strftime('%Y-%m-%dT%H:%M:%S+08:00')

    # 3. 确定目标目录 slug
    slug = custom_slug or fm.get('slug') or sanitize_slug(base_name)
    
    if note_type == 'diary':
        target_dir = BLOG_ROOT / 'content' / 'diary' / slug
    else:
        target_dir = BLOG_ROOT / 'content' / 'posts' / slug

    target_attachments_dir = target_dir / 'attachments'
    target_attachments_dir.mkdir(parents=True, exist_ok=True)

    copied_files = set()
    first_image_path = None

    # 4. 转换 Obsidian WikiLinks 语法 ![[filename|alt]]
    def replace_wikilink(match):
        nonlocal first_image_path
        inner = match.group(1).strip()
        parts = inner.split('|', 1)
        link_target = parts[0].strip()
        alt_text = parts[1].strip() if len(parts) > 1 else ""

        clean_target_name = Path(link_target).name
        ext = Path(clean_target_name).suffix.lower()

        actual_file = find_attachment_file(md_dir, clean_target_name)
        safe_name = sanitize_filename(clean_target_name)

        final_file_name = safe_name
        if actual_file:
            if ext in IMAGE_EXTENSIONS:
                final_file_name = convert_to_webp_if_possible(actual_file, target_attachments_dir, safe_name)
            else:
                dest = target_attachments_dir / safe_name
                shutil.copy2(actual_file, dest)
            copied_files.add(final_file_name)

        rel_dest = f"attachments/{final_file_name}"

        if ext in IMAGE_EXTENSIONS:
            if not first_image_path:
                first_image_path = rel_dest
            label = alt_text or Path(clean_target_name).stem
            return f"![{label}]({rel_dest})"
        elif ext in DOC_EXTENSIONS:
            label = alt_text or clean_target_name
            return f"[📄 查看文档 {label}]({rel_dest})"
        else:
            return f"[{alt_text or clean_target_name}]({rel_dest})"

    new_body = re.sub(r'!\[\[(.*?)\]\]', replace_wikilink, body)

    # 转换内部双链 [[笔记名|别名]] 或 [[笔记名]]
    def replace_page_link(match):
        inner = match.group(1).strip()
        parts = inner.split('|', 1)
        return parts[1].strip() if len(parts) > 1 else parts[0].strip()

    new_body = re.sub(r'\[\[(.*?)\]\]', replace_page_link, new_body)

    # 5. 转换已有标准 Markdown 图片语法：![](attachments/xxx) 或 ![](./attachments/xxx)
    def replace_std_markdown_link(match):
        nonlocal first_image_path
        alt = match.group(1)
        link = match.group(2)
        if "attachments/" in link:
            clean_target_name = Path(link.split("attachments/", 1)[1]).name
            import urllib.parse
            clean_target_name = urllib.parse.unquote(clean_target_name)
            ext = Path(clean_target_name).suffix.lower()
            
            actual_file = find_attachment_file(md_dir, clean_target_name)
            safe_name = sanitize_filename(clean_target_name)
            final_file_name = safe_name
            if actual_file:
                if ext in IMAGE_EXTENSIONS:
                    final_file_name = convert_to_webp_if_possible(actual_file, target_attachments_dir, safe_name)
                else:
                    dest = target_attachments_dir / safe_name
                    shutil.copy2(actual_file, dest)
                copied_files.add(final_file_name)
            
            rel_dest = f"attachments/{final_file_name}"
            if not first_image_path:
                first_image_path = rel_dest
            return f"![{alt}]({rel_dest})"
        return match.group(0)

    new_body = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_std_markdown_link, new_body)

    # 5.5. 转换 Obsidian 文本高亮 ==内容== 为 HTML <mark>内容</mark>
    new_body = re.sub(r'==([^=\n]+?)==', r'<mark>\1</mark>', new_body)

    # 5.6. 转换 Obsidian Callout 标注块
    new_body = convert_obsidian_callouts(new_body)

    # 6. 生成 Front Matter
    final_cover = fm.get('cover')
    if not final_cover and first_image_path:
        final_cover = first_image_path

    out_fm = ["---"]
    out_fm.append(f"title: '{title}'")
    out_fm.append(f"date: {date_str}")
    out_fm.append(f"draft: {'true' if draft else 'false'}")

    if note_type == 'diary':
        mood = fm.get('mood') or fm.get('weather') or '惬意'
        out_fm.append(f"mood: '{mood}'")
        if 'location' in fm:
            out_fm.append(f"location: '{fm['location']}'")
        if final_cover:
            out_fm.append(f"cover: '{final_cover}'")
        cur_tags = tags or (fm.get('tags', '').strip('[]').split(',') if 'tags' in fm else ['生活', '手记'])
        cur_tags = [t.strip().strip("'\"") for t in cur_tags if t.strip()]
        out_fm.append(f"tags: {cur_tags}")
        out_fm.append(f"likes: {fm.get('likes', 5)}")
    else:
        # 智能提取摘要：跳过图片与空行，提取首段纯文字
        summary = fm.get('summary')
        if not summary:
            clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', new_body)
            clean_text = re.sub(r'<[^>]+>', '', clean_text)
            clean_text = re.sub(r'\[.*?\]\(.*?\)', '', clean_text)
            clean_text = re.sub(r'[#*`$\\]', '', clean_text)
            for line in clean_text.splitlines():
                line = line.strip()
                if line and len(line) >= 2:
                    summary = line[:80].replace("'", "")
                    break
        if summary:
            out_fm.append(f"summary: '{summary}'")
        
        if final_cover:
            out_fm.append(f"cover: '{final_cover}'")
            # 若正文中已包含该图片，隐藏文章顶部冗余的 400px 裁切横幅，保持 Obsidian 原生自然排版
            if final_cover in new_body or 'attachments/' in new_body:
                out_fm.append("hideCover: true")
        
        out_fm.append("pinned: false")

        if '$' in new_body:
            out_fm.append("math: true")
        
        cur_cat = category or fm.get('categories') or '随笔'
        if isinstance(cur_cat, str):
            cur_cat = [c.strip().strip("'\"") for c in cur_cat.strip('[]').split(',') if c.strip()]
        out_fm.append(f"categories: {cur_cat}")

        cur_tags = tags or (fm.get('tags', '').strip('[]').split(',') if 'tags' in fm else ['Obsidian'])
        cur_tags = [t.strip().strip("'\"") for t in cur_tags if t.strip()]
        out_fm.append(f"tags: {cur_tags}")

    out_fm.append("---\n")

    # 7. 写入最终 index.md
    target_md = target_dir / 'index.md'
    with open(target_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_fm))
        f.write('\n' + new_body.lstrip('\n'))

    print(f"\n🎉 成功发布 Obsidian 笔记！")
    print(f"📁 目标目录：{target_dir.relative_to(BLOG_ROOT)}")
    print(f"📄 文章入口：{target_md.relative_to(BLOG_ROOT)}")
    print(f"🖼️ 提取附件：{len(copied_files)} 个")
    for f in sorted(copied_files):
        print(f"   └── attachments/{f}")
    if final_cover:
        print(f"🎨 自动封面：{final_cover}")
    
    print("\n👉 下一步操作建议：")
    print("1. 本地启动预览：hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender")
    print("2. 提交并推送到 GitHub：")
    print(f"   git add {target_dir.relative_to(BLOG_ROOT)}")
    print(f"   git commit -m \"feat: 发布《{title}》\"")
    print("   git push origin main\n")
    return True

def process_ipynb_notebook(ipynb_path: Path, note_type: str, custom_slug: str | None, tags: list[str], category: str | None, draft: bool):
    import json
    import base64

    if not ipynb_path.exists():
        print(f"❌ 错误：找不到文件 {ipynb_path}")
        return False

    with open(ipynb_path, 'r', encoding='utf-8') as f:
        try:
            nb_data = json.load(f)
        except Exception as e:
            print(f"❌ 解析 .ipynb JSON 失败：{e}")
            return False

    base_name = ipynb_path.stem
    slug = custom_slug or sanitize_slug(base_name)

    if note_type == 'diary':
        target_dir = BLOG_ROOT / 'content' / 'diary' / slug
    else:
        target_dir = BLOG_ROOT / 'content' / 'posts' / slug

    target_attachments_dir = target_dir / 'attachments'
    target_attachments_dir.mkdir(parents=True, exist_ok=True)

    cells = nb_data.get("cells", [])
    body_parts = []
    first_title = None
    first_image_path = None
    has_math = False
    img_counter = 0

    for i, cell in enumerate(cells):
        ctype = cell.get("cell_type")
        source = "".join(cell.get("source", []))
        
        if ctype == "markdown":
            if "$" in source:
                has_math = True
            if not first_title:
                h1_match = re.search(r"^#\s+(.+)$", source, flags=re.MULTILINE)
                if h1_match:
                    first_title = h1_match.group(1).strip()
                    source = re.sub(r"^#\s+.+\n?", "", source, count=1, flags=re.MULTILINE)
            
            # 处理单元格内部嵌入的附件 (attachment:name)
            if "attachments" in cell:
                for att_name, att_data in cell["attachments"].items():
                    for mime, b64 in att_data.items():
                        raw_bytes = base64.b64decode(b64)
                        safe_att = sanitize_filename(att_name)
                        tmp_path = target_attachments_dir / safe_att
                        tmp_path.write_bytes(raw_bytes)
                        final_att = convert_to_webp_if_possible(tmp_path, target_attachments_dir, safe_att)
                        source = source.replace(f"attachment:{att_name}", f"attachments/{final_att}")
            
            body_parts.append(source.strip())

        elif ctype == "code":
            if not source.strip():
                continue
            body_parts.append(f"```python\n{source.strip()}\n```")
            
            outputs = cell.get("outputs", [])
            for out in outputs:
                otype = out.get("output_type")
                if otype == "stream":
                    text = "".join(out.get("text", [])).strip()
                    if text:
                        body_parts.append(f"<div class=\"notebook-output-block\">\n{text}\n</div>")
                elif otype in ("display_data", "execute_result"):
                    data = out.get("data", {})
                    # 图表输出（Matplotlib / Seaborn / Plotly）
                    if "image/png" in data or "image/jpeg" in data:
                        img_counter += 1
                        mime = "image/png" if "image/png" in data else "image/jpeg"
                        ext = ".png" if mime == "image/png" else ".jpg"
                        b64_data = data[mime]
                        raw_bytes = base64.b64decode(b64_data)
                        
                        out_name = f"plot-cell-{i+1}-{img_counter}{ext}"
                        out_path = target_attachments_dir / out_name
                        out_path.write_bytes(raw_bytes)
                        
                        final_name = convert_to_webp_if_possible(out_path, target_attachments_dir, out_name)
                        rel_img = f"attachments/{final_name}"
                        if not first_image_path:
                            first_image_path = rel_img
                        body_parts.append(f"![图表输出]({rel_img})")
                    elif "text/html" in data:
                        html_table = "".join(data["text/html"]).strip()
                        body_parts.append(f"<div class=\"notebook-table\">\n{html_table}\n</div>")
                    elif "text/plain" in data:
                        text = "".join(data["text/plain"]).strip()
                        if text and not text.startswith("<Figure"):
                            body_parts.append(f"<div class=\"notebook-output-block\">\n{text}\n</div>")
                elif otype == "error":
                    tb = "\n".join(out.get("traceback", []))
                    clean_tb = re.sub(r"\x1b\[[0-9;]*m", "", tb).strip()
                    if clean_tb:
                        body_parts.append(f"<div class=\"notebook-output-block\" style=\"border-left-color: #ff4757;\">\n{clean_tb}\n</div>")

    title = first_title or base_name
    mtime = datetime.fromtimestamp(ipynb_path.stat().st_mtime)
    date_str = mtime.strftime('%Y-%m-%dT%H:%M:%S+08:00')

    new_body = "\n\n".join(body_parts)

    out_fm = ["---"]
    out_fm.append(f"title: '{title}'")
    out_fm.append(f"date: {date_str}")
    out_fm.append(f"draft: {'true' if draft else 'false'}")
    
    clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', new_body)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    clean_text = re.sub(r'[#*`$\\]', '', clean_text)
    summary = ""
    for line in clean_text.splitlines():
        line = line.strip()
        if line and len(line) >= 4 and not line.startswith("import") and not line.startswith("from"):
            summary = line[:80].replace("'", "")
            break
    if summary:
        out_fm.append(f"summary: '{summary}'")

    if first_image_path:
        out_fm.append(f"cover: '{first_image_path}'")
        out_fm.append("hideCover: true")

    out_fm.append("pinned: false")
    if has_math or '$' in new_body:
        out_fm.append("math: true")

    cur_cat = category or '数据科学'
    out_fm.append(f"categories: {['Jupyter', cur_cat]}")

    cur_tags = tags or ['Jupyter', 'Python', '数据分析']
    out_fm.append(f"tags: {cur_tags}")
    out_fm.append("---\n")

    target_md = target_dir / 'index.md'
    with open(target_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_fm))
        f.write('\n' + new_body.lstrip('\n'))

    print(f"\n🎉 成功将 Jupyter Notebook (.ipynb) 发布为 Hugo 页面！")
    print(f"📁 目标目录：{target_dir.relative_to(BLOG_ROOT)}")
    print(f"📄 文章入口：{target_md.relative_to(BLOG_ROOT)}")
    print(f"🖼️ 提取图表：{img_counter} 个并自动转为 WebP")
    if first_image_path:
        print(f"🎨 自动封面：{first_image_path}")

    print("\n👉 下一步操作建议：")
    print("1. 本地启动预览：hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender")
    print("2. 提交并推送到 GitHub：")
    print(f"   git add {target_dir.relative_to(BLOG_ROOT)}")
    print(f"   git commit -m \"feat: 发布 Notebook《{title}》\"")
    print("   git push origin main\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="一键管理与发布 Markdown (.md) 与 Jupyter Notebook (.ipynb) 到 Hugo 博客")
    parser.add_argument("file", nargs="?", help="笔记文件路径（支持 .md 或 .ipynb）")
    parser.add_argument("--type", choices=['post', 'diary'], default='post', help="发布类型：post（博文长文）或 diary（微光日记，默认 post）")
    parser.add_argument("--slug", help="指定的英文文件夹别名（若不指定则自动根据标题生成）")
    parser.add_argument("--category", help="博文分类，例如 '技术'、'机器学习'")
    parser.add_argument("--tags", help="标签列表（逗号分隔），例如 'Python,Jupyter,数据分析'")
    parser.add_argument("--draft", action="store_true", help="是否保存为草稿（默认直接发布 draft: false）")
    parser.add_argument("--list", action="store_true", help="列出全站所有文章/日记及其发布状态")
    parser.add_argument("--unpublish", help="下架指定文章（设为草稿 draft: true），支持按标题或 slug 匹配")
    parser.add_argument("--publish", help="重新上架指定文章（设为 draft: false），支持按标题或 slug 匹配")
    parser.add_argument("--delete", help="彻底删除指定文章及关联的附件目录，支持按标题或 slug 匹配")

    args = parser.parse_args()

    if args.list:
        list_all_articles()
        return

    if args.unpublish:
        set_draft_status(args.unpublish, set_draft=True)
        return

    if args.publish:
        set_draft_status(args.publish, set_draft=False)
        return

    if args.delete:
        delete_article(args.delete)
        return

    if not args.file:
        parser.print_help()
        return

    file_path = Path(args.file).resolve()
    tags_list = [t.strip() for t in args.tags.split(',')] if args.tags else []

    if file_path.suffix.lower() == '.ipynb':
        process_ipynb_notebook(
            ipynb_path=file_path,
            note_type=args.type,
            custom_slug=args.slug,
            tags=tags_list,
            category=args.category,
            draft=args.draft
        )
    else:
        process_obsidian_note(
            md_path=file_path,
            note_type=args.type,
            custom_slug=args.slug,
            tags=tags_list,
            category=args.category,
            draft=args.draft
        )

if __name__ == '__main__':
    main()
