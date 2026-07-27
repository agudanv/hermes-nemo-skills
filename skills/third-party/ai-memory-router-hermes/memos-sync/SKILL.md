---
name: third-party-ai-memory-router-hermes-memos-sync
description: "Synchronize OpenClaw local memory to MemOS master database. Automatically sync memory files, learning logs, preferences, and important events to the centralized MemOS instance at 100.106.127.15:8000. Supports bidirectional sync, conflict resolution, and intelligent memory management."
---

# MemOS Sync — Centralized Memory Synchronization

## Overview

This skill synchronizes OpenClaw's local memory system with a centralized **MemOS database** running at `100.106.127.15:8000` via Tailscale. It enables:

1. **Centralized memory storage** — All memories in one searchable database
2. **Cross-device access** — Access memories from any device
3. **Collaborative memory** — Share memories across team members
4. **Backup and recovery** — Never lose important memories
5. **Advanced search** — Powerful semantic search across all memories

## MemOS API Configuration

### Base Configuration
```yaml
# ~/.openclaw/workspace/memos-config.yaml
memos:
  # MemOS server configuration
  server:
    base_url: "http://100.106.127.15:8000"
    api_prefix: "/product"
    timeout: 30
    retry_attempts: 3
    
  # Authentication (if required)
  auth:
    enabled: false
    token: ""
    user_id: ""
    
  # Sync settings
  sync:
    auto_sync: true
    sync_interval: 300  # seconds
    batch_size: 50
    max_file_size: 10485760  # 10MB
    
  # Memory types to sync
  memory_types:
    - daily_notes    # memory/YYYY-MM-DD.md
    - long_term      # MEMORY.md
    - learnings      # memory/learnings/*.md
    - preferences    # memory/preferences.md
    - skills         # skills/*/SKILL.md (metadata only)
    - events         # Important events and decisions
    
  # Conflict resolution
  conflict_resolution: "server_wins"  # or: local_wins, merge, prompt
```

## Core Sync Operations

### 1. Initial Setup & Health Check
```bash
# Test connection to MemOS
memos-sync health

# Get server status
memos-sync status

# Initialize sync configuration
memos-sync init --server 100.106.127.15:8000
```

### 2. One-Time Full Sync
```bash
# Sync all local memories to MemOS
memos-sync push --all

# Sync specific memory types
memos-sync push --type daily_notes --date 2026-04-01
memos-sync push --type learnings --category technical

# Sync with custom tags
memos-sync push --tag "openclaw" --tag "skills" --tag "installation"
```

### 3. Incremental Sync
```bash
# Sync new memories since last sync
memos-sync push --incremental

# Sync recent daily notes
memos-sync push --recent 7  # Last 7 days

# Sync only changed files
memos-sync push --changed
```

### 4. Pull from MemOS
```bash
# Pull memories from MemOS to local
memos-sync pull --all

# Pull specific memory by ID
memos-sync pull --memory-id "mem_abc123"

# Pull memories with specific tags
memos-sync pull --tag "decision" --tag "important"
```

### 5. Bidirectional Sync
```bash
# Full bidirectional sync
memos-sync sync --bidirectional

# Sync with conflict resolution
memos-sync sync --resolve merge

# Dry run (show what would be synced)
memos-sync sync --dry-run
```

## Memory Mapping

### Local → MemOS Mapping
```
Local Structure                    MemOS Structure
---------------                    ---------------
memory/2026-04-01.md              → Daily memory with date tag
MEMORY.md                         → Long-term curated memories
memory/learnings/api_errors.md    → Learning memory with category
memory/preferences.md             → Preference memory
skills/evolver/SKILL.md           → Skill metadata
workspace/decisions.json          → Decision memory
```

### Memory Metadata
```json
{
  "source": "openclaw",
  "source_id": "local_memory_123",
  "type": "daily_note|learning|preference|skill|event|decision",
  "timestamp": "2026-04-01T09:31:00Z",
  "created_at": "2026-04-01T08:00:00Z",
  "updated_at": "2026-04-01T09:31:00Z",
  "tags": ["openclaw", "skills", "installation", "memOS"],
  "category": "technical|personal|work|learning",
  "priority": "low|medium|high|critical",
  "privacy": "private|shared|public",
  "version": 1,
  "checksum": "sha256:abc123..."
}
```

## API Integration Examples

### 1. Health Check
```python
def check_memos_health():
    """Check if MemOS server is healthy"""
    response = requests.get(
        "http://100.106.127.15:8000/health",
        timeout=10
    )
    return response.status_code == 200
```

