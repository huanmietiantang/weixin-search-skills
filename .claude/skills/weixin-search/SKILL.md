---
name: weixin-search
description: |
  搜索搜狗微信公众号文章。Use when the user wants to search WeChat/微信 public account articles,
  or asks about recent WeChat articles on a topic. Returns title, link, and publish time.
argument-hint: [关键词] [页码]
arguments:
  - query
  - page
allowed-tools:
  - Bash
  - PowerShell
  - Read
disable-model-invocation: false
---

# 搜索微信公众号文章

通过搜狗微信搜索获取微信公众号文章列表。

## 使用方式

确定项目根目录（`$CLAUDE_SKILL_DIR` 的上两级，即 `.claude/skills/weixin-search/` → 项目根）。

**Windows：**
```powershell
<项目根>\.venv\Scripts\python.exe <项目根>\scripts\search.py "$query" --page $page
```

**macOS / Linux：**
```bash
<项目根>/.venv/bin/python <项目根>/scripts/search.py "$query" --page $page
```

- `$query`：搜索关键词（必填）
- `$page`：页码（可选，默认 1）

如果用户没有指定页码，省略 `--page` 参数。

## 输出格式

脚本输出 JSON 数组，每个元素包含：
- `title`：文章标题
- `account`：公众号名称
- `summary`：文章摘要（搜索引擎截取的片段）
- `link`：搜狗跳转链接（非真实链接）
- `real_url`：真实微信链接（默认为空，需要用 `/weixin-resolve-url` 解析）
- `publish_time`：发布时间（格式 `YYYY-MM-DD HH:MM`）
- `page`：所在页码

## 结果展示

将搜索结果以表格形式展示给用户，包含序号、标题、公众号、发布时间。如果用户需要查看文章内容，提示可以使用 `/weixin-resolve-url` 获取真实链接，再用 `/weixin-article` 获取正文（但 URL 解析成功率较低，详见 `/weixin-resolve-url` 的注意事项）。

## 注意事项

- 每次搜索会向搜狗发送约 3 个请求（2 个预热 + 1 个搜索），内置 3 秒间隔控制访问频率
- 搜狗不支持按时间筛选，结果按相关性排序
- 如果返回空结果，可能是访问频率过高，建议等待几分钟后重试
