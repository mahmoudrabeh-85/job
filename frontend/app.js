/* ═══════════════════════════════════════════════════════════════════════
   Smart Job Matcher — SPA Application (app.js)
   Router + State + API Client + i18n (AR/EN)
   ═══════════════════════════════════════════════════════════════════════ */

// ─── i18n ──────────────────────────────────────────────────────────────
const LANG = {
  ar: {
    dir: 'rtl',
    brand: 'محلل الوظائف الذكي',
    nav: { dashboard: 'لوحة التحكم', jobs: 'الوظائف', analytics: 'التحليلات', hr: 'أدوات HR', gaps: 'فجوات المهارات', settings: 'الإعدادات', myapps: 'تقديماتي' },
    stats: { totalJobs: 'وظيفة مطابقة', avgScore: 'متوسط التقييم', highMatch: 'تطابق عالي', sources: 'مصادر' },
    search: { placeholder: 'ابحث بالاسم، الشركة، الموقع...', clear: 'مسح' },
    filters: { all: 'الكل', high: 'عالٍ', mid: 'متوسط', low: 'منخفض' },
    sort: { scoreDesc: 'الأعلى تقييماً', scoreAsc: 'الأدنى تقييماً', titleAsc: 'الاسم (أ-ي)', source: 'المصدر' },
    job: { apply: 'قدّم الآن ←', score: 'نسبة التطابق', matched: 'المهارات المطابقة', missing: 'الفجوة — دورات مقترحة', hrLetter: 'رسالة HR', copy: '📋 نسخ الرسالة', copied: 'تم نسخ الرسالة ✓', copyFail: 'فشل النسخ' },
    empty: { title: 'لا توجد وظائف مطابقة', desc: 'جرّب تغيير الفلتر أو كلمات البحث', searchDesc: 'لا نتائج لبحثك. جرّب كلمات أخرى', reset: 'عرض كل الوظائف' },
    loading: 'جاري التحميل...',
    error: 'فشل تحميل البيانات',
    retry: 'إعادة المحاولة',
    refresh: '⟳ تحديث',
    refreshing: 'جاري التحديث...',
    theme: { dark: '🌙', light: '☀️' },
    lang: 'EN',
    analytics: {
      scoreDistTitle: 'توزيع التقييمات',
      topSkillsTitle: 'أكثر المهارات المطلوبة',
      sourcesTitle: 'الوظائف حسب المصدر',
      swotTitle: 'تحليل SWOT',
      strengths: 'نقاط القوة', weaknesses: 'نقاط الضعف', opportunities: 'الفرص', threats: 'التهديدات',
    },
    hr: {
      builderTitle: 'منشئ رسائل التغطية',
      selectJob: 'اختر وظيفة أو اكتب العنوان',
      company: 'اسم الشركة',
      tone: 'النبرة',
      tones: { formal: 'رسمي', semi: 'شبه رسمي' },
      generate: 'توليد الرسالة',
      templates: 'قوالب جاهزة',
      followUp: 'متابعة بعد التقديم',
      thankYou: 'شكر بعد المقابلة',
      salaryNeg: 'تفاوض الراتب',
    },
    settings: {
      profile: 'الملف الشخصي',
      sourcesTitle: 'مصادر الوظائف',
      exportTitle: 'تصدير البيانات',
      exportCSV: 'تصدير CSV',
      exportJSON: 'تصدير JSON',
      themeTitle: 'المظهر',
      langTitle: 'اللغة',
    },
    priority: { high: 'مهم', medium: 'متوسط', low: 'منخفض' },
  },
  en: {
    dir: 'ltr',
    brand: 'Smart Job Matcher',
    nav: { dashboard: 'Dashboard', jobs: 'Jobs', analytics: 'Analytics', hr: 'HR Tools', gaps: 'Skill Gaps', settings: 'Settings', myapps: 'My Applications' },
    stats: { totalJobs: 'Matched Jobs', avgScore: 'Avg Score', highMatch: 'High Match', sources: 'Sources' },
    search: { placeholder: 'Search by title, company, location...', clear: 'Clear' },
    filters: { all: 'All', high: 'High', mid: 'Medium', low: 'Low' },
    sort: { scoreDesc: 'Highest Score', scoreAsc: 'Lowest Score', titleAsc: 'Name (A-Z)', source: 'Source' },
    job: { apply: 'Apply Now →', score: 'Match Score', matched: 'Matched Skills', missing: 'Gaps — Suggested Courses', hrLetter: 'HR Letter', copy: '📋 Copy Letter', copied: 'Letter copied ✓', copyFail: 'Copy failed' },
    empty: { title: 'No matching jobs', desc: 'Try changing your filters or search terms', searchDesc: 'No results for your search. Try different keywords', reset: 'Show all jobs' },
    loading: 'Loading...',
    error: 'Failed to load data',
    retry: 'Retry',
    refresh: '⟳ Refresh',
    refreshing: 'Refreshing...',
    theme: { dark: '🌙', light: '☀️' },
    lang: 'عربي',
    analytics: {
      scoreDistTitle: 'Score Distribution',
      topSkillsTitle: 'Most Demanded Skills',
      sourcesTitle: 'Jobs by Source',
      swotTitle: 'SWOT Analysis',
      strengths: 'Strengths', weaknesses: 'Weaknesses', opportunities: 'Opportunities', threats: 'Threats',
    },
    hr: {
      builderTitle: 'Cover Letter Builder',
      selectJob: 'Select a job or type title',
      company: 'Company Name',
      tone: 'Tone',
      tones: { formal: 'Formal', semi: 'Semi-formal' },
      generate: 'Generate Letter',
      templates: 'Ready Templates',
      followUp: 'Follow-up After Application',
      thankYou: 'Thank You After Interview',
      salaryNeg: 'Salary Negotiation',
    },
    settings: {
      profile: 'Profile',
      sourcesTitle: 'Job Sources',
      exportTitle: 'Export Data',
      exportCSV: 'Export CSV',
      exportJSON: 'Export JSON',
      themeTitle: 'Theme',
      langTitle: 'Language',
    },
    priority: { high: 'High', medium: 'Medium', low: 'Low' },
  },
};

// ─── State ─────────────────────────────────────────────────────────────
const state = {
  lang: localStorage.getItem('sjm-lang') || 'ar',
  theme: localStorage.getItem('sjm-theme') || 'dark',
  currentPage: 'dashboard',
  allJobs: [],
  filteredJobs: [],
  currentFilter: 'all',
  currentWorkType: 'all',
  selectedSkills: [],
  selectedSources: [],
  selectedCategories: [],
  currentSort: 'score_desc',
  searchTerm: '',
  searchTimer: null,
  stats: null,
  modalHrEn: '',
  modalHrAr: '',
  modalJob: null,
  appliedIds: null,
  applyType: 'all',
  // Pagination state
  pageSize: 20,
  currentPageNum: 1,
  hasMore: true,
  filterSig: '',
};

function t() { return LANG[state.lang]; }

// ─── API Client ────────────────────────────────────────────────────────
const API_BASE = window.location.origin;

async function api(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const r = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error(`API error: ${endpoint}`, e);
    throw e;
  }
}

// ─── Router ────────────────────────────────────────────────────────────
function navigate(page) {
  if (state.currentPage === page) return;
  document.querySelectorAll('.page-view, .page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  const nav = document.querySelector(`[data-page="${page}"]`);
  if (el) { el.classList.add('active'); state.currentPage = page; }
  if (nav) nav.classList.add('active');
  // Update topbar title
  const titles = { dashboard: t().nav.dashboard, jobs: t().nav.jobs, analytics: t().nav.analytics, hr: t().nav.hr, gaps: t().nav.gaps, settings: t().nav.settings, myapps: t().nav.myapps };
  document.getElementById('topbarTitle').textContent = titles[page] || '';
  // Lazy-load page data
  if (page === 'dashboard' && !state.stats) loadStats();
  if (page === 'jobs' && state.allJobs.length === 0) loadJobs();
  if (page === 'jobs' && state.allJobs.length > 0) renderJobs(getFilteredJobs());
  if (page === 'analytics' && !state.stats) loadStats();
  if (page === 'analytics' && state.stats) renderAnalyticsPage();
  if (page === 'hr') renderHRPage();
  if (page === 'gaps') renderSkillGapsPage();
  if (page === 'settings') renderSettingsPage();
  if (page === 'myapps') renderApplicationsPage();
  location.hash = '#/' + page;
}

function initRouter() {
  const hash = location.hash.replace('#/', '');
  const valid = ['dashboard', 'jobs', 'analytics', 'hr', 'gaps', 'settings', 'myapps'];
  if (valid.includes(hash)) navigate(hash);
  else navigate('dashboard');
}

// ─── Theme ─────────────────────────────────────────────────────────────
function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('sjm-theme', state.theme);
  document.getElementById('themeBtn').textContent = state.theme === 'dark' ? t().theme.dark : t().theme.light;
}

