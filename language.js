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
