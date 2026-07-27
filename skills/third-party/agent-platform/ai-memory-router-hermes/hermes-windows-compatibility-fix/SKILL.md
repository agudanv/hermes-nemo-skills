---
name: third-party-ai-memory-router-hermes-hermes-windows-compatibility-fix
description: Fix Hermes compatibility issues on Windows - fcntl module errors, file locking, process management, and Unicode display
tags: [windows, compatibility, hermes, fcntl, msvcrt, file-locking]
created: 2026-04-08
updated: 2026-04-08
---

# Hermes Windows Compatibility Fix

Fix common Windows compatibility issues when running Hermes on Windows systems.

## When to Use

Use this skill when you encounter:
- `No module named 'fcntl'` errors on Windows
- `OSError: [WinError 11]` when starting Hermes gateway
- Unicode character display issues in Windows terminal
- Process management failures on Windows
- File locking compatibility problems

## The Problem

Hermes uses Unix-specific modules and patterns that don't work on Windows:
1. `fcntl` module is Unix-only (Windows uses `msvcrt`)
2. `os.kill(pid, 0)` for process checking fails on Windows
3. Unicode characters (✓, ✗, 🧠, etc.) display incorrectly
4. File locking mechanisms differ between platforms

## Solution Steps

### 1. Fix memory_tool.py fcntl imports

Replace Unix-only `fcntl` imports with cross-platform file locking:

```python
# Cross-platform file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False
```

### 2. Fix _file_lock() function

Update the file locking function to work on both Unix and Windows:

```python
@staticmethod
@contextmanager
def _file_lock(path: Path):
    """Acquire an exclusive file lock for read-modify-write safety."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = open(lock_path, "w")
    try:
        # Cross-platform file locking
        if HAS_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_EX)
        elif HAS_MSVCRT:
            msvcrt.locking(fd.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # No file locking available, just proceed
            pass
        yield
    finally:
        if HAS_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_UN)
        elif HAS_MSVCRT:
            msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
        fd.close()
```

### 3. Fix Windows process checking

Replace `gateway/status.py` with Windows-compatible version:

```python
import os
import json
import time
from pathlib import Path

def get_running_pid():
    """Get the PID of a running Hermes Gateway process on Windows."""
    pid_file = _pid_file_path()
    if not pid_file.exists():
        return None
    
    try:
        with open(pid_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pid = data.get('pid')
        started_at = data.get('started_at', 0)
        
        if not pid:
            return None
        
        # On Windows, check if PID file was recently modified
        file_mtime = pid_file.stat().st_mtime
        current_time = time.time()
        
        # If file modified in last 5 minutes, assume process is running
        if current_time - file_mtime < 300:  # 5 minutes
            return pid
        else:
            # File is stale, remove it
            remove_pid_file()
            return None
            
    except (json.JSONDecodeError, OSError):
        return None
```

### 4. Fix Unicode character display

Replace special Unicode characters with text equivalents in gateway files:

```python
# Replace these Unicode characters:
replacements = {
    '✓': '[OK]',
    '✗': '[FAIL]',
    '🧠': '[BRAIN]',
    '⚠': '[WARN]',
    '⚡': '[FAST]',
    '🔒': '[LOCK]',
    '🔓': '[UNLOCK]'
}
```

### 5. Create Windows startup script

Create `HERMES_WINDOWS.bat`:

```batch
@echo off
chcp 65001 >nul
title Hermes Gateway - Windows 版本
color 0A

echo.
echo 启动 Hermes Gateway (Windows 兼容版)...
echo.

cd /d "C:\Users\sap\hermes-agent"

:: Set Windows-compatible environment variables
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set HERMES_WINDOWS_MODE=1

:: Clean old PID file
python -c "import os, json, time, sys; sys.path.insert(0, '.'); from gateway.status import remove_pid_file; remove_pid_file()"

echo.
echo ===============================================
echo   正在启动 Hermes Gateway...
echo   按 Ctrl+C 停止程序
echo ===============================================
echo.

python hermes gateway
```

### 6. Create model switching script

Create `SWITCH_MODEL.bat` for easy model switching:

```batch
@echo off
chcp 65001 >nul
title Hermes 模型切换器
color 0A

echo.
echo 请选择要切换的模型:
echo 1. DeepSeek (deepseek-chat) - 免费，中文优秀
echo 2. OpenAI GPT-4o (gpt-4o) - 全能，速度快
echo 3. Claude Sonnet (claude-sonnet-4-6) - 长上下文
echo 4. Google Gemini (gemini-2.5-pro) - 多模态
echo 5. Kimi (kimi-k2.5) - 中文优秀
echo.
set /p choice=请输入数字 (1-5):

if "%choice%"=="1" set MODEL=deepseek-chat
if "%choice%"=="2" set MODEL=gpt-4o
if "%choice%"=="3" set MODEL=claude-sonnet-4-6
if "%choice%"=="4" set MODEL=gemini-2.5-pro
if "%choice%"=="5" set MODEL=kimi-k2.5

echo.
echo 正在切换到 %MODEL% ...
python hermes setup --model %MODEL%

echo.
echo 切换完成！当前模型: %MODEL%
echo 测试: python hermes "你好，测试一下新模型"
pause
```

## Verification Steps

After applying fixes, verify with:

```bash
# Test memory_tool import
python -c "from tools.memory_tool import MemoryTool; print('✅ memory_tool import OK')"

# Test gateway status import
python -c "from gateway.status import get_running_pid; print('✅ gateway status import OK')"

# Test Hermes startup
python hermes gateway --version
```

## Pitfalls and Troubleshooting

### Common Issues

1. **Syntax errors after patching**
   - Check indentation in modified files
   - Look for duplicate imports or code blocks

2. **Windows still shows Unicode errors**
   - Ensure terminal uses UTF-8: `chcp 65001`
   - Check all gateway files for remaining Unicode chars

3. **Process checking still fails**
   - Verify `gateway/status.py` was completely replaced
   - Check PID file permissions

4. **File locking not working**
   - Test with simple Python script to verify locking works
   - Check if `msvcrt` module is available

### Windows-Specific Notes

1. **Environment variables**
   - Set `PYTHONIOENCODING=utf-8`
   - Set `PYTHONUTF8=1`
   - Set `HERMES_WINDOWS_MODE=1`

2. **Terminal encoding**
   - Always use `chcp 65001` for UTF-8
   - Use compatible fonts (Consolas, Cascadia Code)

3. **Path separators**
   - Use `\\` in batch files, `/` in Python
   - Be careful with path conversions between WSL and Windows

## Related Skills

- `hermes-windows-setup-and-provider-config` - Initial Windows setup
- `hermes-windows-wsl-gateway` - WSL-specific gateway issues
- `github-auth` - GitHub authentication on Windows

## References

Created after fixing Windows compatibility for Hermes installation that had:
- `No module named 'fcntl'` errors
- `OSError: [WinError 11]` when starting gateway
- Unicode display issues
- Process management failures

The solution creates a complete Windows-compatible Hermes environment with easy model switching and startup scripts.