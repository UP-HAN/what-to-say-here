# 여기서 뭐라고 해요?

장소를 검색하면 그곳에서 쓸 영어 문장을 꺼내주는 왕초보용 웹앱.

## 실행

```bash
python3 -m http.server 8000
```

브라우저에서 http://localhost:8000 열기.

`index.html`을 더블클릭해서 여는 건 안 됩니다. `data/cards.json`을 못 읽어요.

## 구조

| 경로 | 무엇 |
|---|---|
| `index.html` | 화면 뼈대 |
| `css/style.css` | 스타일 |
| `js/app.js` | 전체 로직 |
| `data/cards.json` | **문장 데이터. 제품의 핵심** |
| `sw.js` | 오프라인 캐시 |
| `docs/` | 기획서·현황 |
| `CLAUDE.md` | Claude Code 지침 |

## 카드를 고쳤다면

`data/cards.json`을 수정한 뒤 `sw.js`의 `CACHE` 값을 올리세요.
안 그러면 사용자 폰에 옛날 데이터가 남습니다.

```js
const CACHE = 'phrase-v1';  →  'phrase-v2'
```
