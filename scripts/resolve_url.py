"""CLI: 将搜狗微信链接解析为真实 mp.weixin.qq.com URL"""
import sys
import os
import json
import argparse
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weixin_search import get_real_url_from_sogou


def main():
    parser = argparse.ArgumentParser(description="解析搜狗微信链接为真实URL")
    parser.add_argument("sogou_url", help="搜狗微信链接")
    args = parser.parse_args()

    real_url = get_real_url_from_sogou(args.sogou_url)

    print(json.dumps({"sogou_url": args.sogou_url, "real_url": real_url}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
