/**
 * HDATTAHER MOBILE - JavaScript Principal
 * Gère le thème, la langue, la navigation, les animations
 */

// ============================================================
//  THEME (Mode sombre / clair)
// ============================================================
const ThemeManager = {
  init() {
    const saved = localStorage.getItem('theme') || 'light';
    this.set(saved);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  },
  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  },
  toggle() {
    const current = localStorage.getItem('theme') || 'light';
    this.set(current === 'dark' ? 'light' : 'dark');
  }
};

// ============================================================
//  MULTILINGUE
// ============================================================
const translations = {
  fr: {
    home: 'Accueil', products: 'Produits', about: 'À propos', contact: 'Contact',
    search: 'Rechercher...', all_categories: 'Toutes les catégories',
    sort_by: 'Trier par', newest: 'Plus récent', price_asc: 'Prix croissant',
    price_desc: 'Prix décroissant', popular: 'Populaire',
    in_stock: 'En stock', low_stock: 'Stock faible', out_of_stock: 'Rupture',
    buy_whatsapp: 'Commander via WhatsApp', view_details: 'Voir détails',
    hero_title: 'Les Meilleurs', hero_title2: 'Smartphones', hero_title3: 'au Niger',
    hero_desc: 'Découvrez notre collection exclusive de smartphones et accessoires. Qualité premium, prix imbattables.',
    shop_now: 'Acheter maintenant', our_products: 'Nos Produits',
    featured: 'Produits Vedettes', latest: 'Nouveautés',
    featured_desc: 'Nos meilleurs produits sélectionnés pour vous',
    special_offers: 'Offres Spéciales', view_all: 'Voir tout',
    views: 'vues', fcfa: 'FCFA',
    about_us: 'À Propos de Nous', our_categories: 'Nos Catégories',
    footer_desc: 'Votre destination de confiance pour les smartphones et accessoires au Niger.',
    quick_links: 'Liens Rapides', contact_us: 'Contactez-nous',
    follow_us: 'Suivez-nous', all_rights: 'Tous droits réservés',
    products_count: 'Produits', brands_count: 'Marques', clients_count: 'Clients satisfaits',
    min_price: 'Prix min', max_price: 'Prix max', filter: 'Filtrer',
    related_products: 'Produits Similaires', category: 'Catégorie',
    stock: 'Stock', brand: 'Marque',
  },
  en: {
    home: 'Home', products: 'Products', about: 'About', contact: 'Contact',
    search: 'Search...', all_categories: 'All categories',
    sort_by: 'Sort by', newest: 'Newest', price_asc: 'Price ascending',
    price_desc: 'Price descending', popular: 'Popular',
    in_stock: 'In stock', low_stock: 'Low stock', out_of_stock: 'Out of stock',
    buy_whatsapp: 'Order via WhatsApp', view_details: 'View details',
    hero_title: 'The Best', hero_title2: 'Smartphones', hero_title3: 'in Niger',
    hero_desc: 'Discover our exclusive collection of smartphones and accessories. Premium quality, unbeatable prices.',
    shop_now: 'Shop now', our_products: 'Our Products',
    featured: 'Featured Products', latest: 'New Arrivals',
    featured_desc: 'Our best products selected for you',
    special_offers: 'Special Offers', view_all: 'View all',
    views: 'views', fcfa: 'FCFA',
    about_us: 'About Us', our_categories: 'Our Categories',
    footer_desc: 'Your trusted destination for smartphones and accessories in Niger.',
    quick_links: 'Quick Links', contact_us: 'Contact Us',
    follow_us: 'Follow Us', all_rights: 'All rights reserved',
    products_count: 'Products', brands_count: 'Brands', clients_count: 'Happy clients',
    min_price: 'Min price', max_price: 'Max price', filter: 'Filter',
    related_products: 'Related Products', category: 'Category',
    stock: 'Stock', brand: 'Brand',
  },
  ar: {
    home: 'الرئيسية', products: 'المنتجات', about: 'حولنا', contact: 'اتصل بنا',
    search: '...بحث', all_categories: 'جميع الفئات',
    sort_by: 'ترتيب حسب', newest: 'الأحدث', price_asc: 'السعر تصاعدياً',
    price_desc: 'السعر تنازلياً', popular: 'الأكثر شعبية',
    in_stock: 'متوفر', low_stock: 'مخزون منخفض', out_of_stock: 'نفذ',
    buy_whatsapp: 'اطلب عبر واتساب', view_details: 'عرض التفاصيل',
    hero_title: 'أفضل', hero_title2: 'الهواتف الذكية', hero_title3: 'في النيجر',
    hero_desc: 'اكتشف مجموعتنا الحصرية من الهواتف الذكية والإكسسوارات. جودة عالية وأسعار لا تقبل المنافسة.',
    shop_now: 'تسوق الآن', our_products: 'منتجاتنا',
    featured: 'منتجات مميزة', latest: 'وصل حديثاً',
    featured_desc: 'أفضل منتجاتنا المختارة لكم',
    special_offers: 'عروض خاصة', view_all: 'عرض الكل',
    views: 'مشاهدات', fcfa: 'فرنك',
    about_us: 'من نحن', our_categories: 'فئاتنا',
    footer_desc: 'وجهتك الموثوقة للهواتف الذكية والإكسسوارات في النيجر.',
    quick_links: 'روابط سريعة', contact_us: 'اتصل بنا',
    follow_us: 'تابعنا', all_rights: 'جميع الحقوق محفوظة',
    products_count: 'منتجات', brands_count: 'علامات', clients_count: 'عملاء سعداء',
    min_price: 'أقل سعر', max_price: 'أعلى سعر', filter: 'تصفية',
    related_products: 'منتجات مشابهة', category: 'الفئة',
    stock: 'المخزون', brand: 'العلامة',
  }
};

