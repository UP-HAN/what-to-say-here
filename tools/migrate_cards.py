# -*- coding: utf-8 -*-
"""
카드 구조 다국어 이관 스크립트 (2026-08-01)

기존:  { en, ko, sound, note?, volatile?, reply:[{en,sound,ko}] }
신규:  { intent(한국어), say:{en:{t,s}}, reply:{en:[{t,s,ko}]}, note?, volatile? }

- intent = 한국어 의도(옛 ko). 카드의 축.
- say.<lang> = { t: 그 언어 문장, s: 한글 소리 표기 }
- reply.<lang> = [{ t, s, ko(뜻) }]
- 손으로 다시 쓰지 않는다. 옛 en/sound/reply를 그대로 en 슬롯에 넣는다.
- 명소(landmarks)에는 lang 필드(현지어)를 붙인다. 현재 전부 미국 → "en".
- countries / languages 메타를 추가한다.

실행:  python tools/migrate_cards.py
원본은 data/cards.pre-i18n.json 으로 백업된다. 이미 이관된 파일이면 그대로 둔다.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "cards.json")
BAK = os.path.join(ROOT, "data", "cards.pre-i18n.json")


def conv_card(c):
    """옛 카드 1장 → 신규 구조. 이미 신규면 그대로 반환."""
    if "say" in c:                       # 이미 이관됨
        return c
    out = {
        "intent": c.get("ko", ""),
        "say": {"en": {"t": c.get("en", ""), "s": c.get("sound", "")}},
        "reply": {"en": [
            {"t": r.get("en", ""), "s": r.get("sound", ""), "ko": r.get("ko", "")}
            for r in c.get("reply", [])
        ]},
    }
    if c.get("note"):
        out["note"] = c["note"]
    if c.get("volatile"):
        out["volatile"] = True
    return out


def conv_cards(lst):
    return [conv_card(c) for c in lst]


def main():
    with open(SRC, encoding="utf-8") as f:
        d = json.load(f)

    # 이미 이관됐는지 감지 (아무 카드나 하나 확인)
    sample = d["common"][next(iter(d["common"]))]["cards"][0]
    already = "say" in sample
    if already:
        print("이미 이관된 파일입니다. 변경 없음.")
        return

    # 원본 백업 (한 번만)
    if not os.path.exists(BAK):
        with open(BAK, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("원본 백업:", os.path.relpath(BAK, ROOT))

    n = 0
    # types.*.situations.*.cards
    for t in d["types"].values():
        for sit in t["situations"]:
            sit["cards"] = conv_cards(sit["cards"]); n += len(sit["cards"])
    # common.*.cards
    for cm in d["common"].values():
        cm["cards"] = conv_cards(cm["cards"]); n += len(cm["cards"])
    # landmarks.*.cards  (+ 현지어 lang 부여)
    for lm in d["landmarks"].values():
        lm["cards"] = conv_cards(lm["cards"]); n += len(lm["cards"])
        lm.setdefault("lang", "en")          # 현재 명소는 전부 미국

    # 나라 / 언어 메타
    d["countries"] = [
        {"code": "jp", "label": "일본", "lang": "ja", "hint": "도쿄 · 오사카 · 후쿠오카 · 삿포로", "ready": False},
        {"code": "us", "label": "미국", "lang": "en", "hint": "뉴욕 · LA · 하와이 · 괌", "ready": True},
    ]
    d["languages"] = {
        "en": {"label": "ENGLISH", "tts": "en-US"},
        "ja": {"label": "日本語", "tts": "ja-JP"},
    }
    d["version"] = "2026-08-01 v3 (i18n)"
    d["note"] = ("다국어 구조. intent=한국어 의도가 축. say/reply는 언어별. "
                 "sound는 한글 소리 표기. 없는 언어는 en으로 폴백.")

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"이관 완료: 카드 {n}장 → say/reply 구조")
    print("landmarks lang 부여:", len(d["landmarks"]), "곳 (전부 en)")


if __name__ == "__main__":
    main()
