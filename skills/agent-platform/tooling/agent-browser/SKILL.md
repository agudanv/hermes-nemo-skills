---
name: agent-agent-browser
description: "A headless browser automation CLI that lets AI agents control web pages through structured commands. Enables navigation, interaction, and data capture across pages. Use when the agent needs to automate web tasks, scrape data, fill forms, click elements, take screenshots, or interact with dynamic web applications. Trigger on phrases like 'browse to', 'click the', 'fill form', 'scrape data', 'take screenshot', or 'automate web task'."
---

# Agent Browser — Headless Web Automation

## Overview

Agent Browser transforms AI agents into **web automation experts** capable of controlling real browsers to navigate, interact with, and extract data from web pages. It provides a structured CLI interface for headless (or headed) browser automation without requiring manual scripting.

## Core Capabilities

### 1. Browser Control
```bash
# Launch browser session
agent-browser start --headless  # Run without visible window
agent-browser start --headed    # Show browser for debugging

# Navigate to URLs
agent-browser goto "https://example.com"
agent-browser goto "https://github.com" --wait 5000  # Wait 5 seconds

# Navigate history
agent-browser back
agent-browser forward
agent-browser reload
```

### 2. Page Interaction
```bash
# Click elements
agent-browser click "button#submit"
agent-browser click "text=Login"
agent-browser click "xpath=//button[@type='submit']"

# Fill forms
agent-browser fill "input#username" "myusername"
agent-browser fill "input[name='password']" "mypassword"
agent-browser fill "textarea" "Long text content..."

# Type text (character by character)
agent-browser type "input.search" "search query"

# Select dropdowns
agent-browser select "select#country" "United States"
agent-browser select "select[name='category']" "value=tech"
```

### 3. Data Extraction
```bash
# Extract text content
agent-browser text "div.content" --output content.txt
agent-browser text "h1, h2, h3" --format json

# Extract HTML
agent-browser html "table.data" --output table.html
agent-browser html "div.article" --clean

# Extract attributes
agent-browser attr "a.link" "href" --output links.txt
agent-browser attr "img" "src,alt" --format csv

# Screenshots
agent-browser screenshot --full-page --output page.png
agent-browser screenshot "div.widget" --output widget.png
```

### 4. Advanced Operations
```bash
# Execute JavaScript
agent-browser js "window.scrollTo(0, document.body.scrollHeight)"
agent-browser js "return document.title" --output title.txt

# Wait for conditions
agent-browser wait "div.loaded" --timeout 10000
agent-browser wait "text=Success" --visible

# Handle alerts and dialogs
agent-browser alert accept  # Click OK
agent-browser alert dismiss # Click Cancel
agent-browser alert text "Enter value" --input "test"

# Manage cookies
agent-browser cookies get --output cookies.json
agent-browser cookies set "session_id" "abc123" --domain ".example.com"
```

## When to Use This Skill

### Scenario 1: Web Scraping & Data Collection
```
Task: "Collect product prices from e-commerce site"
Agent Browser Usage:
1. Navigate to product category page
2. Extract product names and prices
3. Paginate through results
4. Export to structured format
```

### Scenario 2: Form Automation
```
Task: "Automate login and form submission"
Agent Browser Usage:
1. Navigate to login page
2. Fill username and password
3. Click login button
4. Wait for dashboard to load
5. Fill complex multi-step form
6. Submit and verify success
```

### Scenario 3: Web Application Testing
```
Task: "Test user registration flow"
Agent Browser Usage:
1. Navigate to registration page
2. Fill all required fields
3. Submit form
4. Verify confirmation message
5. Check email inbox (if accessible)
6. Take screenshots for documentation
```

### Scenario 4: Content Monitoring
```
Task: "Monitor news website for updates"
Agent Browser Usage:
1. Navigate to news site
2. Extract latest headlines
3. Compare with previous snapshot
4. Send alert if new content found
5. Archive screenshots of changes
```

## Installation & Setup

### Quick Install
```bash
# Install via npm (recommended)
npm install -g @thesethrose/agent-browser-cli

# Or via package manager
pip install agent-browser

# Verify installation
agent-browser --version
```

### Browser Requirements
```bash
# Install required browsers
# Chrome/Chromium (recommended)
agent-browser setup chrome

# Firefox
agent-browser setup firefox

# Check browser availability
agent-browser browsers list
```

### OpenClaw Integration
```bash
# Copy skill to workspace
mkdir -p ~/.openclaw/workspace/skills/agent-browser
cp agent-browser-skill.md ~/.openclaw/workspace/skills/agent-browser/SKILL.md

# Test integration
echo "Browse to example.com and take screenshot" | openclaw
```

## Command Reference

### Navigation Commands
```bash
# Basic navigation
goto <url>                    # Navigate to URL
back                         # Go back
forward                      # Go forward  
reload                       # Reload page
wait <ms>                    # Wait milliseconds
wait <selector>              # Wait for element

# Frame management
frame <selector>             # Switch to frame
frame top                    # Switch to top frame
frames list                  # List all frames
```

