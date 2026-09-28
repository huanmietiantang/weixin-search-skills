"""CLI: 获取微信公众号文章正文内容"""
import sys
import os
import json
import argparse
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weixin_search import get_article_content


def main():
    parser = argparse.ArgumentParser(description="获取微信公众号文章正文")
    parser.add_argument("url", help="真实微信公众号文章链接")
    parser.add_argument("--referer", default=None, help="请求来源（可选）")
    args = parser.parse_args()

    content = get_article_content(args.url, args.referer)

    print(json.dumps({"url": args.url, "content": content}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
