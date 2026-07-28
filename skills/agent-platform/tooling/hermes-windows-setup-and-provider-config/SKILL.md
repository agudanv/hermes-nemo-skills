---
name: agent-hermes-windows-setup-and-provider-config
title: Hermes Windows Setup and Provider Configuration
description: Fix Hermes Gateway startup errors on Windows and configure all major AI providers/models for easy switching
trigger: When encountering Hermes Gateway startup errors on Windows, or when needing to configure multiple AI providers
tags: [hermes, windows, gateway, providers, models, configuration]
difficulty: intermediate
---

# Hermes Windows Setup and Provider Configuration

## Overview
Complete guide to fixing Hermes Gateway startup errors on Windows and configuring all major AI providers (OpenAI, Anthropic, DeepSeek, Google Gemini, etc.) for easy model switching.

## Prerequisites
- Windows system with Python 3.11+
- Hermes Agent installed
- Basic terminal/command prompt knowledge

## Common Windows Issues and Fixes

### 1. Unicode Character Encoding Errors
Hermes uses Unicode symbols that cause issues on Windows:

```python
# Fix by replacing problem characters in gateway/run.py
python -c "
import re
file_path = r'gateway\\run.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('✓', '[OK]')
content = content.replace('✗', '[FAIL]')
content = content.replace('🧠', '[BRAIN]')
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
"
```

### 2. `logout` String Corruption
Random `logout` strings appear in Python files:

```bash
# Find and fix logout strings
cd /mnt/c/Users/sap/hermes-agent
grep -n "logout" gateway/run.py

# Fix the indentation errors around logout strings
# Look for patterns like:
# logout
#        args = event.get_command_args()
# And fix to:
#        args = event.get_command_args()
```

### 3. Windows Process Checking Errors
Windows `os.kill()` compatibility issue:

```python
# Create a Windows-compatible version of gateway/status.py
# Replace os.kill(pid, 0) with file-based process checking
```

### 4. Environment Variables for Windows
```batch
@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python hermes gateway
```

## Complete Provider Configuration

### Step 1: Update config.yaml
Add all major providers to `~/.hermes/config.yaml`:

```yaml
providers:
  openai:
    api: https://api.openai.com/v1
    name: openai
    transport: chat_completions
  anthropic:
    api: https://api.anthropic.com
    name: anthropic
    transport: chat_completions
  deepseek:
    api: https://api.deepseek.com
    name: deepseek
    transport: chat_completions
  gemini:
    api: https://generativelanguage.googleapis.com/v1beta
    name: gemini
    transport: chat_completions
  zai:
    api: https://open.bigmodel.cn/api/paas/v4
    name: zai
    transport: chat_completions
  moonshot:
    api: https://api.moonshot.cn/v1
    name: moonshot
    transport: chat_completions
  openrouter:
    api: https://openrouter.ai/api/v1
    name: openrouter
    transport: chat_completions
  nous:
    api: https://inference-api.nousresearch.com/v1
    name: nous
    transport: chat_completions
```

### Step 2: Create Environment Variables Guide
Create `ENV_VARS.md` with all API key instructions:

```markdown
# Environment Variables Needed

## DeepSeek (Recommended - Free)
- `DEEPSEEK_API_KEY`: Get from https://platform.deepseek.com/api_keys
- Models: deepseek-chat, deepseek-reasoner, deepseek-v3.2

## OpenAI
- `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys
- Models: gpt-5.4, gpt-4o, gpt-4o-mini

## Anthropic (Claude)
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com/settings/keys
- Models: claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5

## Google Gemini
- `GOOGLE_API_KEY`: Get from https://makersuite.google.com/app/apikey
- Models: gemini-2.5-pro, gemini-3.1-pro-preview
```

### Step 3: Create Model Switching Scripts

**SWITCH_MODEL.bat** (Windows):
```batch
@echo off
chcp 65001 >nul
title Hermes Model Switcher
color 0A

echo Available models:
echo   1. deepseek-chat (DeepSeek - Free)
echo   2. gpt-4o (OpenAI)
echo   3. claude-sonnet-4-6 (Anthropic)
echo   4. gemini-2.5-pro (Google)
echo   5. kimi-k2.5 (Moonshot)

set /p MODEL="Enter model name or number: "

if "%MODEL%"=="1" set MODEL=deepseek-chat
if "%MODEL%"=="2" set MODEL=gpt-4o
if "%MODEL%"=="3" set MODEL=claude-sonnet-4-6
if "%MODEL%"=="4" set MODEL=gemini-2.5-pro
if "%MODEL%"=="5" set MODEL=kimi-k2.5

cd /d "C:\Users\sap\hermes-agent"
python hermes setup --model "%MODEL%"
pause
```

**Python configuration script** (UPDATE_CONFIG.py):
```python
#!/usr/bin/env python3
"""
Update Hermes config with all providers
"""
import yaml
import os

config_path = "/path/to/.hermes/config.yaml"
# ... (full script from conversation)
```

## Recommended Models by Use Case

### For Chinese Users (Free)
- `deepseek-chat` - Best free Chinese model
- `kimi-k2.5` - Excellent Chinese, long context
- `glm-5` - Good Chinese, affordable

### For Coding
- `deepseek-reasoner` - Best free coding model
- `gpt-5.3-codex` - OpenAI's coding model
- `deepseek-coder` - Specialized for code

### For General Use
- `gpt-4o` - Fast, capable, balanced
- `claude-sonnet-4-6` - Good reasoning, long context
- `gemini-2.5-pro` - Strong multimodal

## Testing Configuration

Create `TEST_MODELS.bat`:
```batch
@echo off
echo Testing model switching...
python hermes setup --model deepseek-chat
python hermes "Hello, which model am I using?"
python hermes setup --model gpt-4o
python hermes "Hello, which model am I using now?"
pause
```

## Troubleshooting

### Gateway Won't Start
1. Check for Unicode errors in `gateway/run.py`
2. Look for `logout` string corruption
3. Ensure Python environment variables are set:
   ```batch
   set PYTHONIOENCODING=utf-8
   set PYTHONUTF8=1
   ```

### Model Switching Doesn't Work
1. Check API keys are set in environment
2. Verify provider is configured in `config.yaml`
3. Try clearing cache:
   ```bash
   rm -rf ~/.hermes/cache
   hermes setup --model deepseek-chat --force
   ```

### API Connection Errors
1. Check network connectivity
2. Verify API key is valid
3. Check rate limits on the provider's platform

## Quick Reference Commands

```bash
# List all available models
hermes setup --list-models

# Switch to a model
hermes setup --model <model-name>

# Test current model
hermes "What model are you?"

# Check configuration
cat ~/.hermes/config.yaml | grep -A5 "providers:"
```

## Pitfalls to Avoid

1. **Don't edit Python files without backups** - Hermes updates may overwrite changes
2. **Don't hardcode API keys** - Always use environment variables
3. **Test each provider separately** - Don't configure all at once without testing
4. **Keep documentation updated** - When adding new providers, update ENV_VARS.md

## Verification Steps

After configuration:
1. Gateway starts without errors
2. `hermes setup --list-models` shows all providers
3. Can switch between at least 3 different models
4. Each model responds with unique characteristics

## Related Skills
- `hermes-windows-wsl-gateway` - For WSL-specific gateway issues
- `github-auth` - For GitHub Copilot provider setup
- `opencli-skill` - For command-line AI interactions