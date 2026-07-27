---
name: third-party-ai-memory-router-hermes-graphify
description: AI coding assistant skill that turns any folder of code, docs, papers, or images into a queryable knowledge graph. Uses Claude vision to extract concepts and relationships, supports 20+ programming languages via tree-sitter AST.
tags: [code-analysis, knowledge-graph, documentation, visualization, ast]
---

# Graphify Skill

Graphify is an AI coding assistant skill that transforms any folder of code, documentation, papers, or images into a queryable knowledge graph. It uses Claude vision to extract concepts and relationships, and supports 20+ programming languages via tree-sitter AST.

## Features

- **Multimodal analysis**: Works with code, PDFs, markdown, screenshots, diagrams, whiteboard photos, and images
- **20+ language support**: Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Objective-C, Julia
- **Two-pass analysis**: Deterministic AST extraction + Claude subagents for semantic analysis
- **Interactive output**: HTML graph visualization, JSON queryable graph, and audit report
- **Persistent cache**: SHA256-based caching for incremental updates

## Installation

Graphify requires Python 3.10+ and the `graphifyy` package. Install it with:

```bash
# Create virtual environment (if needed)
python3 -m venv ~/.hermes/venv/graphify
source ~/.hermes/venv/graphify/bin/activate

# Install graphifyy
pip install graphifyy
```

## Usage

### Basic Usage

To analyze a directory and create a knowledge graph:

```bash
# Activate the virtual environment first
source ~/.hermes/venv/graphify/bin/activate

# Run graphify on a directory
graphify /path/to/your/codebase
```

Or from within Hermes:

```bash
terminal "source ~/.hermes/venv/graphify/bin/activate && graphify ."
```

### Output Structure

Graphify creates a `graphify-out/` directory with:

- `graph.html` - Interactive graph visualization (click nodes, search, filter)
- `GRAPH_REPORT.md` - Analysis report with god nodes, surprising connections, suggested questions
- `graph.json` - Persistent graph data for querying later
- `cache/` - SHA256 cache for incremental updates

### Querying the Graph

After building a graph, you can query it:

```bash
# Query the graph with a question
graphify query "How does authentication work in this codebase?" --graph graphify-out/graph.json

# Use DFS instead of BFS
graphify query "Find all database-related functions" --dfs

# Limit output tokens
graphify query "Explain the architecture" --budget 1000
```

### Platform Integration

To make your AI assistant always use the graph:

```bash
# For Hermes/OpenClaw-like environments
graphify claw install
```

This writes graph-aware rules to `AGENTS.md` in your project root.

### Excluding Files

Create a `.graphifyignore` file to exclude directories:

```
# .graphifyignore
node_modules/
vendor/
dist/
*.generated.py
```

## Examples

### 1. Analyze Current Directory

```bash
cd /path/to/project
source ~/.hermes/venv/graphify/bin/activate
graphify .
```

### 2. Query Specific Architecture Questions

```bash
graphify query "What are the main components and their relationships?" --graph graphify-out/graph.json
graphify query "Show me all API endpoints" --graph graphify-out/graph.json
graphify query "How is error handling implemented?" --graph graphify-out/graph.json
```

### 3. Save Query Results for Feedback Loop

```bash
graphify save-result --question "How does authentication work?" --answer "Authentication uses JWT tokens..." --type query --nodes auth.js user.js
```

### 4. Benchmark Token Reduction

```bash
graphify benchmark graphify-out/graph.json
```

## How It Works

1. **AST Pass**: Extracts structure from code files (classes, functions, imports, call graphs) using tree-sitter
2. **Claude Subagents**: Run in parallel over docs, papers, images to extract concepts and relationships
3. **Graph Construction**: Merges results into a NetworkX graph with Leiden community detection
4. **Output Generation**: Creates interactive HTML, queryable JSON, and audit report

## Relationship Tags

Every relationship is tagged for transparency:
- `EXTRACTED`: Found directly in source
- `INFERRED`: Reasonable inference with confidence score
- `AMBIGUOUS`: Flagged for review

## Tips

1. **Start small**: Run on a single directory first to understand the output
2. **Use .graphifyignore**: Exclude build artifacts and dependencies
3. **Check GRAPH_REPORT.md**: Always review the audit report first
4. **Query strategically**: Start with broad questions, then drill down
5. **Save useful queries**: Use `save-result` to build a knowledge base

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all tree-sitter language parsers are installed
2. **Memory issues**: For large codebases, exclude non-essential directories
3. **Claude API limits**: Graphify uses Claude for semantic analysis; ensure API access

### Verification

```bash
# Check graphify installation
source ~/.hermes/venv/graphify/bin/activate
graphify --help

# Test with a small directory
mkdir test-graphify && cd test-graphify
echo "def hello(): print('world')" > test.py
graphify .
```

## Related Skills

- `graph-analysis`: Network analysis with NetworkX
- `codebase-inspection`: Basic codebase statistics
- `ontology`: Knowledge graph management