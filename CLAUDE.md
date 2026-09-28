# weixin-search-skills

微信公众号文章搜索工具集，通过搜狗微信搜索获取文章。

## 可用 Skills

本项目提供 4 个 skill，协作完成微信文章的搜索、链接解析和内容获取：

- `/weixin-search [关键词] [页码]` — 搜索微信文章，返回标题、链接、发布时间
- `/weixin-search-all [关键词] [最大页数]` — 多页自动翻页搜索
- `/weixin-resolve-url [搜狗链接]` — 将搜狗跳转链接解析为真实 mp.weixin.qq.com URL
- `/weixin-article [文章链接] [referer]` — 获取微信文章纯文本正文

## 工作流

典型使用顺序：搜索 → 解析 URL → 获取正文。

1. 先用 `/weixin-search` 搜索关键词，获得结果列表
2. 从结果的 `link` 字段用 `/weixin-resolve-url` 解析出真实微信链接
3. 用 `/weixin-article` 获取文章正文

如果用户只想看搜索结果列表，第 1 步就够了。

> **注意**：第 2 步成功率较低——搜狗对跳转链接页面有独立的图片验证码保护，与搜索列表页不同。即使访问频率很低也可能被拦截。如果用户已有 `mp.weixin.qq.com` 开头的真实链接，可跳过第 2 步直接用第 3 步。对于只需标题+摘要的场景（如日报生成），搜索结果本身已足够。

## 脚本路径

所有 Python 脚本位于项目根目录下的 `scripts/` 目录，使用项目 venv 运行：

- **Windows:** `.venv\Scripts\python.exe scripts\<脚本名>.py`
- **macOS / Linux:** `.venv/bin/python scripts/<脚本名>.py`

## 访问策略注意事项

- **跨进程全局速率控制已内置**：`GlobalRateLimiter` 通过文件锁协调所有进程，即使并发调用也会自动排队（间隔 ≥ 3 秒，2 分钟窗口最多 20 次请求）
- 每次 skill 调用是独立进程，会自动初始化 Session（约 2 个预热请求），预热请求也受全局限流保护
- 搜狗对同一 IP 的频繁访问可能触发验证
- 多页搜索（`/weixin-search-all`）消耗请求较多，建议 max_pages ≤ 3
- 如果返回空结果，通常是访问频率过高，需等待几分钟
- 搜狗不支持按时间筛选，结果按相关性排序；如需筛选最近文章，搜索后按 publish_time 过滤
