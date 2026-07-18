#!/usr/bin/env python3
"""경쟁 지형 분석 — 심사 피드백("경쟁기업도 분석해서 결과물 도출") 반영.

소비자의 세계에는 우리 자극만 있는 게 아니다: 경쟁 브랜드의 시딩 흔적을 수집해
우리 후보 풀과 겹침을 분석한다. 세 가지 신호:
  경쟁 검증  — 경쟁 브랜드 1~2곳이 이미 거쳐간 채널 = 뷰티 시딩 수용성이 검증됨
  협찬 과다  — 3곳 이상 겹침 = 진정성 하락 리스크 (신중)
  화이트스페이스 — 어떤 경쟁 브랜드도 안 잡은 채널 = 선점 기회
+ 경쟁사는 쓰는데 우리 풀에 없는 채널 = 신규 후보 제안.

사용법:
    python tools/competitor_analysis.py            # data/competitor-landscape.csv 생성
    python tools/competitor_analysis.py selftest
"""
import csv
import io
import sys

COMP = "data/competitor-mentions.csv"
SCORES = "data/influencer-scores.csv"
OUT = "data/competitor-landscape.csv"
NEW_CANDIDATE_TOP = 5


def brand_of(query):
    return query.split()[0]


def tag_of(n_brands):
    if n_brands == 0:
        return "화이트스페이스"
    if n_brands <= 2:
        return "경쟁 검증"
    return "협찬 과다"


def analyze(comp_rows, pool_rows):
    # 채널 → 언급된 경쟁 브랜드 집합 (검색어 첫 단어 = 브랜드)
    ch_brands, ch_views = {}, {}
    for r in comp_rows:
        ch = r["channel"]
        ch_brands.setdefault(ch, set()).add(brand_of(r["query"]))
        ch_views[ch] = max(ch_views.get(ch, 0), int(r["views"] or 0))

    pool_names = {r["channel"] for r in pool_rows}
    out = []
    # ① 우리 풀 채널 태깅
    for r in pool_rows:
        brands = sorted(ch_brands.get(r["channel"], set()))
        out.append({
            "type": "풀", "channel": r["channel"], "score": r["total"],
            "brands": "·".join(brands), "brand_count": len(brands),
            "tag": tag_of(len(brands)), "views": "",
        })
    # ② 경쟁사가 쓰는데 우리 풀에 없는 채널 = 신규 후보 (조회수 상위)
    newcomers = [(ch, bs) for ch, bs in ch_brands.items() if ch not in pool_names]
    newcomers.sort(key=lambda x: -ch_views.get(x[0], 0))
    for ch, bs in newcomers[:NEW_CANDIDATE_TOP]:
        out.append({
            "type": "신규후보", "channel": ch, "score": "",
            "brands": "·".join(sorted(bs)), "brand_count": len(bs),
            "tag": "경쟁사 검증·미시딩", "views": ch_views.get(ch, 0),
        })
    return out


def selftest():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    comp = [
        {"channel": "A", "query": "라운드랩 선크림", "views": "1000"},
        {"channel": "A", "query": "달바 선크림", "views": "500"},
        {"channel": "B", "query": "라운드랩 선크림", "views": "100"},
        {"channel": "B", "query": "조선미녀 선크림", "views": "100"},
        {"channel": "B", "query": "스킨1004 선크림", "views": "100"},
        {"channel": "NEW", "query": "달바 선크림", "views": "9999"},
    ]
    pool = [{"channel": "A", "total": "70"}, {"channel": "B", "total": "60"},
            {"channel": "C", "total": "50"}]
    res = analyze(comp, pool)
    by = {r["channel"]: r for r in res}
    checks = [
        ("경쟁 1~2곳 겹침 = 경쟁 검증", by["A"]["tag"] == "경쟁 검증"),
        ("경쟁 3곳 이상 = 협찬 과다", by["B"]["tag"] == "협찬 과다"),
        ("겹침 0 = 화이트스페이스", by["C"]["tag"] == "화이트스페이스"),
        ("풀 밖 경쟁 채널 = 신규 후보 제안", by["NEW"]["type"] == "신규후보"),
        ("결정론: 같은 입력 = 같은 결과", res == analyze(comp, pool)),
    ]
    passed = 0
    for name, ok in checks:
        passed += ok
        out.write(f"{'PASS' if ok else 'FAIL'}  {name}\n")
    out.write(f"\n{passed}/{len(checks)} passed\n")
    out.flush()
    return 0 if passed == len(checks) else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    with open(COMP, encoding="utf-8-sig") as fh:
        comp = list(csv.DictReader(fh))
    with open(SCORES, encoding="utf-8-sig") as fh:
        pool = list(csv.DictReader(fh))
    res = analyze(comp, pool)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
        w.writeheader()
        w.writerows(res)

    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    tags = {}
    for r in res:
        if r["type"] == "풀":
            tags[r["tag"]] = tags.get(r["tag"], 0) + 1
    out.write(f"우리 풀 {sum(tags.values())}채널: " + " · ".join(f"{k} {v}" for k, v in tags.items()) + "\n")
    for r in res:
        if r["type"] == "풀" and r["brand_count"]:
            out.write(f"  [{r['tag']}] {r['channel'][:16]:16} ← {r['brands']}\n")
    out.write("신규 후보 (경쟁사 검증·미시딩):\n")
    for r in res:
        if r["type"] == "신규후보":
            out.write(f"  {r['channel'][:20]:20} 브랜드 {r['brand_count']}곳 ({r['brands']}) · 대표 조회 {r['views']:,}\n")
    out.write(f"저장: {OUT}\n")
    out.flush()


if __name__ == "__main__":
    main()