### Interaction Commands
```bash
# Mouse actions
click <selector>             # Click element
dblclick <selector>          # Double click
rightclick <selector>        # Right click
hover <selector>             # Hover over element

# Keyboard actions
type <selector> <text>       # Type text
press <key>                  # Press key (Enter, Tab, etc.)
hotkey <modifier+key>        # Press hotkey (Ctrl+C, etc.)

# Form actions
fill <selector> <value>      # Fill input field
select <selector> <option>   # Select dropdown option
check <selector>             # Check checkbox
uncheck <selector>           # Uncheck checkbox
```

### Extraction Commands
```bash
# Content extraction
text <selector>              # Get text content
html <selector>              # Get HTML content
attr <selector> <attribute>  # Get attribute value

# Screenshots
screenshot                   # Capture viewport
screenshot --full-page       # Capture entire page
screenshot <selector>        # Capture element

# Page info
title                        # Get page title
url                          # Get current URL
cookies                      # Get cookies
localstorage                 # Get local storage
```

### JavaScript Execution
```bash
# Execute JS
js <code>                    # Execute JavaScript
js <code> --return           # Execute and return value

# Common JS operations
js "window.scrollTo(0, 1000)"           # Scroll down
js "document.querySelector('button').click()"  # Click via JS
js "return document.body.innerText"     # Return page text
```

## Best Practices

### 1. Element Selection
```bash
# Prefer stable selectors
agent-browser click "button[data-testid='submit']"  # Good: data attribute
agent-browser click "button#login-button"           # Good: ID selector
agent-browser click "text=Submit"                   # Good: text content

# Avoid fragile selectors  
agent-browser click "div:nth-child(3) > button"     # Bad: positional
agent-browser click "button.btn-primary"            # Caution: may change
```

### 2. Waiting Strategies
```bash
# Always wait after navigation
agent-browser goto "https://example.com" --wait 2000

# Wait for specific elements
agent-browser wait "div.loaded" --timeout 10000

# Combine waits with interactions
agent-browser goto "login.page"
agent-browser wait "input#username"
agent-browser fill "input#username" "user"
```

### 3. Error Handling
```bash
# Use try-catch for robustness
agent-browser try "click button.submit" --catch "click button[type='submit']"

# Set reasonable timeouts
agent-browser config set default_timeout 30000

# Enable logging for debugging
agent-browser --log-level debug click "button.submit"
```

### 4. Performance Optimization
```bash
# Use headless mode for automation
agent-browser start --headless

# Disable images for faster loading
agent-browser config set disable_images true

# Use caching when appropriate
agent-browser cache enable
```

## Integration Examples

### With Agent Reach
```bash
# Combine browser automation with content reading
# 1. Use Agent Browser to navigate and interact
agent-browser goto "https://twitter.com/search?q=OpenClaw"
agent-browser wait "article[data-testid='tweet']"
agent-browser screenshot --full-page --output tweets.png

# 2. Use Agent Reach to extract and process content
agent-reach extract tweets.png --format markdown --output tweets.md
```

### With Multi-Search Engine
```bash
# Automated search and data collection
# 1. Search using multiple engines
multi-search "OpenClaw skills" --engines google,github --limit 20

# 2. Automate browser to visit top results
for url in search_results:
    agent-browser goto url
    agent-browser text "body" --output "${url_slug}.txt"
    agent-browser screenshot --output "${url_slug}.png"
```

### With ClawTeam
```python
# Distributed web automation team
def create_browser_team():
    """Create team for web automation tasks"""
    
    team = {
        "navigator": {
            "role": "Navigate to URLs and handle page loading",
            "commands": ["goto", "wait", "back", "forward"]
        },
        "interactor": {
            "role": "Interact with page elements",
            "commands": ["click", "fill", "type", "select"]
        },
        "extractor": {
            "role": "Extract data and take screenshots",
            "commands": ["text", "html", "screenshot", "attr"]
        },
        "validator": {
            "role": "Validate results and handle errors",
            "commands": ["validate", "retry", "fallback"]
        }
    }
    
    return team
```

### With Self-Improving Agent
```python
# Learn from browser automation patterns
def learn_browser_patterns():
    """Record successful browser interaction patterns"""
    
    patterns = {
        "login_flow": {
            "steps": [
                "goto login_url",
                "wait input#username",
                "fill input#username {username}",
                "fill input#password {password}",
                "click button[type='submit']",
                "wait div.dashboard"
            ],
            "success_rate": 0.95,
            "average_time": 8.2
        },
        "form_submission": {
            "steps": [
                "wait form",
                "fill all inputs",
                "validate required fields",
                "click button.submit",
                "wait .success-message"
            ],
            "success_rate": 0.88,
            "average_time": 12.5
        }
    }
    
    return patterns
```

## Use Case Examples

