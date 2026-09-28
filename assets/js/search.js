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

  const runSearch = (query) => {
    const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    results.replaceChildren();
    if (!terms.length) {
      status.textContent = '输入标题、正文或标签中的关键词，搜索全部文章。';
      return;
    }

    const matches = documents.filter((document) => {
      const haystack = `${document.title} ${document.text}`.toLocaleLowerCase();
      return terms.every((term) => haystack.includes(term));
    });

    status.textContent = matches.length ? `找到 ${matches.length} 篇文章` : '没有找到相关文章，换个词试试。';
    for (const match of matches) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = match.url;
      link.textContent = match.title;
      item.append(link);
      results.append(item);
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
  runSearch(input.value);
})();
