/**
 * DFEMS – Main JavaScript
 * Provides: live clock, flash auto-dismiss, mobile sidebar.
 */

/* ── Live clock ────────────────────────────────────────────────────────── */
function updateClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toUTCString().replace(' GMT', ' UTC').slice(0, 25);
}
updateClock();
setInterval(updateClock, 1000);

/* ── Auto-dismiss flash messages after 5 s ─────────────────────────────── */
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s ease, transform .4s ease';
    el.style.opacity    = '0';
    el.style.transform  = 'translateX(20px)';
    setTimeout(() => el.remove(), 400);
  }, 5000);
});

/* ── Close sidebar when clicking outside on mobile ──────────────────────── */
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  if (window.innerWidth <= 900 && sidebar.classList.contains('sidebar--open')) {
    if (!sidebar.contains(e.target) && !e.target.closest('.topbar__toggle')) {
      sidebar.classList.remove('sidebar--open');
    }
  }
});

/* ── Table row click → navigate to first link ──────────────────────────── */
document.querySelectorAll('.table--hover tbody tr').forEach(row => {
  const link = row.querySelector('a');
  if (link) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', e => {
      if (e.target.closest('a, button, form')) return;
      link.click();
    });
  }
});
