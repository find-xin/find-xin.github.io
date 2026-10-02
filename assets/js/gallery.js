(() => {
  // Elements
  const tabBtns = document.querySelectorAll('.album-filter-tab, .album-tab-btn');
  const sections = document.querySelectorAll('.album-section');
  const dialog = document.querySelector('.lightbox');

  // Category Tab Switching
  const switchCategory = (cat) => {
    tabBtns.forEach(btn => {
      const isActive = btn.dataset.cat === cat;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    sections.forEach(sec => {
      if (cat === 'all' || sec.dataset.category === cat) {
        sec.style.display = '';
        sec.classList.remove('is-hidden');
      } else {
        sec.style.display = 'none';
        sec.classList.add('is-hidden');
      }
    });

    if (cat !== 'all') {
      history.replaceState(null, '', '#' + cat);
    } else {
      history.replaceState(null, '', window.location.pathname);
    }
  };

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchCategory(btn.dataset.cat));
  });

  // Tag Filtering within each section
  sections.forEach(sec => {
    const secCat = sec.dataset.category;
    const tagBtns = sec.querySelectorAll('.tag-filter-btn');
    const cards = sec.querySelectorAll('.album-card');
    const emptyMsg = sec.querySelector('.album-empty-msg');

    const filterByTag = (tag) => {
      tagBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tag === tag);
      });

      let visibleCount = 0;
      cards.forEach(card => {
        const cardTags = (card.dataset.tags || '').split(' ').filter(Boolean);
        const match = (tag === 'all') || cardTags.includes(tag);
        if (match) {
          card.style.display = '';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      if (emptyMsg) {
        emptyMsg.style.display = visibleCount === 0 ? 'block' : 'none';
      }
    };

    tagBtns.forEach(btn => {
      btn.addEventListener('click', () => filterByTag(btn.dataset.tag));
    });

    // Tag pills inside card click
    sec.querySelectorAll('.album-card-tag, .card-tag-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const tag = pill.dataset.tag;
        filterByTag(tag);
      });
    });
  });

  // Handle URL hash on load
  const initialHash = window.location.hash.replace('#', '');
  if (['photography', 'daily', 'anime'].includes(initialHash)) {
    switchCategory(initialHash);
  }

  // Lightbox Implementation
  if (!dialog) return;

  const lbImage = dialog.querySelector('.lightbox-image');
  const lbCaption = dialog.querySelector('.lightbox-caption');
  const lbCategory = dialog.querySelector('.lightbox-category-tag');
  const lbTags = dialog.querySelector('.lightbox-tags-display');
  const lbCount = dialog.querySelector('.lightbox-count');
  const lbOriginal = dialog.querySelector('.lightbox-original');
  const lbClose = dialog.querySelector('.lightbox-close');
  const lbPrev = dialog.querySelector('.lightbox-prev');
  const lbNext = dialog.querySelector('.lightbox-next');

  let currentVisibleLinks = [];
  let currentIndex = 0;

  const getVisibleLinks = () => {
    return Array.from(document.querySelectorAll('.album-section:not(.is-hidden) .album-card:not([style*="display: none"]) .gallery-open'));
  };

  const showLightboxImage = (index) => {
    if (!currentVisibleLinks.length) return;
    currentIndex = (index + currentVisibleLinks.length) % currentVisibleLinks.length;
    const link = currentVisibleLinks[currentIndex];

    lbImage.src = link.dataset.image;
    lbImage.alt = link.dataset.caption;
    if (lbCaption) lbCaption.textContent = link.dataset.caption;
    if (lbCategory) lbCategory.textContent = link.dataset.category || '';
    if (lbTags) lbTags.textContent = link.dataset.tags ? `标签: ${link.dataset.tags}` : '';
    if (lbCount) lbCount.textContent = `${String(currentIndex + 1).padStart(2, '0')} / ${String(currentVisibleLinks.length).padStart(2, '0')}`;
    if (lbOriginal) lbOriginal.href = link.href;
  };

  document.addEventListener('click', (e) => {
    const link = e.target.closest('.gallery-open');
    if (!link) return;

    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();

    currentVisibleLinks = getVisibleLinks();
    const idx = currentVisibleLinks.indexOf(link);
    if (idx !== -1) {
      showLightboxImage(idx);
    } else {
      currentVisibleLinks = [link];
      showLightboxImage(0);
    }

    dialog.showModal();
    document.body.classList.add('viewing-art');
  });

  if (lbClose) lbClose.addEventListener('click', () => dialog.close());
  if (lbPrev) lbPrev.addEventListener('click', () => showLightboxImage(currentIndex - 1));
  if (lbNext) lbNext.addEventListener('click', () => showLightboxImage(currentIndex + 1));

  dialog.addEventListener('close', () => {
    document.body.classList.remove('viewing-art');
  });

  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) dialog.close();
  });

  dialog.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      showLightboxImage(currentIndex - 1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      showLightboxImage(currentIndex + 1);
    }
  });

  // Touch Swipe Gesture Support on Mobile
  let touchStartX = 0;
  let touchStartY = 0;
  let touchEndX = 0;
  let touchEndY = 0;

  dialog.addEventListener('touchstart', (e) => {
    if (e.touches.length > 0) {
      touchStartX = e.touches[0].screenX;
      touchStartY = e.touches[0].screenY;
    }
  }, { passive: true });

  dialog.addEventListener('touchend', (e) => {
    if (e.changedTouches.length > 0) {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      handleSwipe();
    }
  }, { passive: true });

  const handleSwipe = () => {
    const diffX = touchEndX - touchStartX;
    const diffY = touchEndY - touchStartY;
    // Horizontal swipe threshold: 45px, horizontal dominance
    if (Math.abs(diffX) > 45 && Math.abs(diffX) > Math.abs(diffY) * 1.4) {
      if (diffX < 0) {
        showLightboxImage(currentIndex + 1); // Swipe left -> Next
      } else {
        showLightboxImage(currentIndex - 1); // Swipe right -> Prev
      }
    } else if (diffY > 90 && Math.abs(diffY) > Math.abs(diffX) * 2) {
      dialog.close(); // Swipe down -> Close
    }
  };
})();
