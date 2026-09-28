"""CLI: 搜索搜狗微信公众号文章（多页）"""
import sys
import os
import json
import argparse
import re
import datetime
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weixin_search import sogou_weixin_search_all


def parse_timestamp(raw: str) -> str:
    m = re.search(r"timeConvert\('(\d+)'\)", raw)
    if m:
        return datetime.datetime.fromtimestamp(int(m.group(1))).strftime('%Y-%m-%d %H:%M')
    return raw


def main():
    parser = argparse.ArgumentParser(description="搜索搜狗微信公众号文章（多页）")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--max-pages", type=int, default=10, help="最大页数，默认10")
    args = parser.parse_args()

    results = sogou_weixin_search_all(args.query, max_pages=args.max_pages)

    for r in results:
        r['publish_time'] = parse_timestamp(r['publish_time'])

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
