---
name: agent-daily-wechat-digest
version: "1.0.0"
description: 每日微信公众号热词摘要技能 - 自动获取B站热词→搜索微信文章→AI总结→转录飞书
argument-hint: 'digest, 每日摘要, 微信公众号总结'
allowed-tools: Bash, Read, Write, WebSearch
agent-compatibility: "支持 OpenClaw, Cursor, Claude Code 等 Agent 平台"
author: MuGe
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins:
        - python3
        - curl
      env:
        - WECHAT_API_KEY (可选)
    files:
      - "daily_wechat_digest.py"
    tags:
      - wechat
      - digest
      - daily
      - summary
      - feishu
---

# daily-wechat-digest - 每日微信公众号热词摘要

## 功能

自动化工作流程，每天 9:00 和 10:00 执行：

### 9:00 任务（每日微信公众号摘要）
1. 从 B站/百度 获取当前最热话题
2. 用 web_search 搜索相关微信公众号文章（前5篇）
3. 用 jina-ai-skill 总结每篇文章的核心内容和思想
4. 保存每日摘要到 `memory/daily-wechat-digest/`

### 10:00 任务（飞书同步与提炼）
1. 读取9点生成的摘要
2. 调用 feishu-knowledge-manager 转录到飞书
3. 对内容进行二次提炼
4. 汇入飞书知识库对应分类

## 工作流程

```
9:00 Cron ─┬─→ last30days 获取热词
           └─→ web_search 搜微信文章 → jina.ai 获取内容 → AI总结 → 保存MD

10:00 Cron ──→ feishu-knowledge-manager → 转录飞书 → 二次提炼 → 汇入知识库
```

## 手动执行

```bash
# 生成当日任务（由 cron 自动调用）
python skills/daily-wechat-digest/daily_wechat_digest.py
```

## 输出文件

- **每日任务**: `memory/daily-wechat-digest/daily-task-YYYY-MM-DD.json`
- **Agent提示**: `memory/daily-wechat-digest/agent-prompt-YYYY-MM-DD.txt`
- **摘要文档**: `memory/daily-wechat-digest/wechat-digest-YYYY-MM-DD.md`
- **飞书任务**: `memory/daily-wechat-digest/feishu-task-YYYY-MM-DD.json`

## 定时任务配置

| 任务 | 时间 | Cron表达式 | 说明 |
|------|------|-----------|------|
| 每日微信公众号摘要 | 9:00 | `0 9 * * *` | 获取热词、搜索、总结 |
| 飞书同步与提炼 | 10:00 | `0 10 * * *` | 转录飞书、二次提炼 |

## 依赖技能

- `last30days-skill-cn` - 获取热词
- `wechat-search-release` - 搜索微信文章
- `smart-summarize` - 总结文章
- `feishu-knowledge-manager` - 转录到飞书

## 注意事项

1. **微信搜索**: 使用 `site:mp.weixin.qq.com` 过滤，无需 API key
2. **飞书集成**: 需要配置飞书 API credentials
3. **内容提炼**: 10点任务会对比9点内容进行去重和知识点提取

---

*此技能整合了热词获取、微信搜索、AI总结、飞书同步四个步骤，形成完整的每日情报摘要流程。*