const LangManager = {
  init() {
    const saved = localStorage.getItem('lang') || 'fr';
    this.set(saved);
    const sel = document.getElementById('langSelect');
    if (sel) {
      sel.value = saved;
      sel.addEventListener('change', (e) => this.set(e.target.value));
    }
  },
  set(lang) {
    localStorage.setItem('lang', lang);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    const t = translations[lang] || translations['fr'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key]) el.textContent = t[key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (t[key]) el.placeholder = t[key];
    });
  }
};

// ============================================================
//  NAVIGATION
// ============================================================
const NavManager = {
  init() {
    const toggle = document.querySelector('.mobile-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', () => links.classList.toggle('active'));
      links.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => links.classList.remove('active'));
      });
    }
    window.addEventListener('scroll', () => {
      const nav = document.querySelector('.navbar');
      if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
    });
  }
};

// ============================================================
//  ANIMATIONS (Intersection Observer)
// ============================================================
const AnimationManager = {
  init() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
  }
};

// ============================================================
//  FORMAT PRIX
// ============================================================
function formatPrice(price) {
  return new Intl.NumberFormat('fr-FR').format(price) + ' FCFA';
}

// ============================================================
//  FLASH MESSAGES AUTO-DISMISS
// ============================================================
function initFlashMessages() {
  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(100%)';
      setTimeout(() => msg.remove(), 400);
    }, 4000);
  });
}

// ============================================================
//  SEARCH LIVE
// ============================================================
function initSearch() {
  const input = document.getElementById('liveSearch');
  const results = document.getElementById('searchResults');
  if (!input || !results) return;
  let timeout;
  input.addEventListener('input', function () {
    clearTimeout(timeout);
    const q = this.value.trim();
    if (q.length < 2) { results.style.display = 'none'; return; }
    timeout = setTimeout(() => {
      fetch('/api/products?q=' + encodeURIComponent(q))
        .then(r => r.json())
        .then(data => {
          if (data.length === 0) { results.style.display = 'none'; return; }
          results.innerHTML = data.map(p => `
            <a href="/product/${p.id}" class="search-result-item">
              <span>${p.name}</span>
              <span class="search-price">${formatPrice(p.price)}</span>
            </a>
          `).join('');
          results.style.display = 'block';
        });
    }, 300);
  });
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !results.contains(e.target))
      results.style.display = 'none';
  });
}

// ============================================================
//  COUNTER ANIMATION
// ============================================================
function initCounters() {
  const counters = document.querySelectorAll('.counter');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-target'));
        let current = 0;
        const increment = target / 60;
        const timer = setInterval(() => {
          current += increment;
          if (current >= target) { current = target; clearInterval(timer); }
          el.textContent = Math.floor(current).toLocaleString('fr-FR');
        }, 25);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => observer.observe(c));
}

// ============================================================
//  INITIALISATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  LangManager.init();
  NavManager.init();
  AnimationManager.init();
  initFlashMessages();
  initSearch();
  initCounters();
});
