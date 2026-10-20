# -*- coding: utf-8 -*-
"""
감수를 통과한 _stage_*.json 을 data/cards.json 에 병합한다.

원칙
  - 통과한 파일만 STAGE_APPROVED 에 적는다. 미통과 파일은 넣지 않는다.
  - 기존 220장은 건드리지 않는다. 추가와 keywords 주입만 한다.
  - 병합 전에 백업을 뜨고, 병합 후 구조를 검증한다.
  - 검증에 실패하면 아무것도 쓰지 않는다.

사용
  python merge_stage.py --dry-run    # 무엇이 들어가는지만 출력
  python merge_stage.py              # 실제 병합
"""
import json, os, sys, shutil, argparse
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CARDS = None  # --cards 로 지정

# ── 감수 통과한 것만 여기에 ──────────────────────────────
STAGE_APPROVED = [
    "_stage_types_e.json",      # 바·우체국  (4라운드 통과)
    "_stage_types_c.json",      # 박물관·안내소  (7라운드 통과)
    # "_stage_types_a.json",    # 병원·은행
    # "_stage_types_b.json",    # 옷가게·미용실
    # "_stage_types_d.json",    # 렌터카·주유소
    # "_stage_common.json",     # 공통 상황
]
KEYWORDS_FILE = "_stage_keywords.json"   # 기존 48개 상황에 주입

# ── 문장 통일 (같은 영어가 파일마다 다르게 적힌 것) ──────
# 병합 후 전체에 적용. 값은 "이걸로 통일한다".
SOUND_CANON = {
    # "영어 원문(소문자)": "통일할 한글 소리 표기"
}
# 같은 의도를 다른 영어로 쓰던 것
TEXT_CANON = {
    # "옛 영어": "새 영어"
}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def iter_cards(db):
    """(카드, 어디에 있는지) 전부 훑는다. 카드는 참조라 그 자리에서 고칠 수 있다."""
    for k, v in db.get("types", {}).items():
        for s in v["situations"]:
            for c in s["cards"]:
                yield c, f"types/{k}/{s['label']}"
    for cs in db.get("common_situations", []):
        for c in cs["cards"]:
            yield c, f"common_situations/{cs['key']}"
    for k, v in db.get("common", {}).items():
        for c in v.get("cards", []):
            yield c, f"common/{k}"
    for k, v in db.get("landmarks", {}).items():
        for c in v["cards"]:
            yield c, f"landmarks/{k}"


def validate(db):
    """구조 검증. 문제를 리스트로 돌려준다. 비어 있으면 통과."""
    errs = []
    for c, where in iter_cards(db):
        if not c.get("intent"):
            errs.append(f"{where}: intent 없음")
        say = c.get("say")
        if not isinstance(say, dict) or not say:
            errs.append(f"{where}: say 없음 -> {c.get('intent')}")
            continue
        for lang, s in say.items():
            if not s.get("t"):
                errs.append(f"{where}: say.{lang}.t 비었음 -> {c['intent']}")
            if not s.get("s"):
                errs.append(f"{where}: say.{lang}.s(소리표기) 비었음 -> {c['intent']}")
            if len(s.get("t", "").split()) > 8:
                errs.append(f"{where}: 8단어 초과 -> {s['t']}")
        for lang, rs in (c.get("reply") or {}).items():
            for r in rs:
                for key in ("t", "s", "ko"):
                    if not r.get(key):
                        errs.append(f"{where}: reply.{lang}.{key} 비었음 -> {c['intent']}")
    # 상황마다 keywords 가 있는지
    for k, v in db.get("types", {}).items():
        if not v.get("keywords"):
            errs.append(f"types/{k}: 장소 keywords 없음")
        for s in v["situations"]:
            if not s.get("keywords"):
                errs.append(f"types/{k}/{s['label']}: 상황 keywords 없음")
    return errs


