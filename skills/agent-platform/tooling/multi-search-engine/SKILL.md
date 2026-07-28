---
name: agent-multi-search-engine
description: "Multi-search engine integration with 17 engines (8 CN + 9 Global). Supports advanced search operators, time filters, site search, privacy engines, and WolframAlpha knowledge queries. Use when facing large amounts of search information or unknown knowledge domains. No API keys required for most engines."
---

# Multi-Search Engine — Comprehensive Web Search Integration

## Overview

When facing **large amounts of search information** or **unknown knowledge domains**, this skill provides comprehensive search capabilities across 17 search engines. It intelligently selects the best engine for each query type, aggregates results, and provides unified, high-quality information.

## Supported Search Engines

### Global Engines (9)
1. **Google** — Comprehensive web search
2. **Bing** — Microsoft's search engine
3. **DuckDuckGo** — Privacy-focused search
4. **Startpage** — Google results with privacy
5. **Qwant** — European privacy search
6. **Ecosia** — Eco-friendly search (plants trees)
7. **Swisscows** — Family-friendly privacy search
8. **Mojeek** — Independent crawler-based search
9. **WolframAlpha** — Computational knowledge engine

### Chinese Engines (8)
1. **Baidu** (百度) — Dominant Chinese search
2. **Sogou** (搜狗) — Chinese web search
3. **360 Search** (360搜索) — Chinese alternative
4. **Bing China** (必应中国) — Microsoft in China
5. **Zhihu Search** (知乎搜索) — Q&A focused
6. **WeChat Search** (微信搜索) — Within WeChat ecosystem
7. **Douyin Search** (抖音搜索) — Short video content
8. **Bilibili Search** (B站搜索) — Video and community

## When to Use This Skill

### Scenario 1: Large Information Domains
```
Situation: Researching "quantum computing advancements 2026"
Challenge: Too many sources, conflicting information
Solution: Use multiple engines to get comprehensive coverage
```

### Scenario 2: Unknown Knowledge Domains
```
Situation: Learning about "neuro-symbolic AI"
Challenge: Don't know where to start or which sources are authoritative
Solution: Use WolframAlpha for fundamentals, then expand with web search
```

### Scenario 3: Cross-Regional Research
```
Situation: Understanding "AI regulations in China vs EU"
Challenge: Need both Chinese and international perspectives
Solution: Use Baidu for Chinese sources, Google/DuckDuckGo for international
```

### Scenario 4: Privacy-Sensitive Topics
```
Situation: Researching "personal data protection"
Challenge: Don't want search history tracked
Solution: Use DuckDuckGo, Startpage, Qwant for privacy
```

## Core Features

### 1. Intelligent Engine Selection
```bash
# Basic search (auto-selects best engine)
multi-search "OpenClaw skills tutorial"

# Specify engine category
multi-search "quantum computing" --category academic

# Force specific engine
multi-search "latest news" --engine google --count 20
```

### 2. Advanced Search Operators
```bash
# Site-specific search
multi-search "site:github.com OpenClaw" --operator site

# Time-filtered search
multi-search "AI breakthroughs" --time "past month"

# File type search
multi-search "PDF deep learning" --filetype pdf

# Exact phrase
multi-search "\"multi-agent systems\"" --operator exact
```

### 3. Parallel Search & Aggregation
```bash
# Search multiple engines in parallel
multi-search "climate change solutions" --engines google,baidu,duckduckgo --parallel

# Aggregate and deduplicate results
multi-search "Python async programming" --aggregate --deduplicate

# Compare results across engines
multi-search "best programming language 2026" --compare
```

### 4. WolframAlpha Integration
```bash
# Computational queries
multi-search "integrate x^2 from 0 to 1" --engine wolfram

# Factual queries
multi-search "population of Shanghai" --engine wolfram

# Unit conversions
multi-search "100 miles to kilometers" --engine wolfram

# Mathematical computations
multi-search "solve x^2 + 2x + 1 = 0" --engine wolfram
```

### 5. Result Processing
```bash
# Filter by language
multi-search "machine learning" --language en,zh --filter

# Extract key information
multi-search "COVID-19 statistics" --extract numbers,dates

# Generate summary
multi-search "history of AI" --summarize --length medium

# Export results
multi-search "research papers" --export json --output results.json
```

## Search Strategies for Different Scenarios

### Strategy 1: Broad Unknown Topics
```
1. Start with WolframAlpha for foundational knowledge
2. Use Google/Bing for comprehensive web coverage
3. Check specialized engines (GitHub for code, arXiv for papers)
4. Use privacy engines for sensitive aspects
```

### Strategy 2: Time-Sensitive Information
```
1. Use time filters (past 24h, week, month)
2. Prioritize news-focused engines
3. Check social media search for real-time updates
4. Verify with multiple sources
```

### Strategy 3: Regional/Local Information
```
1. Use local engines (Baidu for China, Yandex for Russia)
2. Check regional social media (WeChat, Douyin)
3. Use translation for cross-language comparison
4. Consider cultural context in results
```

### Strategy 4: Technical/Academic Research
```
1. Start with academic search engines
2. Use site: operators for .edu, .gov, arXiv
3. Check GitHub for code and implementations
4. Use WolframAlpha for mathematical computations
```

