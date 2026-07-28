---
name: agent-hermes-windows-wsl-gateway
description: Troubleshoot and fix Hermes Gateway compatibility issues on Windows and WSL. Specifically addresses Windows process management errors and missing dependencies.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, gateway, windows, wsl, troubleshooting, compatibility]
    related_skills: [hermes-agent]
    platforms: [windows, wsl, linux]
---

# Hermes Gateway Windows/WSL Troubleshooting

This skill addresses common issues when running Hermes Gateway on Windows and WSL environments, particularly process management compatibility errors.

## Common Error Patterns

### Error 1: Windows Process Management Compatibility
```
Traceback (most recent call last):
  File "hermes_cli/gateway.py", line 1305, in run_gateway
    success = asyncio.run(start_gateway(replace=replace, verbosity=verbosity))
  File "asyncio/runners.py", line 190, in run
    return runner.run(main)
  File "asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
  File "gateway/run.py", line 7409, in start_gateway
    existing_pid = get_running_pid()
  File "gateway/status.py", line 370, in get_running_pid
    os.kill(pid, 0)  # signal 0 = existence check, no actual signal sent
OSError: [WinError 11] 试图加载格式不正确的程序
```

**Root Cause**: Hermes uses Unix-style process management (`os.kill(pid, 0)`) which has compatibility issues on native Windows. The `os.kill()` function with signal 0 (process existence check) fails on Windows with error 11.

**Direct Solution**: Patch the `get_running_pid()` function in `gateway/status.py` to be Windows-compatible:

```python
def get_running_pid():
    """
    获取当前运行的 Hermes Gateway 进程 PID
    Windows 兼容版本：跳过有问题的 os.kill 检查
    """
    pid_file = _pid_file_path()
    if not pid_file.exists():
        return None
    
    try:
        with open(pid_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pid = data.get('pid')
        if not pid:
            return None
        
        # Windows 兼容检查：只检查文件是否存在，不调用 os.kill
        if sys.platform == 'win32':
            # 在 Windows 上，我们只检查 PID 文件是否有效
            # 不进行实际的进程检查，避免 "试图加载格式不正确的程序" 错误
            try:
                # 简单检查：如果 PID 文件最近被修改过，假设进程还在运行
                mtime = pid_file.stat().st_mtime
                if time.time() - mtime < 300:  # 5分钟内修改过
                    return pid
                return None
            except:
                return None
        else:
            # Unix/Linux: 正常检查
            try:
                os.kill(pid, 0)
                return pid
            except (OSError, ProcessLookupError):
                return None
                
    except Exception:
        return None
```

**Required imports** (add to top of `gateway/status.py` if missing):
```python
import os
import sys
import json
import time
from pathlib import Path
```

### Error 2: Corrupted Python Files
```
SyntaxError: invalid syntax
  File "/home/sap/hermes-agent/gateway/run.py", line 1063
    "GATEWAY_ALLOWED_USERS")
    ^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: invalid syntax
```

**Root Cause**: Python files may contain corrupted `logout` strings inserted into code, breaking syntax. Common patterns:
- `selflogout` instead of `self`
- `faillogout` instead of `failed` 
- Broken strings across lines
- Missing platform names like `Plogout\nlatform.logout\nSLACK:` instead of `Platform.SLACK:`
- Standalone `logout` lines causing indentation errors

### Error 3: Unicode Encoding Errors in Windows Console
```
--- Logging error ---
Traceback (most recent call last):
  File "C:\Python311\Lib\logging\__init__.py", line 1113, in emit
    stream.write(msg + self.terminator)
UnicodeEncodeError: 'gbk' codec can't encode character '\u2713' in position 42: illegal multibyte sequence
Message: '✓ %s connected'
Arguments: ('webhook',)
```

**Root Cause**: Windows console uses GBK encoding by default, cannot handle Unicode characters like checkmarks (✓ U+2713, ✗ U+2717, 🧠 U+1F9E0) used in Hermes logging.

