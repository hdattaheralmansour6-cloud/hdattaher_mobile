/* HDATTAHER MOBILE — installer l'application sur l'écran d'accueil */
(function () {
    // 1. Service worker (ouverture plus rapide + page « Pas de connexion »)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {});
        });
    }

    var ua = navigator.userAgent || '';
    var isIOS = /iphone|ipad|ipod/i.test(ua) || (/macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
    var isAndroid = /android/i.test(ua);
    var inApp = /FBAN|FBAV|FB_IAB|Instagram|Line\/|Snapchat|TikTok|musical_ly|BytedanceWebview/i.test(ua);
    var standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
    var mobile = isIOS || isAndroid;

    var bar = document.getElementById('pwaBar');
    var sheet = document.getElementById('pwaSheet');
    var nativeBtn = document.getElementById('pwaNative');
    if (!sheet) return;

    function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

    if (standalone) {
        store('pwa_installed', '1');
        return; // déjà ouverte comme application : rien à proposer
    }

    var deferred = window.__hmBip || null; // invite d'installation Android / Chrome (captée dès le début de la page)
    var isChrome = /Chrome\/\d+/.test(ua) && !/SamsungBrowser|OPR|Opera|EdgA|PHX|Phoenix|UCBrowser|MiuiBrowser|HeyTap|VivoBrowser|Firefox|YaBrowser|wv\)/.test(ua);
    function setNative(state) { // 'wait' (Chrome se prépare) ou 'ready'
        if (!nativeBtn) return;
        var lab = nativeBtn.querySelector('span');
        nativeBtn.classList.toggle('wait', state === 'wait');
        nativeBtn.disabled = state === 'wait';
        if (lab) lab.textContent = state === 'wait' ? (document.documentElement.lang === 'ar' ? 'جارٍ التحضير…' : document.documentElement.lang === 'en' ? 'Getting ready…' : 'Préparation…')
                                                    : (document.documentElement.lang === 'ar' ? 'ثبّت الآن' : document.documentElement.lang === 'en' ? 'Install now' : 'Installer maintenant');
    }
    function gotPrompt() {
        deferred = window.__hmBip || deferred;
        if (nativeBtn) { nativeBtn.hidden = !deferred; if (deferred) setNative('ready'); }
        showEntry();
    }
    document.addEventListener('hm-bip', gotPrompt);
    window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); window.__hmBip = e; gotPrompt(); });
    window.addEventListener('appinstalled', function () {
        store('pwa_installed', '1'); deferred = null;
        hideBar(); close();
        document.querySelectorAll('.pwa-menu-link').forEach(function (a) { a.hidden = true; });
    });

    function showEntry() {
        document.querySelectorAll('.pwa-menu-link').forEach(function (a) { a.hidden = false; });
    }
    if (mobile || deferred) showEntry();

    function open(ev) {
        if (ev) ev.preventDefault();
        if (typeof window.closeMobileMenu === 'function') { try { window.closeMobileMenu(); } catch (e) {} }
        var os = isIOS ? 'ios' : 'android';
        sheet.querySelectorAll('[data-pwa-os]').forEach(function (b) { b.hidden = b.getAttribute('data-pwa-os') !== os; });
        var ia = sheet.querySelector('[data-pwa-inapp]'); if (ia) ia.hidden = !(isIOS && inApp);
        if (nativeBtn) {
            if (deferred) { nativeBtn.hidden = false; setNative('ready'); }
            else if (isAndroid && isChrome) { nativeBtn.hidden = false; setNative('wait'); } // Chrome demande ~30 s sur la page
            else nativeBtn.hidden = true;
        }
        sheet.hidden = false;
        requestAnimationFrame(function () { sheet.classList.add('open'); });
        document.body.style.overflow = 'hidden';
    }
    function close() {
        sheet.classList.remove('open');
        document.body.style.overflow = '';
        setTimeout(function () { sheet.hidden = true; }, 250);
    }
    function hideBar() { if (bar) { bar.classList.remove('show'); setTimeout(function () { bar.hidden = true; }, 300); } }

    document.querySelectorAll('[data-pwa-open]').forEach(function (b) {
        b.addEventListener('click', function (ev) {
            if (deferred && !isIOS) { // Android : la vraie fenêtre d'installation directement
                ev.preventDefault();
                deferred.prompt();
                deferred.userChoice.then(function () { deferred = null; hideBar(); }).catch(function () {});
                return;
            }
            open(ev);
        });
    });
    sheet.querySelectorAll('[data-pwa-close]').forEach(function (b) { b.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !sheet.hidden) close(); });
    if (nativeBtn) nativeBtn.addEventListener('click', function () {
        if (!deferred) return;
        deferred.prompt();
        deferred.userChoice.then(function () { deferred = null; close(); hideBar(); }).catch(function () {});
    });

    // 2. Petite barre « Installer » : sur téléphone, à partir de la 2e visite, pas pendant un achat,
    //    et pas plus d'une fois tous les 14 jours si le client l'a fermée.
    var quiet = (document.currentScript && document.currentScript.getAttribute('data-quiet')) ||
        (document.querySelector('script[src*="pwa.js"]') || { getAttribute: function () { return '0'; } }).getAttribute('data-quiet');
    var visits = parseInt(store('pwa_visits') || '0', 10) + 1;
    store('pwa_visits', String(visits));
    var closedAt = parseInt(store('pwa_bar_closed') || '0', 10);
    var recentlyClosed = closedAt && (Date.now() - closedAt) < 14 * 864e5;
    if (bar && mobile && visits >= 2 && quiet !== '1' && !recentlyClosed && store('pwa_installed') !== '1') {
        setTimeout(function () {
            bar.hidden = false;
            requestAnimationFrame(function () { bar.classList.add('show'); });
        }, 2500);
    }
    var x = document.getElementById('pwaBarX');
    if (x) x.addEventListener('click', function () { store('pwa_bar_closed', String(Date.now())); hideBar(); });
})();