function applyTheme() {
  if (state.theme === 'light') document.documentElement.setAttribute('data-theme', 'light');
}

// ─── Language ──────────────────────────────────────────────────────────
function toggleLang() {
  state.lang = state.lang === 'ar' ? 'en' : 'ar';
  localStorage.setItem('sjm-lang', state.lang);
  document.documentElement.setAttribute('dir', t().dir);
  document.documentElement.setAttribute('lang', state.lang);
  rebuildUI();
}

function rebuildUI() {
  // Re-render all translatable text
  const tr = t();
  document.getElementById('brandText').textContent = tr.brand;
  document.getElementById('topbarTitle').textContent = tr.nav[state.currentPage] || '';
  document.getElementById('themeBtn').textContent = state.theme === 'dark' ? tr.theme.dark : tr.theme.light;
  document.getElementById('langBtn').textContent = tr.lang;
  document.getElementById('refreshBtn').textContent = tr.refresh;
  // Nav items
  document.querySelectorAll('.nav-item').forEach(n => {
    const page = n.dataset.page;
    const label = n.querySelector('.nav-label');
    if (label && tr.nav[page]) label.textContent = tr.nav[page];
  });
  // Search
  const sb = document.getElementById('searchBox');
  if (sb) sb.placeholder = tr.search.placeholder;
  // Filter buttons
  document.querySelectorAll('.filter-btn[data-filter]').forEach(b => {
    const f = b.dataset.filter;
    const span = b.querySelector('.filter-count');
    const countText = span ? span.outerHTML : '';
    if (tr.filters[f]) b.innerHTML = tr.filters[f] + ' ' + countText;
  });
  // Sort
  const sortSel = document.getElementById('sortSelect');
  if (sortSel) {
    sortSel.options[0].text = tr.sort.scoreDesc;
    sortSel.options[1].text = tr.sort.scoreAsc;
    sortSel.options[2].text = tr.sort.titleAsc;
    sortSel.options[3].text = tr.sort.source;
  }
  // Stat labels
  document.querySelectorAll('[data-stat-label]').forEach(el => {
    const key = el.dataset.statLabel;
    if (tr.stats[key]) el.textContent = tr.stats[key];
  });
  // Re-render current page data
  if (state.allJobs.length) { updateStatCards(); renderJobs(getFilteredJobs()); }
  renderAnalyticsPage();
  renderHRPage();
  renderSettingsPage();
}

