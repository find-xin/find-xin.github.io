(() => {
  const root = document.documentElement;

  // 1. Theme switcher with smooth transition
  const button = document.querySelector('.theme-toggle');
  if (button) {
    const updateButton = () => {
      const dark = root.dataset.theme === 'dark';
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', dark ? '切换为白天模式' : '切换为夜间模式');
      button.querySelector('.theme-icon').textContent = dark ? '☀' : '☾';
      button.querySelector('.theme-label').textContent = dark ? '白天' : '夜间';
    };

    const switchTheme = () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = theme;
      root.classList.toggle('dark-mode', theme === 'dark');
      document.body.classList.toggle('dark-mode', theme === 'dark');
      try { localStorage.setItem('xin-theme', theme); } catch (_) { /* Storage may be disabled. */ }
      updateButton();

      // Sync theme to Giscus iframe
      const giscusFrame = document.querySelector('iframe.giscus-frame');
      if (giscusFrame && giscusFrame.contentWindow) {
        giscusFrame.contentWindow.postMessage(
          { giscus: { setConfig: { theme: theme === 'dark' ? 'noborder_gray' : 'light' } } },
          'https://giscus.app'
        );
      }
    };

    button.addEventListener('click', () => {
      switchTheme();
    });

    updateButton();
  }

  // 2. Reading Progress Bar
  const progressBar = document.getElementById('reading-progress');
  const updateProgress = () => {
    if (!progressBar) return;
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (totalHeight > 10) {
      const progress = (window.scrollY / totalHeight) * 100;
      progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    } else {
      progressBar.style.width = '0%';
    }
  };

  // 3. Smooth Back to Top
  const btt = document.getElementById('back-to-top');
  const updateBackToTop = () => {
    if (!btt) return;
    if (window.scrollY > 320) {
      btt.classList.add('is-visible');
    } else {
      btt.classList.remove('is-visible');
    }
  };

  window.addEventListener('scroll', () => {
    updateProgress();
    updateBackToTop();
  }, { passive: true });

  if (btt) {
    btt.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // 4. Mobile Menu Click Outside to Close
  const mobileMenu = document.querySelector('.mobile-menu');
  if (mobileMenu) {
    document.addEventListener('click', (e) => {
      if (mobileMenu.open && !mobileMenu.contains(e.target)) {
        mobileMenu.removeAttribute('open');
      }
    });

    // Close when clicking nav items inside
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenu.removeAttribute('open');
      });
    });
  }

  // 5. Code Block Enhancement (Mac Window Dots, Lang Badge & Copy)
  const codeBlocks = document.querySelectorAll('.post-content pre, .diary-single-content pre');
  codeBlocks.forEach(pre => {
    if (pre.querySelector('.code-copy-btn')) return;

    // Detect language from code class
    const codeEl = pre.querySelector('code');
    let lang = 'CODE';
    if (codeEl) {
      const langClass = Array.from(codeEl.classList).find(c => c.startsWith('language-') || c.startsWith('lang-'));
      if (langClass) {
        lang = langClass.replace(/^(language-|lang-)/, '').toUpperCase();
      }
    }

    // Create macOS Header Bar
    const headerBar = document.createElement('div');
    headerBar.className = 'code-window-header';
    headerBar.innerHTML = `
      <div class="code-window-dots" aria-hidden="true">
        <span class="code-dot dot-red"></span>
        <span class="code-dot dot-yellow"></span>
        <span class="code-dot dot-green"></span>
        <span class="code-window-lang">${lang}</span>
      </div>
    `;
    pre.insertBefore(headerBar, pre.firstChild);

    // Copy Button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'code-copy-btn';
    copyBtn.type = 'button';
    copyBtn.setAttribute('aria-label', '复制代码');
    copyBtn.innerHTML = '<span class="copy-icon" aria-hidden="true"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></span><span class="copy-text">复制</span>';

    copyBtn.addEventListener('click', async () => {
      const codeElement = pre.querySelector('code') || pre;
      const textToCopy = (codeElement.innerText || '').replace(/\n\n$/, '');

      try {
        await navigator.clipboard.writeText(textToCopy);
        copyBtn.classList.add('is-copied');
        copyBtn.innerHTML = '<span class="copy-icon" aria-hidden="true">✓</span><span class="copy-text">已复制</span>';
        setTimeout(() => {
          copyBtn.classList.remove('is-copied');
          copyBtn.innerHTML = '<span class="copy-icon" aria-hidden="true"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg></span><span class="copy-text">复制</span>';
        }, 2000);
      } catch (err) {
        copyBtn.querySelector('.copy-text').textContent = '失败';
        setTimeout(() => {
          copyBtn.querySelector('.copy-text').textContent = '复制';
        }, 2000);
      }
    });

    pre.style.position = 'relative';
    pre.appendChild(copyBtn);
  });

  // 6. Article Images Spotlight / Zoom Lightbox
  const articleImages = document.querySelectorAll('.post-content img:not(.avatar), .diary-single-content img');
  if (articleImages.length > 0) {
    let overlay = document.getElementById('image-zoom-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'image-zoom-overlay';
      overlay.className = 'image-zoom-overlay';
      overlay.setAttribute('role', 'dialog');
      overlay.setAttribute('aria-modal', 'true');
      overlay.setAttribute('aria-label', '图片预览');
      overlay.innerHTML = `
        <div class="zoom-backdrop"></div>
        <div class="zoom-content">
          <img class="zoom-img" alt="" src="" />
          <p class="zoom-caption"></p>
        </div>
        <button class="zoom-close-btn" type="button" aria-label="关闭预览">×</button>
      `;
      document.body.appendChild(overlay);

      const closeZoom = () => {
        overlay.classList.remove('is-active');
        document.body.classList.remove('is-zoomed');
      };

      overlay.addEventListener('click', (e) => {
        if (!e.target.closest('.zoom-img')) {
          closeZoom();
        }
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('is-active')) {
          closeZoom();
        }
      });
    }

    const zoomImg = overlay.querySelector('.zoom-img');
    const zoomCaption = overlay.querySelector('.zoom-caption');

    articleImages.forEach(img => {
      if (img.closest('a')) return;

      img.classList.add('zoomable-image');
      img.addEventListener('click', () => {
        zoomImg.src = img.currentSrc || img.src;
        zoomImg.alt = img.alt || '文章配图';
        zoomCaption.textContent = img.alt || '';
        overlay.classList.add('is-active');
        document.body.classList.add('is-zoomed');
      });
    });
  }

  // 7. Table of Contents (TOC) Scroll Spy
  const tocContainer = document.querySelector('.post-toc-content');
  if (tocContainer) {
    const tocLinks = Array.from(document.querySelectorAll('.post-toc-content a, .post-toc-mobile .post-toc-content a'));
    const headings = tocLinks.map(link => {
      const href = link.getAttribute('href');
      if (!href || !href.startsWith('#')) return null;
      try {
        const id = decodeURIComponent(href.slice(1));
        return document.getElementById(id);
      } catch (_) {
        return null;
      }
    }).filter(Boolean);

    if (headings.length > 0) {
      let activeIndex = -1;
      const updateTocSpy = () => {
        const scrollY = window.scrollY;
        const triggerOffset = 130;

        let current = -1;
        for (let i = 0; i < headings.length; i++) {
          if (headings[i].offsetTop - triggerOffset <= scrollY) {
            current = i;
          } else {
            break;
          }
        }

        if (current !== activeIndex) {
          activeIndex = current;
          tocLinks.forEach((link, idx) => {
            const isTarget = Math.floor(idx % headings.length) === activeIndex;
            link.classList.toggle('is-active', isTarget);
            if (isTarget && link.closest('.post-toc')) {
              const parent = link.closest('.post-toc');
              const linkTop = link.offsetTop - parent.offsetTop;
              if (linkTop < parent.scrollTop || linkTop > parent.scrollTop + parent.clientHeight - 40) {
                link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
              }
            }
          });
        }
      };

      window.addEventListener('scroll', updateTocSpy, { passive: true });
      updateTocSpy();
    }
  }

  // 8. Spotlight Command Palette Search Modal
  const spotlightModal = document.getElementById('spotlight-modal');
  const spotlightInput = document.getElementById('spotlight-input');
  const spotlightResults = document.getElementById('spotlight-results');
  const spotlightStatus = document.getElementById('spotlight-status');
  let searchDocuments = null;
  let activeIndex = -1;

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

  const renderSpotlightInitial = () => {
    if (!spotlightResults) return;
    spotlightResults.innerHTML = `
      <div class="spotlight-state-empty">
        <span class="spotlight-empty-spark">✦</span>
        <p>输入关键词实时检索 · 支持方向键 ↑ ↓ 选择 · 回车直达</p>
      </div>
    `;
    activeIndex = -1;
  };

  const openSpotlight = async () => {
    if (!spotlightModal) return;
    spotlightModal.classList.add('is-open');
    spotlightModal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('is-modal-open');
    if (spotlightInput) {
      spotlightInput.value = '';
      spotlightInput.focus();
    }
    renderSpotlightInitial();

    if (!searchDocuments) {
      if (spotlightStatus) spotlightStatus.textContent = '加载索引...';
      try {
        const res = await fetch('/index.json');
        if (res.ok) {
          searchDocuments = await res.json();
          if (spotlightStatus) spotlightStatus.textContent = `${searchDocuments.length} 篇内容已就绪`;
        }
      } catch (_) {
        if (spotlightStatus) spotlightStatus.textContent = '索引异常';
      }
    }
  };

  const closeSpotlight = () => {
    if (!spotlightModal) return;
    spotlightModal.classList.remove('is-open');
    spotlightModal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('is-modal-open');
    activeIndex = -1;
  };

  const updateActiveItem = (items) => {
    items.forEach((item, idx) => {
      const isTarget = idx === activeIndex;
      item.classList.toggle('is-active', isTarget);
      if (isTarget) {
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });
  };

  const performSearch = (query) => {
    if (!spotlightResults) return;
    const q = query.trim().toLowerCase();
    if (!q) {
      renderSpotlightInitial();
      return;
    }

    if (!searchDocuments) {
      spotlightResults.innerHTML = '<div class="spotlight-state-empty"><p>索引加载中，请稍候...</p></div>';
      return;
    }

    const matches = searchDocuments.filter(doc => {
      const titleMatch = (doc.title || '').toLowerCase().includes(q);
      const snippetMatch = (doc.snippet || '').toLowerCase().includes(q);
      const tagMatch = (doc.tags || []).some(t => (t || '').toLowerCase().includes(q));
      return titleMatch || snippetMatch || tagMatch;
    });

    if (matches.length === 0) {
      spotlightResults.innerHTML = `
        <div class="spotlight-state-empty">
          <span class="spotlight-empty-spark">🪐</span>
          <p>未找到关于 “${escapeHTML(query)}” 的相关内容</p>
        </div>
      `;
      activeIndex = -1;
      return;
    }

    activeIndex = 0;
    spotlightResults.innerHTML = matches.map((item, idx) => {
      const isDiary = item.section === 'diary';
      const isGallery = item.section === 'gallery';
      const sectionBadge = isDiary ? '日记' : (isGallery ? (item.category ? `相册 · ${item.category}` : '相册') : (item.section === 'posts' ? '文章' : '页面'));
      const badgeClass = isDiary ? 'badge-diary' : (isGallery ? 'badge-gallery' : 'badge-post');
      const timeDisplay = isGallery ? (item.date || '') : `${item.year ? item.year + '-' : ''}${item.date || ''}`;
      return `
        <a class="spotlight-item${idx === 0 ? ' is-active' : ''}" href="${item.url}" data-index="${idx}">
          <div class="spotlight-item-header">
            <span class="spotlight-badge ${badgeClass}">${sectionBadge}</span>
            <span class="spotlight-item-title">${highlightMatch(item.title || '', q)}</span>
            <time class="spotlight-item-date">${timeDisplay}</time>
          </div>
          ${item.snippet ? `<p class="spotlight-item-snippet">${highlightMatch(item.snippet, q)}</p>` : ''}
        </a>
      `;
    }).join('');

    spotlightResults.querySelectorAll('.spotlight-item').forEach(el => {
      el.addEventListener('mouseenter', () => {
        spotlightResults.querySelectorAll('.spotlight-item').forEach(i => i.classList.remove('is-active'));
        el.classList.add('is-active');
        activeIndex = parseInt(el.dataset.index, 10);
      });
    });
  };

  if (spotlightInput) {
    spotlightInput.addEventListener('input', (e) => {
      performSearch(e.target.value);
    });

    spotlightInput.addEventListener('keydown', (e) => {
      const items = Array.from(spotlightResults ? spotlightResults.querySelectorAll('.spotlight-item') : []);
      if (items.length === 0) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        activeIndex = (activeIndex + 1) % items.length;
        updateActiveItem(items);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        activeIndex = (activeIndex - 1 + items.length) % items.length;
        updateActiveItem(items);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (activeIndex >= 0 && items[activeIndex]) {
          window.location.href = items[activeIndex].href;
        }
      }
    });
  }

  // Bind Open/Close Triggers
  const navSearchLinks = document.querySelectorAll('.nav-search');
  navSearchLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      openSpotlight();
    });
  });

  const spotlightBackdrop = document.getElementById('spotlight-backdrop');
  if (spotlightBackdrop) spotlightBackdrop.addEventListener('click', closeSpotlight);

  const spotlightCloseBtn = document.getElementById('spotlight-close-btn');
  if (spotlightCloseBtn) spotlightCloseBtn.addEventListener('click', closeSpotlight);

  document.addEventListener('keydown', (e) => {
    const activeEl = document.activeElement;
    const isInput = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable);

    if (e.key === 'Escape' && spotlightModal && spotlightModal.classList.contains('is-open')) {
      e.preventDefault();
      closeSpotlight();
      return;
    }

    if (!isInput && ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || e.key === '/')) {
      e.preventDefault();
      if (spotlightModal && spotlightModal.classList.contains('is-open')) {
        closeSpotlight();
      } else {
        openSpotlight();
      }
    }
  });

  // 9. External Links Security & Subtle Indicator
  const contentLinks = document.querySelectorAll('.post-content a:not(.tag):not(.gallery-open), .diary-detail-content a:not(.diary-card-tag)');
  contentLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (href.startsWith('http://') || href.startsWith('https://')) {
      try {
        const linkUrl = new URL(href);
        if (linkUrl.hostname !== window.location.hostname) {
          link.setAttribute('target', '_blank');
          link.setAttribute('rel', 'noopener noreferrer');
          link.classList.add('is-external-link');
        }
      } catch (_) {}
    }
  });

  // 10. Blog running days counter
  const daysEl = document.getElementById('blog-days');
  if (daysEl) {
    const startDate = new Date('2026-01-01T00:00:00');
    const now = new Date();
    const diffTime = Math.abs(now - startDate);
    const diffDays = Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
    daysEl.textContent = String(diffDays);
  }

  // 11. Mouse Tracking Spotlight Effect (Linear / Apple style)
  const spotlightCards = document.querySelectorAll('.article-card, .diary-card, .friend-card, .post-signature-card');
  spotlightCards.forEach(card => {
    card.classList.add('has-spotlight');
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });

  // 12. Subtle Magic Sparkle Click Feedback (Mana dust & starlight particles)
  const sparkleTypes = ['sparkle-mana', 'sparkle-gold', 'sparkle-star'];
  document.addEventListener('click', (e) => {
    // Only spawn 3-4 delicate particles
    const count = 3;
    for (let i = 0; i < count; i++) {
      const sparkle = document.createElement('span');
      const type = sparkleTypes[(i + Math.floor(Math.random() * sparkleTypes.length)) % sparkleTypes.length];
      sparkle.className = `magic-sparkle ${type}`;
      sparkle.style.left = `${e.clientX}px`;
      sparkle.style.top = `${e.clientY}px`;
      const angle = (Math.PI * 2 * i) / count + (Math.random() * 0.6);
      const dist = 14 + Math.random() * 18;
      sparkle.style.setProperty('--dx', `${Math.cos(angle) * dist}px`);
      sparkle.style.setProperty('--dy', `${Math.sin(angle) * dist}px`);
      document.body.appendChild(sparkle);
      setTimeout(() => sparkle.remove(), 650);
    }
  }, { passive: true });

  // 13. High-Speed Hover & Touch Prefetcher (Instant Navigation)
  const prefetchedUrls = new Set();
  const prefetchUrl = (url) => {
    if (!url || prefetchedUrls.has(url)) return;
    try {
      const parsed = new URL(url, window.location.href);
      if (parsed.origin !== window.location.origin) return;
      if (parsed.pathname === window.location.pathname) return;
      if (parsed.pathname.endsWith('.xml') || parsed.pathname.endsWith('.pdf') || parsed.pathname.endsWith('.zip')) return;

      prefetchedUrls.add(url);
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    } catch (_) {}
  };

  let hoverTimer = null;
  document.addEventListener('mouseover', (e) => {
    const a = e.target.closest('a');
    if (!a || !a.href) return;
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(() => prefetchUrl(a.href), 65);
  }, { passive: true });

  document.addEventListener('touchstart', (e) => {
    const a = e.target.closest('a');
    if (a && a.href) prefetchUrl(a.href);
  }, { passive: true });

  // 15. Obsidian Callout Box Parser & Renderer
  const calloutMap = {
    'note': { icon: 'ℹ️', title: 'Note', class: 'callout-note' },
    'info': { icon: 'ℹ️', title: 'Info', class: 'callout-note' },
    'tip': { icon: '💡', title: 'Tip', class: 'callout-tip' },
    'hint': { icon: '💡', title: 'Hint', class: 'callout-tip' },
    'important': { icon: '❗', title: 'Important', class: 'callout-important' },
    'warning': { icon: '⚠️', title: 'Warning', class: 'callout-warning' },
    'caution': { icon: '🔥', title: 'Caution', class: 'callout-caution' },
    'danger': { icon: '🛑', title: 'Danger', class: 'callout-danger' },
    'quote': { icon: '💬', title: 'Quote', class: 'callout-quote' },
    'example': { icon: '📝', title: 'Example', class: 'callout-example' }
  };

  document.querySelectorAll('.post-content blockquote, .diary-single-content blockquote').forEach(bq => {
    const firstP = bq.querySelector('p');
    if (!firstP) return;
    const match = firstP.innerHTML.match(/^\s*\[!([a-zA-Z]+)\]\s*(.*?)(?:<br\s*\/?>|\n|$)/);
    if (match) {
      const type = match[1].toLowerCase();
      const config = calloutMap[type] || { icon: '📌', title: match[1].toUpperCase(), class: 'callout-note' };
      const customTitle = match[2].trim() || config.title;

      firstP.innerHTML = firstP.innerHTML.replace(/^\s*\[!([a-zA-Z]+)\]\s*(.*?)(?:<br\s*\/?>|\n|$)/, '');
      if (!firstP.innerHTML.trim()) firstP.remove();

      bq.classList.add('obsidian-callout', config.class);
      const header = document.createElement('div');
      header.className = 'callout-header';
      header.innerHTML = `<span class="callout-icon" aria-hidden="true">${config.icon}</span><span class="callout-title">${customTitle}</span>`;
      bq.insertBefore(header, bq.firstChild);
    }
  });
})();
