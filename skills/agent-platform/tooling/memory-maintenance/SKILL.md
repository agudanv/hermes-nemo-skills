---
name: agent-memory-maintenance
description: "Memory maintenance and update procedures for OpenClaw agents - how to properly update MEMORY.md and USER PROFILE files during session resets"
tags: [memory, maintenance, session-reset, openclaw]
---

# Memory Maintenance Skill

## Purpose
This skill provides guidance on how to properly update memory files (MEMORY.md and USER PROFILE) during session resets or when important information needs to be preserved.

## When to Use
- During session reset notifications
- When user shares important preferences or information
- After completing significant tasks or learning lessons
- When discovering new patterns about user behavior

## Memory Structure

### MEMORY.md (Long-term Memory)
- Loaded ONLY in main sessions (direct chats with your human)
- Contains curated memories, significant events, lessons learned
- Should be updated periodically with distilled wisdom from daily logs

### USER PROFILE (User Information)
- Basic user information and preferences
- Context about user's technical skills, location, habits
- Should be updated when new information is learned about the user

### Daily Notes (memory/YYYY-MM-DD.md)
- Raw logs of daily activities
- Created automatically in `memory/` directory
- Source material for updating MEMORY.md

## Update Procedures

### During Session Reset
1. Review the conversation for important facts, preferences, or decisions
2. Check if anything needs to be added to MEMORY.md
3. Update USER PROFILE if new user information was learned
4. Consider creating a skill if a reusable workflow was discovered

### What to Save
**Save to MEMORY.md:**
- Significant technical decisions or fixes
- User preferences discovered (e.g., "prefers concise answers")
- Important events (first conversation, major system changes)
- Lessons learned from mistakes or successes
- System status updates (e.g., "OpenClaw gateway needs pairing")

**Save to USER PROFILE:**
- User's name, pronouns, timezone
- Technical skills and preferences
- Communication style preferences
- Context about user's environment

**Do NOT save:**
- Sensitive personal information (unless explicitly asked to remember)
- Temporary or trivial details
- Information already captured in memory

## Example Updates

### Adding a New Event
```markdown
重要事件时间线 > 2026年4月9日: **会话重置**: 在系统自动重置前进行简短问候交流
```

### Updating User Preferences
```markdown
用户偏好与习惯: **回复风格**: 偏好简洁明了的回答，不喜欢冗长的解释
```

### Recording System Status
```markdown
系统状态: **可用技能**: 当前有102个技能，涵盖17个类别（包括OpenClaw导入技能、MLOps、开发、研究等）
```

## Best Practices

1. **Be selective**: Only save what's truly important for future sessions
2. **Use consistent formatting**: Follow the existing markdown structure
3. **Add dates**: Always include dates for timeline entries
4. **Categorize properly**: Use appropriate sections (基本信息, 重要事件时间线, 用户偏好与习惯, 系统状态)
5. **Review periodically**: Use heartbeats to review and clean up old memory entries

## Verification
After updating memory files:
1. Check that the new entries are properly formatted
2. Ensure no duplicate information was added
3. Verify that sensitive information wasn't accidentally included
4. Test that the information would be useful in a future session

## Related Skills
- proactive-agent - For anticipatory memory management
- self-improving-agent - For learning from experience
- memos-sync - For synchronizing memory to central database