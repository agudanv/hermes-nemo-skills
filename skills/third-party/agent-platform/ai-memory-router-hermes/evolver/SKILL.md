---
name: third-party-ai-memory-router-hermes-evolver
description: "Meta-skill that allows OpenClaw agents to inspect their own runtime history, identify failures or inefficiencies, and autonomously write new code or update their own memory to improve performance. Use when an agent needs to self-improve, audit past performance, optimize workflows, or adapt to new patterns without human intervention."
---

# Evolver — Autonomous Agent Self-Improvement

## What It Is

The Evolver is a **meta-skill** that enables OpenClaw agents to:

1. **Self-audit** — Review their own execution history and decision logs
2. **Identify patterns** — Detect recurring failures, inefficiencies, or bottlenecks
3. **Autonomous improvement** — Write new code, update skills, or modify memory
4. **Adaptive learning** — Evolve behavior based on performance metrics

## When to Use

This skill activates automatically when:
- An agent completes a complex task and should reflect on its performance
- Multiple similar failures occur in sequence
- Performance metrics indicate suboptimal workflows
- New patterns emerge that could be codified into skills

## How It Works

### Phase 1: Audit
```yaml
1. Scan recent session history
2. Extract decision points and outcomes
3. Calculate success/failure ratios
4. Identify high-cost or slow operations
```

### Phase 2: Analysis
```yaml
1. Cluster similar failure modes
2. Trace root causes through decision chains
3. Compare against known best practices
4. Generate improvement hypotheses
```

### Phase 3: Implementation
```yaml
1. Write new helper functions or scripts
2. Update SKILL.md files with learned patterns
3. Modify memory/ preferences based on outcomes
4. Create automated checks to prevent recurrence
```

### Phase 4: Validation
```yaml
1. Test changes in isolated environment
2. Monitor performance metrics
3. Roll back if degradation detected
4. Document learnings for future reference
```

## Examples

### Example 1: Optimizing File Operations
```
Before: Agent reads entire 10MB file for each search query
After: Evolver creates indexed lookup and caches frequent queries
Result: 90% reduction in file I/O operations
```

### Example 2: Fixing Recurring API Errors
```
Before: Agent retries failed API calls 5 times with fixed delays
After: Evolver implements exponential backoff + circuit breaker
Result: 75% reduction in timeout-related failures
```

### Example 3: Learning User Preferences
```
Before: Agent asks for confirmation on every file write
After: Evolver detects user always approves .md edits, rarely approves .exe
Result: Auto-approve .md edits, still ask for .exe
```

## Safety Constraints

The Evolver operates within strict boundaries:

1. **No external changes** — Cannot modify systems outside OpenClaw workspace
2. **Human oversight** — Major changes require approval (configurable)
3. **Rollback capability** — All changes are versioned and reversible
4. **Transparency** — Every evolution is logged with reasoning

## Configuration

```yaml
# In ~/.openclaw/workspace/evolver-config.yaml
evolver:
  enabled: true
  audit_frequency: "after_major_tasks"  # or: hourly, daily, on_failure
  auto_apply_minor: true                # Auto-apply low-risk changes
  require_approval_for:
    - new_skills
    - memory_updates
    - external_tool_changes
  performance_metrics:
    - execution_time
    - success_rate  
    - user_satisfaction
    - token_efficiency
```

## Integration with Other Skills

- **ClawTeam** — Evolver can optimize multi-agent coordination patterns
- **Healthcheck** — Evolver can improve security and performance audits
- **Coding Agent** — Evolver can refine code generation templates
- **Memory System** — Evolver can enhance memory retention and recall

## Quick Start

To manually trigger an evolution audit:

```bash
# Check if Evolver skill is loaded
openclaw skills list | grep evolver

# View evolution logs
cat ~/.openclaw/workspace/memory/evolver-log.md

# Force an audit of the last 24 hours
echo "Run Evolver audit on last 24 hours of activity" | openclaw
```

## Development

The Evolver skill itself can evolve. To contribute improvements:

1. Fork the [OpenClaw skills repository](https://github.com/openclaw/skills)
2. Modify `skills/autogame-17/evolver/SKILL.md`
3. Submit a pull request

---

*"The most intelligent systems are those that can improve themselves."*