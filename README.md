# weixin-search-skills

**让 AI 编程助手帮你搜索微信公众号文章。** 一句话搜索、自动翻页、提取正文——全部通过自然语言完成。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![AI Agent Skills](https://img.shields.io/badge/AI_Agent-Skills-blueviolet)](#compatible-agents)
[![Dependencies](https://img.shields.io/badge/Dependencies-3-green.svg)](requirements.txt)

> WeChat article search skills for AI coding agents. Search, resolve, and extract WeChat articles using natural language — powered by Sogou WeChat Search.
>
> 微信公众号文章搜索 Skills，适用于各类 AI 编程助手。通过搜狗微信搜索实现搜索、链接解析、正文提取。

---

## Demo

```
You:    搜索最近关于大模型的微信文章
Agent:  正在搜索...

| # | 标题 | 公众号 | 发布时间 |
|---|------|--------|----------|
| 1 | 大模型应用落地的十个关键问题 | AI前线 | 2026-09-25 |
| 2 | GPT-5 发布后的行业影响分析 | 机器之心 | 2026-09-24 |
| ... | ... | ... | ... |

You:    帮我看看第一篇的全文
Agent:  正在获取文章内容...（自动解析链接 → 提取正文）
```

**不需要写代码，不需要记 API——用自然语言告诉 AI 你想搜什么。**

## Features

| Skill | 说明 |
|-------|------|
| **weixin-search** | 搜索微信文章（单页，~10 条） |
| **weixin-search-all** | 自动翻页搜索（多页） |
| **weixin-resolve-url** | 搜狗链接 → 真实微信 URL |
| **weixin-article** | 获取文章纯文本正文 |

### 为什么用 Skills 而不是直接写脚本？

| | 传统方式 | weixin-search-skills |
|---|---------|---------------------|
| **使用方式** | 写 Python 脚本 | 用自然语言告诉 AI |
| **集成方式** | 独立运行 | 嵌入 AI 工作流 |
| **速率控制** | 自己实现 | 跨进程自动协调 |
| **依赖** | 10+ 个包 | 3 个（requests + lxml + loguru） |
| **输出** | 原始 JSON | AI 自动整理为表格/报告 |

## Compatible Agents

本项目使用 **Skills** 格式（`.claude/skills/` 目录下的 SKILL.md 文件），兼容支持此格式的各类 AI 编程助手：

| Agent | 状态 | 说明 |
|-------|------|------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | ✅ 已验证 | Anthropic 官方 CLI，原生支持 Skills |
| [Cursor](https://www.cursor.com/) | ✅ 兼容 | 通过 Rules / Notepads 加载 |
| [Windsurf](https://codeium.com/windsurf) | ✅ 兼容 | 通过 Rules 加载 |
| [Cline](https://github.com/cline/cline) | ✅ 兼容 | VS Code 扩展，支持自定义指令 |
| 其他 AI Agent | 🔧 可适配 | 只需将 SKILL.md 内容作为系统指令即可 |

> Skills 本质上是结构化的 AI 指令文件。任何能读取指令并调用 Shell 的 AI agent 都可以使用本项目的核心脚本。

## Quick Start

### 1. 安装

```bash
git clone https://github.com/huanmietiantang/weixin-search-skills.git
cd weixin-search-skills

python -m venv .venv

# Windows
.\.venv\Scripts\pip install -r requirements.txt

# macOS / Linux
.venv/bin/pip install -r requirements.txt
```

### 2. 在 AI 助手中使用

在项目目录下启动你的 AI 编程助手，Skills 自动生效：

```
/weixin-search AI 大模型
/weixin-search-all 自动驾驶 3
/weixin-resolve-url https://weixin.sogou.com/link?url=...
/weixin-article https://mp.weixin.qq.com/s/...
```

**全局安装**（任意目录可用）：

```bash
# macOS / Linux
cp -r .claude/skills/weixin-* ~/.claude/skills/

# Windows PowerShell
Copy-Item -Recurse .claude\skills\weixin-* $env:USERPROFILE\.claude\skills\
```

### 3. 作为独立 CLI

所有脚本输出 JSON，可脱离 AI 助手独立使用：

```bash
# 搜索
.venv/bin/python scripts/search.py "AI 大模型"

# 多页搜索
.venv/bin/python scripts/search_all.py "AI 大模型" --max-pages 3

# 解析链接
.venv/bin/python scripts/resolve_url.py "https://weixin.sogou.com/link?url=..."

# 获取正文
.venv/bin/python scripts/get_content.py "https://mp.weixin.qq.com/s/..."
```

<details>
<summary>Windows PowerShell 命令</summary>

```powershell
.\.venv\Scripts\python.exe scripts\search.py "AI 大模型"
.\.venv\Scripts\python.exe scripts\search_all.py "AI 大模型" --max-pages 3
.\.venv\Scripts\python.exe scripts\resolve_url.py "https://weixin.sogou.com/link?url=..."
.\.venv\Scripts\python.exe scripts\get_content.py "https://mp.weixin.qq.com/s/..."
```

</details>

## Workflow

```
搜索 → 解析链接 → 获取正文
```

1. **搜索** — 获取搜索结果（标题 + 摘要 + 公众号 + 时间）
2. **解析链接** — 将搜狗链接解析为真实微信 URL
3. **获取正文** — 提取文章纯文本内容

> **提示**：对于日报生成、资讯监控等只需标题和摘要的场景，第 1 步就够了——无需后续步骤。

## Polite Request Strategy

内置 6 项措施，确保礼貌、合规地访问：

| 措施 | 说明 |
|------|------|
| **跨进程速率协调** | 文件锁 + 共享状态，所有进程排队，避免并发 |
| Session 复用 | 自动管理 Cookie 和会话 |
| 随机 User-Agent | 10 个真实浏览器 UA 随机轮换 |
| 请求限速 | 最少间隔 3s，翻页间隔 5s |
| 指数退避重试 | 3 次重试，退避 3s → 6s → 12s |
| 搜索与解析解耦 | 默认搜索仅 1 次请求（非 N+1） |

**跨进程安全**：即使同时发起多个查询，`GlobalRateLimiter` 通过文件锁将请求串行化（间隔 ≥3s，2 分钟窗口最多 20 次）。

## Project Structure

```
weixin-search-skills/
├── .claude/skills/          # AI Agent Skills 定义
│   ├── weixin-search/       # 单页搜索
│   ├── weixin-search-all/   # 多页搜索
│   ├── weixin-resolve-url/  # URL 解析
│   └── weixin-article/      # 文章正文
├── scripts/                 # Python 核心逻辑 + CLI
│   ├── http_client.py       # SogouSession + GlobalRateLimiter
│   ├── weixin_search.py     # 搜索/解析/提取
│   ├── search.py            # CLI: 单页搜索
│   ├── search_all.py        # CLI: 多页搜索
│   ├── resolve_url.py       # CLI: URL 解析
│   └── get_content.py       # CLI: 文章内容
├── tests/                   # 单元测试
├── requirements.txt         # 仅 3 个依赖
├── CLAUDE.md                # Claude Code 项目指令
└── LICENSE                  # MIT
```

## Known Limitations

- **搜狗不支持按时间筛选**，结果按相关性排序。需要最近文章时，可搜索后按 `publish_time` 过滤
- **URL 解析成功率较低**：搜狗跳转页面有独立的验证码保护，即使低频访问也可能触发
- **纯文本提取**：文章正文不含图片和格式

## Disclaimer / 免责声明

本项目仅供学习和研究目的使用。使用者应遵守相关法律法规及目标网站的服务条款。

- 本工具不存储、不分发任何文章内容
- 使用者应自行承担使用本工具产生的任何法律责任
- 如目标网站认为本项目侵犯其权益，请通过 Issue 联系，将及时处理

This project is for educational and research purposes only. Users must comply with applicable laws and the target website's terms of service.

## Acknowledgments / 致谢

核心搜索逻辑源自 [fancyboi999/weixin_search_mcp](https://github.com/fancyboi999/weixin_search_mcp)（作者：**mini**，MIT 协议）。本项目在其基础上：

- 从 MCP 服务改造为 AI Agent Skills
- 依赖从 11 个包精简到 3 个
- 增加跨进程速率控制、Session 管理、指数退避等礼貌访问策略
- 搜索与 URL 解析解耦（单次搜索请求从 11 次降至 1 次）

感谢原作者的开源贡献。

## License

[MIT](LICENSE) — 详见 LICENSE 文件中的 Third-Party Notices。