### Error 4: Missing Function Import Errors
```
ImportError: cannot import name 'remove_pid_file' from 'gateway.status'
```

**Root Cause**: Simplified or corrupted `gateway/status.py` missing required functions that `gateway/run.py` expects to import.

### Error 3: Missing Dependencies in WSL
```
ModuleNotFoundError: No module named 'httpx'
```

**Root Cause**: Python's externally-managed environment restrictions in WSL prevent system-wide package installation.

## Solutions

### Step 0: Fix All Common File Issues

#### Fix Corrupted Python Files
If getting syntax errors, check and fix corrupted files:

```bash
# Search for corrupted 'logout' strings
grep -n "logout" /home/sap/hermes-agent/gateway/run.py

# Remove standalone logout lines (causes indentation errors)
sed -i '/^[[:space:]]*logout[[:space:]]*$/d' /home/sap/hermes-agent/gateway/run.py

# Or using Python:
python3 -c "
with open('/home/sap/hermes-agent/gateway/run.py', 'r', encoding='utf-8') as f:
    lines = [line for line in f if line.strip() != 'logout']
with open('/home/sap/hermes-agent/gateway/run.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Removed standalone logout lines')
"

# Common fixes using patch tool
# Fix broken variable names
patch(mode='replace', path='/home/sap/hermes-agent/gateway/run.py',
      old_string='selflogout', new_string='self', replace_all=True)

# Fix broken strings
patch(mode='replace', path='/home/sap/hermes-agent/gateway/run.py',
      old_string='logger.debug("Plugin command dispatch faillogout\ned (non-fatal): %s", e)',
      new_string='logger.debug("Plugin command dispatch failed (non-fatal): %s", e)')

# Fix broken platform names  
patch(mode='replace', path='/home/sap/hermes-agent/gateway/run.py',
      old_string='elif platform == Plogout\nlatform.logout\nSLACK:',
      new_string='elif platform == Platform.SLACK:')
```

#### Fix Unicode Encoding Errors
Replace Unicode characters that break Windows console:

```bash
# Replace problematic Unicode characters in gateway/run.py
sed -i 's/✓/[OK]/g' /home/sap/hermes-agent/gateway/run.py
sed -i 's/✗/[FAIL]/g' /home/sap/hermes-agent/gateway/run.py
sed -i 's/🧠/[BRAIN]/g' /home/sap/hermes-agent/gateway/run.py

# Or using Python (more reliable):
python3 -c "
with open('/home/sap/hermes-agent/gateway/run.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('🧠', '[BRAIN]')
with open('/home/sap/hermes-agent/gateway/run.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed Unicode characters for Windows compatibility')
"
```

#### Fix Missing Functions in status.py
Ensure `gateway/status.py` has all required functions. If missing, restore from backup or create complete version:

```python
# Check if status.py.backup exists and restore if needed
if [ -f "/home/sap/hermes-agent/gateway/status.py.backup" ]; then
    cp "/home/sap/hermes-agent/gateway/status.py.backup" "/home/sap/hermes-agent/gateway/status.py"
    echo "Restored status.py from backup"
else
    # Create minimal Windows-compatible version with all required functions
    cat > /home/sap/hermes-agent/gateway/status.py << 'EOF'
"""
Gateway runtime status helpers - Windows 兼容版本
"""
import os
import sys
import json
import time
from pathlib import Path
from hermes_constants import get_hermes_home

def _get_pid_path():
    """Return the path to the gateway PID file."""
    home = get_hermes_home()
    return home / "gateway.pid"

def get_running_pid():
    """Get running gateway PID - Windows compatible version."""
    pid_file = _get_pid_path()
    if not pid_file.exists():
        return None
    
    try:
        with open(pid_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pid = data.get('pid')
        if not pid:
            return None
        
        # Windows compatible check
        if sys.platform == 'win32':
            try:
                mtime = pid_file.stat().st_mtime
                if time.time() - mtime < 300:  # 5 minutes
                    return pid
                return None
            except:
                return None
        else:
            # Unix/Linux normal check
            try:
                os.kill(pid, 0)
                return pid
            except (OSError, ProcessLookupError):
                return None
                
    except Exception:
        return None

def remove_pid_file():
    """Remove the gateway PID file if it exists."""
    try:
        _get_pid_path().unlink(missing_ok=True)
    except Exception:
        pass

def write_pid_file():
    """Write current process PID to gateway PID file."""
    pid_file = _get_pid_path()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'pid': os.getpid(),
        'argv': list(sys.argv),
        'platform': sys.platform
    }
    
    with open(pid_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# Add other required functions as needed
def write_runtime_status(**kwargs):
    """Stub function - implement if needed."""
    pass

def read_runtime_status():
    """Stub function - implement if needed."""
    return None

EOF
    echo "Created Windows-compatible status.py with all required functions"
fi
```

