'use strict';
// Real language links work without JavaScript; storage is only a convenience.
try {
  if (location.pathname === '/' && localStorage.getItem('manifesto-language') === 'en') {
    location.replace('/en/' + location.search + location.hash);
  }
} catch { /* Browsers may deny access to storage. */ }
document.querySelectorAll('[data-language]').forEach(link => {
  link.addEventListener('click', () => {
    link.hash = location.hash;
    try { localStorage.setItem('manifesto-language', link.dataset.language); }
    catch { /* Navigation still works when storage is unavailable. */ }
  });
});

const copyStatus = document.querySelector('.copy-status');
const russian = document.documentElement.lang === 'ru';
document.querySelectorAll('[data-copy]').forEach(button => {
  button.hidden = false;
  button.addEventListener('click', async () => {
    const field = document.getElementById(button.dataset.copy);
    field.focus();
    field.select();
    button.disabled = true;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(field.value);
      copyStatus.textContent = russian ? 'Скопировано.' : 'Copied.';
    } catch {
      copyStatus.textContent = russian
        ? 'Текст выделен. Нажмите Ctrl+C или выберите «Копировать».'
        : 'Text selected. Press Ctrl+C or choose Copy.';
    } finally {
      button.disabled = false;
    }
  });
});
