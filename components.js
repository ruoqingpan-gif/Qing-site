// Shared nav, footer, and common interactions for all pages

const NAV_ITEMS = [
  { href: 'index.html', label: 'Home', key: 'home' },
  { href: 'projects.html', label: 'Projects', key: 'projects' },
  { href: 'game-design.html', label: 'Design', key: 'design' },
  { href: 'pmp-notes.html', label: 'PM', key: 'pm' },
  { href: 'life.html', label: 'Life', key: 'life' },
];

function renderNav(activeKey) {
  const isHome = activeKey === 'home';
  const navClass = isHome ? 'nav-inner nav-inner-wide' : 'nav-inner';
  const backLink = isHome ? '' : '<a href="index.html" class="nav-back">&larr; Home</a>';
  const leftWrap = isHome
    ? '<span class="nav-name">Pan Ruoqing</span>'
    : `<div class="nav-left">${backLink}<span class="nav-name">Pan Ruoqing</span></div>`;

  const links = NAV_ITEMS.map(item => {
    const cls = item.key === activeKey ? ' class="active"' : '';
    return `<a href="${item.href}"${cls}>${item.label}</a>`;
  }).join('\n        ');

  const html = `
  <nav>
    <div class="${navClass}">
      ${leftWrap}
      <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')" aria-label="Menu">&#9776;</button>
      <div class="nav-links">
        ${links}
        <a href="#contact">Contact</a>
      </div>
    </div>
  </nav>`;

  document.getElementById('nav-placeholder').outerHTML = html;
}

function renderFooter() {
  const containerClass = document.querySelector('nav .nav-inner-wide') ? 'container-wide' : 'container';

  const html = `
  <footer id="contact">
    <div class="${containerClass}">
      <div class="contact-links">
        <span class="contact-item">
          <span class="contact-label">Email</span>
          <a href="mailto:390331711@qq.com">390331711@qq.com</a>
          <span class="contact-sep">/</span>
          <a href="mailto:23211520024@m.fudan.edu.cn">23211520024@m.fudan.edu.cn</a>
        </span>
        <span class="contact-item">
          <span class="contact-label">GitHub</span>
          <a href="https://github.com/ruoqingpan-gif" target="_blank">github.com/ruoqingpan-gif</a>
        </span>
      </div>
      <p>&copy; 2026 Pan Ruoqing. Built with curiosity.</p>
    </div>
  </footer>

  <button class="back-to-top" onclick="window.scrollTo({top:0,behavior:'smooth'})" aria-label="Back to top">&uarr;</button>`;

  document.getElementById('footer-placeholder').outerHTML = html;
}

function initCommon() {
  // Fade-in on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

  // Back to top button
  const backToTop = document.querySelector('.back-to-top');
  window.addEventListener('scroll', () => {
    backToTop.classList.toggle('visible', window.scrollY > 400);
  });
}
