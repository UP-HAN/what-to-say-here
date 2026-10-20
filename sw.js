// 오프라인 동작의 핵심. 여기 목록에 있는 파일은 폰에 저장돼 인터넷 없이 열린다.
const CACHE = 'phrase-v19';
const FILES = [
  './', './index.html', './app.html', './css/style.css', './js/app.js',
  './data/cards.json', './manifest.json',
  './icons/icon-192.png', './icons/icon-512.png'
];

// 글꼴은 구글 서버에서 받아온다. 위 목록에 넣으면 안 된다 —
// 하나라도 실패하면 install 전체가 무너져 앱이 통째로 오프라인이 안 된다.
// 대신 인터넷이 있을 때 지나가는 걸 붙잡아 따로 저장해둔다. 다음부터는 비행기 안에서도 글꼴이 산다.
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];
const FONT_CACHE = CACHE + '-font';

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  const keep = [CACHE, FONT_CACHE];   // 글꼴 캐시도 함께 살려둔다
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => !keep.includes(k)).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

// 캐시 우선. 없으면 네트워크. 카드 데이터를 바꾸면 CACHE 이름의 숫자를 올릴 것.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const isFont = FONT_HOSTS.includes(new URL(e.request.url).hostname);
  e.respondWith(
    caches.match(e.request).then(hit => {
      if (hit) return hit;
      return fetch(e.request).then(res => {
        if (isFont) {
          const copy = res.clone();
          caches.open(FONT_CACHE).then(c => c.put(e.request, copy));
        }
        return res;
      }).catch(() => hit);
    })
  );
});
