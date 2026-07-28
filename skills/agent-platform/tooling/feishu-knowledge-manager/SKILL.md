---
name: agent-feishu-knowledge-manager
version: "1.0.1"
description: 飞书知识管理工具 - 自动获取外部文章内容、存入飞书文档、归纳知识要点到知识库
argument-hint: 'feishu, 飞书, 知识库, 存入飞书'
allowed-tools: Bash, Read, Write, WebFetch
agent-compatibility: "支持 OpenClaw 等 Agent 平台"
author: MuGe
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "📒"
    requires:
      bins:
        - python3
      env:
        - FEISHU_APP_ID
        - FEISHU_APP_SECRET
    files:
      - "feishu_api.py"
      - "feishu_knowledge.py"
    tags:
      - feishu
      - knowledge-base
      - document
      - sync
---

# feishu-knowledge-manager - 飞书知识管理

## 功能

1. 获取外部链接内容（微信公众号、通用网页）
2. 创建飞书云文档
3. 归纳知识要点到知识库分类
4. 定时整理知识库

## 配置

环境变量（已配置）：
- `FEISHU_APP_ID`: cli_a9242dbee9fa1cc6
- `FEISHU_APP_SECRET`: 已配置

## 使用方法

### 方式一：Agent 直接调用

```
请将以下内容存入飞书知识库：
标题：xxx
链接：xxx
内容：xxx
```

### 方式二：Python 脚本

```bash
# 创建文档
python feishu_api.py create --title "标题" --content "内容"

# 搜索知识库
python feishu_knowledge.py search --query "关键词"

# 添加到知识库
python feishu_knowledge.py add --doc_token "文档token" --kb_token "知识库token"
```

## 核心 API

### 认证
- `get_tenant_access_token()` - 获取 tenant token

### 文档操作
- `create_document(title, content)` - 创建云文档
- `get_document(doc_token)` - 获取文档内容

### 知识库操作
- `list_knowledge_bases()` - 列出知识库
- `add_to_knowledge_base(doc_token, kb_token)` - 添加文档到知识库

## 定时任务

| 任务 | 时间 | 说明 |
|------|------|------|
| 每日知识库整理 | 9:00 | 检查重复、优化结构 |

---

*需要配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量*