// ─── Data Loading ──────────────────────────────────────────────────────
async function loadJobs() {
  showSkeletons();
  try {
    const d = await api('/api/v1/jobs?page=1&page_size=500');
    state.allJobs = d.items || d.jobs || [];
    updateStatCards();
    populateSourceChips();
    renderJobs(state.allJobs);
  } catch (e) {
    document.getElementById('jobsGrid').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h2>${t().error}</h2>
        <button class="btn btn-primary" onclick="loadJobs()">${t().retry}</button>
      </div>`;
  }
}

async function loadStats() {
  try {
    state.stats = await api('/api/v1/stats');
    updateStatCards();
    renderAnalyticsPage();
  } catch (e) {
    console.error('Stats load failed', e);
  }
}

function showSkeletons() {
  const g = document.getElementById('jobsGrid');
  if (!g) return;
  g.innerHTML = Array.from({ length: 6 }).map(() =>
    `<div class="sk-card"><div class="skeleton sk-line w80"></div><div class="skeleton sk-line w40"></div><div class="skeleton sk-line w60"></div><div class="skeleton sk-line w30"></div></div>`
  ).join('');
}

// ─── Stat Cards ────────────────────────────────────────────────────────
function updateStatCards() {
  const jobs = state.allJobs;
  const scores = jobs.map(j => j.analysis?.score || 0);
  const total = jobs.length;
  const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  const high = scores.filter(s => s > 50).length;
  const mid = scores.filter(s => s >= 25 && s <= 50).length;
  const low = scores.filter(s => s < 25).length;
  const sources = new Set(jobs.map(j => j.source)).size;

  animateCounter('countAll', total);
  animateCounter('countHigh', high);
  setText('statAvgVal', avg + '%');
  animateCounter('statSourcesVal', sources);

  // Status pill
  const statusText = document.getElementById('liveStatusText');
  if (statusText) {
    statusText.textContent = state.lang === 'ar' ? `${total} وظيفة مفهرسة` : `${total} Jobs Indexed`;
  }

  // Work type counts
  let countRemote = 0, countHybrid = 0, countOnsite = 0;
  const skillFreq = {};

  jobs.forEach(j => {
    const loc = (j.location || '').toLowerCase();
    const title = (j.title || '').toLowerCase();
    const combined = loc + ' ' + title;

    if (combined.includes('remote') || combined.includes('عن بعد')) {
      countRemote++;
    } else if (combined.includes('hybrid') || combined.includes('هجين')) {
      countHybrid++;
    } else {
      countOnsite++;
    }

    (j.analysis?.matched || []).forEach(m => {
      const cat = m.category;
      if (cat) skillFreq[cat] = (skillFreq[cat] || 0) + 1;
    });
  });

  setText('countWorkAll', total);
  setText('countWorkRemote', countRemote);
  setText('countWorkHybrid', countHybrid);
  setText('countWorkOnsite', countOnsite);

  setText('countFilterHigh', high);
  setText('countFilterMid', mid);
  setText('countFilterLow', low);

  // Apply-type counts
  let cFree = 0, cLinkedin = 0, cPaid = 0;
  jobs.forEach(j => { const t = getApplyType(j); if (t === 'free') cFree++; else if (t === 'linkedin') cLinkedin++; else if (t === 'paid') cPaid++; });
  setText('countApplyAll', total);
  setText('countApplyFree', cFree);
  setText('countApplyLinkedin', cLinkedin);
  setText('countApplyPaid', cPaid);

  // Build Top Skills Cloud
  const skillsCloud = document.getElementById('skillsChipsCloud');
  if (skillsCloud) {
    const topSkills = Object.entries(skillFreq).sort((a, b) => b[1] - a[1]).slice(0, 10);
    skillsCloud.innerHTML = topSkills.map(([skill, count]) => {
      const isSelected = state.selectedSkills.includes(skill);
      return `<div class="filter-chip ${isSelected ? 'active' : ''}" onclick="toggleSkillChip('${skill}', this)">
        <span>${esc(skill)}</span>
        <span class="chip-count">${count}</span>
      </div>`;
    }).join('');
  }
}

function animateCounter(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  if (start === target) { el.textContent = target; return; }
  const duration = 600;
  const startTime = performance.now();
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

// ─── Search & Filter ───────────────────────────────────────────────────
function onSearchInput(v) {
  state.searchTerm = v.trim().toLowerCase();
  document.getElementById('searchClear').classList.toggle('show', state.searchTerm.length > 0);
  clearTimeout(state.searchTimer);
  state.searchTimer = setTimeout(() => renderJobs(getFilteredJobs()), 300);
}

function clearSearch() {
  document.getElementById('searchBox').value = '';
  state.searchTerm = '';
  document.getElementById('searchClear').classList.remove('show');
  renderJobs(getFilteredJobs());
}


function setWorkType(type, el) {
  state.currentWorkType = type;
  document.querySelectorAll('#workTypeGroup .filter-chip').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  renderJobs(getFilteredJobs());
}

function setScoreFilter(score, el) {
  state.currentFilter = score;
  document.querySelectorAll('#matchScoreGroup .filter-chip').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  renderJobs(getFilteredJobs());
}

function getApplyType(job) {
  const url = (job.url || '').toLowerCase();
  const src = (job.source || '').toLowerCase();
  // لينكدإن: رابط لينكدإن أو مصدر لينكدإن
  if (url.includes('linkedin.com') || src.includes('linkedin')) return 'linkedin';
  // مدفوع: معظم مصادرنا الحالية مجانية 100%، لكن نحتفظ بالفلتر للمستقبل (API مدفوع أو Bayt Premium)
  if (url.includes('premium') || url.includes('subscription') || src.includes('premium')) return 'paid';
  // افتراضي: مجاني مباشر (التقديم عبر رابط الشركة مباشرة بلا دفع)
  return 'free';
}

function setApplyType(type, el) {
  state.applyType = type;
  document.querySelectorAll('#applyTypeGroup .filter-chip').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  renderJobs(getFilteredJobs());
}

function buildLinkedInUrl(job) {
  const q = job ? `${job.title} ${job.company || ''}`.trim() : (state.searchTerm || document.getElementById('searchBox')?.value || '').trim() || 'procurement';
  return 'https://www.linkedin.com/jobs/search/?keywords=' + encodeURIComponent(q);
}

function toggleSkillChip(skill, el) {
  const idx = state.selectedSkills.indexOf(skill);
  if (idx > -1) {
    state.selectedSkills.splice(idx, 1);
    if (el) el.classList.remove('active');
  } else {
    state.selectedSkills.push(skill);
    if (el) el.classList.add('active');
  }
  renderJobs(getFilteredJobs());
}

// ─── Sources & Categories (multi-select) ───────────────────────────────
const CATEGORY_KEYWORDS = {
  pharma: ['pharma', 'pharmacy', 'pharmacist', 'medical', 'healthcare', 'health', 'clinical', 'صيدل', 'طبي', 'دواء'],
  supply: ['procurement', 'supply_chain', 'supply chain', 'logistics', 'purchasing', 'warehouse', 'inventory', 'sourcing', 'مشتريات', 'إمداد'],
  sales: ['sales', 'marketing', 'business development', 'account executive', 'مبيعات', 'تسويق'],
  tech: ['dev', 'engineer', 'software', 'data', 'analyst', 'ai_ml', 'تقنية', 'بيانات', 'مبرمج'],
  mgmt: ['management', 'operations', 'project', 'إدارة', 'عمليات'],
};

function toggleSourceChip(src, el) {
  const idx = state.selectedSources.indexOf(src);
  if (idx > -1) {
    state.selectedSources.splice(idx, 1);
    if (el) el.classList.remove('active');
  } else {
    state.selectedSources.push(src);
    if (el) el.classList.add('active');
  }
  renderJobs(getFilteredJobs());
}

function toggleCategoryChip(cat, el) {
  const idx = state.selectedCategories.indexOf(cat);
  if (idx > -1) {
    state.selectedCategories.splice(idx, 1);
    if (el) el.classList.remove('active');
  } else {
    state.selectedCategories.push(cat);
    if (el) el.classList.add('active');
  }
  renderJobs(getFilteredJobs());
}

function populateSourceChips() {
  const box = document.getElementById('sourceChipsCloud');
  if (!box) return;
  const counts = {};
  state.allJobs.forEach(j => {
    const s = (j.source || 'other').toLowerCase();
    counts[s] = (counts[s] || 0) + 1;
  });
  const names = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  box.innerHTML = names.map(s =>
    `<div class="filter-chip${state.selectedSources.includes(s) ? ' active' : ''}" data-source="${esc(s)}" onclick="toggleSourceChip('${esc(s)}', this)">` +
    `<span>🔗 ${esc(s)}</span><span class="chip-count">${counts[s]}</span></div>`
  ).join('') || '<span style="color:var(--text-muted);font-size:.82rem">لا مصادر بعد</span>';
}

function handleOverlayClick(e) {
  if (e.target.id === 'modalOverlay') {
    closeModal();
  }
}

function setFilter(f, el) {
  state.currentFilter = f;
  document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  renderJobs(getFilteredJobs());
}

function sortJobs() {
  state.currentSort = document.getElementById('sortSelect').value;
  renderJobs(getFilteredJobs());
}

function getFilteredJobs() {
  let filtered = state.allJobs;

  if (state.searchTerm) {
    filtered = filtered.filter(j => {
      const search = (j.title + ' ' + j.company + ' ' + j.location + ' ' + j.source + ' ' +
        (j.analysis?.matched || []).map(m => m.category).join(' ')).toLowerCase();
      return search.includes(state.searchTerm);
    });
  }

  // Work Type Filter
  if (state.currentWorkType && state.currentWorkType !== 'all') {
    filtered = filtered.filter(j => {
      const loc = (j.location || '').toLowerCase();
      const title = (j.title || '').toLowerCase();
      const combined = loc + ' ' + title;
      if (state.currentWorkType === 'remote') return combined.includes('remote') || combined.includes('عن بعد');
      if (state.currentWorkType === 'hybrid') return combined.includes('hybrid') || combined.includes('هجين');
      if (state.currentWorkType === 'onsite') return !combined.includes('remote') && !combined.includes('عن بعد');
      return true;
    });
  }

  // Score Filter
  if (state.currentFilter === 'high') {
    filtered = filtered.filter(j => (j.analysis?.score || 0) > 50);
  } else if (state.currentFilter === 'mid') {
    filtered = filtered.filter(j => { const s = j.analysis?.score || 0; return s >= 25 && s <= 50; });
  } else if (state.currentFilter === 'low') {
    filtered = filtered.filter(j => (j.analysis?.score || 0) < 25);
  }

  // Skills filter
  if (state.selectedSkills.length > 0) {
    filtered = filtered.filter(j => {
      const matchedCats = (j.analysis?.matched || []).map(m => m.category);
      return state.selectedSkills.some(reqSkill => matchedCats.includes(reqSkill));
    });
  }

  // Apply-type filter: مجاني / لينكدإن / مدفوع
  if (state.applyType && state.applyType !== 'all') {
    filtered = filtered.filter(j => getApplyType(j) === state.applyType);
  }

  // Sources filter (multi-select: empty = all sites)
  if (state.selectedSources.length > 0) {
    filtered = filtered.filter(j => state.selectedSources.includes((j.source || '').toLowerCase()));
  }

  // Categories filter (multi-select: e.g. pharma only)
  if (state.selectedCategories.length > 0) {
    filtered = filtered.filter(j => {
      const hay = ((j.title || '') + ' ' + (j.company || '') + ' ' + (j.category || '') + ' ' +
        (j.analysis?.matched || []).map(m => m.category).join(' ')).toLowerCase();
      return state.selectedCategories.some(cat =>
        (CATEGORY_KEYWORDS[cat] || []).some(kw => hay.includes(kw.toLowerCase()))
      );
    });
  }

  state.filteredJobs = sortArray(filtered);
  return state.filteredJobs;
}

function getPaginatedJobs() {
  // نمط «تحميل المزيد» التراكمي: كل ضغطة تضيف 20 دون استبدال المعروض سابقاً
  const end = state.currentPageNum * state.pageSize;
  const paginated = state.filteredJobs.slice(0, end);
  state.hasMore = end < state.filteredJobs.length;
  return paginated;
}

function calcFilterSig() {
  return [
    state.searchTerm,
    state.currentFilter,
    state.currentWorkType,
    state.applyType,
    state.currentSort,
    state.allJobs.length,
    state.selectedSkills.join('|'),
    state.selectedSources.join('|'),
    state.selectedCategories.join('|')
  ].join('::');
}

function updateResultsCounter() {
  const total = state.filteredJobs.length;
  const displayed = Math.min(state.currentPageNum * state.pageSize, total);
  const counter = document.getElementById('resultsCounter');
  if (counter) {
    counter.textContent = state.lang === 'ar'
      ? `عرض ${displayed} من ${total}`
      : `Showing ${displayed} of ${total}`;
  }
  const loadMoreBtn = document.getElementById('loadMoreBtn');
  if (loadMoreBtn) {
    loadMoreBtn.style.display = state.hasMore ? 'inline-flex' : 'none';
  }
  const footerCounters = document.querySelectorAll('.jobs-counter');
  footerCounters.forEach(c => {
    c.textContent = state.lang === 'ar'
      ? `عرض ${displayed} من ${total}`
      : `Showing ${displayed} of ${total}`;
  });
  const footerBtns = document.querySelectorAll('.load-more-btn');
  footerBtns.forEach(b => {
    b.style.display = state.hasMore ? '' : 'none';
  });
}

function sortArray(jobs) {
  const s = state.currentSort;
  return [...jobs].sort((a, b) => {
    if (s === 'score_desc') return (b.analysis?.score || 0) - (a.analysis?.score || 0);
    if (s === 'score_asc') return (a.analysis?.score || 0) - (b.analysis?.score || 0);
    if (s === 'title_asc') return (a.title || '').localeCompare(b.title || '');
    if (s === 'source_asc') return (a.source || '').localeCompare(b.source || '');
    return 0;
  });
}

function searchLinkedIn() {
  const q = (state.searchTerm || document.getElementById('searchBox')?.value || '').trim() || 'procurement';
  const url = 'https://www.linkedin.com/jobs/search/?keywords=' + encodeURIComponent(q);
  window.open(url, '_blank', 'noopener');
  toast(state.lang === 'ar' ? 'فتحت بحث لينكدإن بنفس الكلمات' : 'Opened LinkedIn search with same keywords');
}

function searchGulf(board) {
  const q = (state.searchTerm || document.getElementById('searchBox')?.value || '').trim() || 'procurement';
  const urls = {
    bayt: 'https://www.bayt.com/en/international/jobs/?q=' + encodeURIComponent(q),
    wuzzuf: 'https://wuzzuf.net/search/jobs/?q=' + encodeURIComponent(q),
    gulftalent: 'https://www.gulftalent.com/search?searchtext=' + encodeURIComponent(q),
    naukri: 'https://www.naukrigulf.com/search-jobs/?q=' + encodeURIComponent(q),
  };
  window.open(urls[board] || urls.bayt, '_blank', 'noopener');
  toast(state.lang === 'ar' ? 'فتحت البحث بنفس الكلمات' : 'Opened board search with same keywords');
}

function resetAll() {
  state.searchTerm = '';
  state.currentFilter = 'all';
  state.currentWorkType = 'all';
  state.selectedSkills = [];
  state.selectedSources = [];
  state.selectedCategories = [];
  state.applyType = 'all';
  document.querySelectorAll('#workTypeGroup .filter-chip').forEach(b => b.classList.toggle('active', b.dataset.worktype === 'all'));
  document.querySelectorAll('#matchScoreGroup .filter-chip').forEach(b => b.classList.toggle('active', b.dataset.filter === 'all'));
  document.querySelectorAll('#applyTypeGroup .filter-chip').forEach(b => b.classList.toggle('active', b.dataset.apply === 'all'));
  document.querySelectorAll('#sourceChipsCloud .filter-chip').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('#categoryChipsCloud .filter-chip').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('#skillsChipsCloud .filter-chip').forEach(b => b.classList.remove('active'));
  document.getElementById('searchBox').value = '';
  document.getElementById('searchClear').classList.remove('show');
  const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
  if (allBtn) setFilter('all', allBtn);
  else renderJobs(getFilteredJobs());
}

// ─── Render Jobs ───────────────────────────────────────────────────────
function renderJobs(jobs) {
  const g = document.getElementById('jobsGrid');
  const g2 = document.getElementById('jobsExplorerGrid');
  if (!g && !g2) return;
  const tr = t();

  if (!jobs.length) {
    const emptyHtml = `<div class="empty-state">
      <div class="empty-icon">🔍</div>
      <h2 style="font-size:1.2rem; margin-bottom:8px;">${tr.empty.title}</h2>
      <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:16px;">${state.searchTerm ? tr.empty.searchDesc : tr.empty.desc}</p>
      <button class="btn-primary" onclick="resetAll()">${tr.empty.reset}</button>
    </div>`;
    if (g) g.innerHTML = emptyHtml;
    if (g2) g2.innerHTML = emptyHtml;
    return;
  }

  // ── Pagination: عرض أول 20 ثم «تحميل المزيد» — يصفّر عند تغيير أي فلتر ──
  const sig = calcFilterSig();
  if (sig !== state.filterSig) {
    state.filterSig = sig;
    state.currentPageNum = 1;
  }
  state.filteredJobs = jobs || [];
  const shown = getPaginatedJobs();
  updateResultsCounter();

  const html = shown.map((j, idx) => {
    const sc = j.analysis?.score || 0;
    const matchClass = sc > 50 ? 'match-high' : sc >= 25 ? 'match-mid' : 'match-low';
    const initials = (j.company || j.title || 'SJ').substring(0, 2).toUpperCase();

    const loc = (j.location || '').toLowerCase();
    const isRemote = loc.includes('remote') || (j.title || '').toLowerCase().includes('remote');

    const matchedSkills = (j.analysis?.matched || []).slice(0, 3).map(m =>
      `<span class="skill-match-tag">✓ ${esc(m.category)}</span>`
    ).join('');

    return `
    <div class="job-card" style="animation-delay:${Math.min(idx * 30, 300)}ms" onclick='openModal(${JSON.stringify(j).replace(/'/g, "&#39;")})'>
      <div class="job-card-top">
        <div class="job-company-avatar">${esc(initials)}</div>
        <div class="job-meta-primary">
          <div class="job-title">${esc(j.title)}</div>
          <div class="job-company">${esc(j.company || 'Enterprise Partner')} • ${esc(j.source)}</div>
        </div>
        <div class="match-radial ${matchClass}">
          <span>${sc}%</span>
        </div>
      </div>

      <div class="job-tags-row">
        ${isRemote ? '<span class="tag-pill tag-remote">🌐 Remote</span>' : '<span class="tag-pill">🏢 ' + esc(j.location || 'Onsite') + '</span>'}
        ${j.salary ? '<span class="tag-pill tag-salary">💰 ' + esc(j.salary) + '</span>' : ''}
      </div>

      <div class="skills-list">
        ${matchedSkills || '<span style="font-size:0.75rem; color:var(--text-muted)">تحليل المهارات متوفر</span>'}
      </div>

      <div class="job-card-actions" style="flex-wrap:wrap; gap:6px">
        <button class="btn-secondary" onclick="event.stopPropagation(); openModal(${JSON.stringify(j).replace(/'/g, "&#39;")})">
          🔍 التفاصيل
        </button>
        <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center">
          <a class="btn-primary" href="${esc(j.url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="تقديم مجاني مباشر عبر موقع الشركة — لا يحتاج اشتراك">
            🆓 مجاني
          </a>
          <a class="btn-secondary" href="${esc(buildLinkedInUrl(j))}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="قدّم عبر LinkedIn بحسابك الحالي — Easy Apply مجاني">
            💼 لينكدإن
          </a>
        </div>
      </div>
      <div style="display:flex; gap:6px; margin-top:4px; flex-wrap:wrap">
        <span class="tag-pill" style="font-size:.72rem; background:${getApplyType(j) === 'free' ? 'rgba(16,185,129,.12)' : getApplyType(j) === 'linkedin' ? 'rgba(14,165,233,.12)' : 'rgba(245,158,11,.12)'}; border-color:${getApplyType(j) === 'free' ? 'rgba(16,185,129,.25)' : getApplyType(j) === 'linkedin' ? 'rgba(14,165,233,.25)' : 'rgba(245,158,11,.25)'}">${getApplyType(j) === 'free' ? '🆓 تقديم مجاني' : getApplyType(j) === 'linkedin' ? '💼 Easy Apply' : '🔒 اشتراك'}</span>
        <span class="tag-pill" style="font-size:.72rem">🔗 ${esc(j.source)}</span>
      </div>
      ${(state.appliedIds && state.appliedIds.has(String(j.id || j.url))) ? '<div style="margin-top:6px"><span class="skill-chip">✅ قدمت</span></div>' : ''}
    </div>`;
  }).join('');

  // ── Footer: عداد النتائج + زر تحميل المزيد ──
  const total = state.filteredJobs.length;
  const footer = total > state.pageSize
    ? `<div class="jobs-footer">
        <span class="jobs-counter">${state.lang === 'ar' ? `عرض ${Math.min(state.currentPageNum * state.pageSize, total)} من ${total}` : `Showing ${Math.min(state.currentPageNum * state.pageSize, total)} of ${total}`}</span>
        <button type="button" class="btn-secondary load-more-btn" onclick="loadMoreJobs()" ${state.hasMore ? '' : 'style="display:none"'}">${state.lang === 'ar' ? 'تحميل المزيد' : 'Load more'} (${state.pageSize})</button>
      </div>`
    : '';

  if (g) g.innerHTML = html + footer;
  if (g2) g2.innerHTML = html + footer;
}

function loadMoreJobs() {
  state.currentPageNum += 1;
  renderJobs(state.filteredJobs);
}

// ─── Modal ─────────────────────────────────────────────────────────────
async function openModal(job) {
  const tr = t();
  state.modalJob = job;
  document.getElementById('modalOverlay').classList.add('show');
  document.body.style.overflow = 'hidden';
  const mc = document.getElementById('modalContent');
  mc.innerHTML = `<div class="modal-section"><div class="skeleton sk-line w80" style="height:20px"></div></div>
    <div class="modal-section"><div class="skeleton" style="width:90px;height:90px;border-radius:50%;margin:0 auto"></div></div>`;

  try {
    const d = await api('/api/v1/analyze', {
      method: 'POST',
      body: JSON.stringify({ title: job.title, description: job.source || '', company: job.company || '' }),
    });
    const a = d.analysis;
    const sc = a.score;
    const color = sc > 50 ? 'var(--success)' : sc >= 25 ? 'var(--warning)' : 'var(--danger)';
    const ringColor = sc > 50 ? '#00d4aa' : sc >= 25 ? '#ffd700' : '#ff4466';

    state.modalHrEn = d.hr_en;
    state.modalHrAr = d.hr_ar;

    const matchedHtml = '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
      (a.matched.map(m => `<span class="skill-chip" style="font-size:.8rem;padding:4px 10px">${m.category}: ${esc(m.skills.join(', '))}</span>`).join('') ||
        `<span style="color:var(--muted)">${tr.empty.title}</span>`) + '</div>';

    let missingHtml = '';
    if (d.gaps && d.gaps.length) {
      missingHtml = d.gaps.map(g => `<div class="gap-item">
        <div class="info">
          <div class="category">${g.category}</div>
          <div class="advice">${esc(g.course)} — ${esc(g.platform)} (${esc(g.duration)}) — ${esc(g.cost)}</div>
        </div>
        <span class="priority priority-${g.priority}">${tr.priority[g.priority] || g.priority}</span>
      </div>`).join('');
    }

    mc.innerHTML = `
      <h2>${esc(job.title)}</h2>
      <div class="job-meta-line">${esc(job.company)} • ${esc(job.location)} • ${esc(job.source)} ${job.salary ? '• ' + esc(job.salary) : ''}</div>
      <div class="modal-section" style="text-align:center">
        <div class="ring-wrap">
          <svg class="progress-ring" width="110" height="110" viewBox="0 0 110 110">
            <circle class="ring-bg" cx="55" cy="55" r="48"/>
            <circle class="ring-fg" cx="55" cy="55" r="48" stroke="${ringColor}" stroke-dasharray="301.59" stroke-dashoffset="301.59" id="ringFg"/>
          </svg>
          <div style="position:relative;margin-top:-86px;font-size:1.6rem;font-weight:800;color:${color}">${sc}%</div>
        </div>
        <div style="color:var(--muted);font-size:.85rem">${tr.job.score}</div>
      </div>
      <div class="modal-section"><h3>✅ ${tr.job.matched} (${a.matched_count})</h3>${matchedHtml}</div>
      ${missingHtml ? `<div class="modal-section"><h3>⚠️ ${tr.job.missing} (${a.missing_count})</h3>${missingHtml}</div>` : ''}
      <div class="modal-section">
        <h3>📝 ${tr.job.hrLetter}</h3>
        <div class="hr-tabs">
          <div class="hr-tab active" onclick="showHrTab('en',this)">English</div>
          <div class="hr-tab" onclick="showHrTab('ar',this)">عربي</div>
        </div>
        <div class="hr-content" id="hrContent">${esc(d.hr_en)}</div>
        <button class="btn btn-accent2 btn-sm" style="margin-top:var(--s2)" onclick="copyHr()">${tr.job.copy}</button>
      </div>
      <div class="modal-section" id="vetSection">
        <h3>🏢 فحص الشركة وملف التقديم</h3>
        <div style="color:var(--muted);font-size:.85rem">جاري تحليل الراتب والعقد وإشارات الثقة...</div>
      </div>
      <div style="text-align:center;margin-top:var(--s4);display:flex;gap:8px;justify-content:center;flex-wrap:wrap;flex-direction:column;align-items:center">
        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
          <a href="${esc(job.url)}" target="_blank" class="btn btn-primary btn-lg" title="تقديم مجاني مباشر — يفتح موقع الشركة بدون اشتراك">🆓 قدّم مجاناً الآن</a>
          <a href="${esc(buildLinkedInUrl(job))}" target="_blank" class="btn btn-accent2 btn-lg" style="background:var(--info);color:#fff" title="قدّم بحساب LinkedIn الحالي — Easy Apply مجاني بدون اشتراك إضافي">💼 قدّم عبر LinkedIn</a>
        </div>
        <div style="color:var(--muted);font-size:.82rem;max-width:520px">
          <b>🆓 مجاني:</b> يفتح الموقع الأصلي للشركة — التقديم مباشر بلا دفع (الإيميل + السيرة). <b>💼 LinkedIn:</b> يستخدم حسابك الحالي على LinkedIn — <b>Easy Apply = مجاني تماماً</b>، يُرسل بروفايلك مباشرة. لا تحتاج LinkedIn Premium إلا لو طلبتها الشركة نادراً.
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:6px">
          <span class="tag-pill">🔗 المصدر: ${esc(job.source)}</span>
          <span class="tag-pill" style="background:${getApplyType(job) === 'free' ? 'rgba(16,185,129,.12)' : getApplyType(job) === 'linkedin' ? 'rgba(14,165,233,.12)' : 'rgba(245,158,11,.12)'}">${getApplyType(job) === 'free' ? '🆓 هذه الوظيفة مجانية' : getApplyType(job) === 'linkedin' ? '💼 متاحة Easy Apply' : '🔒 قد تطلب اشتراكاً في المصدر'}</span>
        </div>
      </div>
      <div class="modal-section">
        <h3>🚀 التقديم الذكي</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-accent2 btn-sm" onclick="prepareApplication()">📋 جهز التقديم وافتح الصفحة</button>
          <button class="btn btn-sm" onclick="mailApplication()">✉️ إرسال بالبريد</button>
          <button class="btn btn-sm" onclick="markApplied(state.modalJob)">✅ سجل أنك قدمت</button>
        </div>
        <div style="color:var(--muted);font-size:.8rem;margin-top:6px">التجهيز ينسخ الرسالة ويفتح صفحة الشركة — أنت تراجع وترسل بنفسك ثم تسجل</div>
      </div>`;

    loadCompanyVet(job);

    requestAnimationFrame(() => {
      setTimeout(() => {
        const fg = document.getElementById('ringFg');
        if (fg) fg.style.strokeDashoffset = 301.59 - (301.59 * sc / 100);
      }, 50);
    });
  } catch (e) {
    mc.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h2>${tr.error}</h2></div>`;
  }
}

