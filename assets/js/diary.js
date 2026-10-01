(() => {
  // ===== 1. Waterfall Layout (Masonry) & Filtering =====
  const wrapper = document.getElementById('diary-waterfall-wrapper');
  if (wrapper) {
    const originalCards = Array.from(wrapper.querySelectorAll('.diary-card'));

    function getColumnCount() {
      const width = window.innerWidth;
      if (width <= 768) return 2; // Xiaohongshu trademark 2-column mobile feed
      if (width <= 1100) return 3;
      return 4;
    }

    let currentCols = 0;
    let activeTag = 'all';

    function renderMasonry() {
      const cols = getColumnCount();
      currentCols = cols;

      const filtered = originalCards.filter(card => {
        if (activeTag === 'all') return true;
        const tags = (card.dataset.tags || '').split(',').map(s => s.trim());
        return tags.includes(activeTag);
      });

      // Clear container and create column elements
      wrapper.innerHTML = '';
      wrapper.classList.add('is-masonry-active');

      if (filtered.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'diary-empty';
        emptyDiv.innerHTML = '<p>暂时没有该分类的日记～</p>';
        wrapper.appendChild(emptyDiv);
        return;
      }

      const colDivs = [];
      for (let i = 0; i < cols; i++) {
        const col = document.createElement('div');
        col.className = 'diary-waterfall-column';
        wrapper.appendChild(col);
        colDivs.push(col);
      }

      // Append cards to the shortest column for perfect waterfall flow
      filtered.forEach(card => {
        let minCol = colDivs[0];
        let minHeight = minCol.offsetHeight;
        for (let i = 1; i < colDivs.length; i++) {
          const h = colDivs[i].offsetHeight;
          if (h < minHeight) {
            minHeight = h;
            minCol = colDivs[i];
          }
        }
        minCol.appendChild(card);
      });
    }

    // Run layout immediately and after images load
    renderMasonry();
    window.addEventListener('load', () => renderMasonry());

    // Debounced resize handler
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (getColumnCount() !== currentCols) {
          renderMasonry();
        }
      }, 150);
    });

    // Tag filter tab click handling
    const tabs = document.querySelectorAll('.diary-filter-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        activeTag = tab.dataset.tag || 'all';
        renderMasonry();
      });
    });

    // Card click navigation & card tag quick filtering
    wrapper.addEventListener('click', (e) => {
      // 1. If clicked on a tag inside the card, trigger filtering
      const tagEl = e.target.closest('.diary-card-tag');
      if (tagEl) {
        e.preventDefault();
        e.stopPropagation();
        const rawTag = tagEl.textContent.replace(/^#/, '').trim();
        const matchingTab = Array.from(document.querySelectorAll('.diary-filter-tab')).find(
          t => (t.dataset.tag || '') === rawTag
        );
        if (matchingTab) {
          matchingTab.click();
        }
        return;
      }

      // 2. If clicked on like button, don't navigate
      if (e.target.closest('.diary-like-btn')) return;

      // 3. Navigate to article
      const card = e.target.closest('.diary-card');
      if (!card) return;
      const link = card.querySelector('.diary-card-title a') || card.querySelector('a');
      if (!link) return;
      if (e.metaKey || e.ctrlKey) {
        window.open(link.href, '_blank');
      } else {
        window.location.href = link.href;
      }
    });
  }

  // ===== 2. Interactive Xiaohongshu Like Button =====
  function initLikeButtons() {
    const likeButtons = document.querySelectorAll('.diary-like-btn, .diary-detail-like-btn');
    likeButtons.forEach(btn => {
      const id = btn.dataset.id;
      if (!id) return;
      const storageKey = 'diary_liked_' + id;
      const isLiked = localStorage.getItem(storageKey) === 'true';
      const baseLikes = parseInt(btn.dataset.likes, 10) || 0;
      const countEl = btn.querySelector('.like-count');
      const iconEl = btn.querySelector('.heart-icon');

      if (isLiked) {
        btn.classList.add('is-liked');
        if (iconEl) iconEl.textContent = '♥';
        if (countEl) countEl.textContent = baseLikes + 1;
      }

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const likedNow = localStorage.getItem(storageKey) === 'true';
        if (!likedNow) {
          localStorage.setItem(storageKey, 'true');
          btn.classList.add('is-liked', 'animating');
          if (iconEl) iconEl.textContent = '♥';
          if (countEl) countEl.textContent = baseLikes + 1;
        } else {
          localStorage.removeItem(storageKey);
          btn.classList.remove('is-liked');
          if (iconEl) iconEl.textContent = '♡';
          if (countEl) countEl.textContent = baseLikes;
        }
        setTimeout(() => btn.classList.remove('animating'), 300);
      });
    });
  }

  initLikeButtons();

  // ===== 3. Diary Detail Share Button =====
  const shareBtn = document.querySelector('.diary-share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        const originalText = shareBtn.innerHTML;
        shareBtn.innerHTML = '<span>已复制链接 ✓</span>';
        setTimeout(() => { shareBtn.innerHTML = originalText; }, 2000);
      } catch (_) {
        window.prompt('复制文章链接：', window.location.href);
      }
    });
  }
})();
