---
name: third-party-ai-memory-router-hermes-agent-reach
description: "Give your AI agent eyes to see the entire internet. Search and read content from 14+ platforms including Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu (小红书), Zhihu, Weibo, Douyin, and more. One CLI, zero API fees. Transform agents from text generators to informed, data-driven reasoners with real-time web access."
---

# Agent Reach — Internet Eyes for AI Agents

## Overview

Agent Reach transforms AI agents from **text generators** into **informed, data-driven reasoners** by giving them real-time access to the entire internet. With zero API fees and a single CLI command, agents can search, read, and analyze content from 14+ major platforms.

## Supported Platforms

### Social Media
- **Twitter/X** — Tweets, threads, trends, user profiles
- **Reddit** — Subreddits, posts, comments, AMAs
- **Weibo** (微博) — Chinese microblogging
- **XiaoHongShu** (小红书) — Lifestyle and shopping content
- **Zhihu** (知乎) — Chinese Q&A platform

### Video & Streaming
- **YouTube** — Videos, channels, comments, transcripts
- **Bilibili** (哔哩哔哩) — Chinese video sharing
- **Douyin** (抖音) — Chinese short video platform

### Developer & Code
- **GitHub** — Repositories, issues, PRs, code search
- **Stack Overflow** — Questions, answers, code snippets

### News & Articles
- **News sites** — Major news outlets worldwide
- **Blog platforms** — Medium, Dev.to, etc.
- **Forums** — Technical and community forums

### Specialized
- **Product reviews** — E-commerce platforms
- **Academic papers** — Research repositories
- **Government data** — Public datasets

## Core Features

### 1. Unified Search Interface
```bash
# Search across all platforms
agent-reach search "OpenClaw skills" --platforms twitter,reddit,github

# Platform-specific search
agent-reach search "AI agents" --platform twitter --limit 20

# Time-bound search
agent-reach search "latest news" --days 7 --sort recent
```

### 2. Content Reading & Extraction
```bash
# Read specific content
agent-reach read https://twitter.com/user/status/1234567890
agent-reach read https://github.com/openclaw/openclaw/issues/123
agent-reach read https://www.reddit.com/r/MachineLearning/comments/abc123

# Extract clean content
agent-reach extract https://youtube.com/watch?v=xyz --format markdown
```

### 3. Real-time Monitoring
```bash
# Monitor topics
agent-reach monitor "OpenClaw" --platforms twitter,reddit --interval 300

# Track mentions
agent-reach track @username --platform twitter --notify

# Watch trends
agent-reach trends --platform twitter --category technology
```

### 4. Data Export & Analysis
```bash
# Export to various formats
agent-reach export search-results.json --format json
agent-reach export report.md --format markdown
agent-reach export data.csv --format csv

# Analyze sentiment
agent-reach analyze sentiment search-results.json
agent-reach analyze topics search-results.json --top 10
```

## Installation

### Quick Install (Recommended)
```bash
# Install via package manager
pip install agent-reach

# Or clone from GitHub
git clone https://github.com/Panniantong/Agent-Reach.git
cd Agent-Reach
pip install -e .
```

### Platform-Specific Setup
Some platforms require additional setup:

```bash
# Twitter/X setup (cookies required)
agent-reach setup twitter --cookies "cookies.txt"

# YouTube setup (optional, improves reliability)
agent-reach setup youtube --api-key "YOUR_API_KEY"

# Bilibili setup (cookies required)
agent-reach setup bilibili --cookies "bilibili_cookies.txt"
```

### OpenClaw Integration
```bash
# Copy skill to OpenClaw workspace
mkdir -p ~/.openclaw/workspace/skills/agent-reach
cp Agent-Reach/skills/openclaw/SKILL.md ~/.openclaw/workspace/skills/agent-reach/

# Verify installation
openclaw skills list | grep agent-reach
```

## How It Works

### Architecture
```
User Request
    ↓
Agent Reach CLI
    ├── Platform Selector
    ├── Request Router
    └── Format Normalizer
    ↓
Platform Adapters
├── Twitter Adapter (cookies)
├── Reddit Adapter (public)
├── YouTube Adapter (optional API)
├── GitHub Adapter (public)
└── Bilibili Adapter (cookies)
    ↓
Content Fetchers
├── HTML Parser
├── API Client
├── Cookie Manager
└── Rate Limiter
    ↓
Content Processors
├── Text Extractor
├── Media Downloader
├── Translation (optional)
└── Format Converter
    ↓
Normalized Output
```

