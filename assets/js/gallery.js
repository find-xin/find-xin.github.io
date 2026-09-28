(() => {
  const links = [...document.querySelectorAll('.gallery-open')];
  const dialog = document.querySelector('.lightbox');
  if (!dialog || !links.length) return;
  let index = 0;
  const show = (next) => {
    index = (next + links.length) % links.length;
    const link = links[index];
    const image = dialog.querySelector('.lightbox-image');
    image.src = link.dataset.image;
    image.alt = link.dataset.caption;
    dialog.querySelector('.lightbox-caption').textContent = link.dataset.caption;
    dialog.querySelector('.lightbox-count').textContent = `${String(index + 1).padStart(2, '0')} / ${links.length}`;
    dialog.querySelector('.lightbox-original').href = link.href;
  };
  links.forEach((link, i) => link.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); show(i); dialog.showModal(); document.body.classList.add('viewing-art');
  }));
  dialog.querySelector('.lightbox-close').addEventListener('click', () => dialog.close());
  dialog.querySelector('.lightbox-prev').addEventListener('click', () => show(index - 1));
  dialog.querySelector('.lightbox-next').addEventListener('click', () => show(index + 1));
  dialog.addEventListener('close', () => document.body.classList.remove('viewing-art'));
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
  });
})();