### 2. Add Memory
```python
def add_memory_to_memos(content, metadata):
    """Add a memory to MemOS"""
    payload = {
        "content": content,
        "metadata": metadata,
        "tags": metadata.get("tags", []),
        "category": metadata.get("category", "general"),
        "priority": metadata.get("priority", "medium")
    }
    
    response = requests.post(
        "http://100.106.127.15:8000/product/add",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get("memory_id")
    else:
        raise Exception(f"Failed to add memory: {response.text}")
```

### 3. Search Memories
```python
def search_memos(query, filters=None):
    """Search memories in MemOS"""
    payload = {
        "query": query,
        "filters": filters or {},
        "limit": 20,
        "offset": 0
    }
    
    response = requests.post(
        "http://100.106.127.15:8000/product/search",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get("memories", [])
    else:
        raise Exception(f"Search failed: {response.text}")
```

### 4. Get Memory by ID
```python
def get_memory_by_id(memory_id):
    """Retrieve a specific memory"""
    response = requests.get(
        f"http://100.106.127.15:8000/product/get_memory/{memory_id}",
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return None
    else:
        raise Exception(f"Failed to get memory: {response.text}")
```

### 5. Batch Operations
```python
def batch_add_memories(memories):
    """Add multiple memories in batch"""
    responses = []
    for memory in memories:
        try:
            memory_id = add_memory_to_memos(
                memory["content"],
                memory["metadata"]
            )
            responses.append({
                "success": True,
                "memory_id": memory_id,
                "source_id": memory["metadata"].get("source_id")
            })
        except Exception as e:
            responses.append({
                "success": False,
                "error": str(e),
                "source_id": memory["metadata"].get("source_id")
            })
    return responses
```

## Sync Strategies

### Strategy 1: Real-time Sync
```yaml
# Sync immediately when important events occur
triggers:
  - memory file created or modified
  - skill installed or updated
  - important decision made
  - learning captured
  - preference changed
```

### Strategy 2: Scheduled Sync
```bash
# Cron job for regular sync
# Every 5 minutes
*/5 * * * * memos-sync sync --incremental

# Daily full sync at 2 AM
0 2 * * * memos-sync sync --full

# Weekly cleanup and optimization
0 3 * * 0 memos-sync optimize --cleanup
```

### Strategy 3: Event-driven Sync
```python
# Example: Sync when daily note is completed
def on_daily_note_completed(date, content):
    """Sync daily note to MemOS"""
    metadata = {
        "type": "daily_note",
        "date": date,
        "tags": ["daily", "log", date],
        "category": "personal",
        "priority": "medium"
    }
    
    memory_id = add_memory_to_memos(content, metadata)
    
    # Store mapping for future reference
    store_mapping(f"daily_{date}", memory_id)
    
    return memory_id
```

## Conflict Resolution

### Resolution Strategies
```python
def resolve_conflict(local_memory, remote_memory, strategy="server_wins"):
    """Resolve sync conflicts"""
    
    if strategy == "server_wins":
        return remote_memory
        
    elif strategy == "local_wins":
        return local_memory
        
    elif strategy == "merge":
        # Merge content intelligently
        merged = merge_memories(local_memory, remote_memory)
        return merged
        
    elif strategy == "prompt":
        # Ask user to resolve
        resolution = prompt_user_resolution(local_memory, remote_memory)
        return resolution
        
    elif strategy == "new_version":
        # Create new version with both
        return create_merged_version(local_memory, remote_memory)
```

### Merge Algorithm
```python
def merge_memories(local_mem, remote_mem):
    """Intelligently merge two memories"""
    
    # Use newer content as base
    if local_mem["updated_at"] > remote_mem["updated_at"]:
        base = local_mem.copy()
        other = remote_mem
    else:
        base = remote_mem.copy()
        other = local_mem
    
    # Merge tags (unique)
    base_tags = set(base.get("tags", []))
    other_tags = set(other.get("tags", []))
    base["tags"] = list(base_tags.union(other_tags))
    
    # Merge metadata
    for key in ["category", "priority", "privacy"]:
        if key in other and key not in base:
            base[key] = other[key]
    
    # Add merge note
    if "content" in base and "content" in other:
        merge_note = f"\n\n---\n*Merged from local and remote versions*"
        base["content"] += merge_note
    
    return base
```

## Integration with OpenClaw Memory System

### Ready-to-Use Implementation
A complete MemOS sync implementation is available in your workspace:

```bash
# Location of implementation files
ls ~/.openclaw/workspace/scripts/memos_*

# Files included:
# 1. memos_sync.py          - Main sync script
# 2. memos_sync_config.yaml - Configuration
# 3. memos_sync_usage.md    - Usage instructions
# 4. start_memos_sync.bat   - Windows batch script
```

### Quick Test
```bash
# Test connection to MemOS server
cd ~/.openclaw/workspace/scripts
python memos_sync.py --health

# First full sync
python memos_sync.py --full

# Or use the batch script (Windows)
start_memos_sync.bat health
start_memos_sync.bat full
```

