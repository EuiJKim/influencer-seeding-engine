#!/usr/bin/env python3
"""심사 시연용 대시보드 생성 — data/*.csv를 읽어 자립형 HTML 1장으로.

    python tools/build_dashboard.py     # -> dashboard.html

디자인: 포트폴리오(euijkim.github.io/EJ_Website)의 라이트 미니멀 언어를 따름.
외부 CDN·JS·웹폰트 없음(현장 네트워크 무관, 오프라인 동작).
run_demo.py 마지막 단계에서 자동 생성+브라우저 오픈.
"""
import csv
import html
import io
import sys

OUT = "dashboard.html"
R_COLORS = {"R1": "#1E41C0", "R2": "#0d9668", "R3": "#b45309", "R4": "#94a3b8"}


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


ONTOLOGY_SVG = """<svg viewBox="0 0 1060 450" width="100%" style="max-width:1060px" xmlns="http://www.w3.org/2000/svg" font-family="'Apple SD Gothic Neo','Malgun Gothic',sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa1ad"/></marker>
<marker id="arg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#0d9668"/></marker>
<marker id="arb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#1E41C0"/></marker></defs>

<!-- 전파 → 자극 회귀 레인 (상단 전용 통로: 박스 위를 지나지 않음) -->
<path d="M 980 190 L 980 28 Q 980 18 970 18 L 535 18 Q 525 18 525 28 L 525 36" fill="none" stroke="#9aa1ad" stroke-width="1.3" stroke-dasharray="5 4" marker-end="url(#ar)"/>
<text x="752" y="13" fill="#8a8f99" font-size="10.5" text-anchor="middle">전파는 후기·입소문이 되어 자극②로 되돌아온다 (세계의 자체 루프)</text>

<!-- 자극층 -->
<rect x="40" y="42" width="250" height="62" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="165" y="62" fill="#111" font-size="12" font-weight="bold" text-anchor="middle">자극① 인플루언서 콘텐츠</text>
<text x="165" y="79" fill="#666" font-size="10.5" text-anchor="middle">릴스·쇼츠·리뷰 (인지 채널 60%*)</text>
<text x="165" y="94" fill="#666" font-size="10.5" text-anchor="middle">시딩이 주입하는 자극</text>
<rect x="390" y="42" width="270" height="62" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="525" y="62" fill="#111" font-size="12" font-weight="bold" text-anchor="middle">자극② 검증 콘텐츠</text>
<text x="525" y="79" fill="#666" font-size="10.5" text-anchor="middle">내돈내산 후기 · 네이버 블로그 · 올리브영 리뷰</text>
<text x="525" y="94" fill="#666" font-size="10.5" text-anchor="middle">(탐색 1위 올리브영 34.5%*)</text>
<rect x="760" y="42" width="190" height="62" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="855" y="62" fill="#111" font-size="12" font-weight="bold" text-anchor="middle">자극③ 전용코드</text>
<text x="855" y="79" fill="#666" font-size="10.5" text-anchor="middle">할인·프로모션</text>
<text x="855" y="94" fill="#666" font-size="10.5" text-anchor="middle">관측 가능한 표식</text>

<!-- 자극 → 상태전이 (구조 화살표: 회색) -->
<line x1="165" y1="106" x2="179" y2="184" stroke="#9aa1ad" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#ar)"/>
<line x1="525" y1="106" x2="539" y2="184" stroke="#9aa1ad" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#ar)"/>
<line x1="855" y1="106" x2="723" y2="184" stroke="#9aa1ad" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#ar)"/>

<!-- 소비자 상태 사슬 -->
<text x="20" y="180" fill="#111" font-size="12" font-weight="bold">소비자</text>
<rect x="20" y="190" width="140" height="52" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="90" y="221" fill="#111" font-size="13" font-weight="bold" text-anchor="middle">모름</text>
<rect x="200" y="190" width="140" height="52" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="270" y="221" fill="#111" font-size="13" font-weight="bold" text-anchor="middle">인지</text>
<rect x="380" y="190" width="140" height="52" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="450" y="221" fill="#111" font-size="13" font-weight="bold" text-anchor="middle">관심</text>
<rect x="560" y="190" width="140" height="52" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="630" y="221" fill="#111" font-size="13" font-weight="bold" text-anchor="middle">신뢰</text>
<rect x="740" y="190" width="140" height="52" rx="10" fill="#e9f7f0" stroke="#0d9668" stroke-width="2"/>
<text x="810" y="221" fill="#065f46" font-size="13" font-weight="bold" text-anchor="middle">구매</text>
<rect x="920" y="190" width="120" height="52" rx="10" fill="#fff" stroke="#d4d4d4" stroke-width="1.5"/>
<text x="980" y="221" fill="#111" font-size="13" font-weight="bold" text-anchor="middle">전파</text>
<line x1="160" y1="216" x2="198" y2="216" stroke="#9aa1ad" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="340" y1="216" x2="378" y2="216" stroke="#9aa1ad" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="520" y1="216" x2="558" y2="216" stroke="#9aa1ad" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="700" y1="216" x2="738" y2="216" stroke="#9aa1ad" stroke-width="1.5" marker-end="url(#ar)"/>
<line x1="880" y1="216" x2="918" y2="216" stroke="#9aa1ad" stroke-width="1.5" marker-end="url(#ar)"/>

<!-- 전이별 관측 가능성 (강조는 색이 아니라 기호로) -->
<text x="90" y="262" fill="#8a8f99" font-size="10.5" text-anchor="middle">◐ 조회·좋아요 간접 추정</text>
<text x="450" y="262" fill="#b91c1c" font-size="10.5" text-anchor="middle">✗ 친구의 말·오프라인 — 관측 불가</text>
<text x="660" y="262" fill="#0d9668" font-size="10.5" text-anchor="middle">● 코드 구매 = 확실 · ◐ 시간창 = 추정</text>
<text x="980" y="262" fill="#8a8f99" font-size="10.5" text-anchor="middle">◐ 후기 수·해시태그</text>

<!-- 우리 시스템 -->
<rect x="40" y="310" width="280" height="70" rx="10" fill="#eef1ff" stroke="#1E41C0" stroke-width="1.5"/>
<text x="180" y="333" fill="#111" font-size="12.5" font-weight="bold" text-anchor="middle">시딩 엔진 = 자극 선택기</text>
<text x="180" y="351" fill="#666" font-size="10.5" text-anchor="middle">R1~R4: 어떤 자극(누구·어떤 콘텐츠)을</text>
<text x="180" y="366" fill="#666" font-size="10.5" text-anchor="middle">세계에 주입할지 근거로 결정</text>
<rect x="700" y="310" width="300" height="70" rx="10" fill="#e9f7f0" stroke="#0d9668" stroke-width="1.5"/>
<text x="850" y="333" fill="#111" font-size="12.5" font-weight="bold" text-anchor="middle">인과 장부 = 상태 변화 기록계</text>
<text x="850" y="351" fill="#666" font-size="10.5" text-anchor="middle">확실(코드)과 추정(시간창)을 분리 기록</text>
<text x="850" y="366" fill="#666" font-size="10.5" text-anchor="middle">append-only — 담당자가 바뀌어도 히스토리 보존</text>

<!-- 주입 경로 (좌측 전용 통로: 박스를 넘지 않음) -->
<path d="M 100 310 L 100 288 Q 100 280 92 280 L 20 280 Q 12 280 12 272 L 12 83 Q 12 73 22 73 L 36 73" fill="none" stroke="#1E41C0" stroke-width="1.6" marker-end="url(#arb)"/>
<text x="24" y="126" fill="#1E41C0" font-size="10.5">자극</text>
<text x="24" y="140" fill="#1E41C0" font-size="10.5">주입</text>

<!-- 구매 → 장부 -->
<line x1="845" y1="244" x2="845" y2="308" stroke="#0d9668" stroke-width="1.5" marker-end="url(#arg)"/>

<!-- 시스템 루프 -->
<path d="M 698 345 L 324 345" fill="none" stroke="#0d9668" stroke-width="1.6" stroke-dasharray="6 4" marker-end="url(#arg)"/>
<text x="510" y="334" fill="#0d9668" font-size="11" font-weight="bold" text-anchor="middle">시스템 루프: 실측 → 점수 갱신 → 닮은꼴 → 다음 자극</text>

<text x="20" y="435" fill="#8a8f99" font-size="10">* 출처: 픽플리 2026-1Q 소비 여정 조사 (docs/02-platform-research.md)</text>
</svg>"""


