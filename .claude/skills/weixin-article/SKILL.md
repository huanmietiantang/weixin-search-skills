---
name: weixin-article
description: |
  获取微信公众号文章的正文内容。Use when the user wants to read the full text of a WeChat article,
  given a real mp.weixin.qq.com URL (obtained from /weixin-resolve-url).
argument-hint: [文章链接] [referer]
arguments:
  - url
  - referer
allowed-tools:
  - Bash
  - PowerShell
disable-model-invocation: false
---

# 获取微信公众号文章正文

获取微信公众号文章的纯文本正文内容。

## 使用方式

确定项目根目录（`$CLAUDE_SKILL_DIR` 的上两级，即 `.claude/skills/weixin-article/` → 项目根）。

**Windows：**
```powershell
<项目根>\.venv\Scripts\python.exe <项目根>\scripts\get_content.py "$url" --referer "$referer"
```

**macOS / Linux：**
```bash
<项目根>/.venv/bin/python <项目根>/scripts/get_content.py "$url" --referer "$referer"
```

- `$url`：真实微信公众号文章链接（必填，`https://mp.weixin.qq.com/...` 格式）
- `$referer`：来源链接（可选，传入搜狗跳转链接可提高成功率）

如果用户没有提供 referer，省略 `--referer` 参数。

## 输出格式

JSON 对象：
- `url`：输入的文章链接
- `content`：文章纯文本内容（段落用换行分隔）

## 典型工作流

1. `/weixin-search AI CAD` → 获取搜索结果
2. `/weixin-resolve-url <sogou_link>` → 解析真实 URL
3. `/weixin-article <real_url>` → 获取正文

## 注意事项

- 此步骤直接请求 mp.weixin.qq.com，不经过搜狗，不受搜狗访问限制
- **前置依赖**：需要先通过 `/weixin-resolve-url` 获取真实链接。由于搜狗跳转页面有独立的验证码保护，URL 解析成功率较低，因此本功能的可用性依赖于 resolve 步骤是否成功
- 如果用户已经有 `mp.weixin.qq.com` 开头的真实链接（如从微信客户端复制），可以直接使用本功能，无需 resolve 步骤
- 提取的是纯文本，不包含图片和格式
- 部分文章可能因微信自身限制而无法获取