### Zero-API-Fee Model
Agent Reach uses:
1. **Public APIs** where available (GitHub, Reddit, etc.)
2. **Web scraping** with proper rate limiting
3. **Cookie authentication** for platforms requiring login
4. **Caching** to minimize repeated requests

## Use Cases

### Case 1: Market Research
```
Task: "Research competitor AI agent platforms"
Agent Reach Usage:
1. Search Twitter for mentions of competitors
2. Read GitHub repositories for activity levels
3. Analyze Reddit discussions for user sentiment
4. Monitor YouTube for tutorial and review videos
Result: Comprehensive competitive analysis
```

### Case 2: Technical Problem Solving
```
Task: "Debug OpenClaw installation issue"
Agent Reach Usage:
1. Search GitHub issues for similar problems
2. Read Stack Overflow for solutions
3. Check Reddit communities for workarounds
4. Find YouTube tutorials for step-by-step guides
Result: Multiple solution approaches with community validation
```

### Case 3: Content Creation
```
Task: "Write article about AI trends"
Agent Reach Usage:
1. Search latest AI news across platforms
2. Analyze trending topics on Twitter/Reddit
3. Gather expert opinions from Zhihu/Medium
4. Collect data points from GitHub repositories
Result: Data-driven, timely article with multiple sources
```

## Configuration

```yaml
# ~/.agent-reach/config.yaml
agent_reach:
  # General settings
  cache_dir: "~/.cache/agent-reach"
  cache_ttl: 3600  # 1 hour
  max_concurrent: 3
  
  # Rate limiting
  requests_per_minute: 30
  respect_robots_txt: true
  
  # Privacy
  anonymize_requests: true
  clear_cookies_on_exit: false
  
  # Platforms
  platforms:
    twitter:
      enabled: true
      cookies_path: "~/.agent-reach/twitter_cookies.txt"
      
    reddit:
      enabled: true
      user_agent: "AgentReach/1.0"
      
    youtube:
      enabled: true
      api_key: ""  # Optional
      
    github:
      enabled: true
      token: ""  # Optional for higher limits
      
    bilibili:
      enabled: true
      cookies_path: "~/.agent-reach/bilibili_cookies.txt"
  
  # Output
  default_format: "markdown"
  include_metadata: true
  auto_translate: false  # For non-English content
```

## Integration with OpenClaw Skills

### With Proactive Agent
```
Proactive Agent identifies information need
    ↓
Triggers Agent Reach for research
    ↓
Processes and summarizes results
    ↓
Updates knowledge base for future use
```

### With Self-Improving Agent
```
Agent Reach gathers external knowledge
    ↓
Self-Improving Agent analyzes patterns
    ↓
Updates internal models and strategies
    ↓
Improves future research capabilities
```

### With ClawTeam
```
Research Agent uses Agent Reach
    ↓
Analysis Agent processes data
    ↓
Synthesis Agent creates reports
    ↓
Coordinator Agent manages workflow
```

## Best Practices

### Do:
- Start with public platforms (GitHub, Reddit) before requiring cookies
- Use caching to avoid repeated identical requests
- Respect platform rate limits and terms of service
- Anonymize requests when possible
- Regularly update cookies for platforms requiring login

### Don't:
- Don't use for spam or harassment
- Don't bypass paywalls or access restricted content
- Don't make excessive requests to any single platform
- Don't store sensitive cookies unencrypted
- Don't use for illegal activities

## Troubleshooting

### Common Issues

1. **Cookies expired**
   ```bash
   agent-reach setup twitter --cookies "fresh_cookies.txt"
   ```

2. **Rate limited**
   ```bash
   # Wait and retry with backoff
   agent-reach search "query" --retry 3 --backoff 5
   ```

3. **Platform changes**
   ```bash
   # Update adapter
   pip install --upgrade agent-reach
   ```

4. **Content not loading**
   ```bash
   # Try different user agent
   agent-reach --user-agent "Mozilla/5.0" search "query"
   ```

## Development

### Contributing New Platforms
1. Fork the repository
2. Create new platform adapter in `agent_reach/adapters/`
3. Implement required methods:
   - `search(query, limit, **kwargs)`
   - `read(url, **kwargs)`
   - `setup(**kwargs)`
4. Add tests and documentation
5. Submit pull request

### Extending Functionality
- Add new output formats
- Implement advanced analysis (sentiment, topic modeling)
- Create visualization tools
- Add batch processing capabilities

---

*"Information is not knowledge. The only source of knowledge is experience." — With Agent Reach, your AI agents gain the experience of the entire internet.*