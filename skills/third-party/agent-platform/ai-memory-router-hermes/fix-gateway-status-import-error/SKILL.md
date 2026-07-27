---
name: third-party-ai-memory-router-hermes-fix-gateway-status-import-error
title: Fix Hermes Gateway status.py ImportError
description: Diagnose and fix missing import errors in gateway/status.py, particularly 'acquire_scoped_lock' and other missing functions
trigger: When encountering ImportError from gateway.status (e.g., "cannot import name 'acquire_scoped_lock' from 'gateway.status'")
tags: [hermes, gateway, windows, compatibility, import-error]
---

# Fixing Hermes Gateway status.py ImportError

## Problem
Hermes Gateway fails to start with error:
```
ImportError: cannot import name 'acquire_scoped_lock' from 'gateway.status'
```

This typically happens when the `gateway/status.py` file has been replaced with a Windows-compatible version that lacks functions required by platform adapters (feishu.py, discord.py, telegram.py, etc.).

## Root Cause
The Windows-compatible `status.py` contains only basic PID management functions but misses:
- `acquire_scoped_lock` and `release_scoped_lock` - used by all platform adapters for token locking
- `write_runtime_status` and `read_runtime_status` - used for gateway health tracking
- `is_gateway_running` - used by CLI tools

## Solution: Create Hybrid status.py

Create a hybrid version that maintains Windows compatibility while restoring all required functions.

### Step 1: Examine the Current File
```bash
read_file /path/to/hermes-agent/gateway/status.py
```

Check what functions are present. The Windows version typically only has:
- `get_running_pid()`
- `write_pid_file()`
- `remove_pid_file()`
- `release_all_scoped_locks()`

### Step 2: Check Backup File
```bash
read_file /path/to/hermes-agent/gateway/status.py.backup
```

The backup contains the original implementation with all required functions.

### Step 3: Check What's Imported
Search for all imports of `gateway.status` to understand the full scope:
```bash
search_files "from gateway.status import" /path/to/hermes-agent
```

This reveals all required functions.

### Step 4: Create Hybrid Implementation

The hybrid `status.py` should:

1. **Keep Windows PID checking logic**: On Windows, check process existence via file modification time
2. **Add Unix process checking**: On Unix, use `/proc` filesystem and `os.kill()`
3. **Make lock functions platform-aware**: Handle `/proc` access gracefully on Windows
4. **Include all required functions**: See complete list below

### Complete Function List Required

The final `status.py` must include:
- `get_running_pid()` - with platform-specific logic
- `write_pid_file(pid)`
- `remove_pid_file()`
- `acquire_scoped_lock(scope, identity, metadata)`
- `release_scoped_lock(scope, identity)`
- `release_all_scoped_locks()`
- `write_runtime_status()` - with gateway_state, platform, etc. parameters
- `read_runtime_status()`
- `is_gateway_running()`

### Key Implementation Details

#### Platform Detection
```python
import sys
if sys.platform == "win32":
    # Windows-specific logic
else:
    # Unix-specific logic
```

#### Windows Process Checking
On Windows, cannot use `/proc` or `os.kill()` reliably. Instead:
- Check PID file modification time (if < 5 minutes, assume running)
- Return `None` for process start time queries

#### Lock File Paths
```python
def _get_lock_dir() -> Path:
    if sys.platform == "win32":
        # Use HERMES_HOME/gateway/locks on Windows
        hermes_home = Path(os.environ.get('HERMES_HOME', Path.home() / '.hermes'))
        return hermes_home / 'gateway' / 'locks'
    else:
        # Use XDG_STATE_HOME on Unix
        state_home = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        return state_home / "hermes" / "gateway-locks"
```

### Step 5: Test the Fix

Create test script:
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/path/to/hermes-agent')

from gateway.status import (
    get_running_pid,
    write_pid_file,
    remove_pid_file,
    acquire_scoped_lock,
    release_scoped_lock,
    release_all_scoped_locks,
    write_runtime_status,
    read_runtime_status,
    is_gateway_running
)

print("All imports successful!")

# Test lock functions
acquired, existing = acquire_scoped_lock("test", "test-identity", {"test": True})
if acquired:
    release_scoped_lock("test", "test-identity")
```

### Step 6: Verify Gateway Starts
```bash
cd /path/to/hermes-agent
python hermes gateway
```

Should start without ImportError (may show platform configuration warnings).

## Common Pitfalls

1. **Missing hermes_constants**: If `get_hermes_home()` is missing, check `hermes_constants.py` exists
2. **Virtual environment**: Ensure you're in the correct Python environment with all dependencies
3. **Unicode characters**: Windows may have issues with special characters in code - replace ✓/✗ with [OK]/[FAIL]
4. **File permissions**: Ensure status.py is writable

## Verification

Gateway should start with messages like:
```
WARNING gateway.run: Feishu: lark-oapi not installed...
┌─────────────────────────────────────────────────────────┐
│           ⚕ Hermes Gateway Starting...                 │
└─────────────────────────────────────────────────────────┘
```

**No ImportError about `acquire_scoped_lock` or other missing functions.**

## Related Skills
- `hermes-windows-compatibility-fix` - General Windows compatibility fixes
- `hermes-windows-setup-and-provider-config` - Windows setup and configuration