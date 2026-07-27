# Graphify Quick Start Guide

## Installation Check

First, verify graphify is installed:

```bash
# Check if virtual environment exists
ls ~/.hermes/venv/graphify

# Activate and check graphify command
source ~/.hermes/venv/graphify/bin/activate
graphify --help
```

If not installed, run:

```bash
python3 -m venv ~/.hermes/venv/graphify
source ~/.hermes/venv/graphify/bin/activate
pip install graphifyy
```

## Basic Commands

### 1. Analyze a Codebase

```bash
# Navigate to your project
cd /path/to/your/project

# Activate virtual environment
source ~/.hermes/venv/graphify/bin/activate

# Run graphify
graphify .
```

### 2. Query the Knowledge Graph

After analysis, query the graph:

```bash
# Basic query
graphify query "What are the main components?" --graph graphify-out/graph.json

# Find specific functionality
graphify query "How is authentication implemented?" --graph graphify-out/graph.json

# Explore dependencies
graphify query "Show me all imports and their relationships" --graph graphify-out/graph.json
```

### 3. Make AI Assistant Graph-Aware

```bash
# For Hermes/OpenClaw environments
graphify claw install
```

This adds graph awareness to your AI assistant's context.

## Common Use Cases

### Understanding a New Codebase

```bash
cd new-project/
source ~/.hermes/venv/graphify/bin/activate
graphify .
# Then open graphify-out/graph.html in browser
# Read graphify-out/GRAPH_REPORT.md
```

### Finding Architecture Patterns

```bash
graphify query "What design patterns are used?" --graph graphify-out/graph.json
graphify query "Show me the module dependency graph" --graph graphify-out/graph.json
```

### Documentation Generation

```bash
graphify query "Generate documentation for the API" --graph graphify-out/graph.json --budget 4000
```

### Code Review Preparation

```bash
graphify query "What are potential code smells or issues?" --graph graphify-out/graph.json
graphify query "Find tightly coupled components" --graph graphify-out/graph.json
```

## Integration with Hermes

### As a Skill

Load the graphify skill when working with codebases:

```bash
# In Hermes, you can use:
terminal "source ~/.hermes/venv/graphify/bin/activate && graphify ."
```

### Automated Analysis

Create a script for regular analysis:

```bash
#!/bin/bash
# analyze-codebase.sh
source ~/.hermes/venv/graphify/bin/activate
graphify .
echo "Analysis complete. Open graphify-out/graph.html to explore."
```

## Tips for Best Results

1. **Exclude unnecessary files** with `.graphifyignore`:
   ```
   node_modules/
   vendor/
   dist/
   *.log
   ```

2. **Start with small directories** to understand the output format

3. **Review GRAPH_REPORT.md first** - it highlights key insights

4. **Use specific queries** rather than broad questions

5. **Save useful queries** with `graphify save-result` for future reference

## Example Workflow

```bash
# 1. Setup
cd my-project
source ~/.hermes/venv/graphify/bin/activate

# 2. Create .graphifyignore if needed
echo -e "node_modules/\nvendor/\n*.log" > .graphifyignore

# 3. Analyze
graphify .

# 4. Explore
open graphify-out/graph.html  # On macOS
# Or: xdg-open graphify-out/graph.html  # On Linux

# 5. Query
graphify query "What's the entry point and main flow?" --graph graphify-out/graph.json
graphify query "Show database interactions" --graph graphify-out/graph.json

# 6. Integrate with AI
graphify claw install
```

## Troubleshooting

### Graphify not found
```bash
source ~/.hermes/venv/graphify/bin/activate
pip install graphifyy
```

### Memory issues
Add to `.graphifyignore`:
```
*.min.js
*.bundle.js
*.map
```

### Slow analysis
Exclude large directories:
```
data/
logs/
build/
```

## Next Steps

1. Try the test script: `scripts/test-graphify.sh`
2. Analyze a real project
3. Explore the interactive HTML graph
4. Integrate with your AI workflow using `graphify claw install`