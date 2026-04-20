/* ── Utility: escape HTML ─────────────────────────────── */
function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/* ── Toast Notifications ──────────────────────────────── */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const icons = {
    success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    info:    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
  };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = (icons[type] || icons.info) + `<span>${escHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(110%)';
    toast.style.transition = 'opacity .3s, transform .3s';
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

/* ── Button Loading State ─────────────────────────────── */
function setLoading(btn, loading) {
  const textEl = btn.querySelector('.btn-text');
  const spinnerEl = btn.querySelector('.spinner');
  if (loading) {
    btn.disabled = true;
    if (textEl) textEl.style.opacity = '0.5';
    if (spinnerEl) spinnerEl.style.display = 'inline-block';
  } else {
    btn.disabled = false;
    if (textEl) textEl.style.opacity = '1';
    if (spinnerEl) spinnerEl.style.display = 'none';
  }
}

/* ── Auth Helpers ─────────────────────────────────────── */
function getToken() { return localStorage.getItem('token'); }
function getUser()  { return JSON.parse(localStorage.getItem('user') || 'null'); }
function logout()   { localStorage.removeItem('token'); localStorage.removeItem('user'); window.location.href = '/'; }

function requireAuth(requiredRole) {
  const token = getToken();
  const user  = getUser();
  if (!token || !user) { window.location.href = '/login'; return; }
  if (requiredRole && user.role !== requiredRole) {
    window.location.href = user.role === 'lecturer' ? '/lecturer' : '/student';
  }
}

/* ── API Helpers ──────────────────────────────────────── */
async function apiFetch(url, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res  = await fetch(url, { ...options, headers });
  const data = await res.json().catch(() => ({ success: false, message: 'Invalid server response' }));
  if (!data.success) {
    const err = new Error(data.message || data.error || 'Request failed');
    err.status = res.status;
    throw err;
  }
  return data;
}
async function apiGet(url)        { return apiFetch(url, { method: 'GET' }); }
async function apiPost(url, body) { return apiFetch(url, { method: 'POST', body: JSON.stringify(body) }); }

/* ── Modals ───────────────────────────────────────────── */
function openModal(id)  { const el = document.getElementById(id); if (el) el.style.display = 'flex'; }
function closeModal(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }
function closeModalOnOverlay(event, id) { if (event.target === event.currentTarget) closeModal(id); }

/* ── Lazy Script Loader ───────────────────────────────── */
function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
    const s = document.createElement('script');
    s.src = src; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
}

/* ── Device Performance Detection ────────────────────── */
const devicePerf = (function() {
  const mem   = navigator.deviceMemory || 4;
  const cores = navigator.hardwareConcurrency || 4;
  const score = mem + cores;
  return { low: score < 6, mid: score >= 6 && score < 10, high: score >= 10 };
})();

/* ── Particles ────────────────────────────────────────── */
(function initParticles() {
  if (devicePerf.low) return;
  const canvas = document.getElementById('particlesCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [], raf;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  const COUNT = devicePerf.high ? 55 : 30;
  function spawn() {
    particles = [];
    for (let i = 0; i < COUNT; i++) {
      particles.push({
        x: Math.random() * (W || 1000),
        y: Math.random() * (H || 800),
        r: Math.random() * 1.5 + 0.3,
        dx: (Math.random() - 0.5) * 0.3,
        dy: -Math.random() * 0.4 - 0.1,
        a: Math.random() * 0.6 + 0.2
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99,102,241,${p.a})`;
      ctx.fill();
      p.x += p.dx; p.y += p.dy;
      if (p.y < -5) { p.y = H + 5; p.x = Math.random() * W; }
      if (p.x < -5) p.x = W + 5;
      if (p.x > W + 5) p.x = -5;
    });
    raf = requestAnimationFrame(draw);
  }

  window.addEventListener('resize', function() {
    cancelAnimationFrame(raf);
    resize();
    spawn();
    draw();
  }, { passive: true });

  requestAnimationFrame(() => {
    resize(); spawn(); draw();
  });
})();

/* ── Cursor Spotlight ─────────────────────────────────── */
(function initSpotlight() {
  const el = document.getElementById('cursorSpotlight');
  if (!el || devicePerf.low) return;
  let visible = false;
  document.addEventListener('mousemove', function(e) {
    if (!visible) { el.style.opacity = '1'; visible = true; }
    el.style.left = e.clientX + 'px';
    el.style.top  = e.clientY + 'px';
  }, { passive: true });
  document.addEventListener('mouseleave', function() { el.style.opacity = '0'; visible = false; });
})();

/* ── Card Tilt on Cursor ──────────────────────────────── */
(function initCardTilt() {
  if (devicePerf.low) return;
  let raf = null;
  document.addEventListener('mousemove', function(e) {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = null;
      document.querySelectorAll('.section-card, .stat-card, .qr-card, .attendance-card, .step-card, .auth-card').forEach(card => {
        const rect = card.getBoundingClientRect();
        const cx   = rect.left + rect.width  / 2;
        const cy   = rect.top  + rect.height / 2;
        const dx   = (e.clientX - cx) / (rect.width  / 2);
        const dy   = (e.clientY - cy) / (rect.height / 2);
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1.5) {
          card.style.transform = `perspective(800px) rotateY(${dx * 3}deg) rotateX(${-dy * 3}deg) translateY(-2px)`;
        } else {
          card.style.transform = '';
        }
      });
    });
  }, { passive: true });
  document.addEventListener('mouseleave', function() {
    document.querySelectorAll('.section-card, .stat-card, .qr-card, .attendance-card, .step-card, .auth-card').forEach(c => { c.style.transform = ''; });
  });
})();

/* ── Button Magnetic Effect ───────────────────────────── */
(function initMagnet() {
  if (devicePerf.low) return;
  document.addEventListener('mousemove', function(e) {
    document.querySelectorAll('.btn-primary, .btn-success').forEach(btn => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width  / 2;
      const cy = rect.top  + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 80) {
        const pull = (80 - dist) / 80;
        btn.style.transform = `translate(${dx * pull * 0.3}px, ${dy * pull * 0.3}px)`;
      } else {
        btn.style.transform = '';
      }
    });
  }, { passive: true });
})();

/* ── Debounced Resize ─────────────────────────────────── */
(function() {
  let t;
  const orig = window.onresize;
  window.addEventListener('resize', function(e) {
    clearTimeout(t);
    t = setTimeout(() => { if (orig) orig(e); }, 150);
  }, { passive: true });
})();