### Use Case 1: E-commerce Price Monitoring
```bash
#!/bin/bash
# Monitor prices on Amazon

# Navigate to product page
agent-browser goto "https://www.amazon.com/dp/B08N5WRWNW"

# Extract product information
agent-browser text "#productTitle" --output product_title.txt
agent-browser text ".a-price-whole" --output price.txt
agent-browser attr "img#landingImage" "src" --output image_url.txt

# Check availability
agent-browser text "#availability" --output availability.txt

# Take screenshot for record
agent-browser screenshot --full-page --output "product_$(date +%Y%m%d).png"

# Compare with previous price
current_price=$(cat price.txt)
previous_price=$(cat previous_price.txt 2>/dev/null || echo "0")

if [ "$current_price" != "$previous_price" ]; then
    echo "Price changed: $previous_price -> $current_price"
    # Send notification
fi

echo "$current_price" > previous_price.txt
```

### Use Case 2: Social Media Automation
```bash
#!/bin/bash
# Automated Twitter posting

# Login to Twitter
agent-browser goto "https://twitter.com/login"
agent-browser wait "input[name='text']"
agent-browser fill "input[name='text']" "$TWITTER_USERNAME"
agent-browser click "text=Next"

agent-browser wait "input[name='password']"
agent-browser fill "input[name='password']" "$TWITTER_PASSWORD"
agent-browser click "text=Log in"

# Wait for login to complete
agent-browser wait "a[href='/compose/tweet']"

# Compose tweet
agent-browser click "a[href='/compose/tweet']"
agent-browser wait "div[data-testid='tweetTextarea_0']"
agent-browser click "div[data-testid='tweetTextarea_0']"
agent-browser type "div[data-testid='tweetTextarea_0']" "Check out this amazing OpenClaw skill: Agent Browser! #OpenClaw #Automation"

# Add image if provided
if [ -f "$IMAGE_PATH" ]; then
    agent-browser click "input[data-testid='fileInput']"
    # File upload would require additional handling
fi

# Post tweet
agent-browser click "div[data-testid='tweetButton']"

# Verify post
agent-browser wait "text=Your Tweet was sent"
agent-browser screenshot --output "tweet_$(date +%Y%m%d_%H%M%S).png"
```

### Use Case 3: Web Application Testing
```bash
#!/bin/bash
# Automated user registration test

TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"

# Navigate to registration page
agent-browser goto "https://app.example.com/register"

# Fill registration form
agent-browser fill "input[name='email']" "$TEST_EMAIL"
agent-browser fill "input[name='password']" "$TEST_PASSWORD"
agent-browser fill "input[name='password_confirm']" "$TEST_PASSWORD"
agent-browser fill "input[name='full_name']" "Test User"
agent-browser select "select[name='country']" "United States"

# Accept terms
agent-browser click "input[name='terms']"

# Submit form
agent-browser click "button[type='submit']"

# Wait for confirmation
agent-browser wait "text=Registration successful" --timeout 15000

if [ $? -eq 0 ]; then
    echo "✓ Registration test passed"
    agent-browser screenshot --output "registration_success_$(date +%Y%m%d).png"
else
    echo "✗ Registration test failed"
    agent-browser screenshot --output "registration_failure_$(date +%Y%m%d).png"
    
    # Check for error messages
    agent-browser text ".error-message" --output error.txt
    echo "Error: $(cat error.txt)"
fi
```

## Configuration

```yaml
# ~/.agent-browser/config.yaml
agent_browser:
  # Browser settings
  browser:
    default: "chrome"  # or: firefox, edge, safari
    headless: true
    window_size: "1920x1080"
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
  # Performance
  performance:
    timeout: 30000  # milliseconds
    wait_time: 2000  # default wait after actions
    retry_attempts: 3
    delay_between_retries: 1000
    
  # Stealth & evasion
  stealth:
    disable_images: false
    block_third_party: false
    random_delays: true
    min_delay: 100
    max_delay: 3000
    
  # Screenshots
  screenshots:
    default_format: "png"
    default_quality: 90
    directory: "./screenshots"
    auto_timestamp: true
    
  # Logging
  logging:
    level: "info"  # debug, info, warn, error
    file: "./agent-browser.log"
    console: true
    
  # Integration
  integration:
    openclaw:
      enabled: true
      auto_load: true
      
    memos_sync:
      enabled: false  # Screenshots to MemOS
      
    proactive_agent:
      enabled: true
      monitor_browser_sessions: true
```

## Troubleshooting

### Common Issues

1. **Browser not launching**
   ```bash
   # Check browser installation
   agent-browser browsers list
   
   # Install missing browser
   agent-browser setup chrome
   
   # Check permissions
   chmod +x $(which agent-browser)
   ```

2. **Element not found**
   ```bash
   # Take screenshot to see current page
   agent-browser screenshot --output debug.png
   
   # List all elements matching selector
   agent-browser query "button" --all
   
   # Use more specific selector
   agent-browser click "button[data-testid='submit']" --instead-of "button.submit"
   ```

3. **Timeout errors**
   ```bash
   # Increase timeout
   agent-browser config set default_timeout 60000
   
   # Add explicit waits
   agent-browser wait "div.loaded" --before "click button"
   
   # Check network conditions
