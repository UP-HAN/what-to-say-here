let DB = null, COUNTRY = null;   // COUNTRY = {code,label,lang,hint}

const out = document.getElementById('out'), qEl = document.getElementById('q');
const savedView = document.getElementById('savedView');
let R = null, activeSit = null, saved = [];
let showLang = 'local';   // 'local'(현지어) | 'en'

/* ---------- 언어 헬퍼 ---------- */
function langMeta(code){ return (DB.languages && DB.languages[code]) || {label:(code||'').toUpperCase(), tts:'en-US'}; }
function sayLang(lang){ return langMeta(lang).tts || 'en-US'; }
// 현재 결과의 현지어: 명소는 이름으로 판별된 lang, 그 외는 고른 나라의 lang
function localLangFor(r){ return (r && r.kind === 'landmark') ? (r.data.lang || 'en') : (COUNTRY ? COUNTRY.lang : 'en'); }
function effLang(){ return showLang === 'en' ? 'en' : localLangFor(R); }
function hasLang(c, lang){ return !!(c.say && c.say[lang] && c.say[lang].t); }
function sayOf(c, lang){ return (c.say && c.say[lang]) || (c.say && c.say.en) || {t:'',s:''}; }
function replyOf(c, lang){ return (c.reply && c.reply[lang]) || (c.reply && c.reply.en) || []; }

/* ---------- 나라 선택 ---------- */
const countryEl = document.getElementById('country');
function loadCountry(){
  const code = localStorage.getItem('country');
  COUNTRY = DB.countries.find(c => c.code === code) || null;
  paintCountryBadge();
}
function paintCountryBadge(){
  const el = document.getElementById('countryBtn');
  el.textContent = (COUNTRY ? COUNTRY.label : '나라 선택') + ' ▾';
}
function openCountry(){
  document.getElementById('countryList').innerHTML = DB.countries.map(c =>
    `<button class="country${c.ready?'':' soon'}" data-code="${c.code}">
       <div class="cty-name">${c.label}${c.ready?'':'<span class="cty-soon">준비 중</span>'}</div>
       <div class="cty-hint">${c.hint}</div></button>`).join('');
  document.getElementById('countryNotice').textContent = '';
  countryEl.classList.add('on');   // 닫기 없음: 반드시 나라를 고르게 한다
}
document.getElementById('countryList').onclick = e => {
  const b = e.target.closest('.country'); if(!b) return;
  const c = DB.countries.find(x => x.code === b.dataset.code); if(!c) return;
  if(!c.ready){   // 아직 데이터가 없는 언어 → 안내만 띄우고 진행 안 함
    document.getElementById('countryNotice').textContent = c.label + '어는 준비 중이에요. 조금만 기다려 주세요.';
    return;
  }
  localStorage.setItem('country', c.code);
  loadCountry();
  showLang = 'local';
  document.getElementById('countryNotice').textContent = '';
  countryEl.classList.remove('on');
  if(R) render();
};
document.getElementById('countryBtn').onclick = () => openCountry();

/* ---------- 저장 ---------- */
// 다국어 이전에 저장된 옛 카드({en,ko,sound,reply}) → 신구조로 자동 승격
function upgradeSaved(c){
  if(c.say) return c;
  return {...c, intent: c.ko || c.intent || '',
    say: {en:{t: c.en||'', s: c.sound||''}},
    reply: {en: (c.reply||[]).map(r=>({t:r.en, s:r.sound, ko:r.ko}))},
    _lang: 'en'};
}
function loadSaved(){
  try{ saved = JSON.parse(localStorage.getItem('mycards') || '[]').map(upgradeSaved); }
  catch(e){ saved = []; }
  paintCount();
}
function persist(){ paintCount(); try{ localStorage.setItem('mycards', JSON.stringify(saved)); }catch(e){} }
function paintCount(){ document.getElementById('cnt').textContent = saved.length; }
function keyOf(c){ return (c.place||'')+'|'+(c.sit||'')+'|'+(c.intent||''); }

