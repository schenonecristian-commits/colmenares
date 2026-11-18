/* Guarda la app en el teléfono para que abra sin señal */
var VERSION = "colmenares-v3";
var ARCHIVOS = ["./", "index.html", "esquema.js", "manifest.webmanifest", "icono-180.png", "icono-192.png", "icono-512.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(ARCHIVOS); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k != VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var req = e.request, url = new URL(req.url);
  if (req.method != "GET") return;
  if (url.hostname.indexOf("script.google") >= 0 || url.hostname.indexOf("googleusercontent") >= 0) return; // datos: siempre a la planilla
  var mismo = url.origin == location.origin, fuente = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!mismo && !fuente) return;
  // Primero lo guardado (abre al instante y sin señal); de fondo baja la versión nueva para la próxima vez
  e.respondWith(caches.open(VERSION).then(function (c) {
    return c.match(req, { ignoreSearch: mismo }).then(function (guardado) {
      var red = fetch(req).then(function (r) { if (r && (r.ok || r.type == "opaque")) c.put(req, r.clone()); return r; }).catch(function () { return guardado; });
      return guardado || red;
    });
  }));
});
