#!/usr/bin/env python3
"""시딩 루프 시뮬레이션 (상태 2→6) — 합성 데이터에 정답을 심고 복원을 증명.

[SYNTHETIC] 판매 데이터는 전부 합성이다. 매출·전환은 가상이며,
각 채널에 '진짜 전환력'(ground truth)을 심어둔 뒤 인과 장부가
그 순위를 복원하는지로 추정 로직 자체를 검증한다.

상태 2: 점수 상위 5개 채널 선정 + 전용코드 부여
상태 3: 게시 시뮬레이션 (D+3~D+7 게시)
상태 4: 28일 합성 판매 로그 (기저 매출 + 코드 구매 + 게시 후 48h 상승)
상태 5: 인과 장부 — 확실(코드) / 추정(시간창 상승) 두 칸 분리
상태 6: 점수 갱신 → 다음 배치 추천

사용법:
    python tools/simulate_loop.py            # 시뮬레이션 실행
    python tools/simulate_loop.py selftest   # 복원 검증
"""
import csv
import io
import random
import re
import sys

SCORES = "data/influencer-scores.csv"
PRICE = 30000          # 객단가(원) — 가상
BASELINE_MEAN = 100    # 기저 일 주문수 — 가상
DAYS = 28
SEED = 20260718        # 본선 날짜. 고정 시드 = 재현 가능

# ground truth: 시딩 점수(사전 예측)와 일부러 어긋나게 심는다.
# 1위 채널은 실제론 중간, 하위권 하나가 실제 에이스 → 루프가 이걸 '발견'해야 함
TRUE_CONV = {0: 0.4, 1: 1.0, 2: 0.3, 3: 0.9, 4: 0.15}  # 선정순위 idx -> 전환력 배수


def _code(channel, i):
    slug = re.sub(r"[^A-Za-z0-9가-힣]", "", channel)[:6].upper() or f"CH{i}"
    return f"MEDI-{slug}{i}"


