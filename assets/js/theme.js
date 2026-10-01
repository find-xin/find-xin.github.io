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

    button.addEventListener('click', () => {
      // Add smooth transition class temporarily
      root.classList.add('theme-transition');
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = theme;
      root.classList.toggle('dark-mode', theme === 'dark');
      document.body.classList.toggle('dark-mode', theme === 'dark');
      try { localStorage.setItem('xin-theme', theme); } catch (_) { /* Storage may be disabled. */ }
      updateButton();

      setTimeout(() => {
        root.classList.remove('theme-transition');
      }, 350);
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
      </div>
      <span class="code-window-lang">${lang}</span>
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

  // 8. Global Search Shortcut (Cmd+K / Ctrl+K / "/")
  document.addEventListener('keydown', (e) => {
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
      return;
    }

    if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || e.key === '/') {
      e.preventDefault();
      const searchInput = document.getElementById('site-search-input');
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      } else {
        const searchLink = document.querySelector('.nav-search');
        if (searchLink) {
          window.location.href = searchLink.href;
        }
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
})();