function showHrTab(lang, el) {
  document.querySelectorAll('.hr-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  const content = lang === 'en' ? state.modalHrEn : state.modalHrAr;
  document.getElementById('hrContent').textContent = content;
  document.getElementById('hrContent').style.direction = lang === 'en' ? 'ltr' : 'rtl';
  document.getElementById('hrContent').style.textAlign = lang === 'en' ? 'left' : 'right';
}

function copyHr() {
  const text = document.getElementById('hrContent').textContent;
  navigator.clipboard.writeText(text)
    .then(() => toast(t().job.copied))
    .catch(() => toast(t().job.copyFail, 'err'));
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('show');
  document.body.style.overflow = '';
}

// ─── Company Vetting ───────────────────────────────────────────────────
async function loadCompanyVet(job) {
  const box = document.getElementById('vetSection');
  if (!box) return;
  try {
    const q = new URLSearchParams({
      company: job.company || '',
      title: job.title || '',
      location: job.location || '',
      salary_raw: job.salary || '',
      url: job.url || '',
      source: job.source || '',
      description: (job.company || '') + ' ' + (job.title || ''),
    }).toString();
    const v = await api('/api/v1/company-vet?' + q);
    const riskColor = v.company.risk_level === 'high' ? 'var(--danger)' : v.company.risk_level === 'medium' ? 'var(--warning)' : 'var(--success)';
    const riskLabel = v.company.risk_level === 'high' ? 'خطر مرتفع — تحقق أولا' : v.company.risk_level === 'medium' ? 'حذر متوسط' : 'مبدئيا سليمة';
    const sal = v.salary_expected;
    const salText = sal.monthly_estimate ? `${sal.monthly_estimate} ${sal.currency.toUpperCase()} شهريا` : 'الراتب غير مذكور — اطلبه كتابة';
    const flagsHtml = (v.company.risk_flags || []).map(f => `<div class="gap-item"><div class="info"><div class="category">⚠️ ${esc(f.msg_ar)}</div></div><span class="priority priority-high">${f.level}</span></div>`).join('') || '<span style="color:var(--muted);font-size:.85rem">لا إشارات خطر من البيانات الحالية</span>';
    const docsHtml = (v.docs || []).map(d => `<label style="display:flex;gap:8px;align-items:center;font-size:.85rem;margin:6px 0"><input type="checkbox" data-doc="${d.id}" ${d.required ? 'checked' : ''} style="width:16px;height:16px"> <span>${esc(d.label_ar)} ${d.required ? '(أساسي)' : '(اختياري)'}</span></label>`).join('');
    const links = v.company.verification_links || {};
    box.innerHTML = `
      <h3>🏢 فحص الشركة وملف التقديم</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0">
        <span class="skill-chip" style="border-color:${riskColor};color:${riskColor}">${riskLabel}</span>
        <span class="skill-chip">💰 ${esc(salText)}</span>
        <span class="skill-chip">📄 ${esc(v.contract.type)}${v.contract.duration ? ' — ' + esc(v.contract.duration) : ''}</span>
      </div>
      <div style="font-size:.9rem;margin:8px 0">✅ القرار المبدئي: ${esc(v.decision_ar)}</div>
      <div style="margin:8px 0">${flagsHtml}</div>
      <div style="margin:10px 0"><b>🔗 تحقق يدوي (سنة التأسيس وآراء الموظفين):</b>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">
          <a href="${links.google}" target="_blank" class="btn btn-sm">Google</a>
          <a href="${links.linkedin}" target="_blank" class="btn btn-sm">LinkedIn</a>
          <a href="${links.glassdoor}" target="_blank" class="btn btn-sm">Glassdoor</a>
          <a href="${links.trustpilot}" target="_blank" class="btn btn-sm">Trustpilot</a>
        </div>
        <div style="color:var(--muted);font-size:.8rem;margin-top:6px">ابحث عن سنة التأسيس وعدد السنوات في السوق وآراء العملاء والموظفين قبل إرسال أوراقك</div>
      </div>
      <div style="margin:10px 0"><b>📎 ما يلزم للتوثيق أثناء التقديم:</b>${docsHtml}
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn btn-sm" onclick="copyVetDocs()">📋 نسخ قائمة الأوراق</button>
          <button class="btn btn-sm" onclick="deepCheckCompany()">🔍 فحص معمق</button>
        </div>
      </div>`;
  } catch (e) {
    box.innerHTML = `<h3>🏢 فحص الشركة وملف التقديم</h3><div style="color:var(--muted);font-size:.85rem">تعذر تحليل الشركة حاليا — تحقق يدويا من الرابط الأصلي</div>`;
  }
}

function copyVetDocs() {
  const items = [...document.querySelectorAll('#vetSection input[data-doc]')].map(el => {
    const label = el.parentElement?.innerText?.trim() || el.getAttribute('data-doc');
    return (el.checked ? '[x] ' : '[ ] ') + label;
  });
  const text = 'قائمة أوراق التقديم:\n' + items.join('\n');
  navigator.clipboard.writeText(text).then(() => toast(t().job.copied)).catch(() => toast(t().job.copyFail, 'err'));
}

function deepCheckCompany() {
  const title = document.querySelector('#modalContent h2')?.textContent || '';
  const meta = document.querySelector('#modalContent .job-meta-line')?.textContent || '';
  const text = `افحص لي هذه الشركة بعمق: ${title} — ${meta}. أريد تاريخ التأسيس وعدد السنوات والتقييم وآراء الموظفين وهل هي حقيقية أم وهمية مع روابط التوثيق.`;
  navigator.clipboard.writeText(text).then(() => toast('تم نسخ طلب الفحص المعمق — الصقه في الشات للبحث المعمق')).catch(() => toast(t().job.copyFail, 'err'));
}

// ─── SWOT strategy → jobs (each strategy linked to its matching jobs) ───
const STRATEGY_ACTIONS = {
  'SO-1': {type: 'search', q: 'oracle'},
  'SO-2': {type: 'search', q: 'sales'},
  'WO-1': {type: 'search', q: 'erp'},
  'WO-2': {type: 'search', q: 'data'},
  'ST-1': {type: 'link', url: 'https://www.linkedin.com/'},
  'ST-2': {type: 'page', page: 'hr'},
  'WT-1': {type: 'reset'},
};

function applyStrategy(code) {
  const a = STRATEGY_ACTIONS[code];
  if (!a) return;
  if (a.type === 'search') {
    document.getElementById('searchBox').value = a.q;
    state.searchTerm = a.q.toLowerCase();
    navigate('jobs');
    renderJobs(getFilteredJobs());
    toast(state.lang === 'ar' ? `عرض وظائف ${a.q} — اختر بطاقة ثم قدّم الآن` : `Showing ${a.q} jobs — pick a card then Apply`);
  } else if (a.type === 'link') {
    window.open(a.url, '_blank', 'noopener');
  } else if (a.type === 'page') {
    navigate(a.page);
  } else if (a.type === 'reset') {
    resetAll();
    navigate('jobs');
  }
}

// ─── Analytics Page ────────────────────────────────────────────────────
function renderAnalyticsPage() {
  const container = document.getElementById('analyticsContent');
  if (!container) return;
  const tr = t();
  const st = state.stats;
  if (!st) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><h2>${tr.loading}</h2></div>`;
    return;
  }

  const dist = st.score_distribution || {};
  const maxDist = Math.max(...Object.values(dist), 1);
  const distBars = Object.entries(dist).map(([range, count]) => {
    const pct = Math.round((count / maxDist) * 100);
    const color = range.startsWith('8') ? 'green' : range.startsWith('6') ? 'green' : range.startsWith('4') ? 'gold' : range.startsWith('2') ? 'gold' : 'red';
    return `<div class="chart-bar-group">
      <div class="chart-bar-label"><span>${range}</span><span>${count}</span></div>
      <div class="chart-bar-track"><div class="chart-bar-fill ${color}" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');

  const srcEntries = Object.entries(st.sources || {});
  const maxSrc = Math.max(...srcEntries.map(e => e[1]), 1);
  const srcBars = srcEntries.map(([src, count]) => {
    const pct = Math.round((count / maxSrc) * 100);
    return `<div class="chart-bar-group">
      <div class="chart-bar-label"><span>${esc(src)}</span><span>${count}</span></div>
      <div class="chart-bar-track"><div class="chart-bar-fill purple" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');

  // Top skills from allJobs
  const skillCounts = {};
  state.allJobs.forEach(j => {
    (j.analysis?.matched || []).forEach(m => {
      skillCounts[m.category] = (skillCounts[m.category] || 0) + 1;
    });
  });
  const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const maxSkill = topSkills.length ? topSkills[0][1] : 1;
  const skillBars = topSkills.map(([skill, count]) => {
    const pct = Math.round((count / maxSkill) * 100);
    return `<div class="chart-bar-group">
      <div class="chart-bar-label"><span>${esc(skill)}</span><span>${count}</span></div>
      <div class="chart-bar-track"><div class="chart-bar-fill blue" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');

  container.innerHTML = `
    <div class="grid-2">
      <div class="card"><div class="card-title">📊 ${tr.analytics.scoreDistTitle}</div><div class="chart-container">${distBars || '<p style="color:var(--muted)">No data</p>'}</div></div>
      <div class="card"><div class="card-title">🏢 ${tr.analytics.sourcesTitle}</div><div class="chart-container">${srcBars || '<p style="color:var(--muted)">No data</p>'}</div></div>
    </div>
    <div class="card" style="margin-top:var(--s4)"><div class="card-title">🔥 ${tr.analytics.topSkillsTitle}</div><div class="chart-container">${skillBars || '<p style="color:var(--muted)">No data</p>'}</div></div>
    <div class="card" style="margin-top:var(--s4)" id="swotCard"><div class="card-title">🧭 ${tr.analytics.swotTitle}</div><div id="swotContent" style="color:var(--muted);font-size:.85rem">${tr.loading}</div></div>`;
  loadSwot();
}

// ─── SWOT Section (live from DB) ───────────────────────────────────────
async function loadSwot() {
  const box = document.getElementById('swotContent');
  if (!box) return;
  try {
    const d = await api('/api/v1/swot');
    const quad = [
      {icon: '💪', label: t().analytics.strengths, items: d.strengths, color: 'var(--success)'},
      {icon: '⚠️', label: t().analytics.weaknesses, items: d.weaknesses, color: 'var(--danger)'},
      {icon: '🚀', label: t().analytics.opportunities, items: d.opportunities, color: 'var(--warning)'},
      {icon: '🛡️', label: t().analytics.threats, items: d.threats, color: 'var(--accent2)'},
    ];
    const quadHtml = quad.map(q =>
      `<div class="card" style="margin:0"><div class="card-title" style="color:${q.color}">${q.icon} ${esc(q.label)}</div>` +
      (q.items || []).map(i => `<div class="gap-item"><div class="info"><div class="category">${esc(i.title)}</div><div class="advice">${esc(i.evidence || '')}</div></div><span class="priority priority-mid">${esc(i.impact || '')}</span></div>`).join('') +
      `</div>`
    ).join('');
    const stratHtml = (d.strategies || []).map(s =>
      `<div class="gap-item"><div class="info"><div class="category">${esc(s.code)} — ${esc(s.name)}</div><div class="advice">${esc(s.desc)}</div><button class="btn btn-sm" style="margin-top:6px" onclick="applyStrategy('${esc(s.code)}')">🔍 عرض وظائف هذه الاستراتيجية</button></div><span class="priority priority-high">${esc(s.win || '')}</span></div>`
    ).join('');
    box.innerHTML = `<div style="color:var(--muted);font-size:.82rem;margin-bottom:8px">مبني على ${d.stats.total} وظيفة حية من القاعدة</div><div class="grid-2" style="margin-bottom:8px">${quadHtml}</div><div class="card-title">🎯 استراتيجيات العمل</div>${stratHtml}`;
  } catch (e) {
    box.textContent = t().error;
  }
}

// ─── HR Tools Page ─────────────────────────────────────────────────────
function renderHRPage() {
  const container = document.getElementById('hrContent2');
  if (!container) return;
  const tr = t();

  container.innerHTML = `
    <div class="card" style="margin-bottom:var(--s4)">
      <div class="card-title">✍️ ${tr.hr.builderTitle}</div>
      <div style="display:grid;gap:var(--s3);margin-top:var(--s3)">
        <input class="input" id="hrJobTitle" placeholder="${tr.hr.selectJob}">
        <input class="input" id="hrCompany" placeholder="${tr.hr.company}">
        <div class="btn-group">
          <button class="btn btn-primary" onclick="generateHR('en')">🇺🇸 English</button>
          <button class="btn btn-accent2" onclick="generateHR('ar')">🇪🇬 عربي</button>
        </div>
        <div class="hr-content" id="hrGeneratedContent" style="min-height:200px;margin-top:var(--s2)"></div>
        <button class="btn btn-sm" onclick="copyGenerated()">${tr.job.copy}</button>
      </div>
    </div>
    <div class="card">
      <div class="card-title">📋 ${tr.hr.templates}</div>
      <div style="display:grid;gap:var(--s2);margin-top:var(--s3)">
        <button class="btn" onclick="showTemplate('followup')">📩 ${tr.hr.followUp}</button>
        <button class="btn" onclick="showTemplate('thankyou')">🙏 ${tr.hr.thankYou}</button>
        <button class="btn" onclick="showTemplate('salary')">💰 ${tr.hr.salaryNeg}</button>
      </div>
    </div>`;
}

async function generateHR(lang) {
  const title = document.getElementById('hrJobTitle').value || 'Position';
  const company = document.getElementById('hrCompany').value || 'Company';
  try {
    const d = await api('/api/v1/hr-template', {
      method: 'POST',
      body: JSON.stringify({ title, company, lang }),
    });
    const el = document.getElementById('hrGeneratedContent');
    el.textContent = d.template;
    el.style.direction = lang === 'en' ? 'ltr' : 'rtl';
    el.style.textAlign = lang === 'en' ? 'left' : 'right';
  } catch (e) {
    toast(t().error, 'err');
  }
}

function copyGenerated() {
  const el = document.getElementById('hrGeneratedContent');
  if (!el) return;
  navigator.clipboard.writeText(el.textContent)
    .then(() => toast(t().job.copied))
    .catch(() => toast(t().job.copyFail, 'err'));
}

const EMAIL_TEMPLATES = {
  followup: {
    en: `Subject: Following Up on My Application — [Your Name]\n\nDear [Hiring Manager],\n\nI wanted to follow up on my application for the [Position] role submitted on [Date]. I remain very enthusiastic about the opportunity and would appreciate any updates on the timeline.\n\nThank you for your time and consideration.\n\nBest regards,\n[Your Name]`,
    ar: `الموضوع: متابعة طلب التوظيف\n\nعزيزي مدير التوظيف،\n\nأود متابعة طلبي لوظيفة [المسمى الوظيفي] المُقدم بتاريخ [التاريخ]. لا يزال لدي حماس كبير تجاه هذه الفرصة وأقدر أي تحديثات حول الجدول الزمني.\n\nشكراً لوقتكم،\n[اسمك]`,
  },
  thankyou: {
    en: `Subject: Thank You for the Interview\n\nDear [Interviewer Name],\n\nThank you for taking the time to interview me for the [Position] role. I enjoyed learning more about the team and the exciting work at [Company].\n\nOur conversation reinforced my enthusiasm for the position. I look forward to hearing from you.\n\nBest regards,\n[Your Name]`,
    ar: `الموضوع: شكراً على المقابلة\n\nعزيزي [اسم المحاور]،\n\nأشكركم على الوقت الذي خصصتموه لمقابلتي لوظيفة [المسمى الوظيفي]. استمتعت بمعرفة المزيد عن الفريق والعمل المثير في [الشركة].\n\nحديثنا عزز حماسي تجاه هذه الوظيفة. أتطلع لسماع الأخبار منكم.\n\nمع خالص التحيات،\n[اسمك]`,
  },
  salary: {
    en: `Subject: Regarding Compensation Discussion\n\nDear [Hiring Manager],\n\nThank you for extending the offer for the [Position] role. I am excited about this opportunity.\n\nAfter careful consideration, I would like to discuss the compensation package. Based on my research and experience, I believe a salary of [Amount] would better reflect the value I bring.\n\nI am open to discussing this further.\n\nBest regards,\n[Your Name]`,
    ar: `الموضوع: بخصوص مناقشة الراتب\n\nعزيزي مدير التوظيف،\n\nشكراً لتقديم عرض لوظيفة [المسمى الوظيفي]. أنا متحمس لهذه الفرصة.\n\nبعد دراسة متأنية، أود مناقشة حزمة التعويضات. بناءً على بحثي وخبرتي، أعتقد أن راتب [المبلغ] سيعكس بشكل أفضل القيمة التي أقدمها.\n\nأنا منفتح لمناقشة هذا الأمر.\n\nمع خالص التحيات،\n[اسمك]`,
  },
};

function showTemplate(type) {
  const tmpl = EMAIL_TEMPLATES[type];
  if (!tmpl) return;
  const lang = state.lang;
  const el = document.getElementById('hrGeneratedContent');
  el.textContent = tmpl[lang] || tmpl.en;
  el.style.direction = lang === 'en' ? 'ltr' : 'rtl';
  el.style.textAlign = lang === 'en' ? 'left' : 'right';
}

// ─── Skill Gaps Page ────────────────────────────────────────────────
async function renderSkillGapsPage() {
  const container = document.getElementById('gapsContent');
  if (!container) return;
  const tr = t();
  container.innerHTML = `<div class="empty-state"><div class="empty-icon">🎯</div><h2>${tr.loading}</h2></div>`;

  try {
    const d = await api('/api/gaps');

    // ─── KPI Row ───
    const kpiHtml = `
      <div class="kpi-grid" style="margin-bottom:var(--s4)">
        <div class="kpi-card">
          <div class="kpi-header"><span class="kpi-title">الوظائف المحللة</span><div class="kpi-icon-wrap">📊</div></div>
          <div class="kpi-value">${d.total_jobs_analyzed}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-header"><span class="kpi-title">فجوات مطلوبة</span><div class="kpi-icon-wrap" style="color:var(--danger)">⚠️</div></div>
          <div class="kpi-value" style="color:var(--danger)">${d.gaps_count}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-header"><span class="kpi-title">مهاراتك مطابقة</span><div class="kpi-icon-wrap" style="color:var(--success)">✅</div></div>
          <div class="kpi-value" style="color:var(--success)">${d.matched_count}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-header"><span class="kpi-title">مهاراتك الإجمالية</span><div class="kpi-icon-wrap" style="color:var(--brand-primary)">💪</div></div>
          <div class="kpi-value">${d.user_skills_count}</div>
        </div>
      </div>`;

    // ─── Matched Skills ───
    let matchedHtml = '';
    if (d.matched && d.matched.length) {
      const rows = d.matched.map(m => {
        const pct = m.percentage || 0;
        const color = pct > 40 ? 'var(--success)' : pct > 20 ? 'var(--warning)' : 'var(--text-muted)';
        return `<div class="gap-item">
          <div class="info">
            <div class="category">${esc(m.name)}</div>
            <div class="advice">مطلوبة في ${m.frequency} وظيفة (${pct}%)</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:80px;height:6px;background:var(--border-subtle);border-radius:3px;overflow:hidden">
              <div style="width:${Math.min(pct,100)}%;height:100%;background:${color};border-radius:3px"></div>
            </div>
            <span style="color:${color};font-weight:700;font-size:.85rem">${pct}%</span>
          </div>
        </div>`;
      }).join('');
      matchedHtml = `<div class="card" style="margin-bottom:var(--s4)"><div class="card-title">✅ المهارات المطابقة (${d.matched_count})</div>${rows}</div>`;
    }

    // ─── Skill Gaps ───
    let gapsHtml = '';
    if (d.gaps && d.gaps.length) {
      const rows = d.gaps.map(g => {
        const priorityColors = { high: 'var(--danger)', medium: 'var(--warning)', low: 'var(--info)' };
        const priorityLabels = { high: 'مهم', medium: 'متوسط', low: 'منخفض' };
        const pc = priorityColors[g.priority] || 'var(--text-muted)';
        const jobsList = (g.example_jobs || []).map(j => `<div style="font-size:.8rem;color:var(--text-muted)">• ${esc(j.title)} — ${esc(j.company)} ${j.salary ? '('+esc(j.salary)+')' : ''}</div>`).join('');
        return `<div class="gap-item" style="flex-direction:column;align-items:flex-start;gap:8px">
          <div style="display:flex;justify-content:space-between;width:100%;align-items:center">
            <div class="info">
              <div class="category">${esc(g.name)}</div>
              <div class="advice">${esc(g.course)} — ${esc(g.platform)} (${esc(g.duration)} — ${esc(g.cost)})</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
              <span style="font-size:.8rem;color:var(--text-muted)">${g.percentage}% من الوظائف</span>
              <span class="priority priority-${g.priority}">${priorityLabels[g.priority] || g.priority}</span>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;width:100%">
            <div style="flex:1;height:6px;background:var(--border-subtle);border-radius:3px;overflow:hidden">
              <div style="width:${Math.min(g.percentage,100)}%;height:100%;background:${pc};border-radius:3px"></div>
            </div>
            <span style="font-size:.8rem;color:var(--success)">+${esc(g.salary_boost)}</span>
          </div>
          ${jobsList ? `<div style="margin-top:4px;border-top:1px solid var(--border-subtle);padding-top:6px">${jobsList}</div>` : ''}
          <button class="btn btn-sm" onclick="showJobsForSkill('${esc(g.skill)}')" style="margin-top:2px">🔍 عرض وظائف هذه المهارة</button>
        </div>`;
      }).join('');
      gapsHtml = `<div class="card"><div class="card-title">⚠️ الفجوات المطلوبة (${d.gaps_count}) — دورات مقترحة لكل مهارة</div>${rows}</div>`;
    }

    container.innerHTML = kpiHtml + matchedHtml + gapsHtml;
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h2>${tr.error}</h2><button class="btn-primary" onclick="renderSkillGapsPage()">${tr.retry}</button></div>`;
  }
}

async function showJobsForSkill(skill) {
  navigate('jobs');
  document.getElementById('searchBox').value = skill;
  state.searchTerm = skill.toLowerCase();
  renderJobs(getFilteredJobs());
  toast(state.lang === 'ar' ? `عرض الوظائف التي تتطلب: ${skill}` : `Showing jobs requiring: ${skill}`);
}

// ─── Settings Page ─────────────────────────────────────────────────────
function renderSettingsPage() {
  const container = document.getElementById('settingsContent');
  if (!container) return;
  const tr = t();

  container.innerHTML = `
    <div class="card" style="margin-bottom:var(--s4)">
      <div class="card-title">🎨 ${tr.settings.themeTitle}</div>
      <div class="setting-item">
        <div><div class="setting-label">${tr.settings.themeTitle}</div></div>
        <label class="toggle"><input type="checkbox" ${state.theme === 'light' ? 'checked' : ''} onchange="toggleTheme()"><span class="toggle-slider"></span></label>
      </div>
    </div>
    <div class="card" style="margin-bottom:var(--s4)">
      <div class="card-title">🌐 ${tr.settings.langTitle}</div>
      <div class="setting-item">
        <div><div class="setting-label">${tr.settings.langTitle}</div></div>
        <button class="btn btn-sm" onclick="toggleLang()">${state.lang === 'ar' ? 'Switch to English' : 'التبديل للعربية'}</button>
      </div>
    </div>
    <div class="card">
      <div class="card-title">📦 ${tr.settings.exportTitle}</div>
      <div class="btn-group" style="margin-top:var(--s3)">
        <button class="btn" onclick="exportData('csv')">📄 ${tr.settings.exportCSV}</button>
        <button class="btn" onclick="exportData('json')">📋 ${tr.settings.exportJSON}</button>
      </div>
    </div>`;
}

function exportData(format) {
  const jobs = state.allJobs;
  if (format === 'json') {
    const blob = new Blob([JSON.stringify(jobs, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'jobs_export.json');
  } else {
    const headers = ['Title', 'Company', 'Location', 'Source', 'Score', 'URL'];
    const rows = jobs.map(j => [j.title, j.company, j.location, j.source, j.analysis?.score || 0, j.url].map(v => `"${String(v).replace(/"/g, '""')}"`).join(','));
    const csv = '\uFEFF' + headers.join(',') + '\n' + rows.join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    downloadBlob(blob, 'jobs_export.csv');
  }
  toast(t().job.copied);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─── Toast ─────────────────────────────────────────────────────────────
function toast(msg, type = 'ok') {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = 'toast ' + (type === 'ok' ? 'show-ok' : 'show-err');
  const icon = type === 'ok'
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  t.innerHTML = icon + '<span>' + msg + '</span>';
  c.appendChild(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 350); }, 2400);
}