def check_search(db):
    """js/app.js 의 lookup() 을 그대로 옮겨 키워드가 엉뚱한 데로 새는지 본다."""
    def norm(s):
        return s.lower().replace(" ", "")

    def lookup(q):
        n = norm(q)
        if not n:
            return None
        for k, v in db.get("landmarks", {}).items():
            if any(norm(w) in n for w in v["keywords"]):
                return ("landmark", k, None)
        for k, v in db.get("types", {}).items():
            if any(norm(w) in n for w in v["keywords"]):
                return ("type", k, None)
        for cs in db.get("common_situations", []):
            if any(norm(w) in n for w in cs.get("keywords", [])):
                return ("commonsit", cs["key"], None)
        for k, v in db.get("types", {}).items():
            for i, s in enumerate(v["situations"]):
                if any(norm(w) in n for w in (s.get("keywords", []) + [s["label"]])):
                    return ("type", k, i)
        return None

    strays = []
    for cs in db.get("common_situations", []):
        for w in cs.get("keywords", []):
            got = lookup(w)
            if not got or got[0] != "commonsit" or got[1] != cs["key"]:
                strays.append(f'공통「{cs["label"]}」의 "{w}" -> {got}')
    for k, v in db.get("types", {}).items():
        for w in v.get("keywords", []):
            got = lookup(w)
            if not got or got[1] != k:
                strays.append(f'{v["label"]}의 "{w}" -> {got}')
        for i, s in enumerate(v["situations"]):
            for w in s.get("keywords", []):
                got = lookup(w)
                if not got or got[1] != k or got[2] != i:
                    strays.append(f'{v["label"]}/{s["label"]}의 "{w}" -> {got}')
    return strays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default="data/cards.json")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    db = load(a.cards)
    before = sum(1 for _ in iter_cards(db))
    added = defaultdict(int)

    # 1) 새 장소 종류 / 공통 상황 추가
    for name in STAGE_APPROVED:
        p = os.path.join(a.data_dir, name)
        if not os.path.exists(p):
            print(f"!! 없음: {p}")
            sys.exit(1)
        st = load(p)
        for k, v in st.get("types", {}).items():
            if k in db["types"]:
                print(f"!! 이미 있는 종류: {k}")
                sys.exit(1)
            db["types"][k] = v
            added[name] += sum(len(s["cards"]) for s in v["situations"])
        if "common_situations" in st:
            db.setdefault("common_situations", [])
            have = {c["key"] for c in db["common_situations"]}
            for cs in st["common_situations"]:
                if cs["key"] in have:
                    print(f"!! 이미 있는 공통 상황: {cs['key']}")
                    sys.exit(1)
                db["common_situations"].append(cs)
                added[name] += len(cs["cards"])

    # 2) 기존 48개 상황에 keywords 주입
    kp = os.path.join(a.data_dir, KEYWORDS_FILE)
    if os.path.exists(kp):
        kw = load(kp)["situation_keywords"]
        for k, arr in kw.items():
            if k not in db["types"]:
                print(f"!! keywords 대상 종류 없음: {k}")
                sys.exit(1)
            sits = db["types"][k]["situations"]
            if len(arr) != len(sits):
                print(f"!! keywords 개수 불일치: {k} {len(arr)} != {len(sits)}")
                sys.exit(1)
            for s, words in zip(sits, arr):
                s["keywords"] = words

    # 3) 문장·소리 표기 통일
    fixed = 0
    for c, _ in iter_cards(db):
        for lang, s in (c.get("say") or {}).items():
            t = s.get("t", "")
            if t in TEXT_CANON:
                s["t"] = TEXT_CANON[t]; fixed += 1
            if s.get("t", "").lower() in SOUND_CANON:
                s["s"] = SOUND_CANON[s["t"].lower()]; fixed += 1
        for lang, rs in (c.get("reply") or {}).items():
            for r in rs:
                if r.get("t", "").lower() in SOUND_CANON:
                    r["s"] = SOUND_CANON[r["t"].lower()]; fixed += 1

    after = sum(1 for _ in iter_cards(db))

    # 4) 검증 — 실패하면 아무것도 안 쓴다
    errs = validate(db)
    strays = check_search(db)

    print(f"카드 {before} -> {after}  (+{after - before})")
    for name, n in added.items():
        print(f"   {name}: +{n}")
    print(f"문장·표기 통일: {fixed}건")
    print(f"구조 오류: {len(errs)}건")
    for e in errs[:30]:
        print("   ", e)
    print(f"검색이 엉뚱한 데로 새는 키워드: {len(strays)}건")
    for s in strays[:30]:
        print("   ", s)

    if errs:
        print("\n구조 오류가 있어 쓰지 않았다.")
        sys.exit(1)
    if a.dry_run:
        print("\n--dry-run 이라 쓰지 않았다.")
        return

    bak = a.cards + ".bak"
    shutil.copy2(a.cards, bak)
    dump(a.cards, db)
    print(f"\n완료. 백업: {bak}")
    print("sw.js 의 CACHE 숫자를 올릴 것.")


if __name__ == "__main__":
    main()