/* ---------- 검색 ---------- */
function norm(s){ return s.toLowerCase().replace(/\s+/g,''); }
function lookup(input){
  const n = norm(input);
  if(!n) return null;
  // 1) 명소 이름
  for(const [k,v] of Object.entries(DB.landmarks))
    if(v.keywords.some(w => n.includes(norm(w)))) return { kind:'landmark', key:k, data:v };
  // 2) 장소 종류 이름
  for(const [k,v] of Object.entries(DB.types))
    if(v.keywords.some(w => n.includes(norm(w)))) return { kind:'type', key:k, data:v };
  // 3) 공통 상황 (화장실·와이파이 등, 장소와 무관)
  if(DB.common_situations)
    for(const s of DB.common_situations)
      if((s.keywords||[]).some(w => n.includes(norm(w)))) return { kind:'commonsit', data:s };
  // 4) 종류 안의 상황 (키워드 또는 상황 이름으로)
  for(const [k,v] of Object.entries(DB.types))
    for(let i=0;i<v.situations.length;i++){
      const s = v.situations[i];
      if((s.keywords||[]).concat([s.label]).some(w => n.includes(norm(w))))
        return { kind:'type', key:k, data:v, sit:i };
    }
  return null;
}

document.getElementById('goBtn').onclick = search;
qEl.addEventListener('keydown', e => { if(e.key==='Enter') search(); });
function pick(k){ qEl.value = DB.types[k].label; search(); }

function search(){
  const r = lookup(qEl.value);
  if(!r){ noResult(); return; }
  R = r;
  activeSit = (r.kind === 'type') ? (r.sit != null ? r.sit : null) : 0;
  render();
}
// 다른 곳 찾아보기: 결과를 지우고 검색 화면으로 돌아간다
function resetSearch(){
  R = null; activeSit = null;
  out.innerHTML = '';
  qEl.value = '';
  window.scrollTo({ top: 0 });
  qEl.focus();
}
function noResult(){
  out.innerHTML = `<div class="nores">
    <b>그 이름은 아직 없어요</b>
    <p>대신 아래에서 비슷한 곳을 골라보세요. 가려는 곳이 어떤 종류인지만 고르면 됩니다.</p>
    <div class="all">${Object.entries(DB.types).map(([k,v])=>
      `<button class="sit" onclick="pick('${k}')">${v.label}</button>`).join('')}</div>
  </div>`;
}

/* ---------- 화면 ---------- */
function render(){
  const isLM = R.kind === 'landmark';
  const isCS = R.kind === 'commonsit';
  const flat = isLM || isCS;   // 상황 고르기 없이 바로 카드
  const label = R.data.label;
  out.innerHTML = `
    <div class="place">
      <div><div class="name">${label}</div>
      <div class="kind">${isLM ? '명소' : isCS ? '어디서나 쓰는 말' : '장소 종류'}</div></div>
      <div class="arrow">→</div>
    </div>
    ${flat ? '' : `<div class="qlabel">어떤 상황인가요?</div>
      <div class="sits" id="sits">${R.data.situations.map((s,i)=>
        `<button class="sit" data-i="${i}" aria-pressed="${activeSit===i}"><em>${s.emoji}</em>${s.label}</button>`).join('')}</div>`}
    <div id="cards"></div>`;
  if(!flat){
    document.getElementById('sits').onclick = e => {
      const b = e.target.closest('.sit'); if(!b) return;
      activeSit = +b.dataset.i; render();
    };
  }
  paintCards();
}

function currentCards(){
  if(!R) return [];
  if(R.kind === 'landmark'){
    const own = R.data.cards.map(c=>({...c, only:true}));
    return own.concat(DB.common['관광지'].cards);
  }
  if(R.kind === 'commonsit') return R.data.cards;
  if(activeSit === null) return [];
  return R.data.situations[activeSit].cards;
}
function stamp(c, lang){
  const sit = R.kind==='landmark' ? '명소'
            : R.kind==='commonsit' ? '어디서나'
            : R.data.situations[activeSit].label;
  return {...c, place:R.data.label, sit, _lang: lang};
}

