#!/usr/bin/env python3
"""유튜브에서 브랜드 언급 영상(기존 시딩/리뷰 흔적)을 수집해 CSV로 저장.

사용법 (본선 현장에서 브랜드/키워드만 바꿔 재실행):
    python tools/collect_youtube.py "메디테라피" "메디테라피 선크림"

출력: data/youtube-mentions.csv (검색어별 상위 N개, UTF-8)
컬럼: query, title, channel, channel_url, views, duration, url, brand_in_title
"""
import csv
import sys
import io

from yt_dlp import YoutubeDL

N_PER_QUERY = 20
OUT = "data/youtube-mentions.csv"


def collect(queries, brand=None):
    brand = brand or queries[0].split()[0]
    rows = []
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with YoutubeDL(opts) as ydl:
        for q in queries:
            info = ydl.extract_info(f"ytsearch{N_PER_QUERY}:{q}", download=False)
            for e in info.get("entries", []):
                title = e.get("title") or ""
                rows.append({
                    "query": q,
                    "title": title,
                    "channel": e.get("channel") or "",
                    "channel_url": e.get("channel_url") or "",
                    "views": e.get("view_count") or 0,
                    "duration": e.get("duration") or "",
                    "url": e.get("url") or "",
                    "brand_in_title": brand.replace(" ", "") in title.replace(" ", ""),
                })
    return rows


def main():
    args = sys.argv[1:]
    out_path = OUT
    if args and args[0].startswith("--out="):
        out_path = args.pop(0)[len("--out="):]
    queries = args or ["메디테라피"]
    rows = collect(queries)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    hits = [r for r in rows if r["brand_in_title"]]
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write(f"수집 {len(rows)}건 -> {out_path}\n")
    out.write(f"제목에 브랜드 직접 언급: {len(hits)}건\n")
    for r in sorted(hits, key=lambda r: -int(r["views"] or 0))[:10]:
        out.write(f"  {r['views']:>9} views | {r['channel']} | {r['title'][:60]}\n")
    out.flush()


if __name__ == "__main__":
    main()