### Integration with Daily Workflow
Add to your HEARTBEAT.md or create a cron job:

```bash
# Add to HEARTBEAT.md
- Check MemOS sync status and sync if needed

# Cron job for automatic sync (every 5 minutes)
*/5 * * * * cd ~/.openclaw/workspace/scripts && python memos_sync.py --incremental
```

### Automatic Sync Triggers
```python
# Sync triggers for different memory types
SYNC_TRIGGERS = {
    "memory/*.md": {
        "priority": "medium",
        "delay": 60,  # seconds
        "batch": True
    },
    "MEMORY.md": {
        "priority": "high",
        "delay": 10,
        "batch": False
    },
    "memory/learnings/*.md": {
        "priority": "high",
        "delay": 30,
        "batch": True
    },
    "memory/preferences.md": {
        "priority": "high",
        "delay": 5,
        "batch": False
    }
}
```

## Usage Examples

### Example 1: Daily Sync Workflow
```bash
# Morning: Check sync status
memos-sync status

# During day: Auto-sync important events
# (configured in triggers)

# Evening: Full sync
memos-sync sync --full --verbose

# Verify sync
memos-sync verify --date $(date +%Y-%m-%d)
```

### Example 2: Recovery Workflow
```bash
# Local memory corruption - restore from MemOS
memos-sync pull --type daily_notes --date 2026-04-01
memos-sync pull --type learnings --all
memos-sync pull --type preferences

# Verify restoration
memos-sync verify --local --remote
```

### Example 3: Collaborative Workflow
```bash
# Share memories with team
memos-sync share --tag "team_project" --users "user1,user2"

# Get team memories
memos-sync pull --shared --tag "team_project"

# Merge team insights
memos-sync merge --source team --strategy intelligent
```

### Example 4: Search Across All Memories
```bash
# Search local and remote memories
memos-sync search "OpenClaw技能安装" --global

# Search with filters
memos-sync search "记忆同步" --type learning --date "2026-03-01..2026-04-01"

# Get suggestions
memos-sync suggest --context "MemOS API"
```

## Advanced Features

### 1. Memory Compression & Optimization
```bash
# Compress old memories
memos-sync compress --older-than 30

# Remove duplicates
memos-sync deduplicate --auto

# Optimize storage
memos-sync optimize --strategy balanced
```

### 2. Memory Analytics
```bash
# Get memory statistics
memos-sync stats --detailed

# Analyze memory patterns
memos-sync analyze --pattern frequency

# Export analytics
memos-sync export-analytics --format json --output stats.json
```

### 3. Backup & Migration
```bash
# Create backup
memos-sync backup --output backup.tar.gz

# Migrate to new server
memos-sync migrate --new-server new.memos.example.com

# Verify migration
memos-sync verify-migration --source old --target new
```

## Troubleshooting

### Common Issues

1. **Connection failed**
   ```bash
   # Check Tailscale connection
   tailscale status
   
   # Test direct connection
   curl -v http://100.106.127.15:8000/health
   
   # Check firewall rules
   memos-sync diagnose --network
   ```

2. **Sync conflicts**
   ```bash
   # List conflicts
   memos-sync conflicts --list
   
   # Resolve all conflicts
   memos-sync conflicts --resolve-all --strategy merge
   
   # Manual resolution
   memos-sync conflicts --interactive
   ```

3. **Performance issues**
   ```bash
   # Enable compression
   memos-sync config set compression.enabled true
   
   # Reduce sync frequency
   memos-sync config set sync.interval 600
   
   # Use smaller batches
   memos-sync config set sync.batch_size 20
   ```

4. **Memory not found**
   ```bash
   # Rebuild index
   memos-sync index --rebuild
   
   # Force resync
   memos-sync push --force --all
   
   # Check mappings
   memos-sync mappings --verify
   ```

## Security Considerations

### Data Privacy
```yaml
# Privacy configuration
privacy:
  # Never sync sensitive files
  exclude_patterns:
    - "*password*"
    - "*secret*"
    - "*key*"
    - "*token*"
    - "*credential*"
  
  # Encrypt sensitive memories
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    
  # Anonymize personal data
  anonymize:
    enabled: true
    fields: ["email", "phone", "address"]
```

### Access Control
```bash
# Set memory privacy levels
memos-sync privacy set memory_id --level private
memos-sync privacy set memory_id --level shared --users user1,user2
memos-sync privacy set memory_id --level public

# Audit access
memos-sync audit --user all --timeframe "7d"
```

---

*"记忆不是存储，而是连接。MemOS Sync确保你的每一个重要想法都不会丢失，并且可以在需要时被找到。"*

**记住**: 这个技能将你的本地记忆系统与中央MemOS数据库连接起来，创建了一个强大、可搜索、可共享的记忆生态系统。