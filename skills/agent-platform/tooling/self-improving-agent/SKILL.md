---
name: agent-self-improving-agent
description: "Autonomous agent that logs learnings, errors, and corrections to enable continuous improvement. Combines official self-improving-agent functionality with Evolver meta-skill capabilities for comprehensive self-improvement."
---

# Self-Improving Agent — Continuous Learning and Improvement

## Overview

This skill enables OpenClaw agents to **continuously learn from experience** by:
1. **Logging errors and corrections** — Building a knowledge base of what works and what doesn't
2. **Capturing learnings** — Documenting successful patterns and solutions
3. **Updating preferences** — Remembering user preferences and context
4. **Autonomous improvement** — Using Evolver meta-skill for self-optimization

## How It Works

### Automatic Activation
The skill activates automatically when:
- An error occurs during task execution
- A successful solution is found after multiple attempts
- User provides correction or feedback
- Agent discovers a non-obvious solution

### Learning Capture Format
```yaml
timestamp: 2026-04-01T09:14:00Z
context: "Web application development task"
situation: "Tried to install package with wrong Python version"
error: "Package requires Python 3.10+, have 3.9"
solution: "Used pyenv to switch to Python 3.11, then installed"
learning: "Always check Python version requirements before installation"
category: "environment_setup"
priority: "medium"
```

### Memory Integration
Learnings are stored in:
- `~/.openclaw/workspace/memory/learnings/` — Categorized learning files
- `~/.openclaw/workspace/memory/preferences.md` — User and task preferences
- Session context — Immediate recall during current session

## Integration with Evolver Meta-Skill

This skill works with the Evolver meta-skill to create a complete self-improvement system:

```
Raw Experience
    ↓
Self-Improving Agent (Capture)
    ├── Log errors and corrections
    ├── Document successful patterns
    └── Update user preferences
    ↓
Evolver Meta-Skill (Analyze & Improve)
    ├── Analyze patterns across learnings
    ├── Identify optimization opportunities
    └── Implement systematic improvements
    ↓
Enhanced Agent Performance
```

## Setup for Different Agents

### OpenClaw
- **Activation**: Workspace injection + inter-agent messaging
- **Setup**: Automatic via skill loading
- **Detection**: Via session tools and workspace files

### Claude Code
- **Activation**: Hooks (UserPromptSubmit, PostToolUse)
- **Setup**: `.claude/settings.json` with hook configuration
- **Detection**: Automatic via hook scripts

### Codex
- **Activation**: Hooks (same pattern as Claude Code)
- **Setup**: `.codex/settings.json` with hook configuration
- **Detection**: Automatic via hook scripts

### GitHub Copilot
- **Activation**: Manual (no hook support)
- **Setup**: Add to `.github/copilot-instructions.md`
- **Detection**: Manual triggering

## Usage Examples

### Example 1: Error Learning
```
Situation: Failed to parse JSON response from API
Action: Log error pattern and solution
Result: Future API calls include better error handling
```

### Example 2: Preference Learning
```
Situation: User prefers markdown tables over bullet lists
Action: Update user preferences
Result: Future responses use markdown tables for similar data
```

### Example 3: Pattern Recognition
```
Situation: Successfully solved similar problem 3 times
Action: Document pattern as reusable skill
Result: New micro-skill created for future use
```

## File Structure

```
~/.openclaw/workspace/
├── memory/
│   ├── learnings/
│   │   ├── api_errors.md
│   │   ├── environment_setup.md
│   │   ├── user_preferences.md
│   │   └── successful_patterns.md
│   └── preferences.md
└── skills/
    └── self-improving-agent/
        └── SKILL.md
```

## Configuration

```yaml
# Optional configuration in workspace
self_improvement:
  # What to capture
  capture_errors: true
  capture_successes: true
  capture_preferences: true
  
  # Storage
  learning_retention_days: 90
  max_learnings_per_file: 100
  
  # Privacy
  exclude_sensitive: true
  hash_identifiable_info: true
  
  # Integration
  enable_evolver_integration: true
  improvement_check_frequency: "weekly"
```

## Quick Start

### Manual Triggering
```bash
# Log a learning manually
echo "After completing this task, evaluate if any learnings should be logged using the self-improvement skill format." | openclaw

# View all learnings
cat ~/.openclaw/workspace/memory/learnings/*.md

# Check improvement status
openclaw skills list | grep -i improve
```

### Automatic Operation
Once installed, the skill automatically:
1. Monitors task execution for learnable moments
2. Captures errors, corrections, and successes
3. Updates memory with new learnings
4. Integrates with Evolver for systematic improvement

## Best Practices

1. **Be specific** — Include context, error, solution, and learning
2. **Categorize** — Use consistent categories for easy retrieval
3. **Prioritize** — Mark high-value learnings for immediate attention
4. **Review regularly** — Periodically review and consolidate learnings
5. **Share learnings** — In multi-agent teams, share relevant learnings

## Safety and Privacy

- **No sensitive data** — Automatically filters passwords, keys, PII
- **Local storage only** — All learnings stay on local machine
- **User control** — Users can review and delete learnings
- **Opt-out available** — Can be disabled per session or globally

---

*"The only true wisdom is in knowing you know nothing — and remembering what you learn along the way."*