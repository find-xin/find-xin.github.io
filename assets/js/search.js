(() => {
  const form = document.querySelector('.site-search');
  const input = document.getElementById('site-search-input');
  const results = document.querySelector('.search-results');
  const status = document.querySelector('.search-status');
  const filterPills = document.getElementById('search-filter-pills');
  if (!form || !input || !results || !status) return;

  let documents = [];
  let currentFilter = 'all';

  const params = new URLSearchParams(location.search);
  input.value = params.get('q') || '';

  const escapeHTML = (str) => {
    return (str || '').replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
  };

  const highlightMatch = (text, query) => {
    if (!query) return escapeHTML(text);
    const escapedText = escapeHTML(text);
    const escapedQuery = escapeHTML(query);
    const regex = new RegExp(`(${escapedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return escapedText.replace(regex, '<mark>$1</mark>');
  };

  const parseQueryScope = (rawQuery) => {
    let scope = null;
    let cleanQuery = (rawQuery || '').trim();

    const prefixMatch = cleanQuery.match(/^([@#]|in:|type:)(日记|文章|相册|diary|posts?|gallery)(?:\s+(.*)|$)/i);
    if (prefixMatch) {
      const typeStr = prefixMatch[2].toLowerCase();
      if (typeStr === '日记' || typeStr === 'diary') scope = 'diary';
      else if (typeStr === '文章' || typeStr === 'post' || typeStr === 'posts') scope = 'posts';
      else if (typeStr === '相册' || typeStr === 'gallery') scope = 'gallery';
      cleanQuery = (prefixMatch[3] || '').trim();
    }

    return { scope, cleanQuery };
  };

  const updateFilterUI = (activeScope) => {
    if (!filterPills) return;
    filterPills.querySelectorAll('.search-filter-pill').forEach(btn => {
      const isTarget = btn.dataset.filter === activeScope;
      btn.classList.toggle('is-active', isTarget);
      btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });
  };

  const updateFilterCounts = (counts) => {
    if (!filterPills) return;
    filterPills.querySelectorAll('.pill-count').forEach(span => {
      const filterKey = span.dataset.count;
      if (filterKey && typeof counts[filterKey] === 'number') {
        span.textContent = counts[filterKey] > 0 ? counts[filterKey] : '';
      } else {
        span.textContent = '';
      }
    });
  };

  const getSectionBadge = (item) => {
    if (item.section === 'diary') return { text: '日记', class: 'diary' };
    if (item.section === 'gallery') return { text: item.category ? `相册 · ${item.category}` : '相册', class: 'gallery' };
    if (item.section === 'posts') return { text: '文章', class: 'post' };
    return { text: '页面', class: 'post' };
  };

  const runSearch = (rawQuery) => {
    const { scope: parsedScope, cleanQuery } = parseQueryScope(rawQuery);
    const effectiveScope = parsedScope || currentFilter || 'all';

    if (parsedScope && currentFilter !== parsedScope) {
      currentFilter = parsedScope;
    }
    updateFilterUI(effectiveScope);

    results.replaceChildren();

    if (!documents.length) {
      status.textContent = '索引加载中，请稍候...';
      return;
    }

    if (!cleanQuery) {
      if (effectiveScope !== 'all') {
        const scopedDocs = documents.filter(d => d.section === effectiveScope);
        renderCards(scopedDocs, '', effectiveScope);
        status.textContent = `共 ${scopedDocs.length} 篇相关内容`;
        return;
      }
      status.textContent = '输入标题、正文、标签或使用 @日记 快速检索全站内容。';
      updateFilterCounts({
        all: documents.length,
        posts: documents.filter(d => d.section === 'posts').length,
        diary: documents.filter(d => d.section === 'diary').length,
        gallery: documents.filter(d => d.section === 'gallery').length
      });
      return;
    }

    const q = cleanQuery.toLowerCase();

    // 1. 全站匹配
    const allMatches = documents.filter(doc => {
      const titleMatch = (doc.title || '').toLowerCase().includes(q);
      const snippetMatch = (doc.snippet || '').toLowerCase().includes(q);
      const tagMatch = (doc.tags || []).some(t => (t || '').toLowerCase().includes(q));
      return titleMatch || snippetMatch || tagMatch;
    });

    // 2. 更新数量
    const counts = {
      all: allMatches.length,
      posts: allMatches.filter(d => d.section === 'posts').length,
      diary: allMatches.filter(d => d.section === 'diary').length,
      gallery: allMatches.filter(d => d.section === 'gallery').length
    };
    updateFilterCounts(counts);

    // 3. 范围过滤
    const matches = effectiveScope === 'all'
      ? allMatches
      : allMatches.filter(d => d.section === effectiveScope);

    const scopeLabel = effectiveScope === 'posts' ? '文章' : (effectiveScope === 'diary' ? '日记' : (effectiveScope === 'gallery' ? '相册' : ''));
    if (matches.length) {
      status.textContent = `在${scopeLabel ? `「${scopeLabel}」` : '全站'}找到 ${matches.length} 篇相关内容`;
    } else {
      status.textContent = `未在${scopeLabel ? `「${scopeLabel}」` : '全站'}找到关于 “${cleanQuery}” 的内容，换个关键词试试～`;
    }

    renderCards(matches, q, effectiveScope);
  };

  const renderCards = (items, term, scope) => {
    for (const match of items) {
      const card = document.createElement('article');
      card.className = 'search-result-card';

      const badge = getSectionBadge(match);
      const titleHTML = term ? highlightMatch(match.title || '', term) : escapeHTML(match.title || '');
      const snippetHTML = match.snippet ? (term ? highlightMatch(match.snippet, term) : escapeHTML(match.snippet)) : '';
      const dateDisplay = match.date ? `${match.year ? match.year + '-' : ''}${match.date}` : '';

      card.innerHTML = `
        <div class="search-result-header">
          <span class="search-result-badge search-result-badge--${badge.class}">${badge.text}</span>
          <span class="search-result-arrow" aria-hidden="true">${dateDisplay || '↗'}</span>
        </div>
        <h3 class="search-result-title"><a href="${match.url}">${titleHTML}</a></h3>
        ${snippetHTML ? `<p class="search-result-snippet">${snippetHTML}</p>` : ''}
      `;

      card.addEventListener('click', (e) => {
        if (!e.target.closest('a')) {
          if (e.metaKey || e.ctrlKey) window.open(match.url, '_blank');
          else window.location.href = match.url;
        }
      });

      results.append(card);
    }
  };

  // Load index data from /index.json
  const loadIndex = async () => {
    try {
      const res = await fetch('/index.json');
      if (res.ok) {
        documents = await res.json();
        runSearch(input.value);
      }
    } catch (_) {
      status.textContent = '加载搜索索引失败，请刷新页面重试。';
    }
  };

  if (filterPills) {
    filterPills.querySelectorAll('.search-filter-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        currentFilter = btn.dataset.filter || 'all';
        updateFilterUI(currentFilter);
        const { scope, cleanQuery } = parseQueryScope(input.value);
        if (scope) {
          if (currentFilter === 'all') input.value = cleanQuery;
          else {
            const prefixName = currentFilter === 'posts' ? '文章' : (currentFilter === 'diary' ? '日记' : '相册');
            input.value = `@${prefixName} ${cleanQuery}`.trim();
          }
        }
        input.focus();
        runSearch(input.value);
      });
    });
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim();
    const nextURL = new URL(location.href);
    if (query) nextURL.searchParams.set('q', query);
    else nextURL.searchParams.delete('q');
    history.replaceState({}, '', nextURL);
    runSearch(query);
  });

  input.addEventListener('input', () => {
    const query = input.value.trim();
    const nextURL = new URL(location.href);
    if (query) nextURL.searchParams.set('q', query);
    else nextURL.searchParams.delete('q');
    history.replaceState({}, '', nextURL);
    runSearch(query);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const filters = ['all', 'posts', 'diary', 'gallery'];
      let idx = filters.indexOf(currentFilter);
      if (idx === -1) idx = 0;
      if (e.shiftKey) {
        idx = (idx - 1 + filters.length) % filters.length;
      } else {
        idx = (idx + 1) % filters.length;
      }
      currentFilter = filters[idx];
      updateFilterUI(currentFilter);

      const { scope, cleanQuery } = parseQueryScope(input.value);
      if (scope) {
        if (currentFilter === 'all') input.value = cleanQuery;
        else {
          const prefixName = currentFilter === 'posts' ? '文章' : (currentFilter === 'diary' ? '日记' : '相册');
          input.value = `@${prefixName} ${cleanQuery}`.trim();
        }
      }
      runSearch(input.value);
      return;
    }

    if (e.key === 'Escape') {
      input.value = '';
      const nextURL = new URL(location.href);
      nextURL.searchParams.delete('q');
      history.replaceState({}, '', nextURL);
      runSearch('');
    }
  });

  loadIndex();
})();
