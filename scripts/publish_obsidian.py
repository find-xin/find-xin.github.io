#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_obsidian.py - 一键将 Obsidian 笔记与 attachments 附件发布到 Hugo 博客

功能：
1. 自动将笔记转换为 Hugo Page Bundle（页面包）架构（folder/index.md + folder/attachments/）。
2. 自动兼容 Obsidian 双链语法：
   - ![[photo.png]] / ![[attachments/photo.png]] -> ![photo](attachments/photo.png)
   - ![[photo.png|400]] -> 自适应图
   - ![[document.pdf]] -> [📄 查看文档 document.pdf](attachments/document.pdf)
   - [[内部文章]] -> 内部文章
3. 自动将附件文件名中的空格和特殊符号替换为 URL 安全字符（如避免网页 404）。
4. 智能提取或补全 Front Matter（标题、日期、分类、标签、封面等）。
5. 复制被引用的附件至对应的 attachments 目录。

用法示例：
  python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/秋日漫步.md"
  python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/随手记.md" --type diary
  python3 scripts/publish_obsidian.py "/Users/xin/Documents/Obsidian/深度学习.md" --slug deep-learning --category 技术 --tags AI,PyTorch
"""

from __future__ import annotations
import os
import sys
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# 支持的图片与文档扩展名
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.bmp'}
DOC_EXTENSIONS = {'.pdf', '.zip', '.tar', '.gz', '.mp4', '.mp3'}

def sanitize_filename(name: str) -> str:
    """将含空格或特殊字符的文件名转为 Web 友好的名称"""
    clean = re.sub(r'[^\w\.\-\u4e00-\u9fa5]', '-', name.strip())
    clean = re.sub(r'-+', '-', clean)
    return clean

def sanitize_slug(text: str) -> str:
    """为文章目录生成干净的英文字符串"""
    # 如果纯英文，直接格式化
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
    # 不区分大小写匹配
    for folder in [md_dir / "attachments", md_dir, md_dir.parent / "attachments"]:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.name.lower() == filename.lower():
                    return item
    return None

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
        # 尝试从 body 的首个 # 标题提取
        h1_match = re.search(r'^#\s+(.+)$', body, flags=re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
            # 移除正文首行 # 标题，避免与模板 h1 重复
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
    
    blog_root = Path(__file__).resolve().parent.parent
    if note_type == 'diary':
        target_dir = blog_root / 'content' / 'diary' / slug
    else:
        target_dir = blog_root / 'content' / 'posts' / slug

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

        # 剥离前缀 attachments/
        clean_target_name = Path(link_target).name
        ext = Path(clean_target_name).suffix.lower()

        actual_file = find_attachment_file(md_dir, clean_target_name)
        safe_name = sanitize_filename(clean_target_name)

        if actual_file:
            dest = target_attachments_dir / safe_name
            shutil.copy2(actual_file, dest)
            copied_files.add(safe_name)

        rel_dest = f"attachments/{safe_name}"

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

    # 匹配 ![[...]]
    new_body = re.sub(r'!\[\[(.*?)\]\]', replace_wikilink, body)

    # 匹配普通内部双链 [[笔记名|别名]] 或 [[笔记名]]
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
            # 解码 url 中的 %20
            import urllib.parse
            clean_target_name = urllib.parse.unquote(clean_target_name)
            
            actual_file = find_attachment_file(md_dir, clean_target_name)
            safe_name = sanitize_filename(clean_target_name)
            if actual_file:
                dest = target_attachments_dir / safe_name
                shutil.copy2(actual_file, dest)
                copied_files.add(safe_name)
            
            rel_dest = f"attachments/{safe_name}"
            if not first_image_path:
                first_image_path = rel_dest
            return f"![{alt}]({rel_dest})"
        return match.group(0)

    new_body = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_std_markdown_link, new_body)

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
        summary = fm.get('summary') or (re.sub(r'[#*`!\[\]\(\)]', '', new_body.strip()).split('\n')[0][:80] if new_body else '')
        if summary:
            out_fm.append(f"summary: '{summary}'")
        if final_cover:
            out_fm.append(f"cover: '{final_cover}'")
        out_fm.append("pinned: false")
        
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
    print(f"📁 目标目录：{target_dir.relative_to(blog_root)}")
    print(f"📄 文章入口：{target_md.relative_to(blog_root)}")
    print(f"🖼️ 复制附件：{len(copied_files)} 个")
    for f in sorted(copied_files):
        print(f"   └── attachments/{f}")
    if final_cover:
        print(f"🎨 自动封面：{final_cover}")
    
    print("\n👉 下一步操作建议：")
    print("1. 本地启动预览：hugo server -D --port 1314 --bind 127.0.0.1 --disableFastRender")
    print("2. 提交并推送到 GitHub：")
    print(f"   git add {target_dir.relative_to(blog_root)}")
    print(f"   git commit -m \"feat: 发布《{title}》\"")
    print("   git push origin main\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="一键将 Obsidian 笔记与 attachments 附件发布到 Hugo 博客")
    parser.add_argument("file", help="Obsidian 笔记的绝对路径或相对路径（.md 文件）")
    parser.add_argument("--type", choices=['post', 'diary'], default='post', help="发布类型：post（博文长文）或 diary（微光日记，默认 post）")
    parser.add_argument("--slug", help="指定的英文文件夹别名（若不指定则自动根据标题生成）")
    parser.add_argument("--category", help="博文分类，例如 '技术'、'思考'")
    parser.add_argument("--tags", help="标签列表（逗号分隔），例如 'Obsidian,Hugo,笔记'")
    parser.add_argument("--draft", action="store_true", help="是否保存为草稿（默认直接发布 draft: false）")

    args = parser.parse_args()

    tags_list = [t.strip() for t in args.tags.split(',')] if args.tags else []
    process_obsidian_note(
        md_path=Path(args.file).resolve(),
        note_type=args.type,
        custom_slug=args.slug,
        tags=tags_list,
        category=args.category,
        draft=args.draft
    )

if __name__ == '__main__':
    main()
