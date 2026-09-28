import time
from typing import Annotated, Dict, List, Optional

from lxml import html
from loguru import logger
from urllib.parse import quote

from http_client import sogou_session, _is_antispider_response

REQUEST_TIMEOUT = 15
PAGE_INTERVAL = 5.0


def sogou_weixin_search(
    query: Annotated[str, "搜索关键词"],
    page: int = 1,
    strict: bool = False,
    resolve_urls: bool = False,
) -> List[Dict[str, str]]:
    """在搜狗微信搜索中搜索指定关键词并返回结果列表

    Args:
        query: 搜索关键词
        page: 页码，默认1
        strict: 严格模式，遇到错误抛异常而非返回空列表
        resolve_urls: 是否自动解析真实URL，默认False以减少请求数
    """
    params = {
        'type': '2',
        's_from': 'input',
        'query': query,
        'ie': 'utf8',
        'page': page,
        '_sug_': 'n',
        '_sug_type_': '',
    }

    try:
        response = sogou_session.get_with_retry(
            'https://weixin.sogou.com/weixin',
            params=params,
            headers={'Referer': f'https://weixin.sogou.com/weixin?query={quote(query)}'},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            if strict:
                raise RuntimeError(f"搜狗微信搜索返回异常状态码: {response.status_code}")
            return []

        if _is_antispider_response(response):
            if strict:
                raise RuntimeError("搜狗微信触发访问验证，分页搜索已中止")
            return []

        tree = html.fromstring(response.text)
        results = []

        items = tree.xpath("//li[contains(@id, 'sogou_vr_11002601_box_')]")

        for item in items:
            title_elem = item.xpath(".//a[contains(@id, 'sogou_vr_11002601_title_')]")
            if not title_elem:
                continue
            title = title_elem[0].text_content().strip()
            link = title_elem[0].get('href')
            if link and not link.startswith('http'):
                link = 'https://weixin.sogou.com' + link

            time_elems = item.xpath(".//div[@class='s-p']/span[@class='s2']")
            publish_time = time_elems[0].text_content().strip() if time_elems else ""

            account_elems = item.xpath(".//div[@class='s-p']/span[@class='all-time-y2']")
            account = account_elems[0].text_content().strip() if account_elems else ""

            summary_elems = item.xpath(".//p[@class='txt-info']")
            summary = summary_elems[0].text_content().strip() if summary_elems else ""

            real_url = ""
            if resolve_urls:
                try:
                    real_url = get_real_url_from_sogou(link)
                except Exception:
                    pass

            results.append({
                'title': title,
                'account': account,
                'summary': summary,
                'link': link,
                'real_url': real_url,
                'publish_time': publish_time,
                'page': str(page),
            })

        return results
    except requests.RequestException as e:
        if strict:
            raise RuntimeError(f"请求搜狗微信搜索失败: {str(e)}") from e
        return []
    except Exception as e:
        if strict:
            raise RuntimeError(f"解析搜狗微信搜索结果失败: {str(e)}") from e
        return []


def sogou_weixin_search_all(query: str, max_pages: int = 10) -> List[Dict[str, str]]:
    """搜索所有页面的结果，自动翻页直到无结果或达到 max_pages"""
    all_results = []
    for page in range(1, max_pages + 1):
        results = sogou_weixin_search(query, page=page, strict=True)
        if not results:
            break
        all_results.extend(results)
        if page < max_pages:
            time.sleep(PAGE_INTERVAL)

    return all_results


def get_real_url_from_sogou(sogou_url: str) -> str:
    """从搜狗微信链接获取真实的微信公众号文章链接"""
    try:
        response = sogou_session.get_with_retry(sogou_url, timeout=REQUEST_TIMEOUT)

        if _is_antispider_response(response):
            return ""

        script_content = response.text
        start_index = script_content.find("url += '") + len("url += '")
        url_parts = []
        while True:
            part_start = script_content.find("url += '", start_index)
            if part_start == -1:
                break
            part_end = script_content.find("'", part_start + len("url += '"))
            part = script_content[part_start + len("url += '"):part_end]
            url_parts.append(part)
            start_index = part_end + 1

        full_url = ''.join(url_parts).replace("@", "")
        if not full_url:
            return ""
        return "https://mp." + full_url
    except Exception:
        return ""


def get_real_url(sogou_url: Annotated[str, "搜狗微信链接,来自于sogou_weixin_search工具结果"]) -> str:
    """从搜狗微信链接获取真实的微信公众号文章链接"""
    return get_real_url_from_sogou(sogou_url)


def get_article_content(real_url: Annotated[str, "真实微信公众号文章链接"], referer: Annotated[Optional[str], "请求来源,get_real_url的返回值"]) -> str:
    """获取微信公众号文章的正文内容"""
    import requests as _requests

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': sogou_session.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    if referer:
        headers['referer'] = referer

    try:
        if not real_url or real_url == "https://mp.":
            return "获取文章内容失败: 未拿到有效的微信公众号文章链接"

        response = _requests.get(real_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        tree = html.fromstring(response.text)
        content_elements = tree.xpath("//div[@id='js_content']//text()")
        cleaned_content = [text.strip() for text in content_elements if text.strip()]
        main_content = '\n'.join(cleaned_content)
        return main_content
    except Exception as e:
        return f"获取文章内容失败: {str(e)}"


# keep requests import available for the except clause in sogou_weixin_search
import requests


if __name__ == '__main__':
    results = sogou_weixin_search("吉利汽车", resolve_urls=True)
    for r in results[:2]:
        print(r['title'], r['real_url'])
