/* HDATTAHER MOBILE — stories (comme les statuts WhatsApp) */
(function () {
    var row = document.getElementById('stoRow'), view = document.getElementById('stoView');
    var dataEl = document.getElementById('stoData');
    if (!row || !view || !dataEl) return;
    var S = [];
    try { S = JSON.parse(dataEl.textContent) || []; } catch (e) { return; }
    if (!S.length) return;

    var stage = document.getElementById('stoStage'), bars = document.getElementById('stoBars');
    var txt = document.getElementById('stoTxt'), cta = document.getElementById('stoCta'), ago = document.getElementById('stoAgo');
    var IMG_MS = 5500, MAX_VIDEO_MS = 30000;
    var cur = -1, timer = null, startAt = 0, elapsed = 0, paused = false, raf = null, dur = IMG_MS, media = null;

    function lang() { return document.documentElement.lang || 'fr'; }
    function T(fr, en, ar) { var l = lang(); return l === 'ar' ? ar : l === 'en' ? en : fr; }
    function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || '[]'); localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return []; } }
    function money(v) { return Math.round(+v || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' FCFA'; }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function since(iso) {
        var d = new Date(String(iso).replace(' ', 'T').replace(/(\.\d+)?(\+00:00|Z)?$/, 'Z'));
        var h = Math.floor((Date.now() - d.getTime()) / 3600000);
        if (!isFinite(h)) return '';
        if (h < 1) return T('à l\'instant', 'just now', 'الآن');
        if (h < 24) return T('il y a ' + h + ' h', h + ' h ago', 'منذ ' + h + ' س');
        var j = Math.floor(h / 24);
        return T('il y a ' + j + ' j', j + ' d ago', 'منذ ' + j + ' ي');
    }

    // Déjà vues : anneau gris, placées à la fin (comme Instagram)
    var seen = store('hm_seen_stories');
    function markSeen(id) {
        if (seen.indexOf(id) < 0) {
            seen.push(id); if (seen.length > 200) seen = seen.slice(-200); store('hm_seen_stories', seen);
            var counted = store('hm_story_views');
            if (counted.indexOf(id) < 0) {   // +1 vue, une seule fois par téléphone
                counted.push(id); store('hm_story_views', counted.slice(-300));
                fetch(view.dataset.viewUrl.replace('__ID__', id), { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': view.dataset.csrf } }).catch(function () {});
            }
        }
        var b = row.querySelector('[data-id="' + id + '"]'); if (b) b.classList.add('seen');
    }
    var items = Array.prototype.slice.call(row.querySelectorAll('.sto-item'));
    items.forEach(function (b) { if (seen.indexOf(b.dataset.id) >= 0) b.classList.add('seen'); });
    items.filter(function (b) { return b.classList.contains('seen'); }).forEach(function (b) { row.appendChild(b); });

    bars.innerHTML = S.map(function () { return '<span><i></i></span>'; }).join('');
    var barEls = bars.querySelectorAll('i');

    function setBars(i, frac) {
        for (var k = 0; k < barEls.length; k++) barEls[k].style.width = (k < i ? 100 : k > i ? 0 : Math.min(100, frac * 100)) + '%';
    }
    function tick() {
        if (cur < 0) return;
        var now = performance.now();
        var e = paused ? elapsed : elapsed + (now - startAt);
        if (media && media.tagName === 'VIDEO' && media.duration && isFinite(media.duration)) {
            dur = Math.min(MAX_VIDEO_MS, media.duration * 1000);
            e = Math.min(e, media.currentTime * 1000 + 1);
        }
        setBars(cur, e / dur);
        if (!paused && e >= dur) { next(); return; }
        raf = requestAnimationFrame(tick);
    }
    function show(i) {
        if (i < 0) i = 0;
        if (i >= S.length) { close(); return; }
        cur = i; elapsed = 0; startAt = performance.now(); paused = false; dur = IMG_MS;
        var s = S[i], p = s.product;
        stage.innerHTML = '';
        stage.classList.toggle('vid', s.type === 'video');
        var bg = document.createElement('div'); bg.className = 'sto-bg';
        if (s.type === 'video') {
            media = document.createElement('video');
            media.src = s.media; media.playsInline = true; media.setAttribute('playsinline', ''); media.muted = false; media.autoplay = true;
            media.className = 'sto-media';
            media.addEventListener('waiting', function () { if (!paused) { elapsed += performance.now() - startAt; paused = 'load'; } });
            media.addEventListener('playing', function () { if (paused === 'load') { paused = false; startAt = performance.now(); } });
            media.addEventListener('error', function () { media = null; });
            var pl = media.play();
            if (pl && pl.catch) pl.catch(function () { media.muted = true; media.play().catch(function () {}); });
            if (p && p.image) bg.style.backgroundImage = 'url("' + p.image + '")';
        } else {
            media = document.createElement('div'); media.className = 'sto-media sto-photo boxed';
            media.style.backgroundImage = 'url("' + s.media + '")';
            bg.style.backgroundImage = 'url("' + s.media + '")';
        }
        stage.appendChild(bg); stage.appendChild(media);
        var shade = document.createElement('div'); shade.className = 'sto-shade'; stage.appendChild(shade);
        var html = '';
        if (s.tag) {
            var cls = /PROMO/.test(s.tag) ? 'red' : /OCCASION/.test(s.tag) ? 'blue' : '';
            html += '<span class="sto-tag ' + cls + '">' + esc(s.tag) + '</span>';
        }
        if (s.title) html += '<h2>' + esc(s.title) + '</h2>';
        if (p) {
            var old = +p.old_price || 0, pr = +p.price || 0;
            if (p.name && p.name !== s.title) html += '<p>' + esc(p.name) + '</p>';
            html += '<div class="sto-price"><b>' + money(pr) + '</b>' + (old > pr ? '<s>' + money(old) + '</s>' : '') + '</div>';
            if ((+p.stock || 0) <= 0) html += '<p class="sto-out">' + T('Épuisé pour le moment', 'Out of stock for now', 'نفد حاليًا') + '</p>';
        }
        txt.innerHTML = html;
        txt.classList.remove('in'); void txt.offsetWidth; txt.classList.add('in');
        if (p && p.id) {
            cta.hidden = false;
            cta.href = view.dataset.productUrl.replace('__ID__', p.id);
            cta.querySelector('span').textContent = (+p.stock || 0) > 0 ? T('Voir le produit', 'See the product', 'عرض المنتج') : T('Voir / être prévenu', 'See / get notified', 'عرض / أعلمني');
        } else cta.hidden = true;
        ago.textContent = since(s.created);
        markSeen(s.id);
        // précharger la suivante
        var n = S[i + 1]; if (n && n.type !== 'video') { var im = new Image(); im.src = n.media; }
        cancelAnimationFrame(raf); raf = requestAnimationFrame(tick);
    }
    function next() { show(cur + 1); }
    function prev() { show(cur > 0 ? cur - 1 : 0); }
    function pause(on) {
        if (cur < 0) return;
        if (on && !paused) { elapsed += performance.now() - startAt; paused = true; if (media && media.pause) media.pause(); }
        else if (!on && paused) { paused = false; startAt = performance.now(); if (media && media.play) media.play().catch(function () {}); }
    }
    function open(i) {
        view.hidden = false;
        document.documentElement.classList.add('sto-lock');
        requestAnimationFrame(function () { view.classList.add('open'); });
        try { history.pushState({ sto: 1 }, ''); } catch (e) {}
        show(i);
    }
    function close(fromPop) {
        if (cur < 0) return;
        cancelAnimationFrame(raf); cur = -1;
        if (media && media.pause) media.pause();
        stage.innerHTML = ''; media = null;
        view.classList.remove('open', 'drag');
        view.style.transform = '';
        document.documentElement.classList.remove('sto-lock');
        setTimeout(function () { view.hidden = true; }, 220);
        if (!fromPop) { try { if (history.state && history.state.sto) history.back(); } catch (e) {} }
    }
    window.addEventListener('popstate', function () { if (cur >= 0) close(true); });

    row.addEventListener('click', function (e) {
        var b = e.target.closest('.sto-item'); if (!b) return;
        open(+b.dataset.i);
    });
    document.getElementById('stoClose').addEventListener('click', function () { close(); });
    document.addEventListener('keydown', function (e) {
        if (cur < 0) return;
        if (e.key === 'Escape') close(); else if (e.key === 'ArrowRight') next(); else if (e.key === 'ArrowLeft') prev();
    });

    // Toucher à gauche / à droite, appui long = pause, glisser vers le bas = fermer
    var downAt = 0, sx = 0, sy = 0, dy = 0, longPress = false, holdT = null, side = null;
    function navDown(e, which) {
        side = which; downAt = Date.now(); longPress = false;
        var pt = e.touches ? e.touches[0] : e; sx = pt.clientX; sy = pt.clientY; dy = 0;
        clearTimeout(holdT); holdT = setTimeout(function () { longPress = true; pause(true); }, 260);
    }
    function navMove(e) {
        if (!side) return;
        var pt = e.touches ? e.touches[0] : e;
        dy = pt.clientY - sy;
        if (Math.abs(dy) > 12 && Math.abs(dy) > Math.abs(pt.clientX - sx)) {
            clearTimeout(holdT); pause(true);
            if (dy > 0) { view.classList.add('drag'); view.style.transform = 'translateY(' + dy + 'px) scale(' + (1 - Math.min(dy, 400) / 2000) + ')'; }
            if (e.cancelable) e.preventDefault();
        }
    }
    function navUp(e) {
        if (!side) return;
        clearTimeout(holdT);
        var which = side; side = null;
        view.classList.remove('drag');
        if (dy > 110) { close(); return; }
        view.style.transform = '';
        if (longPress || Math.abs(dy) > 12) { pause(false); return; }
        if (which === 'next') next(); else prev();
    }
    [['stoPrev', 'prev'], ['stoNext', 'next']].forEach(function (x) {
        var el = document.getElementById(x[0]);
        el.addEventListener('touchstart', function (e) { navDown(e, x[1]); }, { passive: true });
        el.addEventListener('touchmove', navMove, { passive: false });
        el.addEventListener('touchend', function (e) { e.preventDefault(); navUp(e); });
        el.addEventListener('mousedown', function (e) { navDown(e, x[1]); });
    });
    window.addEventListener('mousemove', navMove);
    window.addEventListener('mouseup', navUp);
    document.addEventListener('visibilitychange', function () { if (cur >= 0) pause(document.hidden); });
})();
