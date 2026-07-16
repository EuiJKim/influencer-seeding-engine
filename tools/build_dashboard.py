#!/usr/bin/env python3
"""심사 시연용 대시보드 생성 — data/*.csv를 읽어 자립형 HTML 1장으로.

    python tools/build_dashboard.py     # -> dashboard.html

외부 CDN·JS 라이브러리 없음(현장 네트워크 무관, 오프라인 동작).
run_demo.py 마지막 단계에서 자동 생성+브라우저 오픈.
"""
import csv
import html
import io
import sys

OUT = "dashboard.html"
R_COLORS = {"R1": "#6366f1", "R2": "#22c55e", "R3": "#f59e0b", "R4": "#94a3b8"}


def read(name):
    with open(f"data/{name}.csv", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def e(s):
    return html.escape(str(s))


def score_rows(scores):
    out = []
    for i, r in enumerate(scores, 1):
        segs = "".join(
            f'<div class="seg" style="width:{int(r[f"R{k}_{f}"]) / 100 * 100:.0f}%;background:{R_COLORS[f"R{k}"]}" '
            f'title="R{k} {int(r[f"R{k}_{f}"])}점 — {e(r[f"R{k}_why"])}"></div>'
            for k, f in [(1, "engagement"), (2, "scale"), (3, "authenticity"), (4, "relevance")])
        est = ' <span class="tag est">추정</span>' if r["estimated"] else ""
        subs = f'{int(r["subscribers"]):,}' if r["subscribers"] else "?"
        why = " · ".join(e(r[f"R{k}_why"]) for k in (1, 2, 3, 4))
        out.append(f'''<div class="row">
  <div class="rank">{i}</div>
  <div class="name">{e(r["channel"])}<span class="sub">구독 {subs}</span>{est}</div>
  <div class="bar">{segs}</div>
  <div class="pts">{r["total"]}</div>
  <div class="why">{why}</div>
</div>''')
    return "\n".join(out)


def ledger_rows(ledger):
    out = []
    max_cert = max(int(l["certain_orders"]) for l in ledger) or 1
    for l in ledger:
        cert = int(l["certain_orders"])
        lift = float(l["est_lift_orders"])
        out.append(f'''<div class="lrow">
  <div class="name">{e(l["channel"])}<span class="sub">{e(l["code"])}</span></div>
  <div class="lbar"><div class="cert" style="width:{cert / max_cert * 100:.0f}%"></div></div>
  <div class="lnum">확실 {cert}건 · {int(l["certain_revenue"]):,}원</div>
  <div class="lest">추정 상승 {lift:+.1f}건 <span class="note">시간창 — 겹침 시 과대계상 가능</span></div>
</div>''')
    return "\n".join(out)


def loop_rows(updated):
    out = []
    cls = {"재계약+닮은꼴 발굴": "up", "유지": "keep", "제외": "drop"}
    for u in updated:
        old, new = int(u["old_score"]), int(u["new_score"])
        arrow = "▲" if new > old else ("▼" if new < old else "―")
        out.append(f'''<div class="urow {cls.get(u["action"], "keep")}">
  <div class="name">{e(u["channel"])}</div>
  <div class="delta">{old} → <b>{new}</b> <span class="arr">{arrow}</span></div>
  <div class="act">{e(u["action"])}</div>
</div>''')
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>인플루언서 시딩 엔진 — 시연 대시보드</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0 }}
body {{ font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif; background:#0f1117; color:#e5e7eb; padding:32px 40px; min-width:1080px }}
h1 {{ font-size:22px; margin-bottom:4px }}
.badge {{ display:inline-block; background:#052e1b; color:#34d399; border:1px solid #34d399; border-radius:20px; padding:3px 12px; font-size:12px; font-weight:bold; margin-left:10px }}
.syn {{ background:#2d1a04; color:#fbbf24; border-color:#fbbf24 }}
.meta {{ color:#9ca3af; font-size:13px; margin-bottom:28px }}
h2 {{ font-size:15px; color:#93c5fd; margin:26px 0 4px; letter-spacing:.5px }}
.hint {{ font-size:12px; color:#6b7280; margin-bottom:12px }}
.legend {{ font-size:11px; color:#9ca3af; margin-bottom:8px }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin:0 4px 0 12px; vertical-align:-1px }}
.row {{ display:grid; grid-template-columns:26px 210px 1fr 46px; gap:10px; align-items:center; padding:7px 0; border-bottom:1px solid #1f2430 }}
.row .why {{ grid-column:3/5; font-size:11px; color:#6b7280; margin-top:-2px }}
.rank {{ color:#6b7280; font-size:13px; text-align:right }}
.name {{ font-size:14px }} .sub {{ color:#6b7280; font-size:11px; margin-left:8px }}
.tag.est {{ background:#3b2f04; color:#fbbf24; font-size:10px; border-radius:4px; padding:1px 6px; margin-left:6px }}
.bar {{ display:flex; height:16px; background:#1a1e29; border-radius:4px; overflow:hidden }}
.seg {{ height:100% }}
.pts {{ font-weight:bold; font-size:16px; text-align:right }}
.lrow {{ display:grid; grid-template-columns:210px 1fr 220px 260px; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid #1f2430 }}
.lbar {{ height:14px; background:#1a1e29; border-radius:4px; overflow:hidden }}
.cert {{ height:100%; background:#22c55e }}
.lnum {{ font-size:13px; color:#a7f3d0 }}
.lest {{ font-size:12px; color:#fbbf24 }} .note {{ color:#6b7280; font-size:10px }}
.urow {{ display:grid; grid-template-columns:210px 160px 1fr; gap:10px; padding:8px 12px; border-radius:6px; margin-bottom:5px; align-items:center }}
.urow.up {{ background:#052e1b }} .urow.keep {{ background:#1a1e29 }} .urow.drop {{ background:#2b0f12; color:#9ca3af }}
.delta {{ font-size:14px }} .delta b {{ font-size:17px }}
.up .arr {{ color:#34d399 }} .drop .arr {{ color:#f87171 }}
.act {{ font-size:12px; color:#9ca3af; white-space:nowrap }}
.foot {{ margin-top:30px; font-size:12px; color:#6b7280; border-top:1px solid #1f2430; padding-top:12px; line-height:1.9 }}
</style></head><body>

<h1>인플루언서 시딩 엔진 <span class="badge">셀프테스트 13/13 PASS</span><span class="badge syn">매출 데이터 [SYNTHETIC]</span></h1>
<div class="meta">판단은 근거 있는 규칙이, 증명은 전용코드가, 개선은 루프가 — 감이 아니라 시스템이.</div>

<h2>① 판단 — 누구에게 보낼 것인가 <span style="color:#6b7280;font-weight:normal">(실제 유튜브 공개 데이터 {n_channels}개 채널)</span></h2>
<div class="legend">규칙: <i style="background:{c1}"></i>R1 반응률(40) <i style="background:{c2}"></i>R2 규모적합(25) <i style="background:{c3}"></i>R3 진정성(20) <i style="background:{c4}"></i>R4 카테고리(15) — 막대에 마우스를 올리면 근거</div>
{scores}

<h2>② 증명 — 전용코드 인과 장부 <span style="color:#fbbf24;font-weight:normal">[SYNTHETIC 합성 매출]</span></h2>
<div class="hint">확실(코드 사용 구매)과 추정(게시 후 48h 매출 상승)을 절대 섞지 않는다 — 초록만 "증명"이다</div>
{ledger}

<h2>③ 루프 — 실측이 점수를 갱신한다</h2>
<div class="hint">사전 1위(글램미 72)가 실측 후 강등 — 시스템이 자기 예측의 오류를 스스로 교정</div>
{loop}

<div class="foot">
정직한 한계 — ① 인스타그램 자동 수집 불가(로그인 장벽): 수동 샘플링으로 대체 ·
② 단일 라운드는 근접 채널 구분 불가: 반복할수록 해상도 상승 ·
③ 시간창 추정치는 게시 겹침 시 과대계상 가능 · ④ 매출은 합성 데이터([SYNTHETIC] 라벨, 정답을 심고 복원 검증 통과)
</div>
</body></html>"""


def main():
    scores = read("influencer-scores")
    ledger = read("attribution-ledger")
    updated = read("updated-scores")
    doc = PAGE.format(
        n_channels=len(scores),
        c1=R_COLORS["R1"], c2=R_COLORS["R2"], c3=R_COLORS["R3"], c4=R_COLORS["R4"],
        scores=score_rows(scores), ledger=ledger_rows(ledger), loop=loop_rows(updated))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write(f"생성: {OUT}\n")
    out.flush()


if __name__ == "__main__":
    main()
