#!/usr/bin/env python3
"""시딩 엔진 원커맨드 데모 — 심사 시연용 (상태 0→6 전체).

    python tools/run_demo.py

순서: 검증(셀프테스트 13종) → 상태 0→1 점수화(실데이터) → 상태 2→6 루프(합성).
수집 단계(상태 0, 유튜브 크롤)는 네트워크가 느려 사전 실행해둔 CSV를 사용하며,
재수집은 `python tools/collect_youtube.py "<브랜드>"` + `enrich_youtube.py`.
"""
import io
import os
import subprocess
import sys

PY = sys.executable
# 어느 폴더에서 실행해도 동작: 이 파일 위치 기준으로 프로젝트 루트로 이동
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def say(title):
    print()
    print("=" * 74)
    print(f"  {title}")
    print("=" * 74)


def run(args):
    # stderr를 stdout에 합쳐 캡처: 어떤 환경에서든 에러 원문이 그대로 화면에 보인다
    r = subprocess.run([PY] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    print(r.stdout or "", end="")
    if r.returncode != 0:
        sys.exit(f"데모 중단: {' '.join(args)} 실패 (원인은 위 출력 참조)")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    say("0. 신뢰부터 — 엔진 셀프테스트 (판정 로직이 맞다는 증명)")
    run(["tools/score_influencers.py", "selftest"])
    run(["tools/simulate_loop.py", "selftest"])
    run(["tools/find_lookalikes.py", "selftest"])

    say("1. 판단 — 누구에게 보낼 것인가 (카테고리 검색 후보 풀 20개 채널, 규칙 R1~R4)")
    print("데이터: 유튜브 공개 지표 실수집 (data/youtube-enriched-candidates.csv) · 브랜드 언급 풀은 docs/03 참고")
    run(["tools/score_influencers.py"])

    say("2. 증명과 루프 — 시딩→매출→인과 장부→점수 갱신 ([SYNTHETIC] 합성 매출)")
    run(["tools/simulate_loop.py"])

    say("3. 확장 — 에이스의 닮은꼴 발굴 (다음 배치 후보)")
    run(["tools/find_lookalikes.py"])

    say("4. 대시보드 — 심사용 한 장 (dashboard.html 생성 + 브라우저 오픈)")
    run(["tools/build_dashboard.py"])
    import os
    import webbrowser
    webbrowser.open("file://" + os.path.abspath("dashboard.html"))
    print("브라우저에서 dashboard.html 열림 (오프라인 동작, CDN 없음)")

    say("요약 — 대표의 AX 정의에 대한 응답")
    print("""\
  ① 판단을 시스템이:   규칙 R1~R4가 감이 아닌 근거로 5명을 선정 (출처 있는 룰팩)
  ② 매출로 증명:       전용코드=확실, 시간창=추정 — 두 칸을 절대 섞지 않는 인과 장부
  ③ 루프로 똑똑해짐:   사전 1위가 실측 후 강등, 실제 에이스가 승격 — 예측 오류 자가 교정
  한계도 명시:          단일 라운드는 근접 채널 구분 불가 → 반복할수록 해상도 상승""")


if __name__ == "__main__":
    main()