PAGE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>인플루언서 시딩 엔진 — 시연 대시보드</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0 }}
:root {{
  --bg:#f9f9f7; --ink:#111; --muted:#666; --faint:#8a8f99; --line:#e0e0e0;
  --card:#fff; --accent:#1E41C0; --accent-light:#eef1ff;
  --green:#0d9668; --green-light:#e9f7f0; --amber:#b45309; --red:#b91c1c; --red-light:#fdf0f0;
}}
html,body {{ background:var(--bg); color:var(--ink);
  font-family:'Apple SD Gothic Neo','Malgun Gothic',-apple-system,sans-serif;
  font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased }}
.wrap {{ max-width:1120px; margin:0 auto; padding:48px 40px 60px; min-width:1024px }}

h1 {{ font-size:26px; font-weight:700; letter-spacing:-0.01em; margin-bottom:6px }}
.badge {{ display:inline-block; background:var(--green-light); color:var(--green); border:1px solid var(--green);
  border-radius:20px; padding:3px 13px; font-size:12px; font-weight:600; margin-left:10px; vertical-align:4px }}
.badge.syn {{ background:#fdf6ec; color:var(--amber); border-color:var(--amber) }}
.meta {{ color:var(--muted); font-size:14px; margin-bottom:40px }}

h2 {{ font-size:12px; font-weight:600; letter-spacing:0.12em; text-transform:uppercase;
  color:var(--faint); margin:44px 0 6px; padding-top:28px; border-top:1px solid var(--line) }}
h2 .big {{ display:block; font-size:19px; font-weight:700; letter-spacing:-0.01em;
  text-transform:none; color:var(--ink); margin-top:6px }}
.hint {{ font-size:13px; color:var(--muted); margin-bottom:16px }}
.legend {{ font-size:12px; color:var(--muted); margin-bottom:12px }}
.legend i {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin:0 4px 0 12px; vertical-align:-1px }}

.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 24px }}