// ─── Applications Tracker ──────────────────────────────────────────────
async function loadApplied() {
  try {
    const d = await api('/api/v1/applications');
    state.appliedIds = new Set((d.items || []).map(a => a.job_id));
  } catch (e) { state.appliedIds = new Set(); }
}

async function markApplied(job) {
  try {
    await api('/api/v1/applications', {
      method: 'POST',
      body: JSON.stringify({ job_id: String(job.id || job.url), title: job.title || '', company: job.company || '', url: job.url || '' }),
    });
    state.appliedIds = state.appliedIds || new Set();
    state.appliedIds.add(String(job.id || job.url));
    toast(state.lang === 'ar' ? 'سُجّل تقديمك بنجاح ✓' : 'Application recorded ✓');
    renderJobs(getFilteredJobs());
  } catch (e) { toast(t().error, 'err'); }
}

function prepareApplication() {
  const text = document.getElementById('hrContent')?.textContent || '';
  if (text) navigator.clipboard.writeText(text).catch(() => {});
  const job = state.modalJob;
  if (job?.url && job.url !== '#') window.open(job.url, '_blank', 'noopener');
  toast(state.lang === 'ar' ? 'نُسخت الرسالة وفُتحت صفحة التقديم — الصق وأرسل ثم سجّل' : 'Letter copied and apply page opened — paste, send, then record');
}

