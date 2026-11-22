/* HDATTAHER MOBILE — service worker (application installable)
   - Les pages viennent toujours d'internet (prix, stock et panier toujours à jour).
   - Sans internet : on affiche la page « Pas de connexion ».
   - Les fichiers du site (styles, scripts, logo) sont gardés pour ouvrir l'application plus vite. */
var VERSION = 'hm-__VERSION__';
var STATIC_CACHE = VERSION + '-static';
var OFFLINE_URL = '/hors-ligne';
var PRECACHE = [OFFLINE_URL, '/static/img/logo-hm.png', '/static/pwa/icon-192.png'];
var MAX_STATIC = 120;

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(function (cache) { return cache.addAll(PRECACHE); })
            .then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.filter(function (k) { return k.indexOf(VERSION) !== 0; })
                .map(function (k) { return caches.delete(k); }));
        }).then(function () { return self.clients.claim(); })
    );
});

function trim(cache) {
    cache.keys().then(function (keys) {
        if (keys.length > MAX_STATIC) cache.delete(keys[0]).then(function () { trim(cache); });
    });
}

self.addEventListener('fetch', function (event) {
    var req = event.request;
    if (req.method !== 'GET') return;
    var url = new URL(req.url);
    if (url.origin !== self.location.origin) return;

    // Pages : toujours depuis internet ; sinon page « Pas de connexion »
    if (req.mode === 'navigate') {
        event.respondWith(
            fetch(req).catch(function () {
                return caches.match(OFFLINE_URL).then(function (r) {
                    return r || new Response('Pas de connexion internet.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
                });
            })
        );
        return;
    }

    // Fichiers du site (/static/) : réponse immédiate depuis le téléphone, mise à jour en arrière-plan
    if (url.pathname.indexOf('/static/') === 0 && url.pathname.indexOf('/static/uploads/') !== 0) {
        event.respondWith(
            caches.open(STATIC_CACHE).then(function (cache) {
                return cache.match(req).then(function (cached) {
                    var network = fetch(req).then(function (res) {
                        if (res && res.ok && res.type === 'basic') { cache.put(req, res.clone()); trim(cache); }
                        return res;
                    }).catch(function () { return cached; });
                    return cached || network;
                });
            })
        );
    }
});