/* 현지어 / ENGLISH 두 칸. 메뉴는 만들지 않는다. */
function setLang(m){ showLang = m; paintCards(); }
function langSwitch(){
  const local = localLangFor(R);
  if(local === 'en') return '';   // 이미 영어를 보여주는 중 → 공용어(ENGLISH) 전환 버튼 불필요
  const localLabel = langMeta(local).label;
  const isLocal = showLang !== 'en';
  return `<div class="langsw" role="group" aria-label="언어 고르기">
    <button class="lang ${isLocal?'on':''}" aria-pressed="${isLocal}" onclick="setLang('local')">
      현지어<span class="lang-sub">${localLabel}</span></button>
    <button class="lang ${!isLocal?'on':''}" aria-pressed="${!isLocal}" onclick="setLang('en')">ENGLISH</button>
  </div>`;
}

function paintCards(){
  const box = document.getElementById('cards'); if(!box) return;
  const list = currentCards();
  if(!list.length){ box.innerHTML = ''; return; }
  const lang = effLang();
  const stamped = list.map(c=>stamp(c,lang));
  const allIn = stamped.every(c => saved.some(s => keyOf(s)===keyOf(c)));
  box.innerHTML = langSwitch() + `
    <button class="bulk ${allIn?'done':''}" onclick="saveAll()">
      ${allIn ? '✓ 여기 카드는 모두 담았어요' : '⭐ 이 카드 전부 담아두기'}</button>
    ${list.map((c,i)=>cardHtml(c,i,lang,saved.some(s=>keyOf(s)===keyOf(stamped[i])))).join('')}
    <button class="again" onclick="resetSearch()">다른 곳 찾아보기</button>`;
}

function esc(s){ return (s||'').replace(/'/g,"\\'").replace(/"/g,'&quot;'); }

function cardHtml(c, idx, lang, on){
  const s = sayOf(c, lang), tts = sayLang(lang);
  const fb = (lang !== 'en' && !hasLang(c, lang));   // 현지어 없어서 영어로 폴백
  return `<div class="card">
    ${c.only ? '<span class="tag only">여기서만 쓰는 말</span>'
             : (idx===0 ? '<span class="tag">가장 많이 써요</span>' : '')}
    ${fb ? '<span class="tag fb">영어로 보여드려요</span>' : ''}
    <div class="intent">${c.intent}</div>
    <div class="mine en">${s.t}</div>
    <div class="sound">${s.s}</div>
    ${c.note ? `<div class="note">${c.note}</div>` : ''}
    ${c.volatile ? `<div class="vol">⚠️ 규정이 바뀔 수 있어요. 현장에서 다시 확인하세요.</div>` : ''}
    ${replyHtml(c, lang)}
    <div class="acts">
      <button class="act primary" onclick="showBig('${esc(s.t)}','${tts}')">📱 보여주기</button>
      <button class="act" onclick="say('${esc(s.t)}','${tts}')">🔊 듣기</button>
      <button class="act" onclick="say('${esc(s.t)}','${tts}',0.6)">🐢 천천히</button>
    </div>
    <div class="acts">
      <button class="act ${on?'saved':''}" style="flex:1;justify-content:center"
        onclick="toggleSave(${idx})">${on?'✓ 담았어요':'⭐ 담아두기'}</button>
    </div>
  </div>`;
}
function replyHtml(c, lang){
  const rs = replyOf(c, lang);
  if(!rs.length) return '';
  const tts = sayLang(lang);
  return `<div class="reply"><div class="replyhead">상대방이 이렇게 말할 수 있어요</div>
    ${rs.map(r=>`<div class="rline"><span class="rtag">상대</span><div>
      <div class="ren">${r.t}</div><div class="rsound">${r.s}</div><div class="rko">${r.ko}</div>
      <button class="act" style="margin-top:8px;padding:6px 11px;font-size:12px"
        onclick="say('${esc(r.t)}','${tts}')">🔊 듣기</button></div></div>`).join('')}</div>`;
}