function mailApplication() {
  const job = state.modalJob || {};
  const text = (document.getElementById('hrContent')?.textContent || '').slice(0, 1500);
  const subject = encodeURIComponent(`Application for ${job.title || ''} — [Your Name]`);
  const body = encodeURIComponent(text + `\n\n—\n${job.title || ''} @ ${job.company || ''}\n${job.url || ''}`);
  window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

async function renderApplicationsPage() {
  const box = document.getElementById('myappsContent');
  if (!box) return;
  box.innerHTML = `<div style="color:var(--muted)">${t().loading}</div>`;
  try {
    const d = await api('/api/v1/applications');
    const items = d.items || [];
    if (!items.length) {
      box.innerHTML = `<div class="empty-state"><div class="empty-icon">📁</div><h2>${state.lang === 'ar' ? 'لا تقديمات مسجلة بعد' : 'No applications yet'}</h2><p style="color:var(--muted);font-size:.9rem">${state.lang === 'ar' ? 'افتح أي وظيفة واضغط سجل أنك قدمت' : 'Open any job and press record'}</p></div>`;
      return;
    }
    const opts = ['applied', 'interview', 'offer', 'rejected', 'withdrawn'];
    const labels = {applied: 'قدمت', interview: 'مقابلة', offer: 'عرض', rejected: 'مرفوض', withdrawn: 'سحبت'};
    box.innerHTML = items.map(a => `
      <div class="gap-item"><div class="info">
        <div class="category">${esc(a.title || a.job_id)} — ${esc(a.company || '')}</div>
        <div class="advice">${esc(a.applied_at || '')} • <a href="${esc(a.url || '#')}" target="_blank" style="color:var(--accent2)">رابط التقديم</a></div>
      </div>
      <select onchange="updateApplicationStatus('${esc(a.job_id)}', this.value)" style="background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px">
        ${opts.map(o => `<option value="${o}"${a.status === o ? ' selected' : ''}>${labels[o]}</option>`).join('')}
      </select></div>`).join('');
  } catch (e) { box.innerHTML = `<div style="color:var(--danger)">${t().error}</div>`; }
}

async function updateApplicationStatus(jobId, status) {
  try {
    await api('/api/v1/applications/' + encodeURIComponent(jobId), {method: 'PATCH', body: JSON.stringify({status})});
    toast(state.lang === 'ar' ? 'حُدّثت الحالة ✓' : 'Status updated ✓');
  } catch (e) { toast(t().error, 'err'); }
}

// ─── Utilities ─────────────────────────────────────────────────────────
function esc(s) { return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

function refreshJobs() {
  toast(t().refreshing);
  state.allJobs = [];
  state.stats = null;
  loadJobs();
  loadStats();
}

// ─── Sidebar Toggle ────────────────────────────────────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('collapsed');
  localStorage.setItem('sjm-sidebar', sb.classList.contains('collapsed') ? 'collapsed' : 'expanded');
}

function toggleMobileSidebar() {
  document.getElementById('sidebar').classList.toggle('mobile-open');
}

// ─── Keyboard Shortcuts ────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.ctrlKey && e.key === 'k') { e.preventDefault(); document.getElementById('searchBox')?.focus(); navigate('jobs'); }
});

// ─── Init ──────────────────────────────────────────────────────────────
function init() {
  applyTheme();
  document.documentElement.setAttribute('dir', t().dir);
  document.documentElement.setAttribute('lang', state.lang);
  // Restore sidebar state
  if (localStorage.getItem('sjm-sidebar') === 'collapsed') {
    document.getElementById('sidebar')?.classList.add('collapsed');
  }
  initRouter();
  loadJobs();
  loadStats();
  loadApplied();
}

document.addEventListener('DOMContentLoaded', init);

// Keyboard Shortcut for Search (Ctrl + K or /)
window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    const sb = document.getElementById('searchBox');
    if (sb) { sb.focus(); sb.select(); }
  }
});
