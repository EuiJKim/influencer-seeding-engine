#!/usr/bin/env python3
"""닮은꼴 발굴 — 실측 검증된 에이스와 규칙 프로필(R1~R4)이 비슷한 미시딩 채널 추천.

루프의 '확장' 단계: 잘된 채널을 재계약하는 데서 멈추지 않고,
그 채널과 같은 특성을 가진 새 후보를 찾아 다음 배치에 넣는다.

방법(결정론): R1~R4를 배점으로 정규화한 4차원 벡터 간 거리(작을수록 닮음).
같은 입력 = 같은 추천. 임베딩·AI 추측 없음 — 근거는 규칙 점수 그 자체.

사용법:
    python tools/find_lookalikes.py            # data/lookalikes.csv 생성
    python tools/find_lookalikes.py selftest
"""
import csv
import io
import sys

SCORES = "data/influencer-scores.csv"
UPDATED = "data/updated-scores.csv"
OUT = "data/lookalikes.csv"
WEIGHTS = {"R1_engagement": 40, "R2_scale": 25, "R3_authenticity": 20, "R4_relevance": 15}
TOP_K = 2


def profile(row):
    """R1~R4를 각 배점 대비 0~1로 정규화한 4차원 프로필."""
    return tuple(int(row[k]) / w for k, w in WEIGHTS.items())


def distance(p, q):
    return sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5


def recommend(scores, updated, top_k=TOP_K):
    aces = [u["channel"] for u in updated if u["action"] == "재계약+닮은꼴 발굴"]
    seeded = {u["channel"] for u in updated}
    pool = [r for r in scores if r["channel"] not in seeded]
    out = []
    for ace in aces:
        ace_row = next(r for r in scores if r["channel"] == ace)
        ap = profile(ace_row)
        ranked = sorted(pool, key=lambda r: (distance(ap, profile(r)), r["channel"]))
        for cand in ranked[:top_k]:
            d = distance(ap, profile(cand))
            out.append({
                "ace": ace, "candidate": cand["channel"],
                "distance": round(d, 3),
                "similarity_pct": round(max(0.0, 1 - d / 2) * 100),
                "why": f"프로필 R1~R4 ({cand['R1_engagement']}/{cand['R2_scale']}/"
                       f"{cand['R3_authenticity']}/{cand['R4_relevance']}) ≈ "
                       f"에이스 ({ace_row['R1_engagement']}/{ace_row['R2_scale']}/"
                       f"{ace_row['R3_authenticity']}/{ace_row['R4_relevance']})",
                "subscribers": cand["subscribers"],
            })
    return out


def selftest():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    def row(ch, r1, r2, r3, r4):
        return {"channel": ch, "R1_engagement": str(r1), "R2_scale": str(r2),
                "R3_authenticity": str(r3), "R4_relevance": str(r4), "subscribers": "1000"}

    scores = [row("ACE", 20, 8, 20, 15), row("TWIN", 20, 8, 20, 15),
              row("NEAR", 10, 8, 20, 15), row("FAR", 0, 25, 8, 5)]
    updated = [{"channel": "ACE", "action": "재계약+닮은꼴 발굴"}]
    recs = recommend(scores, updated, top_k=2)
    checks = [
        ("동일 프로필(TWIN)이 1순위, 거리 0", recs[0]["candidate"] == "TWIN" and recs[0]["distance"] == 0),
        ("근접 프로필(NEAR)이 2순위", recs[1]["candidate"] == "NEAR"),
        ("반대 프로필(FAR)은 추천 밖", all(r["candidate"] != "FAR" for r in recs)),
        ("시딩된 채널은 후보에서 제외", all(r["candidate"] != "ACE" for r in recs)),
        ("결정론: 같은 입력 = 같은 추천", recs == recommend(scores, updated, top_k=2)),
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
    with open(SCORES, encoding="utf-8-sig") as fh:
        scores = list(csv.DictReader(fh))
    with open(UPDATED, encoding="utf-8-sig") as fh:
        updated = list(csv.DictReader(fh))
    recs = recommend(scores, updated)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write("닮은꼴 추천 (에이스 → 미시딩 후보)\n")
    for r in recs:
        out.write(f"  {r['ace'][:12]:12} → {r['candidate'][:16]:16} 유사도 {r['similarity_pct']}%  ({r['why']})\n")
    out.write(f"저장: {OUT}\n")
    out.flush()


if __name__ == "__main__":
    main()
