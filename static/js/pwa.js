/* HDATTAHER MOBILE — installer l'application sur l'écran d'accueil
   - Android / ordinateur : le bouton n'apparaît QUE quand Chrome autorise l'installation directe ;
     un toucher ouvre la vraie fenêtre d'installation (aucune explication affichée).
   - iPhone : petit guide (Apple n'a pas de fenêtre d'installation). */
(function () {
    // 1. Service worker (ouverture plus rapide + page « Pas de connexion »)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {});
        });
    }

    var ua = navigator.userAgent || '';
    var isIOS = /iphone|ipad|ipod/i.test(ua) || (/macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
    var inApp = /FBAN|FBAV|FB_IAB|Instagram|Line\/|Snapchat|TikTok|musical_ly|BytedanceWebview/i.test(ua);
    var standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;

    var bar = document.getElementById('pwaBar');
    var sheet = document.getElementById('pwaSheet');
    var nativeBtn = document.getElementById('pwaNative');
    if (!sheet) return;
    if (nativeBtn) nativeBtn.hidden = true;

    function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

    if (standalone) {
        store('pwa_installed', '1');
        return; // déjà ouverte comme application : rien à proposer
    }

    function prompt() { return window.__hmBip || null; }
    function available() { return isIOS || !!prompt(); }

    function refresh() {
        var ok = available();
        document.querySelectorAll('.pwa-menu-link').forEach(function (a) { a.hidden = !ok; });
        if (!ok) hideBar();
    }

    function openSheet() { // iPhone seulement
        if (typeof window.closeMobileMenu === 'function') { try { window.closeMobileMenu(); } catch (e) {} }
        sheet.querySelectorAll('[data-pwa-os]').forEach(function (b) { b.hidden = b.getAttribute('data-pwa-os') !== 'ios'; });
        var ia = sheet.querySelector('[data-pwa-inapp]'); if (ia) ia.hidden = !inApp;
        sheet.hidden = false;
        requestAnimationFrame(function () { sheet.classList.add('open'); });
        document.body.style.overflow = 'hidden';
    }
    function close() {
        sheet.classList.remove('open');
        document.body.style.overflow = '';
        setTimeout(function () { sheet.hidden = true; }, 250);
    }
    function hideBar() { if (bar && !bar.hidden) { bar.classList.remove('show'); setTimeout(function () { bar.hidden = true; }, 300); } }

    function install(ev) {
        if (ev) ev.preventDefault();
        var d = prompt();
        if (d) { // Android / ordinateur : la vraie fenêtre d'installation, directement
            if (typeof window.closeMobileMenu === 'function') { try { window.closeMobileMenu(); } catch (e) {} }
            d.prompt();
            d.userChoice.then(function () { window.__hmBip = null; hideBar(); refresh(); }).catch(function () {});
        } else if (isIOS) {
            openSheet();
        }
    }

    document.querySelectorAll('[data-pwa-open]').forEach(function (b) { b.addEventListener('click', install); });
    sheet.querySelectorAll('[data-pwa-close]').forEach(function (b) { b.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !sheet.hidden) close(); });
    window.addEventListener('appinstalled', function () {
        store('pwa_installed', '1'); window.__hmBip = null; hideBar(); close(); refresh();
    });
    window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); window.__hmBip = e; document.dispatchEvent(new Event('hm-bip')); });

    // 2. Petite barre « Installer » : sur téléphone, à partir de la 2e visite, pas pendant un achat,
    //    et pas plus d'une fois tous les 14 jours si le client l'a fermée.
    var quiet = (document.currentScript && document.currentScript.getAttribute('data-quiet')) ||
        (document.querySelector('script[src*="pwa.js"]') || { getAttribute: function () { return '0'; } }).getAttribute('data-quiet');
    var visits = parseInt(store('pwa_visits') || '0', 10) + 1;
    store('pwa_visits', String(visits));
    var closedAt = parseInt(store('pwa_bar_closed') || '0', 10);
    var recentlyClosed = closedAt && (Date.now() - closedAt) < 14 * 864e5;
    var barAllowed = bar && visits >= 2 && quiet !== '1' && !recentlyClosed && store('pwa_installed') !== '1';
    function showBar() {
        if (!barAllowed || !available() || !bar.hidden) return;
        setTimeout(function () {
            if (!available()) return;
            bar.hidden = false;
            requestAnimationFrame(function () { bar.classList.add('show'); });
        }, isIOS ? 2500 : 600);
    }

    refresh();
    if (isIOS) showBar();
    document.addEventListener('hm-bip', function () { refresh(); showBar(); });

    var x = document.getElementById('pwaBarX');
    if (x) x.addEventListener('click', function () { store('pwa_bar_closed', String(Date.now())); hideBar(); });
})();