## Configuration

```yaml
# ~/.openclaw/workspace/multi-search-config.yaml
multi_search:
  # Default settings
  default_engines: ["google", "duckduckgo", "baidu"]
  results_per_engine: 10
  timeout_seconds: 30
  
  # Privacy settings
  use_privacy_engines: true
  clear_history_on_exit: true
  anonymize_requests: true
  
  # Regional settings
  primary_region: "global"  # or: cn, eu, us
  fallback_regions: ["global", "cn"]
  auto_translate: false
  
  # WolframAlpha settings
  wolfram_app_id: ""  # Optional for extended queries
  wolfram_timeout: 15
  
  # Result processing
  auto_deduplicate: true
  auto_summarize: false
  summary_length: "medium"  # short, medium, long
  
  # Caching
  cache_enabled: true
  cache_ttl_hours: 24
  cache_dir: "~/.cache/multi-search"
  
  # Advanced
  parallel_requests: 3
  retry_failed: true
  user_agent_rotation: true
```

## Integration with Other Skills

### With Agent Reach
```
Multi-Search Engine finds relevant sources
    ↓
Agent Reach reads and extracts content
    ↓
Combined for comprehensive research
```

### With Proactive Agent
```
Proactive Agent identifies knowledge gaps
    ↓
Triggers Multi-Search Engine for information
    ↓
Processes and integrates results into knowledge base
```

### With Self-Improving Agent
```
Multi-Search Engine gathers external knowledge
    ↓
Self-Improving Agent analyzes search patterns
    ↓
Optimizes future search strategies
```

### With ClawTeam
```
Research Agent uses Multi-Search Engine
    ↓
Analysis Agent processes search results
    ↓
Validation Agent cross-checks sources
    ↓
Synthesis Agent creates consolidated report
```

## Best Practices for Large-Scale Searching

### 1. Start Broad, Then Narrow
```bash
# Phase 1: Broad understanding
multi-search "blockchain technology" --engines wolfram,google --summarize

# Phase 2: Specific aspects
multi-search "blockchain consensus algorithms" --engines github,arxiv --time "past year"

# Phase 3: Latest developments
multi-search "blockchain 2026 trends" --engines twitter,reddit --time "past month"
```

### 2. Use Engine Specializations
- **WolframAlpha**: Facts, computations, definitions
- **Google**: Comprehensive web coverage
- **Baidu**: Chinese-language content
- **GitHub**: Code and technical discussions
- **arXiv**: Academic papers
- **Twitter**: Real-time updates and opinions
- **Reddit**: Community discussions and experiences

### 3. Manage Information Overload
```bash
# Limit results initially
multi-search "large topic" --count 5 --summarize

# Use filters to reduce noise
multi-search "topic" --filter "-marketing -sales -advertisement"

# Focus on authoritative sources
multi-search "topic" --sites "*.edu,*.gov,*.org"
```

### 4. Cross-Verify Important Information
```bash
# Check multiple sources
multi-search "important fact" --engines google,duckduckgo,bing --compare

# Look for consensus
multi-search "controversial topic" --analyze sentiment --check consensus

# Trace to primary sources
multi-search "news story" --trace-sources --find-original
```

## Performance Optimization

### For Large Searches
```bash
# Use parallel processing
multi-search "extensive research" --parallel --workers 5

# Cache frequent queries
multi-search "common query" --cache --ttl 3600

# Batch similar searches
multi-search-batch queries.txt --output-dir results/
```

### For Unknown Domains
```bash
# Start with exploratory search
multi-search "new domain" --exploratory --map-concepts

# Build knowledge graph
multi-search "topic" --build-graph --show-connections

# Identify key subtopics
multi-search "broad field" --identify-subtopics --limit 10
```

## Troubleshooting

### Common Issues & Solutions

1. **Too many results**
   ```bash
   multi-search "query" --filter --limit 10 --summarize
   ```

2. **Irrelevant results**
   ```bash
   multi-search "query" --exclude "irrelevant terms" --engine-specific
   ```

3. **Regional restrictions**
   ```bash
   multi-search "query" --engines duckduckgo,startpage,qwant --privacy
   ```

4. **Language barriers**
   ```bash
   multi-search "query" --translate --languages en,zh --compare
   ```

5. **Outdated information**
   ```bash
   multi-search "query" --time "past week" --sort date
   ```

## Development & Extension

### Adding New Search Engines
1. Create engine adapter in `engines/` directory
2. Implement required interface:
   - `search(query, params)`
   - `parse_results(html)`
   - `get_config()`
3. Add to engine registry
4. Test with various query types

### Custom Search Pipelines
```python
# Example custom pipeline
pipeline = SearchPipeline()
pipeline.add_stage("wolfram", "foundational")
pipeline.add_stage("google", "comprehensive")  
pipeline.add_stage("github", "technical")
pipeline.add_stage("arxiv", "academic")
results = pipeline.execute("query")
```

---

*"When you don't know what you don't know, the right search strategy is more important than any single answer."*

**Remember**: Use this skill when facing large amounts of search information or unknown knowledge domains. It's your Swiss Army knife for comprehensive information gathering.