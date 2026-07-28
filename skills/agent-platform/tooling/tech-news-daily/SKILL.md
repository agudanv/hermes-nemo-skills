---
name: agent-tech-news-daily
description: 每日科技新闻汇——从全球多个 RSS 源抓取最新科技新闻，翻译（英→中）、去重、排版成每日简报。当用户询问科技新闻、科技新鲜事、每日科技、技术动态、Daily Tech News 或类似表达时触发此技能。
---

# 每日科技新闻汇总

## 触发条件
用户询问科技新闻、科技新鲜事、每日科技、技术动态、Daily Tech News，或要求"给我今天的科技新闻"等类似表达时使用此 skill。

## 执行流程

### Step 1: 抓取 RSS
运行 `fetch-news.ps1` 脚本，从各 RSS 源获取最新条目（每源最多 20 条）。

### Step 2: 翻译（如标题为英文）
调用当前 AI 模型将英文标题翻译为中文。

### Step 3: 去重
- 标题精确去重（小写+去空格）
- 相似度去重：Jaccard > 0.6 视为重复，保留最短标题

### Step 4: 筛选和格式化
1. 按发布时间排序，取最新30条新闻
2. 按重要性筛选最热门最重要的新闻
3. 格式化为直接展示格式：
   - **摘要**: 新闻内容摘要
   - **链接**: 可点击跳转的新闻链接
   - **来源**: 新闻来源媒体
4. 保存到 `memory/daily-tech-simple-YYYY-MM-DD.md`

### Step 5: 返回给用户
在会话中输出简化格式简报，每条新闻包含摘要、链接、来源三部分。

## 新闻来源（综合国际+国内热点源）

### 🌍 国际源（3个）
| 来源 | RSS 地址 | 特点 | 优先级 |
|------|----------|------|--------|
| Hacker News | https://news.ycombinator.com/rss | 开发者社区，前沿技术 | 1 |
| GitHub Trending | https://github.com/trending/developers.rss | 热门开源项目 | 2 |
| BBC Technology | https://feeds.bbci.co.uk/news/technology/rss.xml | 权威国际新闻 | 3 |

### 🇨🇳 国内热点源（11+个）
#### 技术社区类
| 来源 | RSS 地址 | 特点 | 优先级 |
|------|----------|------|--------|
| 36氪 | https://36kr.com/feed | 创业投资，科技商业 | 4 |
| InfoQ | https://www.infoq.cn/feed | 技术实践，架构演进 | 5 |
| CSDN博客 | https://blog.csdn.net/rss.html | 开发者社区 | 6 |
| OSChina | https://www.oschina.net/news/rss | 开源技术 | 7 |
| SegmentFault | https://segmentfault.com/feeds/blogs | 技术问答 | 8 |

#### 科技媒体类
| 来源 | RSS 地址 | 特点 | 优先级 |
|------|----------|------|--------|
| 爱范儿 | https://www.ifanr.com/feed | 数码科技 | 9 |
| 量子位 | https://www.qbitai.com/rss | AI科技 | 10 |
| 钛媒体 | https://www.tmtpost.com/rss | 科技媒体 | 11 |
| 雷峰网 | https://www.leiphone.com/feed | 科技资讯 | 12 |
| PingWest品玩 | https://www.pingwest.com/feed | 科技文化 | 13 |

#### 英文国内源
| 来源 | RSS 地址 | 特点 | 优先级 |
|------|----------|------|--------|
| TechNode | https://technode.com/feed | 中国科技英文报道 | 14 |
| KrASIA | https://kr-asia.com/feed | 亚洲科技新闻 | 15 |

### 🔄 质量保证机制
1. **链接验证**: 确保所有输出链接真实可达
2. **优先级排序**: 按源质量和重要性排序
3. **智能回退**: 网络异常时使用高质量模拟数据
4. **状态报告**: 显示有效链接比例和源状态

### 📊 输出规格
- **数量**: 30条最新最重要新闻
- **格式**: 摘要、链接、来源（三行式）
- **分类**: 国际/国内分开显示
- **验证**: 链接可达性标记（✅/⚠️）
- **统计**: 显示国际/国内比例和有效链接数

> 注意：技能优先使用真实数据，确保链接可达。如果网络受限，会使用高质量模拟数据并明确标注。

## 脚本
- `scripts/fetch-news.ps1` — PowerShell 5.1 兼容，抓取 + JSON 输出
- 运行：`powershell.exe -ExecutionPolicy Bypass -File scripts/fetch-news.ps1`
- 原始数据保存在 `memory/news-raw-YYYY-MM-DD.json`
- 简报保存在 `memory/daily-tech-YYYY-MM-DD.md`

## 注意
- 每源最多 20 条，合并最多 220 条
- 英文标题自动翻译为中文
- 尊重 robots.txt 和源站规则
