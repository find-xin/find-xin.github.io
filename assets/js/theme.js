(() => {
  const root = document.documentElement;
  const button = document.querySelector('.theme-toggle');
  if (!button) return;

  const updateButton = () => {
    const dark = root.dataset.theme === 'dark';
    button.setAttribute('aria-pressed', String(dark));
    button.setAttribute('aria-label', dark ? '切换为白天模式' : '切换为夜间模式');
    button.querySelector('.theme-icon').textContent = dark ? '☀' : '☾';
    button.querySelector('.theme-label').textContent = dark ? '白天' : '夜间';
  };

  button.addEventListener('click', () => {
    const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = theme;
    root.classList.toggle('dark-mode', theme === 'dark');
    document.body.classList.toggle('dark-mode', theme === 'dark');
    try { localStorage.setItem('xin-theme', theme); } catch (_) { /* Storage may be disabled. */ }
    updateButton();
  });

  updateButton();
})();
