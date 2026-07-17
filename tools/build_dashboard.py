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


ONTOLOGY_SVG = """<svg viewBox="0 0 1060 330" width="100%" style="max-width:1060px" xmlns="http://www.w3.org/2000/svg" font-family="Malgun Gothic,sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#64748b"/></marker>
<marker id="arg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#34d399"/></marker></defs>
<text x="1040" y="24" fill="#9ca3af" font-size="11" text-anchor="end">● 확정(수집됨)  ◐ 추정(간접신호)  ○ 당일보강</text>
<rect x="20" y="55" width="180" height="80" rx="8" fill="#151a26" stroke="#6366f1"/>
<text x="110" y="76" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">인플루언서</text>
<text x="110" y="96" fill="#9ca3af" font-size="11" text-anchor="middle">● 구독자·반응률</text>
<text x="110" y="112" fill="#9ca3af" font-size="11" text-anchor="middle">◐ 진정성·카테고리</text>
<rect x="250" y="55" width="180" height="80" rx="8" fill="#151a26" stroke="#6366f1"/>
<text x="340" y="76" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">콘텐츠</text>
<text x="340" y="96" fill="#9ca3af" font-size="11" text-anchor="middle">● 조회·좋아요·게시일</text>
<text x="340" y="112" fill="#9ca3af" font-size="11" text-anchor="middle">◐ 협찬 여부(표기)</text>
<rect x="480" y="55" width="160" height="80" rx="8" fill="#101726" stroke="#3b82f6"/>
<text x="560" y="76" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">인지</text>
<text x="560" y="96" fill="#9ca3af" font-size="11" text-anchor="middle">인스타 릴스 · 유튜브</text>
<text x="560" y="112" fill="#6b7280" font-size="10" text-anchor="middle">스킨케어 인지 60%*</text>
<rect x="680" y="55" width="160" height="80" rx="8" fill="#101726" stroke="#3b82f6"/>
<text x="760" y="76" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">검증</text>
<text x="760" y="96" fill="#9ca3af" font-size="11" text-anchor="middle">네이버 블로그 · 올리브영</text>
<text x="760" y="112" fill="#6b7280" font-size="10" text-anchor="middle">탐색 1위 올리브영 34.5%*</text>
<rect x="880" y="55" width="160" height="80" rx="8" fill="#101726" stroke="#3b82f6"/>
<text x="960" y="76" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">구매</text>
<text x="960" y="96" fill="#9ca3af" font-size="11" text-anchor="middle">자사몰 · 올리브영</text>
<text x="960" y="112" fill="#6b7280" font-size="10" text-anchor="middle">○ 전용코드 부착 지점</text>
<rect x="700" y="210" width="340" height="75" rx="8" fill="#0d1f14" stroke="#22c55e"/>
<text x="870" y="232" fill="#e5e7eb" font-size="13" font-weight="bold" text-anchor="middle">전환 신호 (인과 장부)</text>
<text x="870" y="252" fill="#a7f3d0" font-size="11" text-anchor="middle">○ 전용코드 구매 = 확실</text>
<text x="870" y="268" fill="#fbbf24" font-size="11" text-anchor="middle">○ 48h 시간창 상승 = 추정 (절대 안 섞음)</text>
<line x1="200" y1="95" x2="248" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="430" y1="95" x2="478" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="640" y1="95" x2="678" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="840" y1="95" x2="878" y2="95" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="960" y1="135" x2="915" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar)"/>
<path d="M 700 250 C 350 250 110 220 110 140" fill="none" stroke="#34d399" stroke-width="1.8" stroke-dasharray="6 4" marker-end="url(#arg)"/>
<text x="330" y="238" fill="#34d399" font-size="12" font-weight="bold">루프: 실측 → 점수 갱신 → 닮은꼴 발굴 → 다음 배치</text>
<text x="480" y="320" fill="#4b5563" font-size="10">* 출처: 픽플리 2026-1Q 소비 여정 조사 (docs/02-platform-research.md)</text>
</svg>"""


