#!/usr/bin/env python3
"""시딩 후보 점수화 — 결정론적 순수 함수 (같은 입력 = 같은 점수).

입력:  data/youtube-enriched.csv + data/seeding-rulepack.json
출력:  data/influencer-scores.csv + 콘솔 랭킹 표

사용법:
    python tools/score_influencers.py            # 점수화 실행
    python tools/score_influencers.py selftest   # 규칙 셀프테스트
"""
import csv
import io
import json
import sys

RULEPACK = "data/seeding-rulepack.json"
SRC = "data/youtube-enriched.csv"
OUT = "data/influencer-scores.csv"


def load_pack():
    with open(RULEPACK, encoding="utf-8") as fh:
        return json.load(fh)["rules"]


def r1_engagement(views, likes, comments, rule):
    if not views:
        return 0, "조회수 0/미확인"
    if views < rule.get("min_views", 0):
        return 0, f"표본 부족(조회수 {views} < {rule['min_views']})"
    rate = (likes + comments) / views
    for threshold, score in rule["bands"]:
        if rate >= threshold:
            return score, f"반응률 {rate:.1%}"
    return 0, f"반응률 {rate:.1%}"


def r2_scale(subscribers, rule):
    if subscribers is None:
        return 8, "구독자 미확인(추정: 최저밴드 보수 처리)"
    for lo, hi, score in rule["bands_subscribers"]:
        if hi is None:
            if subscribers >= lo:
                return score, f"구독자 {subscribers:,}"
        elif lo <= subscribers < hi:
            return score, f"구독자 {subscribers:,}"
    return 8, f"구독자 {subscribers:,}"


def r3_authenticity(title, rule):
    t = title.replace(" ", "")
    if any(m in t for m in rule["markers_organic"]):
        return rule["score_organic"], "내돈내산/솔직 마커"
    if any(m in t for m in rule["markers_paid"]):
        return rule["score_paid"], "협찬/광고 표기"
    return rule["score_neutral"], "마커 없음(중립)"


def r4_relevance(title, rule):
    t = title.replace(" ", "")
    if any(m in t for m in rule["markers"]):
        return rule["score_hit"], "뷰티 키워드 일치"
    return rule["score_miss"], "카테고리 키워드 없음"


def score_row(row, pack):
    views = int(row.get("views") or 0)
    likes = int(row.get("likes") or 0)
    comments = int(row.get("comments") or 0)
    subs = int(row["subscribers"]) if row.get("subscribers") else None
    title = row.get("title", "")

    s1, w1 = r1_engagement(views, likes, comments, pack["R1-ENGAGEMENT"])
    s2, w2 = r2_scale(subs, pack["R2-SCALE-FIT"])
    s3, w3 = r3_authenticity(title, pack["R3-AUTHENTICITY"])
    s4, w4 = r4_relevance(title, pack["R4-RELEVANCE"])
    return {
        "channel": row.get("channel", ""),
        "subscribers": row.get("subscribers", ""),
        "total": s1 + s2 + s3 + s4,
        "R1_engagement": s1, "R1_why": w1,
        "R2_scale": s2, "R2_why": w2,
        "R3_authenticity": s3, "R3_why": w3,
        "R4_relevance": s4, "R4_why": w4,
        "estimated": "Y" if subs is None else "",
        "title": title,
        "url": row.get("url", ""),
    }


def selftest():
    pack = load_pack()
    cases = [
        ("마이크로+내돈내산+뷰티 = 최고점대",
         {"views": "10000", "likes": "480", "comments": "40", "subscribers": "25000",
          "title": "내돈내산 스킨케어 리뷰"}, lambda r: r["total"] == 40 + 25 + 20 + 15),
        ("메가+협찬 = 감점",
         {"views": "1000000", "likes": "3000", "comments": "200", "subscribers": "800000",
          "title": "광고 포함 크림 소개"}, lambda r: r["R2_scale"] == 10 and r["R3_authenticity"] == 8),
        ("구독자 미확인 = 추정 플래그 + 보수 점수",
         {"views": "5000", "likes": "100", "comments": "10", "subscribers": "",
          "title": "세럼 후기"}, lambda r: r["estimated"] == "Y" and r["R2_scale"] == 8),
        ("카테고리 밖 = R4 최저",
         {"views": "5000", "likes": "100", "comments": "10", "subscribers": "20000",
          "title": "캠핑 브이로그"}, lambda r: r["R4_relevance"] == 5),
        ("조회수 0 = R1 0점(에러 아님)",
         {"views": "0", "likes": "0", "comments": "0", "subscribers": "5000",
          "title": "뷰티 리뷰"}, lambda r: r["R1_engagement"] == 0),
        ("표본 부족(조회수 2·반응률 50%) = R1 0점 — 리허설에서 발견한 왜곡 방지",
         {"views": "2", "likes": "1", "comments": "0", "subscribers": "122",
          "title": "선크림 추천 후기"}, lambda r: r["R1_engagement"] == 0),
        ("결정론: 같은 입력 = 같은 출력",
         {"views": "7777", "likes": "333", "comments": "22", "subscribers": "15000",
          "title": "선크림 추천"}, lambda r: r == score_row({"views": "7777", "likes": "333",
          "comments": "22", "subscribers": "15000", "title": "선크림 추천"}, pack)),
    ]
    passed = 0
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for name, row, check in cases:
        r = score_row(row, pack)
        ok = check(r)
        passed += ok
        out.write(f"{'PASS' if ok else 'FAIL'}  {name}\n")
    out.write(f"\n{passed}/{len(cases)} passed\n")
    out.flush()
    return 0 if passed == len(cases) else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    pack = load_pack()
    with open(SRC, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    # 채널 단위로 대표 영상 1개(최고 점수)만 남김
    scored = [score_row(r, pack) for r in rows]
    by_channel = {}
    for s in scored:
        k = s["channel"]
        if k not in by_channel or s["total"] > by_channel[k]["total"]:
            by_channel[k] = s
    ranked = sorted(by_channel.values(), key=lambda s: -s["total"])

    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ranked[0].keys()))
        w.writeheader()
        w.writerows(ranked)

    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write(f"{'순위':<3} {'점수':<4} {'채널':<22} {'구독자':>8}  근거 요약\n")
    out.write("-" * 90 + "\n")
    for i, s in enumerate(ranked, 1):
        est = " (추정)" if s["estimated"] else ""
        out.write(f"{i:<4} {s['total']:<5} {s['channel'][:20]:<22} {s['subscribers'] or '?':>8}{est}"
                  f"  R1:{s['R1_engagement']} R2:{s['R2_scale']} R3:{s['R3_authenticity']} R4:{s['R4_relevance']} | {s['R1_why']}\n")
    out.write(f"\n저장: {OUT} ({len(ranked)}개 채널)\n")
    out.flush()


if __name__ == "__main__":
    main()