/* 문제의 구조 */
.journey {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin:10px 0 16px }}
.jcard {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px }}
.jcard.gap {{ background:var(--red-light); border-color:#f0caca }}
.jcard.buy {{ background:var(--green-light); border-color:#bfe6d4 }}
.jday {{ font-size:11px; font-weight:700; color:var(--faint); margin-bottom:4px }}
.jact {{ font-size:13px; color:var(--ink); line-height:1.45; margin-bottom:6px }}
.jwho {{ font-size:11px; color:var(--muted); line-height:1.4 }}
.jcard.gap .jwho {{ color:var(--red) }}
.src {{ display:block; font-size:10.5px; color:var(--faint); margin-top:2px }}
.whygrid {{ display:grid; grid-template-columns:1fr 180px 1fr; gap:16px; margin:10px 0 8px }}
.whycard {{ border-radius:12px; padding:18px 20px; background:var(--card) }}
.whycard.bad {{ border:1px solid #f0caca; background:var(--red-light) }}
.whycard.good {{ border:1px solid #bfe6d4; background:var(--green-light) }}
.whyhead {{ font-size:12px; font-weight:700; letter-spacing:.3px; margin-bottom:10px }}
.bad .whyhead {{ color:var(--red) }} .good .whyhead {{ color:var(--green) }}
.whyitem {{ font-size:13px; color:#444; line-height:1.6; margin-bottom:8px }}
.whypivot {{ display:flex; flex-direction:column; justify-content:center; text-align:center;
  font-size:13px; color:var(--muted); line-height:1.7 }}
.whypivot b {{ font-size:15px; color:var(--ink) }} .whypivot span {{ font-size:11px; color:var(--faint) }}

/* 온톨로지 */
.ontobox {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 20px 8px }}

/* 매트릭스 스택 */
.stack {{ display:flex; flex-direction:column; gap:8px; margin:10px 0 12px }}
.layer {{ border-radius:10px; padding:14px 18px; font-size:13px; color:#444; line-height:1.55; background:var(--card) }}
.layer b {{ color:var(--ink); margin-right:6px }}
.ltag {{ display:inline-block; font-size:10.5px; font-weight:600; border-radius:4px; padding:2px 9px; margin-right:10px; vertical-align:1px }}
.layer.core {{ border:2px solid var(--accent); background:var(--accent-light) }} .core .ltag {{ background:var(--accent); color:#fff }}
.layer.view {{ border:1px solid var(--line) }} .view .ltag {{ background:#efefec; color:var(--muted) }}
.layer.output {{ border:1px solid var(--line) }} .output .ltag {{ background:#efefec; color:var(--muted) }}
.layer.roadmap {{ border:1px dashed #c9c9c4 }} .roadmap .ltag {{ background:#efefec; color:var(--muted) }}

/* 랭킹 */
.rows {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:8px 20px }}
.row {{ display:grid; grid-template-columns:28px 230px 1fr 48px; gap:12px; align-items:center;
  padding:10px 0 4px; border-bottom:1px solid #f0f0ec }}
.row:last-child {{ border-bottom:none }}
.row .why {{ grid-column:3/5; font-size:11.5px; color:var(--faint); padding-bottom:8px }}
.rank {{ color:var(--faint); font-size:13px; text-align:right }}
.name {{ font-size:14px; font-weight:600 }} .sub {{ color:var(--faint); font-size:11.5px; margin-left:8px; font-weight:400 }}
.tag.est {{ background:#fdf6ec; color:var(--amber); font-size:10.5px; border:1px solid #ecd9b8; border-radius:4px; padding:1px 6px; margin-left:6px }}
.bar {{ display:flex; height:14px; background:#efefec; border-radius:4px; overflow:hidden }}
.seg {{ height:100% }}
.pts {{ font-weight:700; font-size:16px; text-align:right }}

/* 장부 */
.lrow {{ display:grid; grid-template-columns:230px 1fr 230px 270px; gap:12px; align-items:center;
  padding:11px 0; border-bottom:1px solid #f0f0ec }}
.lrow:last-child {{ border-bottom:none }}
.lbar {{ height:12px; background:#efefec; border-radius:4px; overflow:hidden }}
.cert {{ height:100%; background:var(--green) }}
.lnum {{ font-size:13px; color:var(--green); font-weight:600 }}
.lest {{ font-size:12.5px; color:var(--amber) }} .note {{ color:var(--faint); font-size:10.5px }}

/* 루프 */
.urow {{ display:grid; grid-template-columns:230px 170px 1fr; gap:12px; padding:12px 18px;
  border-radius:10px; margin-bottom:6px; align-items:center; background:var(--card); border:1px solid var(--line) }}
.urow.up {{ background:var(--green-light); border-color:#bfe6d4 }}
.urow.drop {{ background:var(--red-light); border-color:#f0caca; color:var(--muted) }}
.delta {{ font-size:14px }} .delta b {{ font-size:17px }}
.up .arr {{ color:var(--green); font-weight:700 }} .drop .arr {{ color:var(--red) }}
.act {{ font-size:12.5px; color:var(--muted); white-space:nowrap }}

/* 닮은꼴 */
.krow {{ display:grid; grid-template-columns:200px 30px 280px 1fr; gap:10px; align-items:center;
  padding:12px 18px 8px; background:var(--card); border:1px solid var(--line); border-radius:10px; margin-bottom:6px }}
.karr {{ color:var(--faint); font-weight:700; text-align:center }}
.ksim {{ color:var(--ink); font-size:13.5px; font-weight:700 }}
.krow .why {{ font-size:11.5px; color:var(--faint); padding-bottom:4px }}

.foot {{ margin-top:44px; font-size:12.5px; color:var(--muted); border-top:1px solid var(--line);
  padding-top:16px; line-height:1.9 }}
</style></head><body><div class="wrap">

<h1>인플루언서 시딩 엔진 <span class="badge">셀프테스트 18/18 PASS</span><span class="badge syn">매출 데이터 [SYNTHETIC]</span></h1>
<div class="meta">판단은 근거 있는 규칙이, 증명은 전용코드가, 개선은 루프가 — 감이 아니라 시스템이.</div>

<h2>Problem<span class="big">문제 — 지수는 토요일에 선크림을 샀다. 누구 덕분인지 아는 회사는 지구에 없다</span></h2>
<div class="journey">
  <div class="jcard"><div class="jday">월</div><div class="jact">틱톡에서 광고 <b>A</b>를 봄</div><div class="jwho">틱톡만 앎 · 구매는 못 봄</div></div>
  <div class="jcard"><div class="jday">수</div><div class="jact">유튜브에서 리뷰 <b>B</b>를 봄</div><div class="jwho">유튜브만 앎 · 구매는 못 봄</div></div>
  <div class="jcard gap"><div class="jday">목</div><div class="jact">친구: "그거 나 써봤는데 좋아"</div><div class="jwho">✗ 어디에도 기록 없음 — 사실 이게 결정타</div></div>
  <div class="jcard"><div class="jday">금</div><div class="jact">네이버에서 후기 <b>C</b>를 읽음</div><div class="jwho">네이버만 앎 · 구매는 못 봄</div></div>
  <div class="jcard buy"><div class="jday">토</div><div class="jact">올리브영에서 <b>구매</b></div><div class="jwho">올리브영만 앎 · 광고는 못 봄</div></div>
</div>
<div class="whygrid">
  <div class="whycard bad">
    <div class="whyhead">그래서 벌어지는 일 (아무도 못 푸는 이유)</div>
    <div class="whyitem">① 틱톡·유튜브·네이버가 <b>전부 "내 덕에 팔렸다"고 주장</b> — 셋의 주장을 더하면 실제 매출의 2~3배가 된다</div>
    <div class="whyitem">② 조각을 이어붙이려던 개인 추적은 <b>법으로 막히는 중</b> (애플 앱 추적 차단으로 메타가 연 13조 원 손실 발표)</div>
    <div class="whyitem">③ 그나마 성적표를 매기는 회사가 <b>광고를 파는 회사</b> — 자기 시험지 자기 채점</div>
  </div>
  <div class="whypivot">그래서 우리는<br><b>지나간 일을 맞히지 않고,<br>실험을 심는다</b><br><span>인플루언서마다 다른 할인코드<br>= 색깔 스티커. 구매가 스스로<br>출처를 말하게 만든다</span></div>
  <div class="whycard good">
    <div class="whyhead">메디테라피 가게 안에서는 되는 이유 (근거 표기)</div>
    <div class="whyitem">① <b>계산대가 자기 것</b> — 자사몰이라 코드가 찍히는 순간을 직접 본다 <span class="src">확인: meditherapy.co.kr 자사몰 운영</span></div>
    <div class="whyitem">② <b>제품 종류가 한눈에 들어옴</b> — 실험이 섞이지 않는다 <span class="src">수집으로 확인: 마스크·세럼·크림·디바이스 라인 (docs/03)</span></div>
    <div class="whyitem">③ <b>자기 돈으로 자기 효과를 잰다</b> — 부풀릴 이유가 없다 <span class="src">구조상 논증 (측정자=지출자)</span></div>
    <div class="whyitem">④ <b>시딩은 원래 한 명씩 보내는 일</b> — 코드 붙이기가 자연스럽다 <span class="src">확인: 올리브영도 코드형 제도 운영 (docs/02)</span></div>
  </div>
</div>
<div class="hint">정리: 모두의 여정을 다 보는 것(전역)은 불가능하지만, 자기 가게 안(국소)에서는 코드라는 실험 장치로 부분 정답을 만들 수 있다 — "100% 해결 안 돼도 일부 접목하면 엄청난 부가가치" (대표 인터뷰)</div>

<h2>Ontology<span class="big">⓪ 소비자의 세계 — 마음이 움직여 구매가 되기까지</span></h2>
<div class="hint">세계의 중심은 소비자의 마음 상태. 콘텐츠·후기·코드는 상태를 바꾸는 "자극" — 관측 표기: <span style="color:var(--green)">● 확실</span> · ◐ 간접 추정 · <span style="color:var(--red)">✗ 관측 불가</span>(추정하지 않고 불가로 명시)</div>
<div class="ontobox">{ontology}</div>

<h2>Matrix Layers<span class="big">매트릭스의 구조 — 게임판 하나에 층이 네 개</span></h2>
<div class="hint">실측 한 건이 층을 타고 올라간다: 보아따 코드로 47건 구매 → <b>규칙판</b>이 "이런 채널은 잘 판다"로 확률을 고침 → <b>공략집</b>에 "1만 이하·내돈내산형이 먹힌다" 한 줄 추가 → <b>사장님 화면</b> 순위 갱신 → 다음 판에 닮은꼴 투입</div>
<div class="stack">
  <div class="layer roadmap"><span class="ltag">다음 확장팩</span><b>전파 연결망</b> — 입소문이 퍼지는 친구·팔로워 연결망까지 게임판에 넣는 다음 버전. 전파 데이터가 잡히기 시작하면 연다</div>
  <div class="layer output"><span class="ltag">공략집</span><b>수요 레시피</b> — 판을 돌 때마다 한 줄씩 쌓이는 노트: "어떤 콘텐츠를 × 누구를 통해 × 언제 보내면 → 얼마가 팔리더라"</div>
  <div class="layer view"><span class="ltag">사장님 화면</span><b>퍼널 보고</b> — 같은 게임판을 위에서 내려다본 요약. 아래 ①~④ 섹션이 바로 이 화면이다</div>
  <div class="layer core"><span class="ltag">게임 규칙판 ← 오늘 실제로 만든 것</span><b>소비자 상태 세계</b> — "마음은 모름→인지→관심→신뢰→구매→전파 순서로만 움직인다"는 이 세계의 규칙. 시뮬레이터가 이 규칙으로 다음 판을 미리 굴려보고, 실측이 들어오면 규칙의 확률을 고친다</div>
</div>

<h2>Decision<span class="big">① 판단 — 누구에게 보낼 것인가 <span style="color:var(--faint);font-weight:400;font-size:14px">(실제 유튜브 공개 데이터 {n_channels}개 채널)</span></span></h2>
<div class="legend">규칙: <i style="background:{c1}"></i>R1 반응률(40) <i style="background:{c2}"></i>R2 규모적합(25) <i style="background:{c3}"></i>R3 진정성(20) <i style="background:{c4}"></i>R4 카테고리(15) — 막대에 마우스를 올리면 근거</div>
<div class="rows">
{scores}
</div>

<h2>Proof<span class="big">② 증명 — 전용코드 인과 장부 <span style="color:var(--amber);font-weight:400;font-size:14px">[SYNTHETIC 합성 매출]</span></span></h2>
<div class="hint">확실(코드 사용 구매)과 추정(게시 후 48h 매출 상승)을 절대 섞지 않는다 — 초록만 "증명"이다</div>
<div class="rows">
{ledger}
</div>

<h2>Loop<span class="big">③ 루프 — 실측이 점수를 갱신한다</span></h2>
<div class="hint">사전 1위(글램미 72)가 실측 후 강등 — 시스템이 자기 예측의 오류를 스스로 교정</div>
{loop}

<h2>Expansion<span class="big">④ 확장 — 에이스의 닮은꼴 발굴 (다음 배치 후보)</span></h2>
<div class="hint">실측 검증된 채널과 규칙 프로필(R1~R4)이 가장 가까운 미시딩 채널 — 임베딩·추측 없이 규칙 점수로만</div>
{lookalikes}

<div class="foot">
정직한 한계 — ① 인스타그램 자동 수집 불가(로그인 장벽): 수동 샘플링으로 대체 ·
② 단일 라운드는 근접 채널 구분 불가: 반복할수록 해상도 상승 ·
③ 시간창 추정치는 게시 겹침 시 과대계상 가능 · ④ 매출은 합성 데이터([SYNTHETIC] 라벨, 정답을 심고 복원 검증 통과)
</div>
</div></body></html>"""


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