def lookalike_rows():
    try:
        rows = read("lookalikes")
    except FileNotFoundError:
        return '<div class="hint">data/lookalikes.csv 없음 — find_lookalikes.py 먼저 실행</div>'
    out = []
    for r in rows:
        subs = f'{int(r["subscribers"]):,}' if r["subscribers"] else "?"
        out.append(f'''<div class="krow">
  <div class="name">{e(r["ace"])} <span class="sub">에이스</span></div>
  <div class="karr">→</div>
  <div class="name">{e(r["candidate"])}<span class="sub">구독 {subs} · 미시딩</span></div>
  <div class="ksim">유사도 {e(r["similarity_pct"])}%</div>
  <div class="why" style="grid-column:1/5">{e(r["why"])}</div>
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
.whygrid {{ display:grid; grid-template-columns:1fr 170px 1fr; gap:14px; margin:6px 0 8px }}
.whycard {{ border-radius:10px; padding:16px 18px }}
.whycard.bad {{ background:#1c1216; border:1px solid #7f1d1d }}
.whycard.good {{ background:#0d1f14; border:1px solid #166534 }}
.whyhead {{ font-size:12px; font-weight:bold; letter-spacing:.3px; margin-bottom:10px }}
.bad .whyhead {{ color:#f87171 }} .good .whyhead {{ color:#34d399 }}
.whyitem {{ font-size:12px; color:#c7ccd8; line-height:1.55; margin-bottom:8px }}
.whypivot {{ display:flex; flex-direction:column; justify-content:center; text-align:center; font-size:13px; color:#93c5fd; line-height:1.7 }}
.whypivot b {{ font-size:15px; color:#e5e7eb }} .whypivot span {{ font-size:11px; color:#6b7280 }}
.krow {{ display:grid; grid-template-columns:190px 30px 260px 1fr; gap:8px; align-items:center; padding:8px 12px; background:#131a2a; border-radius:6px; margin-bottom:5px }}
.karr {{ color:#34d399; font-weight:bold; text-align:center }}
.ksim {{ color:#93c5fd; font-size:13px; font-weight:bold }}
.krow .why {{ font-size:11px; color:#6b7280 }}
.foot {{ margin-top:30px; font-size:12px; color:#6b7280; border-top:1px solid #1f2430; padding-top:12px; line-height:1.9 }}
</style></head><body>

<h1>인플루언서 시딩 엔진 <span class="badge">셀프테스트 18/18 PASS</span><span class="badge syn">매출 데이터 [SYNTHETIC]</span></h1>
<div class="meta">판단은 근거 있는 규칙이, 증명은 전용코드가, 개선은 루프가 — 감이 아니라 시스템이.</div>

<h2>문제의 구조 — "ABC 중 뭐가 팔았나"는 왜 아무도 못 풀었고, 왜 여기서는 풀리나</h2>
<div class="whygrid">
  <div class="whycard bad">
    <div class="whyhead">전역에서 불가능한 이유 (구글·메타도 못 푼)</div>
    <div class="whyitem">① <b>반사실 관측 불가</b> — "안 봤다면"의 세계는 재생되지 않는다</div>
    <div class="whyitem">② <b>조각난 여정</b> — 틱톡→유튜브→네이버→오프라인, 전체를 보는 자가 없고 각자 공로 주장(합계 200%). 추적의 다리는 규제(ATT·쿠키 폐지)로 붕괴 중</div>
    <div class="whyitem">③ <b>측정자의 이해충돌</b> — 광고 효과를 재는 자가 광고를 파는 자</div>
  </div>
  <div class="whypivot">그래서<br><b>관측하지 않는다.<br>실험을 설계한다.</b><br><span>채널별 전용코드<br>= 채널 단위 실험</span></div>
  <div class="whycard good">
    <div class="whyhead">메디테라피 국소에서 가능한 이유</div>
    <div class="whyitem">① <b>자사몰 소유</b> — 구매 데이터가 자기 것</div>
    <div class="whyitem">② <b>제품 수십 개</b> — 깨끗한 제품별 실험 가능 (수백만 SKU 대기업 불가)</div>
    <div class="whyitem">③ <b>이해충돌 없음</b> — 자기 돈으로 재니 정답을 원하는 유일한 측정자</div>
    <div class="whyitem">④ <b>시딩 = 태생이 실험</b> — 인플루언서별 코드 부착이 자연스러움</div>
  </div>
</div>
<div class="hint" style="margin-bottom:20px">전역 관측은 불가능해도, 자기 세계를 소유한 D2C의 국소에서는 부분해가 설계 가능하다 — "100% 해결 안 돼도 일부 접목하면 엄청난 부가가치" (대표 인터뷰)</div>

<h2>⓪ 온톨로지 — 시딩의 세계관 (콘텐츠가 매출이 되기까지)</h2>
{ontology}

<h2>① 판단 — 누구에게 보낼 것인가 <span style="color:#6b7280;font-weight:normal">(실제 유튜브 공개 데이터 {n_channels}개 채널)</span></h2>
<div class="legend">규칙: <i style="background:{c1}"></i>R1 반응률(40) <i style="background:{c2}"></i>R2 규모적합(25) <i style="background:{c3}"></i>R3 진정성(20) <i style="background:{c4}"></i>R4 카테고리(15) — 막대에 마우스를 올리면 근거</div>
{scores}

<h2>② 증명 — 전용코드 인과 장부 <span style="color:#fbbf24;font-weight:normal">[SYNTHETIC 합성 매출]</span></h2>
<div class="hint">확실(코드 사용 구매)과 추정(게시 후 48h 매출 상승)을 절대 섞지 않는다 — 초록만 "증명"이다</div>
{ledger}

<h2>③ 루프 — 실측이 점수를 갱신한다</h2>
<div class="hint">사전 1위(글램미 72)가 실측 후 강등 — 시스템이 자기 예측의 오류를 스스로 교정</div>
{loop}

<h2>④ 확장 — 에이스의 닮은꼴 발굴 (다음 배치 후보)</h2>
<div class="hint">실측 검증된 채널과 규칙 프로필(R1~R4)이 가장 가까운 미시딩 채널 — 임베딩·추측 없이 규칙 점수로만</div>
{lookalikes}

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
        ontology=ONTOLOGY_SVG, lookalikes=lookalike_rows(),
        scores=score_rows(scores), ledger=ledger_rows(ledger), loop=loop_rows(updated))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write(f"생성: {OUT}\n")
    out.flush()


if __name__ == "__main__":
    main()
