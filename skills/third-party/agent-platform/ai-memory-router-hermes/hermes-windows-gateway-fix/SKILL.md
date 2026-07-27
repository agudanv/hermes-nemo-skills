---
name: third-party-ai-memory-router-hermes-hermes-windows-gateway-fix
title: Fix Hermes Gateway on Windows
description: Comprehensive guide to troubleshooting and fixing Hermes Gateway startup issues on Windows
trigger: When hermes gateway fails on Windows with process check errors, Unicode encoding errors, or missing imports
platforms: [cli, gateway]
tags: [windows, troubleshooting, gateway, encoding]
---

# Fixing Hermes Gateway on Windows

This skill addresses common Windows-specific issues when running `hermes gateway`.

## Common Errors

1. **Process check error**: `OSError: [WinError 11]` (trying to load malformed program)
2. **Unicode encoding**: `UnicodeEncodeError: 'gbk' codec can't encode character`
3. **Missing imports**: `ImportError: cannot import name 'remove_pid_file'`

## Step-by-Step Fix

### 1. Fix Process Checking (status.py)

The main issue is in `gateway/status.py` where `os.kill()` fails on Windows. The function needs Windows-compatible logic:

```python
def get_running_pid() -> Optional[int]:
    """Windows compatible version."""
    record = _read_pid_record()
    if not record:
        remove_pid_file()
        return None

    try:
        pid = int(record["pid"])
    except (KeyError, TypeError, ValueError):
        remove_pid_file()
        return None

    if sys.platform == "win32":
        # Windows: check file freshness instead of os.kill()
        try:
            pid_path = _get_pid_path()
            mtime = pid_path.stat().st_mtime
            if time.time() - mtime > 300:  # Older than 5 minutes
                remove_pid_file()
                return None
            return pid
        except:
            remove_pid_file()
            return None
    else:
        # Unix/Linux: normal os.kill check
        try:
            os.kill(pid, 0)
            return pid
        except (ProcessLookupError, PermissionError):
            remove_pid_file()
            return None
```

### 2. Fix Unicode Encoding Errors

Windows console uses GBK encoding. Fix Unicode characters in `gateway/run.py`:

```python
# Quick fix script
import re
with open('gateway/run.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace problematic Unicode characters
replacements = [
    ('✓', '[OK]'),
    ('✗', '[FAIL]'),
    ('🧠', '[BRAIN]'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('gateway/run.py', 'w', encoding='utf-8') as f:
    f.write(content)
```

### 3. Create Windows Batch File

Save as `START_HERMES.bat`:

```batch
@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "C:\Users\sap\hermes-agent"

:: Optional: Fix Unicode characters
python -c "
try:
    with open('gateway\\\\run.py', 'r', encoding='utf-8') as f:
        c = f.read()
    if '✓' in c:
        c = c.replace('✓', '[OK]').replace('✗', '[FAIL]')
        with open('gateway\\\\run.py', 'w', encoding='utf-8') as f:
            f.write(c)
        echo Fixed Unicode characters
except:
    pass
"

python hermes gateway
pause
```

### 4. Complete Python Fix Script

Create `fix_windows_gateway.py`:

```python
"""
Complete fix for Hermes Gateway Windows issues
"""
import os
import sys
from pathlib import Path

def fix_all():
    hermes_dir = Path.cwd()
    
    # 1. Set environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 2. Fix Unicode in gateway/run.py
    run_file = hermes_dir / "gateway" / "run.py"
    if run_file.exists():
        with open(run_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace checkmarks
        if '✓' in content or '✗' in content:
            content = content.replace('✓', '[OK]').replace('✗', '[FAIL]')
            with open(run_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Fixed Unicode characters")
    
    # 3. Clean PID file
    try:
        from hermes_constants import HERMES_HOME
        pid_file = HERMES_HOME / "gateway.pid"
        if pid_file.exists():
            pid_file.unlink()
            print("Cleaned PID file")
    except:
        pass
    
    # 4. Start gateway
    print("Starting Hermes Gateway...")
    os.system(f"{sys.executable} hermes gateway")

if __name__ == "__main__":
    fix_all()
```

## Quick Commands

```bash
# Fix and start in one command
cd C:\Users\sap\hermes-agent
python -c "import os; os.environ['PYTHONIOENCODING']='utf-8'; import sys; sys.path.insert(0,'.'); from hermes_cli.main import main; sys.argv=['hermes','gateway']; main()"
```

## Verification Steps

1. Check process checking works:
   ```python
   python -c "from gateway.status import get_running_pid; print('OK' if get_running_pid() is None else 'Running')"
   ```

2. Check no Unicode errors:
   ```python
   python -c "with open('gateway/run.py', 'r', encoding='utf-8') as f: print('✓' in f.read())"
   ```

3. Start gateway:
   ```bash
   python hermes gateway
   ```

## Pitfalls and Solutions

| Problem | Solution |
|---------|----------|
| `OSError: [WinError 11]` | Replace `os.kill()` with file time check in `status.py` |
| `UnicodeEncodeError` | Replace ✓/✗ with [OK]/[FAIL] in `gateway/run.py` |
| `ImportError` | Ensure `status.py` has all required functions |
| GBK encoding errors | Set `PYTHONIOENCODING=utf-8` and `chcp 65001` |

## Related Skills

- Check `hermes-windows-wsl-gateway` for WSL-specific issues
- Check `gateway-troubleshooting` for general gateway problems