### Option 1: Run in WSL (Recommended)

1. **Check current environment**:
   ```bash
   pwd  # Should show /mnt/c/Users/... for Windows filesystem access
   ```

2. **Navigate to Hermes installation**:
   ```bash
   cd /mnt/c/Users/sap/hermes-agent
   ```

3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv hermes_venv
   source hermes_venv/bin/activate
   ```

4. **Install core dependencies**:
   ```bash
   pip install httpx openai python-dotenv fire rich tenacity prompt_toolkit pyyaml requests jinja2 pydantic PyJWT debugpy
   ```

5. **Check for existing Hermes processes**:
   ```bash
   pgrep -f hermes
   # If any processes found, kill them:
   kill <PID>
   ```

6. **Run Hermes Gateway**:
   ```bash
   python hermes gateway
   ```

### Option 2: Fix Windows Native Installation

1. **Ensure Python is properly installed**:
   ```powershell
   python --version
   pip --version
   ```

2. **Install Hermes in Windows Python environment**:
   ```powershell
   cd C:\Users\sap\hermes-agent
   pip install -e .
   ```

3. **Check Windows PATH**:
   ```powershell
   where hermes
   # If not found, add Python Scripts directory to PATH
   ```

4. **Create Windows startup scripts**:

   **Simple batch file** (`GO.bat`):
   ```batch
   @echo off
   chcp 65001 >nul
   title Hermes Gateway
   color 0A
   
   echo.
   echo 启动 Hermes Gateway...
   echo.
   
   cd /d "C:\Users\sap\hermes-agent"
   
   set PYTHONIOENCODING=utf-8
   set PYTHONUTF8=1
   
   python hermes gateway
   
   pause
   ```

   **Comprehensive cleanup script** (`CLEAN_START.bat`):
   ```batch
   @echo off
   chcp 65001 >nul
   title Hermes Gateway - 完全清理启动
   color 0A
   
   echo ===============================================
   echo    Hermes Gateway 完全清理启动
   echo   解决所有已知问题
   echo ===============================================
   echo.
   
   cd /d "C:\Users\sap\hermes-agent"
   
   :: 1. 清理所有 logout 字符串
   echo [1/4] 清理文件错误...
   python -c "
   import re
   
   file_path = r'gateway\\run.py'
   print('检查文件:', file_path)
   
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()
   
   # 查找并修复所有 logout 字符串
   logout_count = content.count('logout')
   if logout_count > 0:
       print(f'找到 {logout_count} 个 logout 字符串，正在修复...')
       # 删除独立的 logout 行
       lines = content.split('\\n')
       cleaned_lines = []
       for line in lines:
           if line.strip() == 'logout':
               continue
           cleaned_lines.append(line)
       
       content = '\\n'.join(cleaned_lines)
       
       with open(file_path, 'w', encoding='utf-8') as f:
           f.write(content)
       
       print('修复完成！')
   else:
       print('没有找到 logout 字符串')
   "
   
   :: 2. 修复 Unicode 字符
   echo [2/4] 修复 Unicode 字符...
   python -c "
   import re
   
   file_path = r'gateway\\run.py'
   print('修复 Unicode 字符...')
   
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()
   
   # 简单替换所有问题字符
   content = content.replace('✓', '[OK]')
   content = content.replace('✗', '[FAIL]')
   content = content.replace('🧠', '[BRAIN]')
   
   with open(file_path, 'w', encoding='utf-8') as f:
       f.write(content)
   
   print('Unicode 字符已修复')
   "
   
   :: 3. 清理 PID 文件
   echo [3/4] 清理状态文件...
   python -c "
   import os
   import sys
   
   sys.path.insert(0, '.')
   try:
       from gateway.status import remove_pid_file, release_all_scoped_locks
       remove_pid_file()
       removed = release_all_scoped_locks()
       print(f'已清理 PID 文件和锁文件')
   except Exception as e:
       print(f'状态清理: {e}')
   "
   
   :: 4. 设置环境并启动
   echo [4/4] 启动 Hermes Gateway...
   echo.
   echo ===============================================
   echo   正在启动 Hermes Gateway...
   echo   按 Ctrl+C 停止程序
   echo ===============================================
   echo.
   
   set PYTHONIOENCODING=utf-8
   set PYTHONUTF8=1
   
   python hermes gateway
   
   echo.
   echo ===============================================
   echo   Hermes Gateway 已停止
   echo ===============================================
   pause
   ```

   **PowerShell script** (`Start-Hermes.ps1`):
   ```powershell
   $hermesPath = "C:\Users\sap\hermes-agent"
   Set-Location $hermesPath
   
   # Set environment variables for UTF-8 support
   $env:PYTHONIOENCODING = "utf-8"
   $env:PYTHONUTF8 = "1"
   
   # Set console to UTF-8
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   
   # Start Hermes Gateway
   python hermes gateway
   ```

5. **Try alternative startup**:
   ```powershell
   # Use the batch file
   .\START_HERMES.bat
   
   # Or run directly
   python hermes gateway
   ```

### Option 3: Hybrid Approach (WSL with Windows Integration)

1. **Create WSL startup script**:
   ```bash
   cat > ~/start_hermes_gateway.sh << 'EOF'
   #!/bin/bash
   cd /mnt/c/Users/sap/hermes-agent
   source hermes_venv/bin/activate
   python hermes gateway
   EOF
   
   chmod +x ~/start_hermes_gateway.sh
   ```

2. **Create Windows shortcut**:
   ```powershell
   # Create a PowerShell script
   @"
   wsl bash -c "~/start_hermes_gateway.sh"
   "@ | Out-File -FilePath "$HOME\Desktop\Start Hermes Gateway.ps1" -Encoding UTF8
   ```

## Verification Steps

1. **Check gateway is running**:
   ```bash
   pgrep -f hermes
   ```

2. **Check logs for errors**:
   ```bash
   tail -f ~/.hermes/logs/gateway.log
   ```

3. **Verify no platform errors** (warning about no platforms configured is normal):
   ```
   WARNING gateway.run: No adapter available for feishu
   ERROR gateway.run: Gateway failed to connect any configured messaging platform
   ```
   
   This is expected if you haven't configured Telegram, Discord, etc.

## Platform Configuration

If you want to configure messaging platforms:

1. **Run setup wizard**:
   ```bash
   hermes gateway setup
   ```

2. **Configure specific platform** (e.g., Telegram):
   ```bash
   # Set environment variable
   export TELEGRAM_BOT_TOKEN="your_token_here"
   
   # Or add to ~/.hermes/.env
   echo "TELEGRAM_BOT_TOKEN=your_token_here" >> ~/.hermes/.env
   ```

## Troubleshooting Checklist

### If gateway won't start:
- [ ] Check for existing processes: `pgrep -f hermes`
- [ ] Kill existing processes: `kill <PID>`
- [ ] Verify Python virtual environment is activated
- [ ] Check dependencies: `pip list | grep -E "httpx|openai|pydantic"`
- [ ] Look for permission issues in `~/.hermes/logs/`
- [ ] Check for Unicode characters in logs: `grep -n "[✓✗🧠]" gateway/run.py`
- [ ] Check for malformed strings: `grep -n "logout" gateway/run.py`
- [ ] Verify status.py has all required functions: `python -c "from gateway.status import get_running_pid, remove_pid_file"`
- [ ] Set Windows environment variables: `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`

### If getting "externally-managed-environment" error:
- [ ] Always use virtual environment in WSL
- [ ] Never use `--break-system-packages`
- [ ] Use `python3 -m venv venv_name` to create isolated environment

### If gateway starts but immediately exits:
- [ ] Check `~/.hermes/logs/gateway.log` for detailed errors
- [ ] Verify no port conflicts (default port 8080)
- [ ] Check disk space and permissions
- [ ] Note: `hermes gateway` does NOT support `--replace` parameter - remove it if present in startup scripts

## Background Running Options

### Option A: Screen Session (Simplest & Most Reliable)
Create `~/run-hermes-background.sh`:
```bash
#!/bin/bash
SESSION_NAME="hermes-gateway"
HERMES_DIR="/home/sap/hermes-agent"

