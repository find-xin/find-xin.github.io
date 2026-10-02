(() => {
  const indexNode = document.getElementById('search-index');
  const form = document.querySelector('.site-search');
  const input = document.getElementById('site-search-input');
  const results = document.querySelector('.search-results');
  const status = document.querySelector('.search-status');
  if (!indexNode || !form || !input || !results || !status) return;

  const parsedIndex = JSON.parse(indexNode.textContent);
  const documents = typeof parsedIndex === 'string' ? JSON.parse(parsedIndex) : parsedIndex;
  const params = new URLSearchParams(location.search);
  input.value = params.get('q') || '';

  const getSnippet = (text, term) => {
    if (!text) return '';
    const cleanText = text.replace(/\s+/g, ' ').trim();
    if (!term) return cleanText.slice(0, 110) + '...';
    const index = cleanText.toLocaleLowerCase().indexOf(term.toLocaleLowerCase());
    if (index === -1) return cleanText.slice(0, 110) + '...';
    const start = Math.max(0, index - 35);
    const end = Math.min(cleanText.length, index + 85);
    const prefix = start > 0 ? '...' : '';
    const suffix = end < cleanText.length ? '...' : '';
    return prefix + cleanText.slice(start, end) + suffix;
  };

  const getSectionBadge = (url) => {
    if (url.includes('/diary/')) return '日记';
    if (url.includes('/posts/')) return '文章';
    if (url.includes('/gallery/')) return '收藏';
    return '页面';
  };

  const runSearch = (query) => {
    const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    results.replaceChildren();
    if (!terms.length) {
      status.textContent = '输入标题、正文或标签中的关键词，搜索全部文章与日记。';
      return;
    }

    const matches = documents.filter((doc) => {
      const tagsStr = Array.isArray(doc.tags) ? doc.tags.join(' ') : (doc.tags || '');
      const haystack = `${doc.title || ''} ${doc.snippet || ''} ${tagsStr}`.toLowerCase();
      return terms.every((term) => haystack.includes(term));
    });

    status.textContent = matches.length ? `找到 ${matches.length} 篇相关内容` : '未找到相关内容，换个关键词试试～';

    for (const match of matches) {
      const card = document.createElement('article');
      card.className = 'search-result-card';

      const sectionBadge = getSectionBadge(match.url);
      const snippet = getSnippet(match.snippet, terms[0]);

      card.innerHTML = `
        <div class="search-result-header">
          <span class="search-result-badge search-result-badge--${sectionBadge === '日记' ? 'diary' : 'post'}">${sectionBadge}</span>
          <span class="search-result-arrow" aria-hidden="true">↗</span>
        </div>
        <h3 class="search-result-title"><a href="${match.url}">${match.title}</a></h3>
        ${snippet ? `<p class="search-result-snippet">${snippet}</p>` : ''}
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

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim();
    const nextURL = new URL(location.href);
    if (query) nextURL.searchParams.set('q', query);
    else nextURL.searchParams.delete('q');
    history.replaceState({}, '', nextURL);
    runSearch(query);
  });

  input.addEventListener('input', () => runSearch(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      input.value = '';
      const nextURL = new URL(location.href);
      nextURL.searchParams.delete('q');
      history.replaceState({}, '', nextURL);
      runSearch('');
    }
  });
  runSearch(input.value);
})();
