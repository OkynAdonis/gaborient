document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('menu-toggle');
  const dropdown = document.querySelector('.dropdown');
  const trigger = document.querySelector('.nav-trigger');
  const submenu = document.querySelector('.nav-submenu');

  if (trigger && dropdown) {
    trigger.addEventListener('click', function (event) {
      event.stopPropagation();
      const open = dropdown.classList.toggle('open');
      trigger.setAttribute('aria-expanded', String(open));
    });
  }

  if (btn && dropdown) {
    btn.addEventListener('click', function () {
      const open = dropdown.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
      if (trigger) {
        trigger.setAttribute('aria-expanded', String(open));
      }
    });
  }

  document.addEventListener('click', function (event) {
    if (!dropdown) return;
    if (!dropdown.contains(event.target)) {
      dropdown.classList.remove('open');
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    }
  });
});
