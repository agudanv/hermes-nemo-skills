---
name: third-party-ai-memory-router-hermes-smart-summarize
description: "智能统一摘要技能 — 自动识别 URL 类型，选择最佳抓取策略，交给 LLM 生成总结。触发词：总结、摘要、summarize、总结这个链接、帮我看看这个页面。适用场景：文章/文档链接、Bilibili 视频、任何网页内容提取。"
---

# Smart Summarize — 智能统一摘要

自动识别 URL 类型，路由到最佳抓取策略，再交由 LLM 生成总结。

## 工作流程

```
用户输入 URL
    │
    ▼
检测 URL 类型
    │
    ├─ Bilibili 视频？ ──→ bilibili-transcript（字幕抓取）
    │                          │
    │                          ▼
    │                      字幕文本 ──→ LLM 总结
    │
    └─ 其他网页/文档？ ──→ jina-ai-skill（Markdown 抓取）
                               │
                               ▼
                           Markdown ──→ LLM 总结
```

## 策略选择

| URL 类型 | 抓取方式 | 说明 |
|----------|----------|------|
| Bilibili 视频 | `bilibili-transcript` | 优先 CC 字幕 → AI 字幕 → Whisper 转写 |
| 其他网页/文档 | `jina-ai-skill` (r.jina.ai) | 干净 Markdown，无需 API Key |

## 使用方式

### 方式一：Python 脚本（推荐）

```bash
python skills/smart-summarize/scripts/smart_summarize.py <URL>
```

### 方式二：直接调用

1. **判断类型** — 检查 URL 是否含 `bilibili.com`
2. **Bilibili** — 调用 `bilibili-transcript` 脚本获取字幕
3. **其他** — 调用 Jina Reader: `curl -s "https://r.jina.ai/<URL>"`
4. **总结** — 将抓取内容交给 LLM 生成结构化总结

## 输出格式

LLM 总结时按以下结构组织：

```
## 📌 核心要点
（3-5 个关键点）

## 📝 内容概要
（1-3 段总结）

## 💡 值得关注的细节
（可选的有价值细节）

## 📎 原文链接
<URL>
```

## 自动触发条件

满足以下任一场景时自动调用：
- 用户发送链接并请求"总结""摘要"
- 用户发送 Bilibili 链接
- 用户要求"看看这个页面说了什么"
- 用户粘贴 URL 并问"能总结一下吗"

## 依赖项

| 依赖 | 来源 | 说明 |
|------|------|------|
| `bilibili-transcript` | 已安装 | B 站字幕提取 |
| `jina-ai-skill` | 已安装 | 通用网页抓取 |
| `curl` | 系统自带 | Jina Reader 调用 |
| `yt-dlp` | 系统自带 | 视频下载（如需 Whisper） |
| `ffmpeg` | 系统自带 | 音频处理 |
| `opencc` | 系统自带 | 繁简转换 |

## 注意事项

- Jina Reader 无需 API Key，速率限制内可直接使用
- Bilibili 字幕优先使用 CC/AI 字幕，失败才走 Whisper
- Whisper 依赖 GPU（本机 RTX 4070 Super 可用 medium 模型）
- 总结时自动判断内容语言，优先使用中文输出
