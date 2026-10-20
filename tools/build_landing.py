# -*- coding: utf-8 -*-
"""
랜딩 페이지 생성기 (2026-08-01)

design/landing.html(가로 1920x1080)과 design/landing-mobile.html(세로 1080x1920)의
아트보드를 하나의 index.html로 합친다.
- PC(가로 방향) → 가로 아트보드, 모바일(세로 방향) → 세로 아트보드 (CSS orientation 분기)
- 각 아트보드의 "시작하기" 버튼 위에 app.html로 가는 투명 링크를 얹는다
- 무거운 base64 이미지는 스크립트가 그대로 복사하므로 손으로 만질 필요 없다

실행:  python tools/build_landing.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DES = os.path.join(ROOT, "design")

# 앱 버전. 큰 업데이트마다 0.1씩 올린다 (예: 1.0 → 1.1 → 1.2 …). 제작자: hanuipyo
APP_VERSION = "1.0"
MAKER = "hanuipyo"
YEAR = "2026"

# (파일, wrap id, 시작하기 버튼 링크 좌표, 버튼 아래 안내문 좌표)  ─ 아트보드 스테이지 기준(px)
SRCS = [
    ("landing.html",        "land-landscape", dict(left=520, top=866,  w=412, h=124), dict(top=1006, w=1920, fs=28)),
    ("landing-mobile.html", "land-portrait",  dict(left=606, top=1640, w=396, h=132), dict(top=1802, w=1080, fs=32)),
]


def extract(path, wid, btn, note):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    # <div class="stage-wrap"> ... </div></div>  (스크립트 직전까지)
    s = t.index('<div class="stage-wrap">')
    e = t.index('<script>', s)
    block = t[s:e].rstrip()
    # wrap에 id 부여
    block = block.replace('<div class="stage-wrap">',
                          f'<div class="stage-wrap" id="{wid}">', 1)
    # 스테이지 여는 태그 바로 뒤에 시작하기 링크 삽입 (스테이지 좌표계 안)
    so = block.index('<div class="stage"')
    gt = block.index('>', so) + 1
    link = (f'<a href="app.html" class="startbtn" aria-label="시작하기" '
            f'style="position:absolute;left:{btn["left"]}px;top:{btn["top"]}px;'
            f'width:{btn["w"]}px;height:{btn["h"]}px;z-index:20;"></a>')
    # 시작하기 버튼 아래 안내문 (홈 화면에 추가 = 오프라인)
    hint = (f'<div style="position:absolute;left:0;top:{note["top"]}px;width:{note["w"]}px;'
            f"text-align:center;font-family:'Gothic A1',sans-serif;font-weight:700;"
            f'font-size:{note["fs"]}px;letter-spacing:-0.02em;color:#131A24;z-index:20;">'
            f'오른쪽 위 <span style="background:#FFD84D;border:3px solid #131A24;'
            f'padding:2px 12px;font-weight:800;white-space:nowrap;">홈 화면에 추가</span>'
            f'를 누르면 인터넷이 없어도 쓸 수 있어요</div>')
    return block[:gt] + link + hint + block[gt:]


blocks = [extract(os.path.join(DES, fn), wid, btn, note) for fn, wid, btn, note in SRCS]

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>여기서 뭐라고 해요?</title>
<meta name="theme-color" content="#131A24" />
<link rel="manifest" href="manifest.json" />
<link rel="apple-touch-icon" href="icons/icon-192.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Gothic+A1:wght@700;800;900&family=Noto+Sans+JP:wght@700;900&display=swap" rel="stylesheet" />
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #EFF1EC; }
  .stage-wrap { position: relative; width: 100%; overflow: hidden; }
  .stage { transform-origin: top left; position: absolute; top: 0; left: 0; }
  .startbtn { display: block; cursor: pointer; }
  .startbtn:focus-visible { outline: 4px solid #2F6BFF; outline-offset: 3px; }
  /* PC=가로 아트보드만. 모바일(세로 방향)=세로 아트보드만 */
  #land-portrait { display: none; }
  @media (orientation: portrait) {
    #land-landscape { display: none; }
    #land-portrait { display: block; }
  }
  /* 홈 화면에 추가 버튼 (기본 숨김, JS가 조건 되면 보여줌) */
  .install-btn { position: fixed; top: 16px; right: 16px; z-index: 40; display: none;
    background: #FFD84D; border: 3px solid #131A24; box-shadow: 4px 4px 0 #131A24;
    padding: 11px 15px; font: 800 15px 'Gothic A1', sans-serif; color: #131A24; cursor: pointer; }
  .install-btn:active { transform: translate(2px, 2px); box-shadow: none; }
  #iosGuide { position: fixed; inset: 0; z-index: 50; display: none;
    background: rgba(19,26,36,.72); align-items: center; justify-content: center; padding: 24px; }
  #iosGuide.on { display: flex; }
  .guide-card { position: relative; background: #fff; border: 4px solid #131A24;
    box-shadow: 8px 8px 0 #131A24; max-width: 360px; width: 100%; padding: 26px 22px 22px;
    font-family: 'Gothic A1', sans-serif; color: #131A24; }
  .guide-card h3 { margin: 0 0 6px; font-size: 22px; font-weight: 900; letter-spacing: -.02em; }
  .guide-card > p { margin: 0 0 18px; font-size: 14px; font-weight: 600; color: #555; line-height: 1.5; }
  .guide-x { position: absolute; top: 10px; right: 10px; width: 40px; height: 40px;
    background: #fff; border: 3px solid #131A24; font-size: 20px; font-weight: 800;
    color: #131A24; cursor: pointer; }
  .guide-step { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 14px;
    font-size: 15px; font-weight: 700; line-height: 1.45; }
  .guide-step:last-child { margin-bottom: 0; }
  .guide-num { flex: 0 0 auto; width: 28px; height: 28px; background: #131A24; color: #fff;
    font-weight: 900; display: flex; align-items: center; justify-content: center; font-size: 15px; }
  /* 우측 하단 저작권 · 제작자 · 버전 */
  .credit { position: fixed; right: 14px; bottom: 12px; z-index: 40;
    font: 700 12px 'Gothic A1', sans-serif; color: #131A24; letter-spacing: -.01em;
    background: rgba(239,241,236,.85); border: 2px solid #131A24; padding: 5px 10px; }
  .credit b { font-weight: 800; }
</style>
</head>
<body>
<button id="installBtn" class="install-btn">📲 홈 화면에 추가</button>
<div class="credit">© __YEAR__ <b>__MAKER__</b> · v__VERSION__</div>
<div id="iosGuide">
  <div class="guide-card">
    <button class="guide-x" id="guideClose" aria-label="닫기">✕</button>
    <h3>홈 화면에 추가</h3>
    <p>이렇게 해두면 앱처럼 열리고, 인터넷이 없어도 열려요. 여행 가기 전에 미리 해두세요.</p>
    <div id="guideSteps"></div>
  </div>
</div>
__LANDSCAPE__

__PORTRAIT__
<script>
  // 화면 폭·높이 둘 다에 맞춰(contain) 축소하고 가운데 배치 → 아래가 안 잘린다
  function fit() {
    var vw = document.documentElement.clientWidth;
    var vh = window.innerHeight;
    var wraps = document.querySelectorAll('.stage-wrap');
    for (var i = 0; i < wraps.length; i++) {
      var wrap = wraps[i];
      if (!wrap.offsetParent) continue;            // 숨겨진 쪽은 건너뛴다
      var st = wrap.querySelector('.stage');
      var base = parseInt(st.style.width, 10) || 1920;
      var high = parseInt(st.style.height, 10) || 1080;
      var s = Math.min(1, vw / base, vh / high);   // 폭·높이 중 더 빡빡한 쪽
      var tx = Math.max(0, (vw - base * s) / 2);
      var ty = Math.max(0, (vh - high * s) / 2);
      st.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')';
      wrap.style.height = vh + 'px';
    }
  }
  addEventListener('resize', fit);
  addEventListener('orientationchange', fit);
  fit();

  // 랜딩에서 서비스워커를 등록해 앱 파일을 미리 폰에 저장한다(=미리 받아두기)
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(function(){});

  // 홈 화면에 추가 버튼
  (function () {
    var btn = document.getElementById('installBtn');
    var guide = document.getElementById('iosGuide');
    var deferred = null;
    function standalone() {
      return matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
    }
    function ios() { return /iphone|ipad|ipod/i.test(navigator.userAgent); }

    // 설치 안 된 상태면 항상 버튼을 보여준다 (안드로이드·아이폰·데스크톱 공통)
    if (!standalone()) btn.style.display = 'block';
    // 안드로이드/크롬: 설치 가능 신호를 붙잡아 둔다 (누르면 네이티브 설치창)
    addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); deferred = e; });
    addEventListener('appinstalled', function () { btn.style.display = 'none'; deferred = null; });

    function openGuide() {
      var steps = ios()
        ? [['1', '맨 아래 <b>공유</b> 버튼(네모+↑)을 누르세요'],
           ['2', '<b>“홈 화면에 추가”</b>를 누르세요'],
           ['3', '오른쪽 위 <b>추가</b>를 누르면 끝이에요']]
        : [['1', '브라우저 메뉴(⋮)를 여세요'],
           ['2', '<b>“홈 화면에 추가”</b> 또는 “앱 설치”를 누르세요']];
      document.getElementById('guideSteps').innerHTML = steps.map(function (s) {
        return '<div class="guide-step"><span class="guide-num">' + s[0] + '</span><span>' + s[1] + '</span></div>';
      }).join('');
      guide.classList.add('on');
    }
    btn.onclick = function () {
      if (deferred) {
        deferred.prompt();
        deferred.userChoice.then(function () { deferred = null; btn.style.display = 'none'; });
      } else { openGuide(); }
    };
    document.getElementById('guideClose').onclick = function () { guide.classList.remove('on'); };
    guide.onclick = function (e) { if (e.target === guide) guide.classList.remove('on'); };
  })();
</script>
</body>
</html>
"""

out = (HTML.replace("__LANDSCAPE__", blocks[0])
           .replace("__PORTRAIT__", blocks[1])
           .replace("__YEAR__", YEAR)
           .replace("__MAKER__", MAKER)
           .replace("__VERSION__", APP_VERSION))

dst = os.path.join(ROOT, "index.html")
with open(dst, "w", encoding="utf-8") as f:
    f.write(out)

print("생성:", os.path.relpath(dst, ROOT), f"({len(out.encode('utf-8'))} bytes)")
print("가로 블록:", len(blocks[0]), "chars / 세로 블록:", len(blocks[1]), "chars")
