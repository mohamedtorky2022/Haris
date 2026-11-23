// Haris service worker: lets the chat be installed as an app and open without a connection.
// Network first for everything, so a new deploy shows at once; the cached copy is only a fallback.
// Nothing from /api or /webhook is ever cached: messages and reports are never stored on the phone.
const CACHE = "haris-shell-v2";
const SHELL = ["/", "/index.html", "/styles.css", "/app.js", "/pwa.js", "/splash.js", "/haris.svg", "/manifest.json", "/icons/icon-192.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/webhook/")) return;
  // The authority pages, the takedown evidence page and the training demo stay online only.
  if (/^\/(reports|authority|evidence|demo)/.test(url.pathname)) return;

  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(req, { ignoreSearch: true }).then((hit) => hit || (req.mode === "navigate" ? caches.match("/") : undefined))
          .then((hit) => hit || new Response("", { status: 503 }))
      )
  );
});