def select_batch_rows(rows):
    """배치 5 = 활용 4 + 탐색 1.
    활용: 반응 절대량(engaged_abs)이 풀 중앙값 이상인 채널 중 총점 상위 4 — 총량(매출)도 효율(점수)도 갖춘 채널.
    탐색: 중앙값 미만(소형·불확실) 중 총점 최상위 1 — 정보 가치를 위해 배치의 20%를 실험에 배정.
    근거: 단일 라운드는 근접 채널을 구분 못 한다(05 문서) → 해상도를 올리는 표본이 필요하다."""
    engaged = sorted(int(r.get("engaged_abs") or 0) for r in rows)
    median = engaged[len(engaged) // 2] if engaged else 0
    big = [r for r in rows if int(r.get("engaged_abs") or 0) >= median]
    small = [r for r in rows if int(r.get("engaged_abs") or 0) < median]
    exploit = sorted(big, key=lambda r: (-int(r["total"]), r["channel"]))[:4]
    explore = sorted(small, key=lambda r: (-int(r["total"]), r["channel"]))[:1]
    return exploit + explore, ["활용"] * len(exploit) + ["탐색"] * len(explore)


def load_top5():
    with open(SCORES, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    batch_rows, roles = select_batch_rows(rows)
    for r, role in zip(batch_rows, roles):
        r["role"] = role
    return batch_rows


def simulate(top5, rng):
    # 상태 2+3: 배치 구성
    batch = []
    for i, r in enumerate(top5):
        batch.append({
            "rank": i + 1, "channel": r["channel"], "old_score": int(r["total"]),
            "role": r.get("role", "활용"),
            "code": _code(r["channel"], i), "post_day": 3 + i,  # D+3부터 하루 간격 게시
            "true_conv": TRUE_CONV[i],  # [SYNTHETIC] 심어둔 정답 (실전엔 없음)
        })

    # 상태 4: 합성 판매 로그
    sales = []  # (day, code_or_"", orders)
    for day in range(1, DAYS + 1):
        base = max(0, round(rng.gauss(BASELINE_MEAN, 8)))
        sales.append({"day": day, "code": "", "orders": base, "kind": "baseline"})
        for b in batch:
            if day >= b["post_day"]:
                age = day - b["post_day"]
                decay = max(0.0, 1.0 - age / 7.0)               # 게시 후 7일 감쇠
                code_orders = round(rng.gauss(12 * b["true_conv"] * decay, 1.5)) if decay else 0
                if code_orders > 0:
                    sales.append({"day": day, "code": b["code"], "orders": code_orders, "kind": "code"})
                if age < 2:                                       # 48h 코드 없는 상승
                    lift = max(0, round(rng.gauss(8 * b["true_conv"], 2)))
                    sales.append({"day": day, "code": "", "orders": lift, "kind": "organic_lift"})
    return batch, sales


def ledger_from(batch, sales):
    """상태 5: 인과 장부. 실전과 동일하게 kind 라벨은 못 보고 코드·날짜만 사용."""
    baseline_days = [d for d in range(1, DAYS + 1) if all(not (b["post_day"] <= d < b["post_day"] + 2) for b in batch)]
    daily_nocode = {}
    for s in sales:
        if not s["code"]:
            daily_nocode[s["day"]] = daily_nocode.get(s["day"], 0) + s["orders"]
    base_avg = sum(daily_nocode.get(d, 0) for d in baseline_days) / len(baseline_days)

    rows = []
    for b in batch:
        certain = sum(s["orders"] for s in sales if s["code"] == b["code"])
        window = [b["post_day"], b["post_day"] + 1]
        lift_orders = sum(daily_nocode.get(d, 0) - base_avg for d in window)
        rows.append({
            "channel": b["channel"], "code": b["code"],
            "certain_orders": certain, "certain_revenue": certain * PRICE,
            "est_lift_orders": round(lift_orders, 1),
            "est_note": "48h 시간창 vs 기저 평균 — 추정치(다른 채널 게시와 겹치면 과대계상 가능)",
        })
    return rows, base_avg


def update_scores(batch, ledger):
    """상태 6: 실측 반영 점수 갱신. new = 0.5*사전점수 + 0.5*실측(확실 주문수 백분위)"""
    max_orders = max(l["certain_orders"] for l in ledger) or 1
    out = []
    for b, l in zip(batch, ledger):
        measured = 100 * l["certain_orders"] / max_orders
        new = round(0.5 * b["old_score"] + 0.5 * measured)
        out.append({"channel": b["channel"], "role": b.get("role", "활용"),
                    "old_score": b["old_score"],
                    "measured_pct": round(measured), "new_score": new,
                    "action": "재계약+닮은꼴 발굴" if new >= 70 else ("유지" if new >= 45 else "제외")})
    return sorted(out, key=lambda r: -r["new_score"])


def run(write_files=True):
    rng = random.Random(SEED)
    top5 = load_top5()
    batch, sales = simulate(top5, rng)
    ledger, base_avg = ledger_from(batch, sales)
    updated = update_scores(batch, ledger)
    if write_files:
        for name, rows in [("seeding-batch", batch), ("synthetic-sales", sales),
                           ("attribution-ledger", ledger), ("updated-scores", updated)]:
            with open(f"data/{name}.csv", "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
    return batch, sales, ledger, updated, base_avg


def selftest():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    b1, s1, l1, u1, _ = run(write_files=False)
    b2, s2, l2, u2, _ = run(write_files=False)
    checks = [
        ("결정론: 같은 시드 = 같은 장부", l1 == l2 and u1 == u2),
        # 근접 전환력(1.0 vs 0.9)은 단일 라운드 노이즈로 구분 불가(통계적 한계) —
        # 뚜렷이 갈린 층위만 복원을 요구한다: 상위 2 집합 일치 + 최하위 일치.
        ("복원: 상위 2 채널 집합 == 심은 상위 2 (근접값은 집합으로 판정)",
         {l["channel"] for l in sorted(l1, key=lambda x: -x["certain_orders"])[:2]}
         == {b["channel"] for b in sorted(b1, key=lambda x: -x["true_conv"])[:2]}),
        ("복원: 최하위 채널 == 심은 최하위 전환력",
         min(l1, key=lambda x: x["certain_orders"])["channel"]
         == min(b1, key=lambda x: x["true_conv"])["channel"]),
        ("분리: 장부에 확실/추정 컬럼이 분리 존재",
         all("certain_orders" in l and "est_lift_orders" in l for l in l1)),
        ("루프 학습: 사전 1위가 실측 반영 후 1위 아님 (심은 정답대로 강등)",
         u1[0]["channel"] != b1[0]["channel"]),
        ("합성 라벨: 판매 로그에 kind 라벨 보존(감사 가능)",
         all("kind" in s for s in s1)),
        ("배치 구성: 활용 4 + 탐색 1 (탐색 = 정보 가치 예산) — 합성 풀 10개로 순수 검증",
         (lambda br: [r[1] for r in [(None, x) for x in br[1]]].count("활용") == 4 and br[1].count("탐색") == 1)(
             select_batch_rows([{"channel": f"C{i}", "total": str(90 - i),
                                 "engaged_abs": str(10000 - i * 1000)} for i in range(10)]))),
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
    batch, sales, ledger, updated, base_avg = run()
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write("[SYNTHETIC] 합성 데이터 시뮬레이션 — 매출·전환은 가상\n\n")
    out.write("상태 2 — 시딩 배치 (활용 4 + 탐색 1, 전용코드 부여)\n")
    for b in batch:
        out.write(f"  {b['rank']}. [{b['role']}] {b['channel'][:16]:16} 사전점수 {b['old_score']:3}  코드 {b['code']:16} D+{b['post_day']} 게시\n")
    out.write(f"\n상태 4 — 28일 합성 판매 로그 {len(sales)}행 (기저 평균 {base_avg:.0f}건/일)\n")
    out.write("\n상태 5 — 인과 장부 (확실 | 추정 분리)\n")
    for l in ledger:
        out.write(f"  {l['channel'][:16]:16} 확실 {l['certain_orders']:3}건 {l['certain_revenue']:>9,}원 | 추정상승 {l['est_lift_orders']:+.1f}건\n")
    out.write("\n상태 6 — 점수 갱신 → 다음 배치\n")
    for u in updated:
        out.write(f"  {u['channel'][:16]:16} {u['old_score']:3} → {u['new_score']:3}  ({u['action']})\n")
    out.write("\n저장: data/seeding-batch.csv, synthetic-sales.csv, attribution-ledger.csv, updated-scores.csv\n")
    out.flush()


if __name__ == "__main__":
    main()
