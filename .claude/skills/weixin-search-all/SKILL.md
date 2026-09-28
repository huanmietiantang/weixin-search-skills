---
name: weixin-search-all
description: |
  搜索搜狗微信公众号文章（多页翻页）。Use when the user wants comprehensive WeChat article search
  across multiple pages, or wants all results for a topic. Auto-paginates with polite request intervals.
argument-hint: [关键词] [最大页数]
arguments:
  - query
  - max_pages
allowed-tools:
  - Bash
  - PowerShell
  - Read
disable-model-invocation: false
---

# 搜索微信公众号文章（多页）

通过搜狗微信搜索获取多页微信公众号文章，自动翻页。

## 使用方式

确定项目根目录（`$CLAUDE_SKILL_DIR` 的上两级，即 `.claude/skills/weixin-search-all/` → 项目根）。

**Windows：**
```powershell
<项目根>\.venv\Scripts\python.exe <项目根>\scripts\search_all.py "$query" --max-pages $max_pages
```

**macOS / Linux：**
```bash
<项目根>/.venv/bin/python <项目根>/scripts/search_all.py "$query" --max-pages $max_pages
```

- `$query`：搜索关键词（必填）
- `$max_pages`：最大页数（可选，默认 10，每页约 10 条）

如果用户没有指定页数，省略 `--max-pages` 参数。

## 输出格式

同 `/weixin-search`，JSON 数组包含所有页的结果。每条包含 `title`、`account`（公众号名称）、`summary`（摘要）、`link`、`real_url`、`publish_time`、`page` 字段。

## 注意事项

- 每页之间间隔 5 秒控制访问频率，多页搜索会比较慢（10 页约需 1 分钟）
- 遇到空结果会自动停止翻页
- 建议 max_pages 不超过 3，以降低触发访问限制的风险
- 如果中途触发访问限制，已获取的结果仍会返回