if screen -list | grep -q "$SESSION_NAME"; then
    echo "Hermes Gateway already running (screen -r $SESSION_NAME)"
    exit 0
fi

cd "$HERMES_DIR"
screen -dmS "$SESSION_NAME" bash -c "source venv/bin/activate && python hermes gateway"

echo "Hermes Gateway started in screen session: $SESSION_NAME"
echo "Connect to view: screen -r $SESSION_NAME"
echo "Detach: Ctrl+A, D"
echo "Stop: Connect then Ctrl+C, then 'exit'"
```

Usage:
```bash
chmod +x ~/run-hermes-background.sh
~/run-hermes-background.sh
```

### Option B: Systemd User Service
Create `~/.config/systemd/user/hermes-gateway.service`:
```ini
[Unit]
Description=Hermes Gateway
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/sap/hermes-agent
ExecStart=/bin/bash -c 'source venv/bin/activate && python hermes gateway'
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway
```

### Option C: System-wide Systemd Service (WSL2)
```bash
sudo nano /etc/systemd/system/hermes-gateway.service
```

Add:
```ini
[Unit]
Description=Hermes Gateway
After=network.target

[Service]
Type=simple
User=sap
WorkingDirectory=/home/sap/hermes-agent
ExecStart=/home/sap/hermes-agent/venv/bin/python hermes gateway
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable hermes-gateway
sudo systemctl start hermes-gateway
```

## Quick Fix Commands

```bash
# One-liner to fix common issues
cd /mnt/c/Users/sap/hermes-agent && \
python3 -c "
import re, sys
with open('gateway/run.py','r',encoding='utf-8') as f: c=f.read()
c=c.replace('✓','[OK]').replace('✗','[FAIL]').replace('🧠','[BRAIN]')
c='\\n'.join([l for l in c.split('\\n') if l.strip()!='logout'])
with open('gateway/run.py','w',encoding='utf-8') as f: f.write(c)
print('Fixed Unicode and logout strings')
"

# Verify fixes
python3 -m py_compile gateway/run.py && echo "Syntax OK" || echo "Syntax error"
python3 -c "from gateway.status import get_running_pid, remove_pid_file" && echo "Imports OK" || echo "Import error"
```

## Environment Setup for Windows

Always set these environment variables for Windows:
```batch
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 65001  # Set console to UTF-8
```

## Related Resources

- [Hermes Agent Documentation](https://hermes-agent.nousresearch.com/docs/)
- [Messaging Platforms Guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)