function toggleSave(i){
  const c = stamp(currentCards()[i], effLang());
  const at = saved.findIndex(s => keyOf(s)===keyOf(c));
  if(at>=0) saved.splice(at,1); else saved.push(c);
  persist(); paintCards();
}
function saveAll(){
  const lang = effLang();
  currentCards().map(c=>stamp(c,lang)).forEach(c=>{
    if(!saved.some(s=>keyOf(s)===keyOf(c))) saved.push(c);
  });
  persist(); paintCards();
}
function removeSaved(k){ saved = saved.filter(s=>keyOf(s)!==k); persist(); renderSaved(); }

/* ---------- 내 카드 ---------- */
document.getElementById('tabFind').onclick = ()=>switchTab('find');
document.getElementById('tabSaved').onclick = ()=>switchTab('saved');
function switchTab(t){
  const f = t==='find';
  document.getElementById('tabFind').setAttribute('aria-selected', f);
  document.getElementById('tabSaved').setAttribute('aria-selected', !f);
  document.getElementById('findView').style.display = f?'':'none';
  savedView.style.display = f?'none':'';
  if(!f) renderSaved();
}
function renderSaved(){
  if(!saved.length){
    savedView.innerHTML = `<div class="empty"><b>아직 담아둔 카드가 없어요</b>
      <p>여행 가기 전에 미리 담아두세요.<br>담아둔 카드는 인터넷이 없어도 열립니다.</p></div>`;
    return;
  }
  const g = {};
  saved.forEach(c => { const k = c.place+'§'+c.sit; (g[k] = g[k]||[]).push(c); });
  savedView.innerHTML = Object.entries(g).map(([k,list])=>{
    const [pl,st] = k.split('§');
    return `<div class="group">
      <div class="grouphead"><div class="g1">${pl}</div><div class="g2">${st} · ${list.length}장</div></div>
      ${list.map(c=>{
        const lang = c._lang || 'en', s = sayOf(c,lang), tts = sayLang(lang);
        return `<div class="card">
        <div class="intent">${c.intent}</div>
        <div class="mine en">${s.t}</div><div class="sound">${s.s}</div>${replyHtml(c,lang)}
        <div class="acts">
          <button class="act primary" onclick="showBig('${esc(s.t)}','${tts}')">📱 보여주기</button>
          <button class="act" onclick="say('${esc(s.t)}','${tts}')">🔊 듣기</button>
          <button class="act" onclick="say('${esc(s.t)}','${tts}',0.6)">🐢 천천히</button>
        </div>
        <div class="acts"><button class="act" style="flex:1;justify-content:center;color:var(--muted)"
          onclick="removeSaved('${esc(keyOf(c))}')">빼기</button></div>
      </div>`;}).join('')}</div>`;
  }).join('');
}

/* ---------- 소리 · 보여주기 ---------- */
function say(text, tts, rate){
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = tts || 'en-US'; u.rate = rate || 0.92;
  speechSynthesis.speak(u);
}
const showEl = document.getElementById('show');
let wake = null;
async function showBig(text, tts){
  document.getElementById('showText').textContent = text;
  document.getElementById('showSpeak').onclick = ()=>say(text, tts);
  showEl.classList.add('on');
  try{ wake = await navigator.wakeLock.request('screen'); }catch(e){}
}
document.getElementById('closeShow').onclick = closeShow;
function closeShow(){ showEl.classList.remove('on'); try{ wake && wake.release(); wake=null; }catch(e){} }
document.addEventListener('keydown', e => { if(e.key==='Escape') closeShow(); });

async function boot(){
  DB = await (await fetch('data/cards.json')).json();
  loadSaved();
  loadCountry();
  openCountry();   // 시작할 때 늘 언어(나라)를 먼저 고르게 한다
  if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(()=>{});
}
boot();
