---
name: agent-proactive-agent
description: "Transform AI agents from task-followers into proactive partners that anticipate needs and continuously improve. Features WAL Protocol, Working Buffer, Autonomous Crons, and battle-tested patterns from the Hal Stack. Merges eleven top-rated OpenClaw skills into a single unified architecture."
---

# Proactive Agent — From Task-Follower to Anticipatory Partner

## Overview

The Proactive Agent skill transforms reactive AI assistants into **anticipatory partners** that:
- **Predict needs** before they're explicitly stated
- **Retain important information** across sessions
- **Run background tasks** without explicit prompts
- **Continuously improve** through experience
- **Manage context** with advanced memory systems

## Core Architecture

### 1. WAL Protocol (Write-Ahead Logging)
**Purpose**: Capture corrections, decisions, and important details before they're lost

```yaml
WAL Entry:
  timestamp: ISO-8601
  event_type: correction|decision|detail|learning
  context: "What was happening"
  content: "The important information"
  priority: critical|high|medium|low
  tags: [relevant_categories]
```

**Features**:
- Real-time capture of meaningful moments
- Survives context window truncation
- Enables step-by-step recovery
- Unified search across all logs

### 2. Working Buffer
**Purpose**: Survive the danger zone between memory flush and context compaction

```
Short-Term Context
    ↓
Working Buffer (Persistent)
    ├── Critical decisions
    ├── User preferences
    ├── Task state
    └── Open questions
    ↓
Long-Term Memory
```

**Features**:
- 4KB persistent buffer outside context window
- Automatic promotion of important items to memory
- Survives session restarts and model switches
- Configurable retention policies

### 3. Autonomous Crons
**Purpose**: Run background tasks without user prompting

```yaml
Cron Types:
  - systemEvent: For main session notifications
  - isolated agentTurn: For independent background work
  - session-bound: For persistent session tasks
```

**Features**:
- Smart scheduling based on user activity patterns
- Resource-aware execution (avoid busy times)
- Result delivery optimization
- Failure recovery and retry logic

### 4. Unified Search
**Purpose**: Search across all knowledge sources simultaneously

```
Search Sources:
├── WAL logs (recent activity)
├── Working Buffer (current context)
├── Long-term Memory (curated knowledge)
├── Skill library (capabilities)
└── External sources (web, APIs)
```

**Features**:
- Semantic search across all data
- Relevance ranking with recency bias
- Cross-reference detection
- Confidence scoring

## Integrated Skills

The Proactive Agent merges 11 top-rated skills:

1. **Memory Manager** — Intelligent memory retention and recall
2. **Context Optimizer** — Dynamic context window management
3. **Predictive Assistant** — Anticipate needs based on patterns
4. **Background Runner** — Autonomous task execution
5. **Learning Capturer** — Continuous improvement from experience
6. **Preference Tracker** — User-specific behavior adaptation
7. **State Maintainer** — Session persistence across interruptions
8. **Priority Manager** — Intelligent task prioritization
9. **Resource Optimizer** — Efficient use of tokens and APIs
10. **Error Recovery** — Graceful failure handling
11. **Communication Optimizer** — Adaptive communication styles

## How It Works

### Phase 1: Observation & Pattern Recognition
```
Monitor user interactions
    ↓
Identify recurring patterns
    ↓
Extract implicit preferences
    ↓
Build predictive models
```

### Phase 2: Anticipation & Preparation
```
Predict likely next actions
    ↓
Prepare resources in advance
    ↓
Run background research
    ↓
Cache relevant information
```

### Phase 3: Proactive Engagement
```
Offer help before asked
    ↓
Provide context-aware suggestions
    ↓
Surface relevant historical data
    ↓
Initiate beneficial background tasks
```

### Phase 4: Learning & Adaptation
```
Analyze interaction outcomes
    ↓
Update predictive models
    ↓
Refine anticipation algorithms
    ↓
Improve resource allocation
```

## Use Cases

### Case 1: Meeting Preparation
```
Before: User asks for meeting prep 30 minutes before meeting
After: Agent notices calendar event, prepares materials 2 hours in advance
Result: Higher quality preparation, less stress
```

### Case 2: Research Continuity
```
Before: User re-explains context each session
After: Agent maintains research state across sessions
Result: Seamless continuation, no context loss
```

### Case 3: Error Prevention
```
Before: User makes same configuration mistake repeatedly
After: Agent anticipates mistake, provides preventive guidance
Result: Fewer errors, faster workflow
```

## Configuration

```yaml
# ~/.openclaw/workspace/proactive-config.yaml
proactive_agent:
  # WAL Protocol
  wal:
    enabled: true
    capture_threshold: "medium"  # low|medium|high|critical
    retention_days: 30
    auto_compact: true
  
  # Working Buffer
  working_buffer:
    size_kb: 4
    promotion_threshold: 3  # mentions before promotion
    persistence: "session"  # session|day|week|permanent
  
  # Autonomous Crons
  crons:
    enabled: true
    max_concurrent: 2
    resource_aware: true
    user_activity_based: true
    
    schedules:
      daily_review: "08:00"
      memory_cleanup: "02:00"
      skill_optimization: "weekly"
  
  # Anticipation
  anticipation:
    enabled: true
    confidence_threshold: 0.7
    max_suggestions_per_hour: 3
    learning_rate: 0.1
  
  # Privacy
  privacy:
    exclude_sensitive: true
    local_only: true
    user_reviewable: true
```

## Setup

### Quick Start
```bash
# Clone the skill (if using Git)
git clone https://github.com/openclaw/skills.git
cp skills/skills/halthelobster/proactive-agent/SKILL.md ~/.openclaw/workspace/skills/proactive-agent/

# Or install via ClawHub
clawhub install halthelobster/proactive-agent
```

### Verification
```bash
# Check if skill is loaded
openclaw skills list | grep proactive

# Test WAL logging
echo "Test WAL entry" | openclaw --note "Testing proactive agent"

# View working buffer
cat ~/.openclaw/workspace/memory/working-buffer.md
```

## Best Practices

### Do:
- Start with conservative anticipation settings
- Regularly review WAL logs for improvement opportunities
- Adjust working buffer size based on typical task complexity
- Use autonomous crons for low-risk, high-value background tasks

### Don't:
- Overwhelm users with too many proactive suggestions
- Run resource-intensive crons during peak usage
- Retain sensitive information in working buffer
- Make irreversible changes without confirmation

## Integration with Other Skills

### With Self-Improving Agent
```
Proactive Agent (Anticipation)
    ↓
Self-Improving Agent (Learning Capture)
    ↓
Evolver (Systematic Improvement)
    ↓
Enhanced Proactive Capabilities
```

### With ClawTeam
```
Proactive Agent identifies need for multi-agent work
    ↓
Creates ClawTeam with appropriate roles
    ↓
Coordinates team using proactive patterns
    ↓
Captures team learnings for future use
```

## Version History

### v3.1.0
- **Autonomous vs Prompted Crons** — Know when to use `systemEvent` vs `isolated agentTurn`
- **Verify Implementation, Not Intent** — Check the mechanism, not just the text
- **Tool Migration Checklist** — When deprecating tools, update ALL references

### v3.0.0
- **WAL Protocol** — Write-Ahead Logging for important moments
- **Working Buffer** — Survive context truncation
- **Compaction Recovery** — Step-by-step context recovery
- **Unified Search** — Search across all knowledge sources

### v2.x
- Initial multi-skill integration
- Basic anticipation algorithms
- Memory management improvements

---

*"The best assistant doesn't just respond to requests—it anticipates needs before they're expressed."*