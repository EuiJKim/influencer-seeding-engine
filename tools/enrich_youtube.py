#!/usr/bin/env python3
"""youtube-mentions.csv에서 브랜드 직접 언급 영상만 골라 상세 지표를 보강 수집.

수집 필드: 구독자 수(channel_follower_count), 좋아요, 댓글 수, 게시일
→ 점수화(score_influencers.py)의 입력이 된다.

사용법: python tools/enrich_youtube.py
출력: data/youtube-enriched.csv (UTF-8)
"""
import csv
import io
import sys

from yt_dlp import YoutubeDL

SRC = "data/youtube-mentions.csv"
OUT = "data/youtube-enriched.csv"


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    src, out_csv, mode_all, cap = SRC, OUT, False, 20
    for a in args:
        if a.startswith("--src="):
            src = a[len("--src="):]
        elif a.startswith("--out="):
            out_csv = a[len("--out="):]
        elif a == "--all":
            mode_all = True  # 후보 풀 모드: 브랜드 필터 없이 전체 (채널 dedupe + 캡)
    with open(src, encoding="utf-8-sig") as fh:
        rows_in = list(csv.DictReader(fh))
    targets = rows_in if mode_all else [r for r in rows_in if r["brand_in_title"] == "True"]
    # 채널 기준 중복 제거(대표 영상 = 조회수 최대), 조회수 상위 cap개로 제한
    by_ch = {}
    for r in targets:
        k = r["channel"]
        if k not in by_ch or int(r["views"] or 0) > int(by_ch[k]["views"] or 0):
            by_ch[k] = r
    uniq = sorted(by_ch.values(), key=lambda r: -int(r["views"] or 0))[:cap]
    out.write(f"보강 대상: {len(uniq)}개 영상 (src={src}, all={mode_all})\n")

    rows = []
    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        for r in uniq:
            try:
                info = ydl.extract_info(r["url"], download=False)
            except Exception as e:
                out.write(f"  skip {r['url']}: {str(e)[:60]}\n")
                continue
            rows.append({
                "channel": info.get("channel") or r["channel"],
                "channel_url": info.get("channel_url") or "",
                "subscribers": info.get("channel_follower_count") or "",
                "title": info.get("title") or r["title"],
                "views": info.get("view_count") or 0,
                "likes": info.get("like_count") or 0,
                "comments": info.get("comment_count") or 0,
                "upload_date": info.get("upload_date") or "",
                "duration": info.get("duration") or "",
                "url": r["url"],
            })
            out.write(f"  ok {rows[-1]['channel'][:20]:20} subs:{rows[-1]['subscribers']}\n")
            out.flush()

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    out.write(f"저장: {out_csv} ({len(rows)}건)\n")
    out.flush()


if __name__ == "__main__":
    main()
