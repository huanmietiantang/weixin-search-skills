---
name: weixin-resolve-url
description: |
  将搜狗微信跳转链接解析为真实的 mp.weixin.qq.com 文章链接。Use when the user has a Sogou WeChat
  redirect link and needs the actual WeChat article URL, typically after using /weixin-search.
argument-hint: [搜狗链接]
arguments:
  - sogou_url
allowed-tools:
  - Bash
  - PowerShell
disable-model-invocation: false
---

# 解析搜狗微信链接

将搜狗微信搜索结果中的跳转链接解析为真实的 mp.weixin.qq.com 文章链接。

## 使用方式

确定项目根目录（`$CLAUDE_SKILL_DIR` 的上两级，即 `.claude/skills/weixin-resolve-url/` → 项目根）。

**Windows：**
```powershell
<项目根>\.venv\Scripts\python.exe <项目根>\scripts\resolve_url.py "$sogou_url"
```

**macOS / Linux：**
```bash
<项目根>/.venv/bin/python <项目根>/scripts/resolve_url.py "$sogou_url"
```

- `$sogou_url`：搜狗微信跳转链接（必填，来自 `/weixin-search` 的 `link` 字段）

## 输出格式

JSON 对象：
- `sogou_url`：输入的搜狗链接
- `real_url`：解析出的真实微信文章链接（如解析失败则为空字符串）

## 注意事项

- 每次解析消耗约 3 个请求（2 个预热 + 1 个解析）
- 解析后的链接以 `https://mp.weixin.qq.com/` 开头
- **解析成功率较低**：搜狗对跳转链接页面有独立的验证码保护（图片点选），与搜索列表页不同，即使访问频率很低也可能触发。返回空 real_url 是常见情况，不一定是访问频率的问题
- 如果返回空，可以尝试等待几分钟后重试，但不保证成功
- 对于只需标题和摘要的场景，建议跳过 URL 解析步骤
