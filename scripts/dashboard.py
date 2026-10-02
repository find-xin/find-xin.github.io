#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard.py - 博客本地可视化控制台 (Web UI)
无需任何外部依赖，启动后自动打开浏览器。
支持：
1. 可视化发布 Obsidian 笔记 (.md) 与 Jupyter Notebook (.ipynb)
2. 全站文章管理（实时搜索、一键下架/重新上架、一键删除）
3. 一键提交并推送到 GitHub
4. 本地 Hugo 服务一键启停与预览
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
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# 导入核心发布与管理模块
CURRENT_DIR = Path(__file__).resolve().parent
BLOG_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))
from publish_obsidian import (
    get_all_articles,
    set_draft_status,
    delete_article,
    process_obsidian_note,
    process_ipynb_notebook
)

PORT = 2026
HUGO_PROCESS = None

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_available_port(start_port: int = 2026) -> int:
    for p in range(start_port, start_port + 20):
        if not is_port_in_use(p):
            return p
    return start_port

def start_hugo_server():
    global HUGO_PROCESS
    if is_port_in_use(1314):
        return True, "Hugo 服务已在运行中 (端口 1314)"
    try:
        HUGO_PROCESS = subprocess.Popen(
            ['hugo', 'server', '-D', '--port', '1314', '--bind', '127.0.0.1', '--disableFastRender'],
            cwd=BLOG_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        import time
        time.sleep(1)
        return True, "已启动 Hugo 本地预览服务"
    except Exception as e:
        return False, f"启动 Hugo 失败: {e}"

def stop_hugo_server():
    global HUGO_PROCESS
    if HUGO_PROCESS and HUGO_PROCESS.poll() is None:
        try:
            HUGO_PROCESS.terminate()
            HUGO_PROCESS.wait(timeout=2)
        except Exception:
            HUGO_PROCESS.kill()
        HUGO_PROCESS = None
    try:
        subprocess.run(['pkill', '-f', 'hugo server'], capture_output=True)
    except Exception:
        pass
    return True, "已停止 Hugo 服务"

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

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>find-xin 博客可视化控制台</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>✨</text></svg>">
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --accent: #ff4757;
      --success: #10b981;
      --warning: #f59e0b;
      --code-bg: #0f172a;
      --code-text: #f8fafc;
      --radius: 12px;
      --shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
    }
    body.dark {
      --bg: #0b0f19;
      --card-bg: #131b2e;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --border: #1e293b;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --code-bg: #070b14;
      --shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      transition: background 0.3s ease, color 0.3s ease;
    }
    .header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 14px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .header-left { display: flex; align-items: center; gap: 14px; }
    .brand-title { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .brand-title span { color: var(--accent); }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.8rem;
      padding: 4px 10px;
      border-radius: 99px;
      background: rgba(16, 185, 129, 0.1);
      color: var(--success);
      font-weight: 500;
    }
    .status-badge.stopped { background: rgba(100, 116, 139, 0.1); color: var(--text-muted); }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    .header-right { display: flex; align-items: center; gap: 12px; }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text);
      transition: all 0.2s ease;
      text-decoration: none;
    }
    .btn:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-1px); }
    .btn-primary { background: var(--primary); color: #fff; border-color: var(--primary); }
    .btn-primary:hover { background: var(--primary-hover); color: #fff; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25); }
    .btn-danger { color: var(--accent); }
    .btn-danger:hover { background: rgba(255, 71, 87, 0.1); border-color: var(--accent); }
    .btn-sm { padding: 4px 10px; font-size: 0.82rem; border-radius: 6px; }

    .container { max-width: 1100px; margin: 28px auto; padding: 0 20px; }
    .nav-tabs {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
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

    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: var(--shadow);
    }
    .card-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
    
    .form-group { margin-bottom: 18px; }
    .form-label { display: block; font-size: 0.88rem; font-weight: 600; margin-bottom: 6px; color: var(--text); }
    .form-hint { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
    .form-input {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font-size: 0.92rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15); }
    
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    @media (max-width: 680px) { .grid-2 { grid-template-columns: 1fr; } }

    .chip-group { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .chip {
      padding: 4px 10px;
      border-radius: 99px;
      font-size: 0.8rem;
      border: 1px solid var(--border);
      background: var(--bg);
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.2s;
    }
    .chip:hover { border-color: var(--primary); color: var(--primary); }

    .terminal-box {
      background: var(--code-bg);
      color: var(--code-text);
      padding: 16px;
      border-radius: 8px;
      font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.86rem;
      line-height: 1.6;
      max-height: 240px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
      margin-top: 14px;
      display: none;
    }

    .table-responsive { width: 100%; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-weight: 600; color: var(--text-muted); background: var(--bg); }
    tr:hover td { background: rgba(99, 102, 241, 0.03); }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.76rem;
      font-weight: 600;
    }
    .badge-post { background: rgba(99, 102, 241, 0.12); color: var(--primary); }
    .badge-diary { background: rgba(245, 158, 11, 0.12); color: var(--warning); }
    .badge-active { background: rgba(16, 185, 129, 0.12); color: var(--success); }
    .badge-draft { background: rgba(100, 116, 139, 0.15); color: var(--text-muted); }

    .article-thumb { width: 44px; height: 32px; border-radius: 4px; object-fit: cover; vertical-align: middle; margin-right: 8px; }
  </style>
</head>
<body>
  <header class="header">
    <div class="header-left">
      <div class="brand-title"><span>✦</span> 博客管理台</div>
      <div id="hugo-status-badge" class="status-badge">
        <span class="status-dot"></span>
        <span id="hugo-status-text">检测 Hugo 服务中...</span>
      </div>
      <button class="btn btn-sm" id="hugo-toggle-btn" onclick="toggleHugo()">▶️ 启动 Hugo</button>
    </div>
    <div class="header-right">
      <a class="btn" href="http://localhost:1314/" target="_blank" rel="noopener">🌐 本地预览</a>
      <a class="btn" href="https://find-xin.github.io/" target="_blank" rel="noopener">🚀 线上站点</a>
      <button class="btn btn-sm" id="theme-btn" onclick="toggleTheme()">🌓 模式</button>
    </div>
  </header>

  <main class="container">
    <nav class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('publish')">✍️ 发布笔记 / Notebook</button>
      <button class="tab-btn" onclick="switchTab('manage')">📚 全站文章管理</button>
      <button class="tab-btn" onclick="switchTab('deploy')">🚀 部署到 GitHub</button>
    </nav>

    <!-- TAB 1: 发布工作台 -->
    <section id="tab-publish">
      <div class="card">
        <h2 class="card-title">📝 一键导入与发布</h2>
        
        <div class="form-group">
          <label class="form-label">笔记文件路径（支持 Obsidian .md 或 Jupyter .ipynb）</label>
          <input type="text" id="file-path" class="form-input" placeholder="例如：/Users/xin/Desktop/Notes/我的文章.md 或 /path/to/demo.ipynb">
          <p class="form-hint">💡 技巧：在 macOS Finder 里选中你的笔记或 .ipynb 文件，按下快捷键 <code>Option + Command + C</code> 即可直接复制绝对路径，粘贴到此处即可。</p>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">发布类型</label>
            <select id="pub-type" class="form-input">
              <option value="post">长篇博文（Post · content/posts/）</option>
              <option value="diary">微光日记（Diary · content/diary/）</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">英文文件夹别名（Slug，可选）</label>
            <input type="text" id="pub-slug" class="form-input" placeholder="留空则自动根据标题或时间戳生成">
          </div>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">分类（可选）</label>
            <input type="text" id="pub-category" class="form-input" placeholder="例如：技术、型月、数据科学">
            <div class="chip-group">
              <span class="chip" onclick="setCategory('型月')">型月</span>
              <span class="chip" onclick="setCategory('技术')">技术</span>
              <span class="chip" onclick="setCategory('数据科学')">数据科学</span>
              <span class="chip" onclick="setCategory('生活随笔')">生活随笔</span>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">标签（逗号分隔，可选）</label>
            <input type="text" id="pub-tags" class="form-input" placeholder="例如：魔法使之夜,Python,教程">
            <div class="chip-group">
              <span class="chip" onclick="addTag('Python')">+ Python</span>
              <span class="chip" onclick="addTag('Obsidian')">+ Obsidian</span>
              <span class="chip" onclick="addTag('魔法使之夜')">+ 魔法使之夜</span>
              <span class="chip" onclick="addTag('随想')">+ 随想</span>
            </div>
          </div>
        </div>

        <div class="form-group" style="display: flex; align-items: center; gap: 8px;">
          <input type="checkbox" id="pub-draft" style="width: 18px; height: 18px; cursor: pointer;">
          <label for="pub-draft" style="font-size: 0.92rem; cursor: pointer;">保存为草稿（仅本地可见，暂不在线上公开）</label>
        </div>

        <div style="margin-top: 24px;">
          <button class="btn btn-primary" id="publish-btn" onclick="doPublish()" style="padding: 10px 24px; font-size: 0.95rem;">
            🚀 立即转换并发布
          </button>
        </div>

        <div id="publish-log" class="terminal-box"></div>
      </div>
    </section>

    <!-- TAB 2: 全站文章管理 -->
    <section id="tab-manage" style="display: none;">
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
          <h2 class="card-title" style="margin-bottom: 0;">📚 已发布内容一览</h2>
          <button class="btn btn-sm" onclick="loadArticles()">🔄 刷新列表</button>
        </div>
        <div class="form-group">
          <input type="text" id="search-input" class="form-input" placeholder="实时过滤标题、类型或 Slug..." oninput="filterArticles()">
        </div>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>状态</th>
                <th>日期</th>
                <th>文章标题</th>
                <th>Slug</th>
                <th>快捷操作</th>
              </tr>
            </thead>
            <tbody id="articles-tbody">
              <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">正在加载文章列表...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: 部署到 GitHub -->
    <section id="tab-deploy" style="display: none;">
      <div class="card">
        <h2 class="card-title">🚀 一键提交并推送到 GitHub</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
          点击下方按钮后，后台会自动执行 <code>git add .</code>、<code>git commit</code> 和 <code>git push origin main</code>，触发 GitHub Actions 自动构建部署。
        </p>

        <div class="form-group">
          <label class="form-label">提交说明（Commit Message）</label>
          <input type="text" id="git-msg" class="form-input" value="feat: 发布新文章并更新内容">
          <div class="chip-group">
            <span class="chip" onclick="setGitMsg('feat: 发布新博文')">feat: 发布新博文</span>
            <span class="chip" onclick="setGitMsg('feat: 发布新日记')">feat: 发布新日记</span>
            <span class="chip" onclick="setGitMsg('fix: 修正排版与内容')">fix: 修正排版与内容</span>
            <span class="chip" onclick="setGitMsg('chore: 更新全站内容')">chore: 更新全站内容</span>
          </div>
        </div>

        <div style="margin-top: 20px;">
          <button class="btn btn-primary" id="deploy-btn" onclick="doDeploy()" style="padding: 10px 24px; font-size: 0.95rem;">
            🚀 提交并推送到 GitHub
          </button>
        </div>

        <div id="deploy-log" class="terminal-box"></div>
      </div>
    </section>
  </main>

  <script>
    let allArticles = [];

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
      document.getElementById('tab-manage').style.display = 'none';
      document.getElementById('tab-deploy').style.display = 'none';

      if (tabId === 'publish') {
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('tab-publish').style.display = 'block';
      } else if (tabId === 'manage') {
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('tab-manage').style.display = 'block';
        loadArticles();
      } else if (tabId === 'deploy') {
        document.querySelectorAll('.tab-btn')[2].classList.add('active');
        document.getElementById('tab-deploy').style.display = 'block';
      }
    }

    function setCategory(cat) { document.getElementById('pub-category').value = cat; }
    function addTag(tag) {
      const el = document.getElementById('pub-tags');
      const cur = el.value.trim();
      el.value = cur ? (cur.includes(tag) ? cur : cur + ',' + tag) : tag;
    }
    function setGitMsg(msg) { document.getElementById('git-msg').value = msg; }

    async function checkHugoStatus() {
      try {
        const res = await fetch('/api/hugo-status');
        const data = await res.json();
        const badge = document.getElementById('hugo-status-badge');
        const text = document.getElementById('hugo-status-text');
        const toggleBtn = document.getElementById('hugo-toggle-btn');
        if (data.running) {
          badge.className = 'status-badge';
          text.textContent = 'Hugo 服务运行中 (1314)';
          toggleBtn.textContent = '⏹️ 停止服务';
          toggleBtn.className = 'btn btn-sm btn-danger';
        } else {
          badge.className = 'status-badge stopped';
          text.textContent = 'Hugo 未运行';
          toggleBtn.textContent = '▶️ 启动服务';
          toggleBtn.className = 'btn btn-sm';
        }
      } catch (e) {}
    }
    setInterval(checkHugoStatus, 5000);
    checkHugoStatus();

    async function toggleHugo() {
      const toggleBtn = document.getElementById('hugo-toggle-btn');
      toggleBtn.disabled = true;
      toggleBtn.textContent = '⏳ 处理中...';
      try {
        await fetch('/api/toggle-hugo', { method: 'POST' });
        setTimeout(async () => {
          await checkHugoStatus();
          toggleBtn.disabled = false;
        }, 800);
      } catch (e) {
        alert('操作失败：' + e.message);
        toggleBtn.disabled = false;
      }
    }

    async function loadArticles() {
      try {
        const res = await fetch('/api/articles');
        allArticles = await res.json();
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
          <td><small style="color:var(--text-muted);">${item.date}</small></td>
          <td>
            <strong>${escapeHtml(item.title)}</strong>
          </td>
          <td><code style="font-size:0.8rem;color:var(--text-muted);">${escapeHtml(item.slug)}</code></td>
          <td>
            <div style="display:flex;gap:6px;">
              <a class="btn btn-sm" href="http://localhost:1314${item.url}" target="_blank" title="在新标签页预览">👁️ 查看</a>
              <button class="btn btn-sm" onclick="toggleDraft('${item.slug}', ${!item.draft})">${item.draft ? '🟢 上架' : '🟡 下架'}</button>
              <button class="btn btn-sm btn-danger" onclick="confirmDelete('${item.slug}', '${escapeHtml(item.title)}')">🗑️ 删除</button>
            </div>
          </td>
        </tr>
      `).join('');
    }

    function filterArticles() {
      const q = document.getElementById('search-input').value.toLowerCase().trim();
      if (!q) { renderArticles(allArticles); return; }
      const filtered = allArticles.filter(a => a.title.toLowerCase().includes(q) || a.slug.toLowerCase().includes(q) || a.type_label.includes(q));
      renderArticles(filtered);
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
          loadArticles();
        } else {
          alert('操作失败：' + data.message);
        }
      } catch (e) { alert('请求异常：' + e.message); }
    }

    async function confirmDelete(slug, title) {
      if (!confirm(`确定要彻底删除《${title}》及其关联附件文件夹吗？此操作无法撤销。`)) return;
      try {
        const res = await fetch('/api/delete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({slug: slug})
        });
        const data = await res.json();
        if (data.success) {
          loadArticles();
        } else {
          alert('删除失败：' + data.message);
        }
      } catch (e) { alert('请求异常：' + e.message); }
    }

    async function doPublish() {
      const path = document.getElementById('file-path').value.trim();
      if (!path) { alert('请输入或粘贴笔记文件的完整路径！'); return; }

      const btn = document.getElementById('publish-btn');
      const log = document.getElementById('publish-log');
      btn.disabled = true;
      btn.textContent = '⏳ 正在转换并提取附件...';
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
          log.textContent += '\\n✅ 处理完成！可前往「全站文章管理」或「部署到 GitHub」查看。';
        } else {
          log.textContent += '\\n❌ 处理失败：' + data.message;
        }
      } catch (e) {
        log.textContent += '\\n❌ 出现异常：' + e.message;
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 立即转换并发布';
      }
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
          log.textContent += '\\n🎉 推送成功！GitHub Actions 已触发自动构建，约 1 分钟后线上即可访问。';
        } else {
          log.textContent += '\\n❌ 推送遇到问题，请检查网络或输出日志。';
        }
      } catch (e) {
        log.textContent += '\\n❌ 出现网络异常：' + e.message;
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 提交并推送到 GitHub';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
  </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默请求日志，保持终端清爽

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif url.path == '/api/articles':
            articles = get_all_articles()
            self.send_json(articles)
        elif url.path == '/api/hugo-status':
            running = is_port_in_use(1314)
            self.send_json({'running': running})
        elif url.path == '/api/git-status':
            status = get_git_status()
            self.send_json(status)
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

            # 捕获函数标准输出
            import io
            from contextlib import redirect_stdout, redirect_stderr
            log_buffer = io.StringIO()

            with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
                if p.suffix.lower() == '.ipynb':
                    ok = process_ipynb_notebook(p, note_type, slug, tags, category, draft)
                else:
                    ok = process_obsidian_note(p, note_type, slug, tags, category, draft)

            output_text = log_buffer.getvalue()
            self.send_json({'success': ok, 'message': '发布完成' if ok else '发布失败', 'output': output_text})

        elif url.path == '/api/set-draft':
            slug = payload.get('slug', '').strip()
            make_draft = bool(payload.get('draft', True))
            ok = set_draft_status(slug, set_draft=make_draft)
            self.send_json({'success': ok, 'message': f'已{"下架" if make_draft else "上架"}' if ok else '未找到该文章'})

        elif url.path == '/api/toggle-hugo':
            running = is_port_in_use(1314)
            if running:
                ok, msg = stop_hugo_server()
            else:
                ok, msg = start_hugo_server()
            self.send_json({'success': ok, 'message': msg, 'running': is_port_in_use(1314)})

        elif url.path == '/api/delete':
            slug = payload.get('slug', '').strip()
            ok = delete_article(slug)
            self.send_json({'success': ok, 'message': '已删除' if ok else '删除失败'})

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
        else:
            self.send_error(404, "API Not Found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def run_server():
    port = get_available_port(PORT)
    server = HTTPServer(('127.0.0.1', port), DashboardHandler)
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"✨ find-xin 博客可视化控制台已启动！")
    print(f"🌐 访问地址：{url}")
    print(f"💡 浏览器将自动打开。按 Ctrl + C 可关闭控制台。")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 控制台已安全退出。")
        server.server_close()

if __name__ == '__main__':
    run_server()
