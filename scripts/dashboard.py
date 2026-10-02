#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard.py - 博客桌面级可视化管理后台 (Web Dashboard 3.0 Ultimate)
零外部依赖，纯原生运行，双击直接启动。
新增与优化功能：
1. ✍️ 发布工作台：macOS 原生文件选择器、近期笔记智能探测、Obsidian attachments 与 Jupyter .ipynb 一键转换
2. 🖼️ 光影相册工作台：单图添加 + 📁 批量目录导入，自动计算物理长宽比、转码高质量 WebP、自动全局编号、写入 YAML
3. 🔍 画廊交互式灯箱：在控制台内直接点击预览大图、查看图片比例与元数据
4. 📚 全站文章管理：一键下架/重新上架、一键彻底清理、✏️ 一键在 Obsidian / 本地编辑器中打开
5. 🚀 一键部署上线：实时 Git 变动检测、预设提交说明、终端流式日志与 GitHub 快捷导航
6. 🍞 现代化 Toast 通知系统：告别阻塞弹窗，交互行云流水
7. ⚡ Hugo 本地服务：顶栏一键启停 Hugo 本地预览服务 (端口 1314)
"""

from __future__ import annotations
import os
import sys
import json
import urllib.parse
import webbrowser
import subprocess
import shutil
import socket
import re
import time
import atexit
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

CURRENT_DIR = Path(__file__).resolve().parent
BLOG_ROOT = CURRENT_DIR.parent
GALLERY_YAML = BLOG_ROOT / 'data' / 'gallery.yaml'
sys.path.insert(0, str(CURRENT_DIR))
from publish_obsidian import (
    get_all_articles,
    set_draft_status,
    delete_article,
    edit_article_meta,
    process_obsidian_note,
    process_ipynb_notebook,
    process_pdf_note,
    parse_resources_yaml,
    add_resource_file,
    add_resource_folder,
    delete_resource
)

PORT = 2026
HUGO_PROCESS = None

MIME_TYPES = {
    '.webp': 'image/webp',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.html': 'text/html; charset=utf-8',
    '.pdf': 'application/pdf',
    '.zip': 'application/zip',
}

def is_hugo_running() -> bool:
    global HUGO_PROCESS
    if HUGO_PROCESS is not None and HUGO_PROCESS.poll() is None:
        return True
    for pgrep_bin in ['/usr/bin/pgrep', 'pgrep']:
        try:
            res = subprocess.run([pgrep_bin, '-f', 'hugo server'], capture_output=True, text=True, timeout=0.5)
            if res.returncode == 0 and res.stdout.strip():
                return True
        except Exception:
            pass
    for lsof_bin in ['/usr/sbin/lsof', 'lsof']:
        try:
            res = subprocess.run([lsof_bin, '-ti:1314'], capture_output=True, text=True, timeout=0.5)
            if res.returncode == 0 and res.stdout.strip():
                return True
        except Exception:
            pass
    for host, family in [('127.0.0.1', socket.AF_INET), ('::1', socket.AF_INET6), ('localhost', socket.AF_INET)]:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex((host, 1314)) == 0:
                    return True
        except Exception:
            pass
    return False

def is_port_in_use(port: int) -> bool:
    if port == 1314:
        return is_hugo_running()
    try:
        res = subprocess.run(['lsof', f'-ti:{port}'], capture_output=True, text=True, timeout=0.5)
        if res.returncode == 0 and res.stdout.strip():
            return True
    except Exception:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

def get_available_port(start_port: int = 2026) -> int:
    for p in range(start_port, start_port + 20):
        if not is_port_in_use(p):
            return p
    return start_port

def get_hugo_bin() -> str:
    candidates = [
        shutil.which('hugo'),
        '/opt/homebrew/bin/hugo',
        '/usr/local/bin/hugo',
        str(Path.home() / 'go/bin/hugo'),
    ]
    for c in candidates:
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    return 'hugo'

def start_hugo_server():
    global HUGO_PROCESS
    if is_hugo_running():
        return True, "Hugo 本地预览服务运行中 (1314)"
    
    # 清理任何僵死占用 1314 端口的进程
    try:
        subprocess.run(['pkill', '-9', '-f', 'hugo server'], capture_output=True)
    except Exception:
        pass
    time.sleep(0.2)

    try:
        hugo_bin = get_hugo_bin()
        env = os.environ.copy()
        env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
        HUGO_PROCESS = subprocess.Popen(
            [hugo_bin, 'server', '-D', '--port', '1314', '--bind', '0.0.0.0', '-b', 'http://localhost:1314/', '--disableFastRender'],
            cwd=BLOG_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env
        )
        for _ in range(25):
            time.sleep(0.1)
            if is_hugo_running():
                return True, "已成功启动 Hugo 本地预览服务 (1314)"
            if HUGO_PROCESS.poll() is not None:
                err = HUGO_PROCESS.stderr.read().decode('utf-8', errors='ignore')
                return False, f"Hugo 启动失败: {err[:200] or '进程异常退出'}"
        return True, "Hugo 服务已启动"
    except Exception as e:
        return False, f"启动 Hugo 失败: {e}"

def stop_hugo_server():
    global HUGO_PROCESS
    if HUGO_PROCESS and HUGO_PROCESS.poll() is None:
        try:
            HUGO_PROCESS.terminate()
            HUGO_PROCESS.wait(timeout=1.5)
        except Exception:
            HUGO_PROCESS.kill()
    HUGO_PROCESS = None
    try:
        subprocess.run(['pkill', '-9', '-f', 'hugo server'], capture_output=True)
    except Exception:
        pass
    try:
        res = subprocess.run(['lsof', '-ti:1314'], capture_output=True, text=True)
        for pid in res.stdout.split():
            if pid.strip():
                subprocess.run(['kill', '-9', pid.strip()], capture_output=True)
    except Exception:
        pass
    time.sleep(0.3)
    return True, "已停止 Hugo 预览服务"

def pick_file_macos(prompt="选择文件", file_types='{"md", "ipynb", "pdf", "markdown"}', is_folder=False) -> str:
    """调用 macOS 系统级原生文件或目录选择框"""
    try:
        if is_folder:
            cmd = f'choose folder with prompt "{prompt}"'
        elif not file_types:
            cmd = f'choose file with prompt "{prompt}"'
        else:
            cmd = f'choose file of type {file_types} with prompt "{prompt}"'
        script = f'''
        try
            tell application "System Events"
                activate
            end tell
            set selectedItem to {cmd}
            return POSIX path of selectedItem
        on error
            return ""
        end try
        '''
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=60)
        return res.stdout.strip()
    except Exception:
        return ""

def open_local_path(target_path: str) -> tuple[bool, str]:
    """在系统默认应用（如 Obsidian/VS Code/访达）中打开指定文件"""
    p = Path(target_path).expanduser()
    if not p.is_absolute():
        p = (BLOG_ROOT / target_path).resolve()
    if not p.exists():
        return False, f"找不到文件: {p}"
    try:
        subprocess.run(['open', str(p)], check=True)
        return True, f"已在系统默认应用中打开: {p.name}"
    except Exception as e:
        return False, f"打开失败: {e}"

def get_image_info(img_path: Path):
    """使用 macOS 内置的 sips 工具提取图片真实物理宽高与长宽比"""
    try:
        res = subprocess.run(
            ['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(img_path)],
            capture_output=True,
            text=True
        )
        w_match = re.search(r'pixelWidth:\s*(\d+)', res.stdout)
        h_match = re.search(r'pixelHeight:\s*(\d+)', res.stdout)
        if w_match and h_match:
            width = int(w_match.group(1))
            height = int(h_match.group(1))
            ratio = round(width / height, 4) if height > 0 else 1.0
            return width, height, ratio
    except Exception:
        pass
    return 1000, 1000, 1.0

def get_gallery_images():
    """解析 data/gallery.yaml 获取相册列表"""
    if not GALLERY_YAML.exists():
        return []
    content = GALLERY_YAML.read_text(encoding='utf-8')
    items = []
    blocks = re.split(r'\n(?=  - image:)', content)
    for b in blocks:
        if 'image:' not in b:
            continue
        item = {}
        for line in b.strip().splitlines():
            line = line.strip()
            if line.startswith('- image:') or line.startswith('image:'):
                item['image'] = line.split('image:', 1)[1].strip().strip('\"\'')
            elif line.startswith('ratio:'):
                try:
                    item['ratio'] = float(line.split('ratio:', 1)[1].strip())
                except:
                    item['ratio'] = 1.0
            elif line.startswith('number:'):
                item['number'] = line.split('number:', 1)[1].strip().strip('\"\'')
            elif line.startswith('category:'):
                item['category'] = line.split('category:', 1)[1].strip().strip('\"\'')
            elif line.startswith('date:'):
                item['date'] = line.split('date:', 1)[1].strip().strip('\"\'')
            elif line.startswith('caption:'):
                item['caption'] = line.split('caption:', 1)[1].strip().strip('\"\'')
            elif line.startswith('tags:'):
                raw = line.split('tags:', 1)[1].strip().strip('[]')
                item['tags'] = [t.strip().strip('\"\'') for t in raw.split(',') if t.strip()]
        if 'image' in item:
            items.append(item)
    return items

def get_next_number(category: str, items: list):
    cat_items = [it for it in items if it.get('category') == category]
    max_num = 0
    for it in cat_items:
        num_str = it.get('number', '')
        digits = re.findall(r'\d+', num_str)
        if digits:
            max_num = max(max_num, int(digits[0]))
    next_idx = max_num + 1
    if category == 'photography':
        return f'p{next_idx:02d}', f'photo-{next_idx:02d}'
    elif category == 'daily':
        return f'd{next_idx:02d}', f'daily-{next_idx:02d}'
    else:
        return f'{next_idx:02d}', f'collection-{next_idx:02d}'

def insert_gallery_entry(yaml_text: str, category: str, new_block: str) -> str:
    if category == 'anime':
        pattern = r'(# =+\s*\n\s*# 2\..*?\n\s*# =+)'
        match = re.search(pattern, yaml_text)
        if match:
            idx = match.start()
            return yaml_text[:idx] + new_block.rstrip() + '\n\n  ' + yaml_text[idx:]
    elif category == 'photography':
        pattern = r'(# =+\s*\n\s*# 3\..*?\n\s*# =+)'
        match = re.search(pattern, yaml_text)
        if match:
            idx = match.start()
            return yaml_text[:idx] + new_block.rstrip() + '\n\n  ' + yaml_text[idx:]
    return yaml_text.rstrip() + '\n' + new_block.rstrip() + '\n'

def remove_gallery_entry(yaml_text: str, image_url: str) -> tuple[str, int]:
    pattern = rf'[ \t]*- image:\s*[\"\'\s]*{re.escape(image_url)}[\"\'\s]*[\s\S]*?(?=(?:[ \t]*- image:|\n\s*# =+|\Z))'
    new_text, count = re.subn(pattern, '', yaml_text)
    new_text = re.sub(r'\n{3,}', '\n\n', new_text)
    return new_text, count

def add_gallery_image(raw_path: str, category: str, caption: str, tags: list[str]) -> tuple[bool, str]:
    src = Path(raw_path).expanduser().resolve()
    if not src.exists() or not src.is_file():
        return False, f"找不到图片文件：{raw_path}"
    
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'}
    if src.suffix.lower() not in valid_exts:
        return False, f"不支持的格式：{src.suffix}（仅支持常见图片）"

    w, h, ratio = get_image_info(src)
    gallery_items = get_gallery_images()

    if category == 'photography':
        dest_dir = BLOG_ROOT / 'static' / 'images' / 'photography'
        num_str, prefix = get_next_number('photography', gallery_items)
        rel_img_url = f"/images/photography/{prefix}.webp"
    elif category == 'daily':
        dest_dir = BLOG_ROOT / 'static' / 'images' / 'daily'
        num_str, prefix = get_next_number('daily', gallery_items)
        rel_img_url = f"/images/daily/{prefix}.webp"
    else:
        category = 'anime'
        dest_dir = BLOG_ROOT / 'static' / 'images' / 'gallery'
        num_str, prefix = get_next_number('anime', gallery_items)
        rel_img_url = f"/images/gallery/{prefix}.webp"

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{prefix}.webp"

    cwebp = shutil.which('cwebp') or '/opt/homebrew/bin/cwebp'
    converted = False
    if src.suffix.lower() == '.webp':
        shutil.copy2(src, dest_file)
        converted = True
    elif os.path.exists(cwebp):
        try:
            res = subprocess.run([cwebp, '-q', '85', str(src), '-o', str(dest_file)], capture_output=True, text=True)
            if res.returncode == 0 and dest_file.exists():
                converted = True
        except Exception:
            pass

    if not converted:
        shutil.copy2(src, dest_file)

    tags_formatted = json.dumps(tags, ensure_ascii=False)
    caption_clean = caption.replace("'", "''")
    yaml_block = f"""  - image: {rel_img_url}
    ratio: {ratio:.4f}
    number: "{num_str}"
    category: "{category}"
    date: '{datetime.now().strftime("%Y-%m-%d")}'
    caption: '{caption_clean}'
    tags: {tags_formatted}
    source: '{src.name}'"""

    content = GALLERY_YAML.read_text(encoding='utf-8')
    new_content = insert_gallery_entry(content, category, yaml_block)
    GALLERY_YAML.write_text(new_content, encoding='utf-8')

    return True, f"成功加入相册！编号：{num_str}，文件：{rel_img_url}（长宽比：{ratio}）"

def batch_add_gallery(folder_path: str, category: str, default_tags: list[str]) -> tuple[bool, str, int]:
    """批量导入文件夹内的所有图片到指定相册分类"""
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        return False, f"找不到目标目录：{folder_path}", 0

    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    images = [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix.lower() in valid_exts]
    if not images:
        return False, f"目录中未找到任何图片文件（支持 PNG/JPG/WebP）", 0

    success_count = 0
    for img in images:
        caption = img.stem.replace('-', ' ').replace('_', ' ').strip()
        ok, _ = add_gallery_image(str(img), category, caption, default_tags)
        if ok:
            success_count += 1

    return True, f"批量导入完成！共将 {success_count} / {len(images)} 幅作品加入相册。", success_count

def delete_gallery_image(image_url: str) -> tuple[bool, str]:
    if not GALLERY_YAML.exists():
        return False, "找不到 data/gallery.yaml"
    content = GALLERY_YAML.read_text(encoding='utf-8')
    new_content, count = remove_gallery_entry(content, image_url)
    if count == 0:
        return False, "未在相册中找到该图片记录"
    GALLERY_YAML.write_text(new_content, encoding='utf-8')
    
    local_file = (BLOG_ROOT / 'static' / image_url.lstrip('/')).resolve()
    if local_file.exists() and local_file.is_file():
        try:
            local_file.unlink()
        except Exception:
            pass
    return True, "已成功从相册中移除"

def update_gallery_image(image_url: str, new_caption: str = None, new_category: str = None, new_tags: list[str] = None, new_date: str = None) -> tuple[bool, str]:
    """更新相册图片的描述配文、分类、标签与日期"""
    if not GALLERY_YAML.exists():
        return False, "找不到 data/gallery.yaml"
    content = GALLERY_YAML.read_text(encoding='utf-8')

    pattern = rf'([ \t]*- image:\s*[\"\'\s]*{re.escape(image_url)}[\"\'\s]*\n)([\s\S]*?)(?=(?:[ \t]*- image:|\n\s*# =+|\Z))'
    match = re.search(pattern, content)
    if not match:
        return False, "未在相册中找到该图片记录"

    header = match.group(1)
    body = match.group(2)

    lines = body.splitlines()
    new_lines = []
    has_caption = False
    has_cat = False
    has_tags = False
    has_date = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('caption:'):
            has_caption = True
            if new_caption is not None:
                clean_cap = new_caption.replace("'", "''")
                new_lines.append(f"    caption: '{clean_cap}'")
            else:
                new_lines.append(line)
            i += 1
            continue
        if stripped.startswith('category:'):
            has_cat = True
            if new_category is not None:
                new_lines.append(f'    category: "{new_category}"')
            else:
                new_lines.append(line)
            i += 1
            continue
        if stripped.startswith('date:'):
            has_date = True
            if new_date is not None:
                new_lines.append(f"    date: '{new_date.strip()}'")
            else:
                new_lines.append(line)
            i += 1
            continue
        if stripped.startswith('tags:'):
            has_tags = True
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('#')):
                i += 1
            if new_tags is not None:
                new_lines.append(f"    tags: {json.dumps(new_tags, ensure_ascii=False)}")
            else:
                new_lines.append(line)
            continue
        new_lines.append(line)
        i += 1

    if not has_caption and new_caption is not None:
        clean_cap = new_caption.replace("'", "''")
        new_lines.append(f"    caption: '{clean_cap}'")
    if not has_cat and new_category is not None:
        new_lines.append(f'    category: "{new_category}"')
    if not has_date and new_date is not None:
        new_lines.append(f"    date: '{new_date.strip()}'")
    if not has_tags and new_tags is not None:
        new_lines.append(f"    tags: {json.dumps(new_tags, ensure_ascii=False)}")

    new_block = header + "\n".join(new_lines) + "\n"
    new_content = content[:match.start()] + new_block + content[match.end():]
    GALLERY_YAML.write_text(new_content, encoding='utf-8')
    return True, "相册作品信息已成功更新"

def get_git_status():
    try:
        res = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=BLOG_ROOT,
            capture_output=True,
            text=True
        )
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        branch_res = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=BLOG_ROOT,
            capture_output=True,
            text=True
        )
        branch = branch_res.stdout.strip() or 'main'
        return {
            'clean': len(lines) == 0,
            'changed_count': len(lines),
            'files': lines,
            'branch': branch
        }
    except Exception as e:
        return {'clean': True, 'changed_count': 0, 'files': [], 'branch': 'main', 'error': str(e)}

def create_site_backup() -> tuple[bool, str]:
    """一键打包全站核心数据（content, data, static, 配置文件）为 ZIP"""
    import zipfile
    backup_dir = BLOG_ROOT / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    filename = f"blog_backup_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = backup_dir / filename
    
    include_dirs = ['content', 'data', 'static']
    include_files = ['hugo.toml', 'README.md']
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in include_files:
                fp = BLOG_ROOT / f
                if fp.exists():
                    zf.write(fp, f)
            for d in include_dirs:
                dp = BLOG_ROOT / d
                if dp.exists():
                    for root, _, files in os.walk(dp):
                        for file in files:
                            if not file.startswith('.'):
                                full = Path(root) / file
                                rel = full.relative_to(BLOG_ROOT)
                                zf.write(full, str(rel))
        size_mb = round(zip_path.stat().st_size / (1024 * 1024), 2)
        return True, f"备份创建成功！文件已存至 backups/{filename}（大小：{size_mb} MB）"
    except Exception as e:
        return False, f"备份失败：{e}"

RECENT_NOTES_CACHE = {'timestamp': 0, 'data': []}

def scan_recent_notes(vault_dir_str: str = ""):
    """探测扫描近期修改的 Markdown、Notebook 或 PDF（极速轻量扫描 + 60秒缓存）"""
    global RECENT_NOTES_CACHE
    now = time.time()
    if not vault_dir_str and now - RECENT_NOTES_CACHE['timestamp'] < 60 and RECENT_NOTES_CACHE['data']:
        return RECENT_NOTES_CACHE['data']

    search_targets = []
    if vault_dir_str.strip():
        search_targets.append((Path(vault_dir_str).expanduser(), 2))
    home = Path.home()
    search_targets.extend([
        (home / 'Desktop' / 'Notes', 2),
        (home / 'Documents' / 'Obsidian', 2),
        (BLOG_ROOT / 'content', 2),
        (home / 'Desktop', 1),     # 桌面仅扫描第1级，避免卡顿
        (home / 'Downloads', 1),   # 下载目录仅扫描第1级
    ])
    
    seen = set()
    found = []
    for sdir, max_depth in search_targets:
        if not sdir.exists():
            continue
        try:
            if max_depth == 1:
                with os.scandir(sdir) as it:
                    for entry in it:
                        if entry.is_file(follow_symlinks=False) and not entry.name.startswith('.'):
                            low = entry.name.lower()
                            if low.endswith('.md') or low.endswith('.ipynb') or low.endswith('.pdf'):
                                p = Path(entry.path)
                                if p not in seen:
                                    seen.add(p)
                                    try:
                                        found.append((entry.stat(follow_symlinks=False).st_mtime, p))
                                    except Exception:
                                        pass
            else:
                for root, dirs, files in os.walk(sdir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'Library', '.git', 'site-packages', 'venv', 'youshu-night', 'Trash')]
                    rel_parts = Path(root).relative_to(sdir).parts
                    if len(rel_parts) >= max_depth:
                        continue
                    for f in files:
                        if f.startswith('.'):
                            continue
                        low = f.lower()
                        if low.endswith('.md') or low.endswith('.ipynb') or low.endswith('.pdf'):
                            p = Path(root) / f
                            if p not in seen:
                                seen.add(p)
                                try:
                                    found.append((p.stat().st_mtime, p))
                                except Exception:
                                    pass
        except Exception:
            pass

    found.sort(key=lambda x: x[0], reverse=True)
    results = []
    for mtime, p in found[:10]:
        diff = now - mtime
        if diff < 3600:
            rel = f"{max(1, int(diff // 60))}分钟前"
        elif diff < 86400:
            rel = f"{int(diff // 3600)}小时前"
        else:
            rel = f"{int(diff // 86400)}天前"
        results.append({
            'name': p.name,
            'path': str(p),
            'rel_time': rel,
            'ext': p.suffix.lower()
        })
    if not vault_dir_str:
        RECENT_NOTES_CACHE['timestamp'] = now
        RECENT_NOTES_CACHE['data'] = results
    return results

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>有珠之夜 · 博客管理控制台 3.0</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>✨</text></svg>">
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --card-subtle: #f1f5f9;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --border-focus: #6366f1;
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --primary-soft: rgba(79, 70, 229, 0.08);
      --accent: #ef4444;
      --accent-soft: rgba(239, 68, 68, 0.08);
      --success: #10b981;
      --success-soft: rgba(16, 185, 129, 0.1);
      --warning: #f59e0b;
      --warning-soft: rgba(245, 158, 11, 0.1);
      --code-bg: #090d16;
      --code-text: #e2e8f0;
      --radius: 12px;
      --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04);
      --shadow-md: 0 4px 16px -2px rgba(0, 0, 0, 0.06);
    }
    body.dark {
      --bg: #090d16;
      --card-bg: #111827;
      --card-subtle: #1a2234;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #1f293d;
      --border-focus: #818cf8;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-soft: rgba(99, 102, 241, 0.15);
      --accent-soft: rgba(239, 68, 68, 0.15);
      --success-soft: rgba(16, 185, 129, 0.15);
      --warning-soft: rgba(245, 158, 11, 0.15);
      --code-bg: #04060a;
      --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
      --shadow-md: 0 4px 16px -2px rgba(0, 0, 0, 0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      transition: background 0.25s ease, color 0.25s ease;
      min-height: 100vh;
    }
    
    .header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: var(--shadow-sm);
    }
    .header-left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
    .brand-title {
      font-size: 1.18rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      letter-spacing: -0.3px;
    }
    .brand-title span { color: #f43f5e; }
    
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.8rem;
      padding: 4px 10px;
      border-radius: 99px;
      background: var(--success-soft);
      color: var(--success);
      font-weight: 500;
    }
    .status-badge.stopped { background: var(--card-subtle); color: var(--text-muted); }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    
    .header-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text);
      transition: all 0.15s ease;
      text-decoration: none;
      white-space: nowrap;
    }
    .btn:hover { border-color: var(--primary); color: var(--primary); }
    .btn-primary {
      background: var(--primary);
      color: #ffffff !important;
      border-color: var(--primary);
    }
    .btn-primary:hover {
      background: var(--primary-hover);
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.28);
    }
    .btn-danger { color: var(--accent); }
    .btn-danger:hover { background: var(--accent-soft); border-color: var(--accent); }
    .btn-sm { padding: 4px 10px; font-size: 0.82rem; border-radius: 6px; }
    .btn:disabled { opacity: 0.55; cursor: not-allowed; }

    .container { max-width: 1140px; margin: 24px auto; padding: 0 20px 48px; }
    
    .nav-tabs {
      display: flex;
      gap: 6px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      overflow-x: auto;
    }
    .tab-btn {
      padding: 10px 18px;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-muted);
      border: none;
      background: transparent;
      cursor: pointer;
      position: relative;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active { color: var(--primary); }
    .tab-btn.active::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      width: 100%;
      height: 2.5px;
      background: var(--primary);
      border-radius: 2px 2px 0 0;
    }
    .tab-counter {
      font-size: 0.72rem;
      background: var(--card-subtle);
      color: var(--text-muted);
      padding: 2px 6px;
      border-radius: 99px;
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: var(--shadow-sm);
    }
    .card-title {
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .card-desc {
      font-size: 0.88rem;
      color: var(--text-muted);
      margin-top: -8px;
      margin-bottom: 18px;
    }
    
    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: var(--card-subtle);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .stat-label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
    .stat-val { font-size: 1.35rem; font-weight: 700; color: var(--text); }

    .form-group { margin-bottom: 18px; }
    .form-label {
      display: block;
      font-size: 0.88rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--text);
    }
    .form-hint { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; line-height: 1.4; }
    .form-input {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 0.92rem;
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .form-input:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px var(--primary-soft);
    }
    .input-with-button {
      display: flex;
      gap: 8px;
    }
    .input-with-button .form-input { flex: 1; }
    
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
    @media (max-width: 720px) {
      .grid-2, .grid-3 { grid-template-columns: 1fr; }
    }

    .chip-group { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .chip {
      padding: 3px 10px;
      border-radius: 99px;
      font-size: 0.78rem;
      border: 1px solid var(--border);
      background: var(--card-subtle);
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.15s;
      user-select: none;
    }
    .chip:hover { border-color: var(--primary); color: var(--primary); }

    .step-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--primary);
      color: #fff;
      font-size: 0.78rem;
      font-weight: 700;
      margin-right: 6px;
    }

    .terminal-box {
      background: var(--code-bg);
      color: var(--code-text);
      padding: 16px;
      border-radius: 8px;
      font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.86rem;
      line-height: 1.6;
      max-height: 280px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
      margin-top: 14px;
      border: 1px solid var(--border);
      display: none;
    }

    .table-responsive { width: 100%; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
    th { font-weight: 600; color: var(--text-muted); background: var(--card-subtle); }
    tr:hover td { background: var(--primary-soft); }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.76rem;
      font-weight: 600;
    }
    .badge-post { background: var(--primary-soft); color: var(--primary); }
    .badge-diary { background: var(--warning-soft); color: var(--warning); }
    .badge-active { background: var(--success-soft); color: var(--success); }
    .badge-draft { background: var(--card-subtle); color: var(--text-muted); }

    .gallery-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
      margin-top: 16px;
    }
    .gallery-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-sm);
      transition: transform 0.2s, box-shadow 0.2s;
      cursor: pointer;
    }
    .gallery-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
      border-color: var(--border-focus);
    }
    .gallery-card-img-wrap {
      width: 100%;
      height: 160px;
      background: #000;
      position: relative;
      overflow: hidden;
    }
    .gallery-card-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s;
    }
    .gallery-card:hover .gallery-card-img { transform: scale(1.04); }
    .gallery-card-badge {
      position: absolute;
      top: 8px;
      left: 8px;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 700;
      background: rgba(0,0,0,0.65);
      color: #fff;
      backdrop-filter: blur(4px);
    }
    .gallery-card-body {
      padding: 12px;
      display: flex;
      flex-direction: column;
      flex: 1;
      justify-content: space-between;
    }
    .gallery-card-title {
      font-size: 0.92rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .gallery-card-meta {
      font-size: 0.76rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .gallery-card-actions {
      display: flex;
      gap: 6px;
      justify-content: flex-end;
    }
    
    .filter-pills {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    .filter-pill {
      padding: 6px 14px;
      border-radius: 99px;
      font-size: 0.85rem;
      font-weight: 500;
      border: 1px solid var(--border);
      background: var(--card-bg);
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.15s;
    }
    .filter-pill.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }

    /* 画廊与快捷编辑 模态框通用结构 */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(8px);
      z-index: 9999;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .modal-overlay.is-active { display: flex; }
    .modal-content {
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 14px;
      max-width: 900px;
      width: 100%;
      max-height: 90vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    .modal-header {
      padding: 16px 22px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      color: var(--text);
    }
    .modal-header h3 {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text);
    }
    .modal-body {
      display: flex;
      flex-direction: column;
      padding: 20px 24px;
      overflow-y: auto;
      background: var(--card-bg);
      color: var(--text);
    }
    .modal-footer {
      padding: 14px 24px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
    }

    /* 仅针对全屏画廊图片 Lightbox 模态框使用全黑居中背景 */
    #gallery-modal .modal-body {
      align-items: center;
      justify-content: center;
      background: #000;
      padding: 20px;
    }
    .modal-img {
      max-width: 100%;
      max-height: 60vh;
      object-fit: contain;
      border-radius: 8px;
    }

    /* 模态框提示卡片 */
    .modal-notice-box {
      padding: 12px 14px;
      background: var(--card-subtle);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-top: 6px;
    }
    .modal-notice-title {
      font-weight: 600;
      font-size: 0.86rem;
      color: var(--text);
    }
    .modal-notice-desc {
      font-weight: 400;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 4px;
      line-height: 1.45;
    }

    /* 模式切换与选项卡 */
    .subtab-buttons {
      display: flex;
      gap: 10px;
      margin-bottom: 16px;
    }
    .res-fmt-tag {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      background: var(--card-subtle);
      border: 1px solid var(--border);
      letter-spacing: 0.05em;
    }
    .res-fmt--pdf { background: rgba(239, 68, 68, 0.12); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
    .res-fmt--zip, .res-fmt--tar, .res-fmt--gz { background: rgba(245, 158, 11, 0.12); color: #f59e0b; border-color: rgba(245, 158, 11, 0.3); }
  </style>
</head>
<body>
  <header class="header">
    <div class="header-left">
      <div class="brand-title"><span>✦</span> 有珠之夜 · 博客管理台</div>
      <div id="hugo-status-badge" class="__HUGO_BADGE_CLASS__">
        <span class="status-dot"></span>
        <span id="hugo-status-text">__HUGO_STATUS_TEXT__</span>
      </div>
      <button class="__HUGO_BTN_CLASS__" id="hugo-toggle-btn" onclick="toggleHugo()">__HUGO_BTN_TEXT__</button>
    </div>
    <div class="header-right">
      <a class="btn" href="http://localhost:1314/" target="_blank" rel="noopener">🌐 本地预览 (1314)</a>
      <a class="btn" href="https://find-xin.github.io/" target="_blank" rel="noopener">🚀 线上站点</a>
      <button class="btn btn-sm" id="theme-btn" onclick="toggleTheme()">🌓 模式</button>
    </div>
  </header>

  <main class="container">
    <nav class="nav-tabs">
      <button class="tab-btn active" id="tab-btn-publish" onclick="switchTab('publish')">
        <span>✍️ 发布文章 / 笔记</span>
      </button>
      <button class="tab-btn" id="tab-btn-resources" onclick="switchTab('resources')">
        <span>📦 资料库与附件管理</span>
        <span class="tab-counter" id="resources-counter">__RESOURCES_COUNT__</span>
      </button>
      <button class="tab-btn" id="tab-btn-gallery" onclick="switchTab('gallery')">
        <span>🖼️ 光影相册管理</span>
        <span class="tab-counter" id="gallery-counter">__GALLERY_COUNT__</span>
      </button>
      <button class="tab-btn" id="tab-btn-manage" onclick="switchTab('manage')">
        <span>📚 全站文章管理</span>
        <span class="tab-counter" id="articles-counter">__ARTICLES_COUNT__</span>
      </button>
      <button class="tab-btn" id="tab-btn-deploy" onclick="switchTab('deploy')">
        <span>🚀 部署到 GitHub</span>
      </button>
    </nav>

    <!-- ========================================== -->
    <!-- TAB 1: ✍️ 发布工作台 -->
    <!-- ========================================== -->
    <section id="tab-publish">
      <div class="card">
        <h2 class="card-title">
          <span><span class="step-badge">1</span> 选择笔记、Notebook 或 PDF 文件</span>
        </h2>
        <p class="card-desc">支持 Obsidian Markdown 笔记（自动抽取 attachments/ 并转为 WebP）、Jupyter Notebook（.ipynb，抽取图表与富文本），以及独立 PDF 文档（.pdf）。PDF 作为文章发布时，页面内嵌交互阅读器与专属下载卡片，<strong>不放入全站资料库</strong>。</p>
        
        <div class="form-group">
          <label class="form-label">笔记绝对路径</label>
          <div class="input-with-button">
            <input type="text" id="file-path" class="form-input" placeholder="点击右侧按钮选择文件，或从下方快速填入...">
            <button class="btn btn-primary" onclick="pickFile('note')">📂 浏览电脑文件...</button>
          </div>
          <div id="recent-notes-container" style="margin-top: 10px;">
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px;">⚡ 近期笔记智能发现：</div>
            <div class="chip-group" id="recent-notes-chips">
              <span class="chip" style="color:var(--text-muted);">正在探测常用笔记库...</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">
          <span><span class="step-badge">2</span> 配置发布属性</span>
        </h2>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">发布所属板块</label>
            <select id="pub-type" class="form-input">
              <option value="post">📄 长篇博文（Post · content/posts/）</option>
              <option value="diary">☕ 生活微光日记（Diary · content/diary/）</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">英文文件夹别名（Slug，可选）</label>
            <input type="text" id="pub-slug" class="form-input" placeholder="留空则自动按时间戳或标题拼音生成">
          </div>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">分类（可选）</label>
            <input type="text" id="pub-category" class="form-input" placeholder="例如：型月、技术、数据科学">
            <div class="chip-group">
              <span class="chip" onclick="setCategory('型月')">型月</span>
              <span class="chip" onclick="setCategory('技术')">技术</span>
              <span class="chip" onclick="setCategory('数据科学')">数据科学</span>
              <span class="chip" onclick="setCategory('生活随笔')">生活随笔</span>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">标签（逗号分隔，可选）</label>
            <input type="text" id="pub-tags" class="form-input" placeholder="例如：魔法使之夜,Python,随想">
            <div class="chip-group">
              <span class="chip" onclick="addTag('魔法使之夜')">+ 魔法使之夜</span>
              <span class="chip" onclick="addTag('Python')">+ Python</span>
              <span class="chip" onclick="addTag('随笔')">+ 随笔</span>
              <span class="chip" onclick="addTag('教程')">+ 教程</span>
            </div>
          </div>
        </div>

        <div class="form-group" style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
          <input type="checkbox" id="pub-draft" style="width: 18px; height: 18px; cursor: pointer;">
          <label for="pub-draft" style="font-size: 0.92rem; cursor: pointer; user-select: none;">保存为本地草稿（仅本地可见，暂不推送到线上）</label>
        </div>

        <div style="margin-top: 24px;">
          <button class="btn btn-primary" id="publish-btn" onclick="doPublish()" style="padding: 10px 24px; font-size: 0.95rem;">
            🚀 立即转换并发布
          </button>
        </div>

        <div id="publish-log" class="terminal-box"></div>
      </div>
    </section>

    <!-- ========================================== -->
    <!-- TAB: 📦 资料库与附件管理 -->
    <!-- ========================================== -->
    <section id="tab-resources" style="display: none;">
      <div class="card">
        <h2 class="card-title">
          <span>📦 上传与打包资料到资料库</span>
        </h2>
        <p class="card-desc">支持上传独立文件（PDF、文档、电子书、安装包、源码）或将包含各类文件的整个文件夹一键打包为 ZIP 供访客下载。在资料库中不展示冗长正文，直接提供一键下载与直链。</p>

        <div class="subtab-buttons">
          <button type="button" class="btn btn-sm btn-primary" id="res-mode-file-btn" onclick="switchResourceMode('file')">📄 单个文件上传 (PDF/文档/压缩包/软件)</button>
          <button type="button" class="btn btn-sm" id="res-mode-folder-btn" onclick="switchResourceMode('folder')">📁 文件夹一键打包为 ZIP (合集包)</button>
        </div>

        <!-- 单文件模式 -->
        <div id="res-mode-file">
          <div class="form-group">
            <label class="form-label">选择文件路径</label>
            <div class="input-with-button">
              <input type="text" id="res-file-path" class="form-input" placeholder="选择或拖拽任意文件（PDF、ZIP、DOCX、EPUB 等）...">
              <button type="button" class="btn btn-primary" onclick="pickResourceFile()">📂 浏览电脑文件...</button>
            </div>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">资料标题 / 显示名称</label>
              <input type="text" id="res-file-title" class="form-input" placeholder="例如：TypeScript 进阶实战手册（留空则默认使用文件名）">
            </div>
            <div class="form-group">
              <label class="form-label">所属分类</label>
              <select id="res-file-cat" class="form-select">
                <option value="docs">📕 文档资料 (docs - PDF/电子书/指南)</option>
                <option value="archives">🗜️ 压缩合集 (archives - 压缩包/文件集)</option>
                <option value="code">💻 源码项目 (code - 源代码/项目包)</option>
                <option value="tools">🛠️ 实用工具 (tools - 工具/脚本/配置)</option>
                <option value="assets">🎨 素材资源 (assets - 图片/壁纸/模板)</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">标签（逗号分隔）</label>
            <input type="text" id="res-file-tags" class="form-input" placeholder="例如：TypeScript,前端,手册">
          </div>
          <div class="form-group">
            <label class="form-label">简要描述 / 备注说明</label>
            <textarea id="res-file-desc" class="form-input" rows="2" placeholder="简要说明这份资料的主要内容或用途..."></textarea>
          </div>
          <div class="form-group" style="display:flex;align-items:center;gap:8px;margin-top:12px;">
            <input type="checkbox" id="res-file-make-post" style="width:18px;height:18px;cursor:pointer;">
            <label for="res-file-make-post" style="cursor:pointer;font-size:0.92rem;font-weight:500;">如果是 PDF 文件，同时在博客中生成内嵌交互阅读文章（自动发布至 /posts/）</label>
          </div>
          <div style="margin-top: 18px;">
            <button type="button" class="btn btn-primary" id="res-file-submit-btn" onclick="doUploadResourceFile()" style="padding:10px 24px;">🚀 上传并收录至资料库</button>
          </div>
        </div>

        <!-- 文件夹打包模式 -->
        <div id="res-mode-folder" style="display: none;">
          <div class="form-group">
            <label class="form-label">选择本地文件夹</label>
            <div class="input-with-button">
              <input type="text" id="res-folder-path" class="form-input" placeholder="选择需要打包的文件夹路径...">
              <button type="button" class="btn btn-primary" onclick="pickResourceFolder()">📁 浏览文件夹...</button>
            </div>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">合集包标题 / 显示名称</label>
              <input type="text" id="res-folder-title" class="form-input" placeholder="例如：开发环境配置文件包（留空默认文件夹名）">
            </div>
            <div class="form-group">
              <label class="form-label">所属分类</label>
              <select id="res-folder-cat" class="form-select">
                <option value="archives">🗜️ 压缩合集 (archives - 压缩包/文件集)</option>
                <option value="code">💻 源码项目 (code - 源代码/项目包)</option>
                <option value="docs">📕 文档资料 (docs - 讲义/文档包)</option>
                <option value="tools">🛠️ 实用工具 (tools - 工具/脚本/配置)</option>
                <option value="assets">🎨 素材资源 (assets - 素材/图片包)</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">标签（逗号分隔）</label>
            <input type="text" id="res-folder-tags" class="form-input" value="文件夹合集,压缩包" placeholder="例如：合集,源码,打包">
          </div>
          <div class="form-group">
            <label class="form-label">简要描述 / 备注说明</label>
            <textarea id="res-folder-desc" class="form-input" rows="2" placeholder="简要说明此文件夹内包含哪些文件或用途..."></textarea>
          </div>
          <div style="margin-top: 18px;">
            <button type="button" class="btn btn-primary" id="res-folder-submit-btn" onclick="doUploadResourceFolder()" style="padding:10px 24px;">🗜️ 自动压缩打包为 ZIP 并收录</button>
          </div>
        </div>
      </div>

      <!-- 资料库文件列表 -->
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
          <h2 class="card-title" style="margin:0;">
            <span>📚 资料库已收录资源 (<span id="res-list-count">0</span>)</span>
          </h2>
          <div style="display:flex;gap:8px;">
            <input type="search" id="res-search-input" class="form-input" placeholder="快速筛选资料..." style="width:220px;padding:6px 12px;" oninput="filterResourcesList()">
            <button class="btn btn-sm" onclick="loadResources()">🔄 刷新列表</button>
          </div>
        </div>
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem;">
            <thead>
              <tr style="border-bottom: 2px solid var(--border); color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">
                <th style="padding: 10px 12px;">类型</th>
                <th style="padding: 10px 12px;">标题 / 文件名</th>
                <th style="padding: 10px 12px;">分类</th>
                <th style="padding: 10px 12px;">大小 / 文件数</th>
                <th style="padding: 10px 12px;">更新日期</th>
                <th style="padding: 10px 12px; text-align: right;">操作</th>
              </tr>
            </thead>
            <tbody id="resources-table-body">
              <tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-muted);">正在加载资料库...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ========================================== -->
    <!-- TAB 2: 🖼️ 光影相册管理 -->
    <!-- ========================================== -->
    <section id="tab-gallery" style="display: none;">
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <h2 class="card-title" style="margin-bottom:0;">📸 添加作品到相册</h2>
          <div class="subtab-buttons">
            <button class="btn btn-sm btn-primary" id="tab-gallery-single-btn" onclick="switchGalleryMode('single')">单图添加</button>
            <button class="btn btn-sm" id="tab-gallery-batch-btn" onclick="switchGalleryMode('batch')">📁 批量导入目录</button>
          </div>
        </div>

        <!-- 单图模式 -->
        <div id="gallery-single-mode">
          <div class="form-group">
            <label class="form-label">选择单张图片（PNG / JPG / JPEG / WebP）</label>
            <div class="input-with-button">
              <input type="text" id="gallery-file-path" class="form-input" placeholder="选择图片，或输入图片绝对路径...">
              <button class="btn btn-primary" onclick="pickFile('image')">📂 选择图片...</button>
            </div>
          </div>

          <div class="grid-3">
            <div class="form-group">
              <label class="form-label">所属相册分类</label>
              <select id="gallery-cat" class="form-input">
                <option value="anime">🎨 动漫插画 (Anime · collection-XX.webp)</option>
                <option value="photography">📷 摄影大片 (Photography · photo-XX.webp)</option>
                <option value="daily">☕ 生活日常 (Daily · daily-XX.webp)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">作品标题 / 描述 (Caption)</label>
              <input type="text" id="gallery-caption" class="form-input" placeholder="例如：苍崎青子·魔弹">
            </div>
            <div class="form-group">
              <label class="form-label">标签 (逗号分隔)</label>
              <input type="text" id="gallery-tags" class="form-input" placeholder="例如：魔法使之夜,型月,壁纸">
            </div>
          </div>

          <button class="btn btn-primary" id="add-gallery-btn" onclick="doAddGallery()">
            ✨ 自动测量宽高、转码并加入相册
          </button>
        </div>

        <!-- 批量导入模式 -->
        <div id="gallery-batch-mode" style="display: none;">
          <div class="form-group">
            <label class="form-label">选择图片所在的文件夹目录</label>
            <div class="input-with-button">
              <input type="text" id="gallery-batch-folder" class="form-input" placeholder="选择包含图片的文件夹路径...">
              <button class="btn btn-primary" onclick="pickFolder()">📂 选择文件夹...</button>
            </div>
            <p class="form-hint">💡 后台将自动扫描该文件夹内所有 PNG/JPG/WebP 图片，自动逐个计算长宽比、按序编号并批量写入相册数据库。</p>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">批量导入分类</label>
              <select id="gallery-batch-cat" class="form-input">
                <option value="photography">📷 摄影大片 (Photography · photo-XX.webp)</option>
                <option value="daily">☕ 生活日常 (Daily · daily-XX.webp)</option>
                <option value="anime">🎨 动漫插画 (Anime · collection-XX.webp)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">默认标签 (逗号分隔)</label>
              <input type="text" id="gallery-batch-tags" class="form-input" placeholder="例如：旅行,风景,街拍">
            </div>
          </div>

          <button class="btn btn-primary" id="batch-gallery-btn" onclick="doBatchGallery()">
            🚀 一键批量扫描并导入相册
          </button>
        </div>

        <div id="gallery-log" class="terminal-box"></div>
      </div>

      <!-- 相册图片展示墙 -->
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
          <h2 class="card-title" style="margin-bottom: 0;">🖼️ 已收录相册一览</h2>
          <div class="filter-pills" style="margin-bottom: 0;">
            <button class="filter-pill active" onclick="filterGallery('all', this)">全部 (<span id="count-all">0</span>)</button>
            <button class="filter-pill" onclick="filterGallery('anime', this)">🎨 动漫 (<span id="count-anime">0</span>)</button>
            <button class="filter-pill" onclick="filterGallery('photography', this)">📷 摄影 (<span id="count-photo">0</span>)</button>
            <button class="filter-pill" onclick="filterGallery('daily', this)">☕ 日常 (<span id="count-daily">0</span>)</button>
          </div>
        </div>

        <div class="gallery-grid" id="gallery-grid">
          <div style="grid-column: 1/-1; text-align: center; padding: 30px; color: var(--text-muted);">正在加载相册数据...</div>
        </div>
      </div>
    </section>

    <!-- ========================================== -->
    <!-- TAB 3: 📚 全站文章管理 -->
    <!-- ========================================== -->
    <section id="tab-manage" style="display: none;">
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-label">📄 长篇博文总数</span>
          <span class="stat-val" id="stat-posts">0</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">☕ 微光日记篇数</span>
          <span class="stat-val" id="stat-diaries">0</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">🟡 当前草稿数量</span>
          <span class="stat-val" id="stat-drafts">0</span>
        </div>
      </div>

      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">
          <h2 class="card-title" style="margin-bottom: 0;">📚 已发布内容一览</h2>
          <button class="btn btn-sm" onclick="loadArticles()">🔄 刷新列表</button>
        </div>
        <div class="form-group">
          <input type="text" id="search-input" class="form-input" placeholder="输入关键词实时过滤标题、类型或 Slug..." oninput="filterArticles()">
        </div>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th style="width: 80px;">类型</th>
                <th style="width: 90px;">状态</th>
                <th style="width: 100px;">日期</th>
                <th>文章标题</th>
                <th style="width: 160px;">Slug 标识</th>
                <th style="width: 250px;">快捷操作</th>
              </tr>
            </thead>
            <tbody id="articles-tbody">
              <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">正在加载文章列表...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ========================================== -->
    <!-- TAB 4: 🚀 部署到 GitHub -->
    <!-- ========================================== -->
    <section id="tab-deploy" style="display: none;">
      <div class="card">
        <h2 class="card-title">🚀 一键提交并推送到 GitHub</h2>
        <p class="card-desc">
          点击下方按钮后，后台将自动执行 <code>git add .</code>、<code>git commit</code> 和 <code>git push origin main</code>，GitHub Actions 将在 1 分钟内自动部署上线。
        </p>

        <div id="git-status-card" class="stat-card" style="margin-bottom: 20px;">
          <div>
            <div class="stat-label">当前本地 Git 状态</div>
            <div id="git-status-summary" style="font-weight: 600; margin-top: 4px;">检测中...</div>
          </div>
          <div style="display:flex; gap:8px;">
            <a class="btn btn-sm" href="https://github.com/find-xin/find-xin.github.io/actions" target="_blank">⚡ 查看 Actions 自动构建</a>
            <button class="btn btn-sm" onclick="checkGitStatus()">🔄 检查变动</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">提交说明（Commit Message）</label>
          <input type="text" id="git-msg" class="form-input" value="feat: 更新博客文章与相册">
          <div class="chip-group">
            <span class="chip" onclick="setGitMsg('feat: 发布新博文')">feat: 发布新博文</span>
            <span class="chip" onclick="setGitMsg('feat: 发布生活日记')">feat: 发布生活日记</span>
            <span class="chip" onclick="setGitMsg('feat: 新增相册照片')">feat: 新增相册照片</span>
            <span class="chip" onclick="setGitMsg('fix: 修正排版与内容')">fix: 修正排版与内容</span>
            <span class="chip" onclick="setGitMsg('chore: 更新全站内容')">chore: 更新全站内容</span>
          </div>
        </div>

        <div style="margin-top: 20px; display: flex; gap: 12px; flex-wrap: wrap;">
          <button class="btn btn-primary" id="deploy-btn" onclick="doDeploy()" style="padding: 10px 24px; font-size: 0.95rem;">
            🚀 提交并推送到 GitHub
          </button>
          <button class="btn" id="pull-btn" onclick="doPull()" style="padding: 10px 18px; font-size: 0.95rem;">
            ⬇️ 拉取远程更新 (Git Pull)
          </button>
          <button class="btn" id="backup-btn" onclick="doBackup()" style="padding: 10px 18px; font-size: 0.95rem;">
            📦 一键打包备份全站 (ZIP)
          </button>
        </div>

        <div id="deploy-log" class="terminal-box"></div>
      </div>
    </section>
  </main>

  <!-- 全屏大图 Lightbox Modal -->
  <div class="modal-overlay" id="gallery-modal" onclick="closeModal(event)">
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="modal-title" style="font-size:1.05rem; font-weight:700;">作品详情</h3>
        <button class="btn btn-sm" onclick="closeModalDirect()">✕ 关闭</button>
      </div>
      <div class="modal-body">
        <img class="modal-img" id="modal-img" src="" alt="">
      </div>
      <div class="modal-footer">
        <div id="modal-meta" style="font-size:0.85rem; color:var(--text-muted);"></div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-sm btn-primary" id="modal-edit-btn" onclick="editFromModal()">✏️ 编辑此作品</button>
          <a class="btn btn-sm" id="modal-orig-link" href="" target="_blank">🔍 查看高清原图</a>
          <button class="btn btn-sm btn-danger" id="modal-del-btn" onclick="deleteFromModal()">🗑️ 移出相册</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 文章/日记 快速编辑 Modal -->
  <div class="modal-overlay" id="edit-article-modal" onclick="closeArticleEditModal(event)">
    <div class="modal-content" style="max-width: 600px;">
      <div class="modal-header">
        <h3 id="edit-article-modal-title">✏️ 快捷编辑文章 / 日记</h3>
        <button class="btn btn-sm" onclick="closeArticleEditModalDirect()">✕ 关闭</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="edit-article-original-slug">
        <div class="form-group">
          <label class="form-label">标题</label>
          <input type="text" id="edit-article-title" class="form-input" placeholder="文章或日记标题">
        </div>
        <div class="form-group">
          <label class="form-label">标识 / Slug (生成网址路径)</label>
          <input type="text" id="edit-article-slug" class="form-input" placeholder="如：tsukihime-game（建议小写英文、数字与短横线）">
          <div class="form-hint">🔗 将决定文章访问网址（如 <code>/posts/标识名/</code> 或 <code>/diary/标识名/</code>）。修改后系统会自动写入重定向别名，旧外链不失效。</div>
        </div>
        <div class="form-group" id="edit-article-cat-group">
          <label class="form-label">分类 (Categories)</label>
          <input type="text" id="edit-article-categories" class="form-input" placeholder="如：型月, 随笔（多个分类用逗号分隔）">
        </div>
        <div class="form-group">
          <label class="form-label">标签 (Tags)</label>
          <input type="text" id="edit-article-tags" class="form-input" placeholder="如：Fate, 魔法使之夜（多个标签用逗号分隔）">
          <div class="form-hint">💡 多个标签以中英文逗号隔开即可。</div>
        </div>
        <div class="form-group">
          <label class="form-label">文章摘要 / 描述</label>
          <textarea id="edit-article-summary" class="form-input" rows="3" style="resize: vertical;" placeholder="简介或卡片摘要"></textarea>
        </div>
        <div class="modal-notice-box">
          <label style="display: flex; align-items: flex-start; gap: 10px; cursor: pointer;">
            <input type="checkbox" id="edit-article-update-lastmod" style="margin-top: 3px; accent-color: var(--primary);">
            <div>
              <div class="modal-notice-title">同时将文末“最后更新时间”刷新为当前时间</div>
              <div class="modal-notice-desc">
                默认未勾选：如果仅仅只是修改标签、分类或标题，文末更新时间<strong>绝不改变</strong>。只有在正文实质更新时才建议勾选。
              </div>
            </div>
          </label>
        </div>
      </div>
      <div class="modal-footer" style="justify-content: flex-end; gap: 10px;">
        <button class="btn" onclick="closeArticleEditModalDirect()">取消</button>
        <button class="btn btn-primary" id="save-article-btn" onclick="submitEditArticle()">💾 保存更改</button>
      </div>
    </div>
  </div>

  <!-- 相册图片 快捷编辑 Modal -->
  <div class="modal-overlay" id="edit-gallery-modal" onclick="closeGalleryEditModal(event)">
    <div class="modal-content" style="max-width: 550px;">
      <div class="modal-header">
        <h3>✏️ 编辑相册作品信息</h3>
        <button class="btn btn-sm" onclick="closeGalleryEditModalDirect()">✕ 关闭</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="edit-gallery-image">
        <div style="text-align: center; margin-bottom: 16px;">
          <img id="edit-gallery-preview" src="" style="max-height: 180px; max-width: 100%; border-radius: 8px; border: 1px solid var(--border); object-fit: contain; background: var(--card-subtle);">
        </div>
        <div class="form-group">
          <label class="form-label">作品配文 / 描述</label>
          <input type="text" id="edit-gallery-caption" class="form-input" placeholder="如：苍崎青子 & 久远寺有珠">
        </div>
        <div class="form-group">
          <label class="form-label">所属相册分类</label>
          <select id="edit-gallery-category" class="form-input">
            <option value="anime">🎨 动漫收藏 (Anime)</option>
            <option value="photography">📷 摄影之光 (Photography)</option>
            <option value="daily">☕ 生活切片 (Daily)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">拍摄/记录日期 (Date)</label>
          <input type="date" id="edit-gallery-date" class="form-input">
        </div>
        <div class="form-group">
          <label class="form-label">标签 (Tags)</label>
          <input type="text" id="edit-gallery-tags" class="form-input" placeholder="如：魔法使之夜, 苍崎青子（逗号分隔）">
          <div class="form-hint">💡 多个标签以逗号隔开。</div>
        </div>
      </div>
      <div class="modal-footer" style="justify-content: flex-end; gap: 10px;">
        <button class="btn" onclick="closeGalleryEditModalDirect()">取消</button>
        <button class="btn btn-primary" id="save-gallery-btn" onclick="submitEditGallery()">💾 保存更改</button>
      </div>
    </div>
  </div>

  <script>
    let allArticles = [];
    let allGallery = [];
    let curGalleryCat = 'all';
    let curModalItem = null;

    /* Toast 提示系统 */
    function showToast(message, type = 'info') {
      let container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed; top:20px; right:20px; z-index:99999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
        document.body.appendChild(container);
      }
      const toast = document.createElement('div');
      const bg = type === 'success' ? 'var(--success)' : (type === 'error' ? 'var(--accent)' : 'var(--primary)');
      toast.style.cssText = `background:${bg}; color:#fff; padding:10px 18px; border-radius:8px; font-size:0.88rem; font-weight:500; box-shadow:0 4px 16px rgba(0,0,0,0.2); display:flex; align-items:center; gap:8px; opacity:0; transform:translateY(-8px); transition:all 0.25s cubic-bezier(0.16,1,0.3,1); pointer-events:auto;`;
      const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
      toast.innerHTML = `<span style="font-weight:700;">${icon}</span><span>${escapeHtml(message)}</span>`;
      container.appendChild(toast);

      requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
      });

      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-8px)';
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    function toggleTheme() {
      document.body.classList.toggle('dark');
      localStorage.setItem('ui-theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    }
    if (localStorage.getItem('ui-theme') === 'dark' || (!localStorage.getItem('ui-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.body.classList.add('dark');
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById('tab-publish').style.display = 'none';
      document.getElementById('tab-resources').style.display = 'none';
      document.getElementById('tab-gallery').style.display = 'none';
      document.getElementById('tab-manage').style.display = 'none';
      document.getElementById('tab-deploy').style.display = 'none';

      if (tabId === 'publish') {
        document.getElementById('tab-btn-publish').classList.add('active');
        document.getElementById('tab-publish').style.display = 'block';
        loadRecentNotes();
      } else if (tabId === 'resources') {
        document.getElementById('tab-btn-resources').classList.add('active');
        document.getElementById('tab-resources').style.display = 'block';
        loadResources();
      } else if (tabId === 'gallery') {
        document.getElementById('tab-btn-gallery').classList.add('active');
        document.getElementById('tab-gallery').style.display = 'block';
        loadGallery();
      } else if (tabId === 'manage') {
        document.getElementById('tab-btn-manage').classList.add('active');
        document.getElementById('tab-manage').style.display = 'block';
        loadArticles();
      } else if (tabId === 'deploy') {
        document.getElementById('tab-btn-deploy').classList.add('active');
        document.getElementById('tab-deploy').style.display = 'block';
        checkGitStatus();
      }
    }

    /* 资料库管理 */
    let allResources = [];

    async function loadResources() {
      try {
        const res = await fetch('/api/resources');
        allResources = await res.json();
        const cntEl = document.getElementById('resources-counter');
        const listCntEl = document.getElementById('res-list-count');
        if (cntEl) cntEl.textContent = allResources.length;
        if (listCntEl) listCntEl.textContent = allResources.length;
        renderResourcesList(allResources);
      } catch (e) {
        document.getElementById('resources-table-body').innerHTML = `
          <tr><td colspan="6" style="text-align:center;padding:24px;color:var(--accent);">加载资料库失败：${escapeHtml(e.message)}</td></tr>
        `;
      }
    }

    function filterResourcesList() {
      const q = (document.getElementById('res-search-input').value || '').trim().toLowerCase();
      if (!q) {
        renderResourcesList(allResources);
        return;
      }
      const filtered = allResources.filter(r => 
        (r.title || '').toLowerCase().includes(q) ||
        (r.filename || '').toLowerCase().includes(q) ||
        (r.description || '').toLowerCase().includes(q) ||
        (r.category || '').toLowerCase().includes(q) ||
        (r.format || '').toLowerCase().includes(q)
      );
      renderResourcesList(filtered);
    }

    function renderResourcesList(list) {
      const tbody = document.getElementById('resources-table-body');
      if (!list || list.length === 0) {
        tbody.innerHTML = `
          <tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-muted);">暂无匹配的资料记录</td></tr>
        `;
        return;
      }

      tbody.innerHTML = list.map(item => {
        const fmtBadge = `<span class="res-fmt-tag res-fmt--${escapeHtml(item.format)}">${escapeHtml((item.format || 'bin').toUpperCase())}</span>`;
        const countStr = item.file_count > 1 ? ` · <span style="color:var(--primary);font-size:0.8rem;">📁 ${item.file_count} 文件</span>` : '';
        const catMap = {
          'docs': '📕 文档资料',
          'archives': '🗜️ 压缩合集',
          'code': '💻 源码项目',
          'tools': '🛠️ 实用工具',
          'assets': '🎨 素材模板'
        };
        const catName = catMap[item.category] || item.category || '未分类';

        return `
          <tr style="border-bottom: 1px solid var(--border);">
            <td style="padding: 12px;">${fmtBadge}</td>
            <td style="padding: 12px;">
              <div style="font-weight: 600; color: var(--text);">${escapeHtml(item.title)}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(item.filename)}</div>
              ${item.description ? `<div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 3px;">${escapeHtml(item.description)}</div>` : ''}
            </td>
            <td style="padding: 12px; font-size: 0.85rem;">${catName}</td>
            <td style="padding: 12px; font-family: monospace; font-size: 0.85rem;">${escapeHtml(item.size)}${countStr}</td>
            <td style="padding: 12px; font-size: 0.82rem; color: var(--text-muted);">${escapeHtml(item.date)}</td>
            <td style="padding: 12px; text-align: right; white-space: nowrap;">
              <button class="btn btn-sm" onclick="openResourceInFinder('${escapeJs(item.filename)}')">📁 定位</button>
              <button class="btn btn-sm" onclick="copyResourceUrl('${escapeJs(item.url)}')">🔗 直链</button>
              <button class="btn btn-sm btn-danger" onclick="confirmDeleteResource('${escapeJs(item.id)}', '${escapeJs(item.title)}')">🗑️ 删除</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function switchResourceMode(mode) {
      const fileBtn = document.getElementById('res-mode-file-btn');
      const folderBtn = document.getElementById('res-mode-folder-btn');
      const fileDiv = document.getElementById('res-mode-file');
      const folderDiv = document.getElementById('res-mode-folder');
      if (mode === 'file') {
        fileBtn.className = 'btn btn-sm btn-primary';
        folderBtn.className = 'btn btn-sm';
        fileDiv.style.display = 'block';
        folderDiv.style.display = 'none';
      } else {
        fileBtn.className = 'btn btn-sm';
        folderBtn.className = 'btn btn-sm btn-primary';
        fileDiv.style.display = 'none';
        folderDiv.style.display = 'block';
      }
    }

    async function pickResourceFile() {
      try {
        const res = await fetch('/api/pick-file?type=resource');
        const data = await res.json();
        if (data.path) {
          document.getElementById('res-file-path').value = data.path;
          const fname = data.path.split('/').pop();
          if (!document.getElementById('res-file-title').value.trim()) {
            document.getElementById('res-file-title').value = fname.replace(/\\.[^.]+$/, '');
          }
          showToast('已选取文件: ' + fname, 'success');
        }
      } catch (e) {
        showToast('选择器调用失败: ' + e.message, 'error');
      }
    }

    async function pickResourceFolder() {
      try {
        const res = await fetch('/api/pick-file?type=folder');
        const data = await res.json();
        if (data.path) {
          document.getElementById('res-folder-path').value = data.path;
          const folderName = data.path.split('/').filter(Boolean).pop();
          if (!document.getElementById('res-folder-title').value.trim()) {
            document.getElementById('res-folder-title').value = folderName;
          }
          showToast('已选取文件夹: ' + folderName, 'success');
        }
      } catch (e) {
        showToast('选择器调用失败: ' + e.message, 'error');
      }
    }

    async function doUploadResourceFile() {
      const path = document.getElementById('res-file-path').value.trim();
      if (!path) {
        showToast('请先选择或拖拽需要上传的文件！', 'warning');
        return;
      }
      const title = document.getElementById('res-file-title').value.trim();
      const cat = document.getElementById('res-file-cat').value;
      const tags = document.getElementById('res-file-tags').value.trim();
      const desc = document.getElementById('res-file-desc').value.trim();
      const makePost = document.getElementById('res-file-make-post').checked;

      const btn = document.getElementById('res-file-submit-btn');
      btn.disabled = true;
      btn.textContent = '⏳ 正在上传收录...';
      try {
        const res = await fetch('/api/resource/add-file', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ path, title, category: cat, tags, description: desc, make_post: makePost })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message + (data.post_created ? ' 并已生成内嵌阅读博文！' : ''), 'success');
          document.getElementById('res-file-path').value = '';
          document.getElementById('res-file-title').value = '';
          document.getElementById('res-file-desc').value = '';
          loadResources();
        } else {
          showToast('上传失败: ' + data.message, 'error');
        }
      } catch (e) {
        showToast('请求异常: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 上传并收录至资料库';
      }
    }

    async function doUploadResourceFolder() {
      const folder = document.getElementById('res-folder-path').value.trim();
      if (!folder) {
        showToast('请先选择需要打包的文件夹！', 'warning');
        return;
      }
      const title = document.getElementById('res-folder-title').value.trim();
      const cat = document.getElementById('res-folder-cat').value;
      const tags = document.getElementById('res-folder-tags').value.trim();
      const desc = document.getElementById('res-folder-desc').value.trim();

      const btn = document.getElementById('res-folder-submit-btn');
      btn.disabled = true;
      btn.textContent = '🗜️ 正在压缩打包中...';
      try {
        const res = await fetch('/api/resource/add-folder', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ folder, title, category: cat, tags, description: desc })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
          document.getElementById('res-folder-path').value = '';
          document.getElementById('res-folder-title').value = '';
          document.getElementById('res-folder-desc').value = '';
          loadResources();
        } else {
          showToast('打包失败: ' + data.message, 'error');
        }
      } catch (e) {
        showToast('请求异常: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '🗜️ 自动压缩打包为 ZIP 并收录';
      }
    }

    async function confirmDeleteResource(id, title) {
      if (!confirm(`确定要从资料库中移除《${title}》及其本地文件吗？`)) return;
      try {
        const res = await fetch('/api/resource/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ id })
        });
        const data = await res.json();
        if (data.success) {
          showToast('已成功移除资料', 'success');
          loadResources();
        } else {
          showToast('删除失败: ' + data.message, 'error');
        }
      } catch (e) {
        showToast('网络错误: ' + e.message, 'error');
      }
    }

    function openResourceInFinder(filename) {
      fetch('/api/open-file', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ path: 'static/resources/' + filename })
      });
    }

    function copyResourceUrl(url) {
      const fullUrl = window.location.origin + url;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(fullUrl).then(() => {
          showToast('已复制下载直链到剪贴板！', 'success');
        });
      } else {
        prompt('请复制链接：', fullUrl);
      }
    }

    /* 近期笔记智能发现 */
    async function loadRecentNotes() {
      try {
        const res = await fetch('/api/recent-notes');
        const notes = await res.json();
        const chipsContainer = document.getElementById('recent-notes-chips');
        if (!notes || notes.length === 0) {
          chipsContainer.innerHTML = '<span class="chip" style="color:var(--text-muted);">（可点击上方浏览按钮选择笔记）</span>';
          return;
        }
        chipsContainer.innerHTML = notes.map(n => `
          <span class="chip" onclick="selectRecentNote('${escapeJs(n.path)}')">
            ${n.ext === '.ipynb' ? '📓' : '📄'} ${escapeHtml(n.name)} <small style="opacity:0.75;">(${n.rel_time})</small>
          </span>
        `).join('');
      } catch (e) {}
    }

    function selectRecentNote(path) {
      document.getElementById('file-path').value = path;
      showToast('已填入笔记路径', 'success');
    }

    async function pickFile(type) {
      try {
        const res = await fetch('/api/pick-file?type=' + type);
        const data = await res.json();
        if (data.path) {
          if (type === 'image') {
            document.getElementById('gallery-file-path').value = data.path;
          } else {
            document.getElementById('file-path').value = data.path;
          }
          showToast('已成功选择文件', 'success');
        }
      } catch (e) {
        showToast('选择器调用失败：' + e.message, 'error');
      }
    }

    async function pickFolder() {
      try {
        const res = await fetch('/api/pick-file?type=folder');
        const data = await res.json();
        if (data.path) {
          document.getElementById('gallery-batch-folder').value = data.path;
          showToast('已选择文件夹', 'success');
        }
      } catch (e) {
        showToast('文件夹选择失败：' + e.message, 'error');
      }
    }

    function setCategory(cat) { document.getElementById('pub-category').value = cat; }
    function addTag(tag) {
      const el = document.getElementById('pub-tags');
      const cur = el.value.trim();
      el.value = cur ? (cur.includes(tag) ? cur : cur + ',' + tag) : tag;
    }
    function setGitMsg(msg) { document.getElementById('git-msg').value = msg; }

    /* 本地 Hugo 1314 浏览器直连探针（双重保障） */
    async function pingHugoLocal() {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 1200);
        await fetch('http://localhost:1314/', { mode: 'no-cors', cache: 'no-store', signal: controller.signal });
        clearTimeout(timer);
        return true;
      } catch (e) {
        return false;
      }
    }

    /* Hugo 状态 */
    async function checkHugoStatus() {
      try {
        const [apiRunning, directRunning] = await Promise.all([
          fetch('/api/hugo-status?_t=' + Date.now(), { cache: 'no-store' })
            .then(r => r.json())
            .then(d => !!d.running)
            .catch(() => false),
          pingHugoLocal()
        ]);
        const isRunning = apiRunning || directRunning;
        const badge = document.getElementById('hugo-status-badge');
        const text = document.getElementById('hugo-status-text');
        const toggleBtn = document.getElementById('hugo-toggle-btn');
        if (isRunning) {
          badge.className = 'status-badge';
          text.textContent = 'Hugo 服务运行中 (1314)';
          toggleBtn.textContent = '⏹️ 停止服务';
          toggleBtn.className = 'btn btn-sm btn-danger';
        } else {
          badge.className = 'status-badge stopped';
          text.textContent = 'Hugo 未运行';
          toggleBtn.textContent = '▶️ 启动 Hugo';
          toggleBtn.className = 'btn btn-sm';
        }
      } catch (e) {
        const directRunning = await pingHugoLocal();
        const badge = document.getElementById('hugo-status-badge');
        const text = document.getElementById('hugo-status-text');
        const toggleBtn = document.getElementById('hugo-toggle-btn');
        if (directRunning) {
          badge.className = 'status-badge';
          text.textContent = 'Hugo 服务运行中 (1314)';
          toggleBtn.textContent = '⏹️ 停止服务';
          toggleBtn.className = 'btn btn-sm btn-danger';
        } else {
          badge.className = 'status-badge stopped';
          text.textContent = 'Hugo 未运行';
          toggleBtn.textContent = '▶️ 启动 Hugo';
          toggleBtn.className = 'btn btn-sm';
        }
      }
    }
    setInterval(checkHugoStatus, 4000);
    checkHugoStatus();

    async function toggleHugo() {
      const toggleBtn = document.getElementById('hugo-toggle-btn');
      toggleBtn.disabled = true;
      toggleBtn.textContent = '⏳ 处理中...';
      try {
        const res = await fetch('/api/toggle-hugo', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
        } else {
          showToast(data.message || '操作失败', 'error');
        }
      } catch (e) {
        showToast('操作异常：' + e.message, 'error');
      } finally {
        await checkHugoStatus();
        toggleBtn.disabled = false;
      }
    }

    /* 发布笔记 */
    async function doPublish() {
      const path = document.getElementById('file-path').value.trim();
      if (!path) { showToast('请先选择或输入笔记文件的完整路径！', 'error'); return; }

      const btn = document.getElementById('publish-btn');
      const log = document.getElementById('publish-log');
      btn.disabled = true;
      btn.textContent = '⏳ 正在解析并转换附件...';
      log.style.display = 'block';
      log.textContent = '正在读取文件并转换附件为 WebP 格式...\\n';

      try {
        const res = await fetch('/api/publish', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            path: path,
            type: document.getElementById('pub-type').value,
            slug: document.getElementById('pub-slug').value.trim(),
            category: document.getElementById('pub-category').value.trim(),
            tags: document.getElementById('pub-tags').value.trim(),
            draft: document.getElementById('pub-draft').checked
          })
        });
        const data = await res.json();
        log.textContent = data.output || data.message;
        if (data.success) {
          showToast('🎉 发布成功！已生成页面包', 'success');
        } else {
          showToast('❌ 发布失败：' + data.message, 'error');
        }
      } catch (e) {
        showToast('出现异常：' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 立即转换并发布';
      }
    }

    /* 相册单图 / 批量切换 */
    function switchGalleryMode(mode) {
      const singleBtn = document.getElementById('tab-gallery-single-btn');
      const batchBtn = document.getElementById('tab-gallery-batch-btn');
      const singleDiv = document.getElementById('gallery-single-mode');
      const batchDiv = document.getElementById('gallery-batch-mode');
      if (mode === 'single') {
        singleBtn.className = 'btn btn-sm btn-primary';
        batchBtn.className = 'btn btn-sm';
        singleDiv.style.display = 'block';
        batchDiv.style.display = 'none';
      } else {
        singleBtn.className = 'btn btn-sm';
        batchBtn.className = 'btn btn-sm btn-primary';
        singleDiv.style.display = 'none';
        batchDiv.style.display = 'block';
      }
    }

    /* 相册管理 */
    async function loadGallery() {
      try {
        const res = await fetch('/api/gallery');
        allGallery = await res.json();
        document.getElementById('gallery-counter').textContent = allGallery.length;
        document.getElementById('count-all').textContent = allGallery.length;
        document.getElementById('count-anime').textContent = allGallery.filter(x => x.category === 'anime').length;
        document.getElementById('count-photo').textContent = allGallery.filter(x => x.category === 'photography').length;
        document.getElementById('count-daily').textContent = allGallery.filter(x => x.category === 'daily').length;
        renderGallery();
      } catch (e) {
        document.getElementById('gallery-grid').innerHTML = '<div style="color:var(--accent);padding:20px;">加载相册失败：' + e.message + '</div>';
      }
    }

    function filterGallery(cat, btn) {
      curGalleryCat = cat;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderGallery();
    }

    function renderGallery() {
      const container = document.getElementById('gallery-grid');
      const list = curGalleryCat === 'all' ? allGallery : allGallery.filter(x => x.category === curGalleryCat);
      if (!list || list.length === 0) {
        container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-muted);">暂无此分类照片</div>';
        return;
      }
      container.innerHTML = list.map((item, idx) => `
        <div class="gallery-card" onclick="openGalleryModal(${idx})">
          <div class="gallery-card-img-wrap">
            <img class="gallery-card-img" src="${item.image}" alt="${escapeHtml(item.caption)}" loading="lazy">
            <span class="gallery-card-badge">#${item.number}</span>
          </div>
          <div class="gallery-card-body">
            <div>
              <div class="gallery-card-title" title="${escapeHtml(item.caption)}">${escapeHtml(item.caption) || '未命名作品'}</div>
              <div class="gallery-card-meta">
                <span>比例: ${item.ratio}</span>
                <span>${item.category === 'anime' ? '🎨 动漫' : (item.category === 'photography' ? '📷 摄影' : '☕ 日常')}</span>
              </div>
              ${item.tags && item.tags.length ? `<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:6px;">${item.tags.map(t => `<span class="badge" style="font-size:0.72rem;padding:1px 5px;">#${escapeHtml(t)}</span>`).join('')}</div>` : ''}
            </div>
            <div class="gallery-card-actions" onclick="event.stopPropagation()">
              <button class="btn btn-sm btn-primary" onclick="openGalleryEditModal('${escapeJs(item.image)}')">✏️ 编辑</button>
              <a class="btn btn-sm" href="${item.image}" target="_blank">🔍 原图</a>
              <button class="btn btn-sm btn-danger" onclick="confirmDeleteGallery('${item.image}', '${escapeHtml(item.caption)}')">🗑️ 移除</button>
            </div>
          </div>
        </div>
      `).join('');
    }

    function openGalleryModal(idx) {
      const list = curGalleryCat === 'all' ? allGallery : allGallery.filter(x => x.category === curGalleryCat);
      const item = list[idx];
      if (!item) return;
      curModalItem = item;
      document.getElementById('modal-title').textContent = (item.caption || '作品详情') + ' (#' + item.number + ')';
      document.getElementById('modal-img').src = item.image;
      document.getElementById('modal-orig-link').href = item.image;
      document.getElementById('modal-meta').innerHTML = `
        <strong>分类：</strong>${item.category} &nbsp;|&nbsp; 
        <strong>长宽比：</strong>${item.ratio} &nbsp;|&nbsp; 
        <strong>标签：</strong>${(item.tags || []).join(', ') || '无'}
      `;
      document.getElementById('gallery-modal').classList.add('is-active');
    }

    function editFromModal() {
      if (!curModalItem) return;
      const img = curModalItem.image;
      closeModalDirect();
      openGalleryEditModal(img);
    }

    function closeModal(e) {
      if (e.target.id === 'gallery-modal') {
        closeModalDirect();
      }
    }
    function closeModalDirect() {
      document.getElementById('gallery-modal').classList.remove('is-active');
    }
    function deleteFromModal() {
      if (!curModalItem) return;
      closeModalDirect();
      confirmDeleteGallery(curModalItem.image, curModalItem.caption);
    }

    /* 相册快捷编辑 */
    function openGalleryEditModal(imageUrl) {
      const item = allGallery.find(g => g.image === imageUrl);
      if (!item) {
        showToast('未找到该图片数据', 'error');
        return;
      }
      document.getElementById('edit-gallery-image').value = item.image;
      document.getElementById('edit-gallery-preview').src = item.image;
      document.getElementById('edit-gallery-caption').value = item.caption || '';
      document.getElementById('edit-gallery-category').value = item.category || 'anime';
      document.getElementById('edit-gallery-date').value = item.date || '';
      document.getElementById('edit-gallery-tags').value = (item.tags || []).join(', ');
      document.getElementById('edit-gallery-modal').classList.add('is-active');
    }

    function closeGalleryEditModal(e) {
      if (e.target.id === 'edit-gallery-modal') closeGalleryEditModalDirect();
    }
    function closeGalleryEditModalDirect() {
      document.getElementById('edit-gallery-modal').classList.remove('is-active');
    }

    async function submitEditGallery() {
      const image = document.getElementById('edit-gallery-image').value;
      const caption = document.getElementById('edit-gallery-caption').value.trim();
      const category = document.getElementById('edit-gallery-category').value;
      const dateVal = document.getElementById('edit-gallery-date').value.trim();
      const tagsStr = document.getElementById('edit-gallery-tags').value.trim();
      const tags = tagsStr ? tagsStr.split(/[,，]/).map(t => t.trim()).filter(Boolean) : [];

      const btn = document.getElementById('save-gallery-btn');
      btn.disabled = true;
      btn.textContent = '⏳ 保存中...';

      try {
        const res = await fetch('/api/gallery/edit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            image: image,
            caption: caption,
            category: category,
            date: dateVal,
            tags: tags
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
          closeGalleryEditModalDirect();
          await loadGallery();
        } else {
          showToast('保存失败: ' + data.message, 'error');
        }
      } catch (e) {
        showToast('请求异常: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '💾 保存更改';
      }
    }

    async function doAddGallery() {
      const path = document.getElementById('gallery-file-path').value.trim();
      if (!path) { showToast('请先选择或输入图片文件路径！', 'error'); return; }

      const btn = document.getElementById('add-gallery-btn');
      const log = document.getElementById('gallery-log');
      btn.disabled = true;
      btn.textContent = '⏳ 正在测量宽高比并转换 WebP...';
      log.style.display = 'block';
      log.textContent = '正在读取图片并使用 macOS 底层引擎提取尺寸...\\n';

      try {
        const res = await fetch('/api/gallery/add', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            path: path,
            category: document.getElementById('gallery-cat').value,
            caption: document.getElementById('gallery-caption').value.trim(),
            tags: document.getElementById('gallery-tags').value.trim()
          })
        });
        const data = await res.json();
        log.textContent = data.message;
        if (data.success) {
          showToast('🎉 成功加入相册！', 'success');
          document.getElementById('gallery-file-path').value = '';
          document.getElementById('gallery-caption').value = '';
          loadGallery();
        } else {
          showToast(data.message, 'error');
        }
      } catch (e) {
        showToast('操作失败：' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '✨ 自动测量宽高、转码并加入相册';
      }
    }

    async function doBatchGallery() {
      const folder = document.getElementById('gallery-batch-folder').value.trim();
      if (!folder) { showToast('请先选择图片文件夹！', 'error'); return; }

      const btn = document.getElementById('batch-gallery-btn');
      const log = document.getElementById('gallery-log');
      btn.disabled = true;
      btn.textContent = '⏳ 正在批量处理中...';
      log.style.display = 'block';
      log.textContent = '正在扫描并逐个测量转码...\\n';

      try {
        const res = await fetch('/api/gallery/batch-add', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            folder: folder,
            category: document.getElementById('gallery-batch-cat').value,
            tags: document.getElementById('gallery-batch-tags').value.trim()
          })
        });
        const data = await res.json();
        log.textContent = data.message;
        if (data.success) {
          showToast(data.message, 'success');
          loadGallery();
        } else {
          showToast(data.message, 'error');
        }
      } catch (e) {
        showToast('批量导入异常：' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 一键批量扫描并导入相册';
      }
    }

    async function confirmDeleteGallery(imgUrl, caption) {
      if (!confirm(`确定要从相册中移除《${caption || imgUrl}》吗？`)) return;
      try {
        const res = await fetch('/api/gallery/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({image: imgUrl})
        });
        const data = await res.json();
        if (data.success) {
          showToast('已从相册中移除', 'success');
          loadGallery();
        } else {
          showToast('移除失败：' + data.message, 'error');
        }
      } catch (e) { showToast('请求异常：' + e.message, 'error'); }
    }

    /* 文章列表管理 */
    async function loadArticles() {
      try {
        const res = await fetch('/api/articles');
        allArticles = await res.json();
        document.getElementById('articles-counter').textContent = allArticles.length;
        
        const posts = allArticles.filter(x => x.type === 'post').length;
        const diaries = allArticles.filter(x => x.type === 'diary').length;
        const drafts = allArticles.filter(x => x.draft).length;
        document.getElementById('stat-posts').textContent = posts;
        document.getElementById('stat-diaries').textContent = diaries;
        document.getElementById('stat-drafts').textContent = drafts;

        renderArticles(allArticles);
      } catch (e) {
        document.getElementById('articles-tbody').innerHTML = '<tr><td colspan="6" style="color:var(--accent);">加载失败：' + e.message + '</td></tr>';
      }
    }

    function renderArticles(list) {
      const tbody = document.getElementById('articles-tbody');
      if (!list || list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:24px;">暂无匹配文章</td></tr>';
        return;
      }
      tbody.innerHTML = list.map(item => `
        <tr>
          <td><span class="badge ${item.type === 'post' ? 'badge-post' : 'badge-diary'}">${item.type_label}</span></td>
          <td><span class="badge ${item.draft ? 'badge-draft' : 'badge-active'}">${item.draft ? '🟡 已下架' : '🟢 正常'}</span></td>
          <td>
            <small style="color:var(--text-muted);">${item.date}</small>
            ${item.lastmod ? `<div style="font-size:0.72rem;color:var(--primary);margin-top:2px;" title="文末更新时间">🕒 ${item.lastmod.slice(0, 16).replace('T', ' ')}</div>` : ''}
          </td>
          <td>
            <strong>${escapeHtml(item.title)}</strong>
            ${item.tags && item.tags.length ? `<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:5px;">${item.tags.map(t => `<span class="badge" style="font-size:0.73rem;padding:1px 6px;">#${escapeHtml(t)}</span>`).join('')}</div>` : ''}
          </td>
          <td><code style="font-size:0.8rem;color:var(--text-muted);">${escapeHtml(item.slug)}</code></td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <a class="btn btn-sm" href="http://localhost:1314${item.url}" target="_blank" title="在新标签页预览">👁️ 预览</a>
              <button class="btn btn-sm btn-primary" onclick="openArticleEditModal('${escapeJs(item.slug)}')">✏️ 快捷编辑</button>
              <button class="btn btn-sm" onclick="openInLocalEditor('${escapeJs(item.path)}')">📂 本地打开</button>
              <button class="btn btn-sm" onclick="toggleDraft('${item.slug}', ${!item.draft})">${item.draft ? '🟢 上架' : '🟡 下架'}</button>
              <button class="btn btn-sm btn-danger" onclick="confirmDelete('${item.slug}', '${escapeHtml(item.title)}')">🗑️ 删除</button>
            </div>
          </td>
        </tr>
      `).join('');
    }

    /* 文章/日记 快捷编辑 */
    function openArticleEditModal(slug) {
      const item = allArticles.find(a => a.slug === slug);
      if (!item) {
        showToast('未找到该文章数据', 'error');
        return;
      }
      document.getElementById('edit-article-original-slug').value = item.slug;
      document.getElementById('edit-article-slug').value = item.slug;
      document.getElementById('edit-article-title').value = item.title || '';
      document.getElementById('edit-article-tags').value = (item.tags || []).join(', ');

      const catInput = document.getElementById('edit-article-categories');
      if (item.type === 'diary') {
        catInput.placeholder = '如：生活手记, 读书札记, 折腾记录（逗号分隔）';
        catInput.value = (item.categories || []).join(', ');
      } else {
        catInput.placeholder = '如：型月, 随笔（多个分类用逗号分隔）';
        catInput.value = (item.categories || []).join(', ');
      }
      document.getElementById('edit-article-cat-group').style.display = 'block';

      document.getElementById('edit-article-summary').value = item.summary || '';
      document.getElementById('edit-article-update-lastmod').checked = false;
      document.getElementById('edit-article-modal-title').textContent = `✏️ 快捷编辑：${item.type_label}「${item.title || item.slug}」`;
      document.getElementById('edit-article-modal').classList.add('is-active');
    }

    function closeArticleEditModal(e) {
      if (e.target.id === 'edit-article-modal') closeArticleEditModalDirect();
    }
    function closeArticleEditModalDirect() {
      document.getElementById('edit-article-modal').classList.remove('is-active');
    }

    async function submitEditArticle() {
      const originalSlug = document.getElementById('edit-article-original-slug').value;
      const newSlug = document.getElementById('edit-article-slug').value.trim();
      const title = document.getElementById('edit-article-title').value.trim();
      const tagsStr = document.getElementById('edit-article-tags').value.trim();
      const tags = tagsStr ? tagsStr.split(/[,，]/).map(t => t.trim()).filter(Boolean) : [];
      const catsStr = document.getElementById('edit-article-categories').value.trim();
      const categories = catsStr ? catsStr.split(/[,，]/).map(c => c.trim()).filter(Boolean) : [];
      const summary = document.getElementById('edit-article-summary').value.trim();
      const updateLastmod = document.getElementById('edit-article-update-lastmod').checked;

      const btn = document.getElementById('save-article-btn');
      btn.disabled = true;
      btn.textContent = '⏳ 保存中...';

      try {
        const res = await fetch('/api/article/edit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            slug: originalSlug,
            new_slug: newSlug,
            title: title,
            tags: tags,
            categories: categories,
            summary: summary,
            update_lastmod: updateLastmod
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
          closeArticleEditModalDirect();
          await loadArticles();
        } else {
          showToast('保存失败: ' + data.message, 'error');
        }
      } catch (e) {
        showToast('请求异常: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '💾 保存更改';
      }
    }

    function filterArticles() {
      const q = document.getElementById('search-input').value.toLowerCase().trim();
      if (!q) { renderArticles(allArticles); return; }
      const filtered = allArticles.filter(a => a.title.toLowerCase().includes(q) || a.slug.toLowerCase().includes(q) || a.type_label.includes(q));
      renderArticles(filtered);
    }

    async function openInLocalEditor(path) {
      try {
        const res = await fetch('/api/open-file', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({path: path})
        });
        const data = await res.json();
        if (data.success) {
          showToast('已在系统默认应用中打开', 'success');
        } else {
          showToast(data.message, 'error');
        }
      } catch (e) { showToast('打开异常：' + e.message, 'error'); }
    }

    async function toggleDraft(slug, makeDraft) {
      try {
        const res = await fetch('/api/set-draft', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({slug: slug, draft: makeDraft})
        });
        const data = await res.json();
        if (data.success) {
          showToast(`已${makeDraft ? '下架为草稿' : '重新上架'}`, 'success');
          loadArticles();
        } else {
          showToast('操作失败：' + data.message, 'error');
        }
      } catch (e) { showToast('请求异常：' + e.message, 'error'); }
    }

    async function confirmDelete(slug, title) {
      if (!confirm(`确定彻底删除《${title}》及其专属附件吗？此操作不可撤销。`)) return;
      try {
        const res = await fetch('/api/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({slug: slug})
        });
        const data = await res.json();
        if (data.success) {
          showToast('已安全删除文章', 'success');
          loadArticles();
        } else {
          showToast('删除失败：' + data.message, 'error');
        }
      } catch (e) { showToast('请求异常：' + e.message, 'error'); }
    }

    /* Git 部署 */
    async function checkGitStatus() {
      try {
        const res = await fetch('/api/git-status');
        const data = await res.json();
        const summary = document.getElementById('git-status-summary');
        if (data.clean) {
          summary.innerHTML = '<span style="color:var(--success);">🟢 工作区干净，所有文件已是最新 (分支: ' + data.branch + ')</span>';
        } else {
          summary.innerHTML = '<span style="color:var(--warning);">🟡 检测到 ' + data.changed_count + ' 个文件待提交推送 (分支: ' + data.branch + ')</span>';
        }
      } catch (e) {}
    }

    async function doDeploy() {
      const msg = document.getElementById('git-msg').value.trim() || 'feat: 更新博客内容';
      const btn = document.getElementById('deploy-btn');
      const log = document.getElementById('deploy-log');

      btn.disabled = true;
      btn.textContent = '⏳ 正在推送到 GitHub...';
      log.style.display = 'block';
      log.textContent = '正在执行 git add . && git commit && git push origin main...\\n';

      try {
        const res = await fetch('/api/git-push', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: msg})
        });
        const data = await res.json();
        log.textContent = data.output;
        if (data.success) {
          showToast('🎉 推送成功！已触发自动构建上线', 'success');
          checkGitStatus();
        } else {
          showToast('❌ 推送遇到问题，请查看日志', 'error');
        }
      } catch (e) {
        showToast('网络异常：' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 提交并推送到 GitHub';
      }
    }

    async function doPull() {
      const btn = document.getElementById('pull-btn');
      const log = document.getElementById('deploy-log');
      btn.disabled = true;
      btn.textContent = '⏳ 正在拉取远程更新...';
      log.style.display = 'block';
      log.textContent = '正在执行 git pull --rebase origin main...\\n';

      try {
        const res = await fetch('/api/git-pull', { method: 'POST' });
        const data = await res.json();
        log.textContent = data.output;
        if (data.success) {
          showToast('🎉 拉取完成，本地代码已是最新！', 'success');
          checkGitStatus();
          loadArticles();
        } else {
          showToast('❌ 拉取遇到问题，请检查日志', 'error');
        }
      } catch (e) {
        showToast('网络异常：' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '⬇️ 拉取远程更新 (Git Pull)';
      }
    }

    async function doBackup() {
      const btn = document.getElementById('backup-btn');
      btn.disabled = true;
      btn.textContent = '⏳ 正在压缩打包中...';
      showToast('正在创建全站备份包...', 'info');
      try {
        const res = await fetch('/api/backup', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          showToast(data.message, 'success');
        } else {
          showToast(data.message, 'error');
        }
      } catch (e) {
        showToast('备份异常: ' + e.message, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '📦 一键打包备份全站 (ZIP)';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function escapeJs(str) {
      if (!str) return '';
      return JSON.stringify(String(str)).slice(1, -1);
    }

    // 支持拖拽文件直接识别填充路径
    window.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
    window.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!e.dataTransfer || !e.dataTransfer.files || e.dataTransfer.files.length === 0) return;
      const file = e.dataTransfer.files[0];
      const isResourcesTab = document.getElementById('tab-resources').style.display === 'block';
      const targetInputId = isResourcesTab ? 'res-file-path' : 'file-path';

      if (file.path) {
        document.getElementById(targetInputId).value = file.path;
        if (isResourcesTab && !document.getElementById('res-file-title').value.trim()) {
          document.getElementById('res-file-title').value = file.name.replace(/\.[^.]+$/, '');
        }
        showToast('已识别拖入文件: ' + file.name, 'success');
        return;
      }
      if (file.name) {
        showToast('正在定位拖入文件: ' + file.name, 'info');
        try {
          const res = await fetch('/api/find-file?name=' + encodeURIComponent(file.name));
          const data = await res.json();
          if (data.found) {
            document.getElementById(targetInputId).value = data.found;
            if (isResourcesTab && !document.getElementById('res-file-title').value.trim()) {
              document.getElementById('res-file-title').value = file.name.replace(/\.[^.]+$/, '');
            }
            showToast('已定位文件路径: ' + data.found, 'success');
          } else {
            showToast('已检测到文件名 ' + file.name + '，建议点击“浏览文件”直接选取', 'warning');
            document.getElementById(targetInputId).value = file.name;
          }
        } catch (err) {
          document.getElementById(targetInputId).value = file.name;
        }
      }
    });

    // 初始化加载
    loadRecentNotes();
    loadResources();
  </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def serve_file(self, filepath: Path):
        mime = MIME_TYPES.get(filepath.suffix.lower(), 'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(filepath.stat().st_size))
        self.send_header('Cache-Control', 'max-age=3600')
        self.end_headers()
        with open(filepath, 'rb') as f:
            shutil.copyfileobj(f, self.wfile)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()

            running = is_hugo_running()
            badge_class = 'status-badge' if running else 'status-badge stopped'
            status_text = 'Hugo 服务运行中 (1314)' if running else 'Hugo 未运行'
            btn_class = 'btn btn-sm btn-danger' if running else 'btn btn-sm'
            btn_text = '⏹️ 停止服务' if running else '▶️ 启动 Hugo'

            try:
                articles_count = len(get_all_articles())
            except Exception:
                articles_count = 0
            try:
                gallery_count = len(get_gallery_images())
            except Exception:
                gallery_count = 0
            try:
                resources_count = len(parse_resources_yaml())
            except Exception:
                resources_count = 0

            html = HTML_PAGE \
                .replace('__HUGO_BADGE_CLASS__', badge_class) \
                .replace('__HUGO_STATUS_TEXT__', status_text) \
                .replace('__HUGO_BTN_CLASS__', btn_class) \
                .replace('__HUGO_BTN_TEXT__', btn_text) \
                .replace('__ARTICLES_COUNT__', str(articles_count)) \
                .replace('__GALLERY_COUNT__', str(gallery_count)) \
                .replace('__RESOURCES_COUNT__', str(resources_count))

            self.wfile.write(html.encode('utf-8'))
        elif url.path.startswith('/images/'):
            local_path = (BLOG_ROOT / 'static' / url.path.lstrip('/')).resolve()
            if local_path.exists() and local_path.is_file():
                self.serve_file(local_path)
            else:
                self.send_error(404, "Image Not Found")
        elif url.path.startswith('/resources/'):
            local_path = (BLOG_ROOT / 'static' / url.path.lstrip('/')).resolve()
            if local_path.exists() and local_path.is_file():
                self.serve_file(local_path)
            else:
                self.send_error(404, "Resource Not Found")
        elif url.path.startswith('/posts/') or url.path.startswith('/diary/'):
            local_path = (BLOG_ROOT / 'content' / url.path.lstrip('/')).resolve()
            if local_path.exists() and local_path.is_file():
                self.serve_file(local_path)
            else:
                self.send_error(404, "File Not Found")
        elif url.path == '/api/articles':
            articles = get_all_articles()
            self.send_json(articles)
        elif url.path == '/api/gallery':
            items = get_gallery_images()
            self.send_json(items)
        elif url.path == '/api/resources':
            items = parse_resources_yaml()
            self.send_json(items)
        elif url.path == '/api/recent-notes':
            notes = scan_recent_notes()
            self.send_json(notes)
        elif url.path == '/api/hugo-status':
            running = is_hugo_running()
            self.send_json({'running': running})
        elif url.path == '/api/git-status':
            status = get_git_status()
            self.send_json(status)
        elif url.path == '/api/pick-file':
            query = urllib.parse.parse_qs(url.query)
            ftype = query.get('type', ['note'])[0]
            if ftype == 'image':
                selected = pick_file_macos("选择相册图片文件", '{"png", "jpg", "jpeg", "webp", "gif"}')
            elif ftype == 'folder':
                selected = pick_file_macos("选择文件夹", is_folder=True)
            elif ftype == 'resource':
                selected = pick_file_macos("选择上传到资料库的文件", file_types=None)
            else:
                selected = pick_file_macos("选择笔记、Notebook或PDF文件", '{"md", "ipynb", "pdf", "markdown"}')
            self.send_json({'path': selected})
        elif url.path == '/api/find-file':
            query = urllib.parse.parse_qs(url.query)
            fname = query.get('name', [''])[0].strip()
            found = ""
            if fname:
                try:
                    res = subprocess.run(['mdfind', '-name', fname], capture_output=True, text=True, timeout=1.5)
                    lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
                    clean_lines = [l for l in lines if not any(p.startswith('.') for p in Path(l).parts) and 'Trash' not in l]
                    if clean_lines:
                        found = clean_lines[0]
                except Exception:
                    pass
                if not found:
                    home = Path.home()
                    for sdir in [home / 'Desktop', home / 'Downloads', BLOG_ROOT]:
                        if sdir.exists():
                            for p in sdir.glob(fname):
                                found = str(p.resolve())
                                break
                            if found:
                                break
            self.send_json({'found': found})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else '{}'
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if url.path == '/api/publish':
            file_path = payload.get('path', '').strip()
            if not file_path:
                self.send_json({'success': False, 'message': '文件路径不能为空'})
                return

            p = Path(file_path).expanduser().resolve()
            if not p.exists():
                self.send_json({'success': False, 'message': f'找不到文件: {file_path}'})
                return

            note_type = payload.get('type', 'post')
            slug = payload.get('slug', '').strip() or None
            category = payload.get('category', '').strip() or None
            tags_raw = payload.get('tags', '').strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
            draft = bool(payload.get('draft', False))

            import io
            from contextlib import redirect_stdout, redirect_stderr
            log_buffer = io.StringIO()

            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                if p.suffix.lower() == '.ipynb':
                    ok = process_ipynb_notebook(p, note_type, slug, tags, category, draft)
                elif p.suffix.lower() == '.pdf':
                    ok = process_pdf_note(p, note_type, slug, tags, category, draft)
                else:
                    ok = process_obsidian_note(p, note_type, slug, tags, category, draft)

            output_text = log_buffer.getvalue()
            self.send_json({'success': ok, 'message': '发布完成' if ok else '发布失败', 'output': output_text})

        elif url.path == '/api/resource/add-file':
            fpath = payload.get('path', '').strip()
            cat = payload.get('category', 'docs').strip()
            title = payload.get('title', '').strip()
            desc = payload.get('description', '').strip()
            tags_raw = payload.get('tags', '').strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
            make_post = bool(payload.get('make_post', False))

            p = Path(fpath).expanduser().resolve()
            ok, msg, item = add_resource_file(p, cat, title, desc, tags)

            post_created = False
            if ok and make_post and p.suffix.lower() == '.pdf':
                try:
                    post_created = process_pdf_note(p, note_type='post', custom_slug=None, tags=tags, category="技术文档", draft=False, description=desc)
                except Exception as e:
                    msg += f"（生成博文时遇到提示：{e}）"

            self.send_json({'success': ok, 'message': msg, 'post_created': post_created})

        elif url.path == '/api/resource/add-folder':
            folder = payload.get('folder', '').strip()
            cat = payload.get('category', 'archives').strip()
            title = payload.get('title', '').strip()
            desc = payload.get('description', '').strip()
            tags_raw = payload.get('tags', '').strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]

            p = Path(folder).expanduser().resolve()
            ok, msg, item = add_resource_folder(p, cat, title, desc, tags)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/resource/delete':
            res_id = payload.get('id', '').strip()
            ok, msg = delete_resource(res_id)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/toggle-hugo':
            running = is_port_in_use(1314)
            if running:
                ok, msg = stop_hugo_server()
            else:
                ok, msg = start_hugo_server()
            self.send_json({'success': ok, 'message': msg, 'running': is_port_in_use(1314)})

        elif url.path == '/api/gallery/add':
            fpath = payload.get('path', '').strip()
            cat = payload.get('category', 'anime').strip()
            caption = payload.get('caption', '').strip()
            tags_raw = payload.get('tags', '').strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
            ok, msg = add_gallery_image(fpath, cat, caption, tags)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/gallery/batch-add':
            folder = payload.get('folder', '').strip()
            cat = payload.get('category', 'photography').strip()
            tags_raw = payload.get('tags', '').strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
            ok, msg, count = batch_add_gallery(folder, cat, tags)
            self.send_json({'success': ok, 'message': msg, 'count': count})

        elif url.path == '/api/gallery/delete':
            img_url = payload.get('image', '').strip()
            ok, msg = delete_gallery_image(img_url)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/gallery/edit':
            img_url = payload.get('image', '').strip()
            caption = payload.get('caption', '').strip() or None
            category = payload.get('category', '').strip() or None
            date_val = payload.get('date', '').strip() or None
            tags_raw = payload.get('tags', '')
            if isinstance(tags_raw, list):
                tags = [str(t).strip() for t in tags_raw if str(t).strip()]
            else:
                tags = [t.strip() for t in str(tags_raw).split(',') if t.strip()]
            ok, msg = update_gallery_image(img_url, new_caption=caption, new_category=category, new_tags=tags, new_date=date_val)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/article/edit':
            slug = payload.get('slug', '').strip()
            new_slug = payload.get('new_slug', '').strip() or None
            title = payload.get('title', '').strip() or None
            tags_raw = payload.get('tags', '')
            if isinstance(tags_raw, list):
                tags = [str(t).strip() for t in tags_raw if str(t).strip()]
            else:
                tags = [t.strip() for t in str(tags_raw).split(',') if t.strip()]
            cat_raw = payload.get('categories', payload.get('category', ''))
            if isinstance(cat_raw, list):
                cats = [str(c).strip() for c in cat_raw if str(c).strip()]
            elif cat_raw:
                cats = [c.strip() for c in str(cat_raw).split(',') if c.strip()]
            else:
                cats = None
            summary = payload.get('summary', '').strip() or None
            update_lastmod = bool(payload.get('update_lastmod', False))

            ok, msg = edit_article_meta(slug, new_slug=new_slug, title=title, tags=tags, categories=cats, summary=summary, update_lastmod=update_lastmod)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/open-file':
            target_path = payload.get('path', '').strip()
            ok, msg = open_local_path(target_path)
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/set-draft':
            slug = payload.get('slug', '').strip()
            make_draft = bool(payload.get('draft', True))
            ok = set_draft_status(slug, set_draft=make_draft)
            self.send_json({'success': ok, 'message': f'已{"下架" if make_draft else "上架"}' if ok else '未找到该文章'})

        elif url.path == '/api/delete':
            slug = payload.get('slug', '').strip()
            ok = delete_article(slug)
            self.send_json({'success': ok, 'message': '已删除' if ok else '删除失败'})

        elif url.path == '/api/backup':
            ok, msg = create_site_backup()
            self.send_json({'success': ok, 'message': msg})

        elif url.path == '/api/git-push':
            msg = payload.get('message', '').strip() or 'feat: 更新博客内容'
            commands = [
                ['git', 'add', '.'],
                ['git', 'commit', '-m', msg],
                ['git', 'push', 'origin', 'main']
            ]
            full_output = []
            success = True
            for cmd in commands:
                full_output.append(f"$ {' '.join(cmd)}")
                res = subprocess.run(cmd, cwd=BLOG_ROOT, capture_output=True, text=True)
                if res.stdout:
                    full_output.append(res.stdout)
                if res.stderr:
                    full_output.append(res.stderr)
                if res.returncode != 0 and 'commit' not in cmd[1]:
                    success = False
                    break
            self.send_json({'success': success, 'output': '\n'.join(full_output)})
        elif url.path == '/api/git-pull':
            cmd = ['git', 'pull', '--rebase', 'origin', 'main']
            full_output = [f"$ {' '.join(cmd)}"]
            res = subprocess.run(cmd, cwd=BLOG_ROOT, capture_output=True, text=True)
            if res.stdout:
                full_output.append(res.stdout)
            if res.stderr:
                full_output.append(res.stderr)
            success = (res.returncode == 0)
            self.send_json({'success': success, 'output': '\n'.join(full_output)})
        elif url.path == '/api/toggle-hugo':
            if is_hugo_running():
                ok, msg = stop_hugo_server()
            else:
                ok, msg = start_hugo_server()
            self.send_json({'success': ok, 'message': msg, 'running': is_hugo_running()})
        else:
            self.send_error(404, "API Not Found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def run_server():
    atexit.register(stop_hugo_server)

    # 自动伴随启动 Hugo 本地预览服务 (1314)，实现完全去终端化的一键体验
    if not is_hugo_running():
        print("⚡ 正在伴随启动 Hugo 本地实时预览服务 (1314)...")
        start_hugo_server()

    port = get_available_port(PORT)
    server = ThreadingHTTPServer(('127.0.0.1', port), DashboardHandler)
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"✨ 有珠之夜 · 博客管理控制台 4.0 Pro 已就绪！")
    print(f"🌐 可视化管理台：{url}")
    print(f"📖 本地实时预览：http://localhost:1314/")
    print(f"💡 浏览器已自动打开控制台，双击即可无缝管理与预览。")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        print("\n👋 正在安全停止控制台与预览服务...")
        stop_hugo_server()
        try:
            server.server_close()
        except Exception:
            pass
        print("👋 已安全退出。")

if __name__ == '__main__':
    run_server()
