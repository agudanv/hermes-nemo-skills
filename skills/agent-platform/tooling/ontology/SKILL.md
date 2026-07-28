---
name: agent-ontology
description: "A typed vocabulary + constraint system for representing knowledge as a verifiable graph. Everything is an entity with a type, properties, and relations to other entities. Use when creating/querying entities (Person, Project, Task, Event, Document), linking related objects, enforcing constraints, planning multi-step actions as graph transformations, or when skills need to share state. Trigger on 'remember', 'what do I know about', 'link X to Y', 'show dependencies', entity CRUD, or cross-skill data access."
---

# Ontology — Typed Knowledge Graph System

## Overview

The Ontology skill provides a **structured knowledge representation system** that transforms unstructured information into a verifiable, queryable graph. It implements a local, file-based typed knowledge graph (ontology) with constraints, validation, and rich query capabilities.

## Core Concepts

### 1. Entity-Based Model
```
Everything is an Entity:
┌─────────────────────────────────────┐
│ Entity                              │
│ ├── Type: Person|Project|Task|Event │
│ ├── Properties: key-value pairs     │
│ └── Relations: links to other entities
└─────────────────────────────────────┘
```

### 2. Type System
```yaml
# Built-in entity types
Person:
  required: [name]
  optional: [email, role, bio]
  relations: [works_on, manages, reports_to]

Project:
  required: [title, status]
  optional: [description, deadline, priority]
  relations: [has_member, depends_on, related_to]

Task:
  required: [description, status]
  optional: [assignee, due_date, priority]
  relations: [part_of, blocks, related_to]

Event:
  required: [title, date]
  optional: [location, description, attendees]
  relations: [has_participant, follows, related_to]

Document:
  required: [title, path]
  optional: [type, tags, summary]
  relations: [authored_by, references, version_of]
```

### 3. Constraint System
```python
# Type constraints
constraints:
  Person:
    email: "must be valid email format"
    role: "must be one of: developer, manager, analyst"
    
  Project:
    status: "must be one of: planning, active, completed, archived"
    deadline: "must be future date if status=active"
    
  Task:
    priority: "must be 1-5"
    due_date: "must be after created_date"
```

## When to Use This Skill

### Scenario 1: Knowledge Organization
```
Situation: "Remember that John is working on the WebApp project"
Action: Create Person(John) and Project(WebApp) entities, link with works_on
Result: Structured knowledge that can be queried later
```

### Scenario 2: Dependency Tracking
```
Situation: "Show me all tasks that depend on the database design"
Action: Query task dependencies as a graph
Result: Visual dependency tree with blocking relationships
```

### Scenario 3: Cross-Skill Data Sharing
```
Situation: Multiple skills need access to the same project information
Action: Store project data in ontology, all skills query from central graph
Result: Consistent data across all skills
```

### Scenario 4: Constraint Validation
```
Situation: "Assign this task to Sarah"
Action: Check if Sarah is a Person, has capacity, skills match task
Result: Valid assignment or specific constraint violations
```

## Core Operations

### 1. Entity Management
```bash
# Create an entity
ontology create Person --name "John Doe" --email "john@example.com" --role "developer"

# Update an entity
ontology update Person john_doe --role "senior developer" --bio "Experienced full-stack developer"

# Delete an entity
ontology delete Person john_doe

# List all entities of a type
ontology list Person
ontology list Project --filter "status=active"
```

### 2. Relation Management
```bash
# Create a relation
ontology relate Person john_doe works_on Project web_app

# Remove a relation
ontology unrelate Person john_doe works_on Project web_app

# Find related entities
ontology relations Person john_doe --type works_on
ontology relations Project web_app --incoming  # Who works on this project?
```

### 3. Query System
```bash
# Simple query
ontology query "Person where role='developer'"

# Complex query with relations
ontology query "Person where (works_on Project where status='active') and role='developer'"

# Graph traversal
ontology traverse Person john_doe --depth 3 --relation works_on,manages

# Find paths between entities
ontology path Person john_doe to Project ai_research --max-hops 5
```

### 4. Constraint Operations
```bash
# Validate all entities
ontology validate --all

# Validate specific type
ontology validate Person

# Check constraints for an entity
ontology constraints Person john_doe

# Add custom constraint
ontology constraint add Person "email must contain '@'"
```

### 5. Import/Export
```bash
# Export ontology to various formats
ontology export --format json --output ontology.json
ontology export --format graphviz --output ontology.dot
ontology export --format csv --output entities.csv

# Import data
ontology import --file data.json --format json
ontology import --file data.csv --format csv --type Person
```

## File Structure

```
~/.openclaw/workspace/memory/ontology/
├── schema/
│   ├── types.yaml          # Entity type definitions
│   ├── constraints.yaml    # Constraint definitions
│   └── relations.yaml      # Relation type definitions
├── entities/
│   ├── Person/
│   │   ├── john_doe.yaml
│   │   └── sarah_smith.yaml
│   ├── Project/
│   │   ├── web_app.yaml
│   │   └── ai_research.yaml
│   └── Task/
│       ├── design_db.yaml
│       └── implement_api.yaml
├── graphs/
│   ├── project_team.graph
│   └── task_dependencies.graph
└── indexes/
    ├── by_type.index
    ├── by_property.index
    └── by_relation.index
```

## Integration Examples

### With MemOS Sync
```yaml
# Ontology entities can be synced to MemOS
Person:
  sync_to_memos: true
  privacy: "private"
  
Project:
  sync_to_memos: true  
  privacy: "shared"  # Share with team
```

### With ClawTeam
```python
# Use ontology to assign tasks to agents
def assign_task_to_agent(task, agents):
    """Find best agent for a task using ontology"""
    
    # Query agents with required skills
    suitable_agents = ontology.query(
        f"Person where skills includes '{task.required_skill}' "
        f"and current_load < max_capacity"
    )
    
    # Consider past performance
    for agent in suitable_agents:
        agent_score = calculate_agent_score(agent, task)
        # Assign to highest scoring agent
    
    return best_agent
```

### With Self-Improving Agent
```python
# Track learning patterns in ontology
def track_learning_pattern(agent, topic, effectiveness):
    """Record learning patterns in ontology"""
    
    # Create or update LearningPattern entity
    pattern = ontology.get_or_create(
        "LearningPattern",
        agent=agent.id,
        topic=topic,
        pattern_type="effectiveness"
    )
    
    # Add effectiveness data point
    pattern.add_data_point(
        timestamp=datetime.now(),
        effectiveness=effectiveness,
        context=agent.current_context
    )
    
    # Analyze patterns over time
    patterns = ontology.query(
        f"LearningPattern where agent='{agent.id}' and topic='{topic}'"
    )
    
    return analyze_patterns(patterns)
```

## Use Case Examples

### Use Case 1: Project Management
```bash
# 1. Create project structure
ontology create Project "Web App" --status "planning" --priority "high"
ontology create Person "Alice" --role "frontend" --skills "React,TypeScript"
ontology create Person "Bob" --role "backend" --skills "Python,FastAPI"
ontology create Person "Carol" --role "devops" --skills "Docker,AWS"

# 2. Assign team members
ontology relate Person alice works_on Project "Web App"
ontology relate Person bob works_on Project "Web App" 
ontology relate Person carol works_on Project "Web App"

# 3. Create tasks with dependencies
ontology create Task "Design UI" --assignee alice --due "2026-04-05"
ontology create Task "Implement API" --assignee bob --due "2026-04-07"
ontology create Task "Deploy to staging" --assignee carol --due "2026-04-10"

ontology relate Task "Implement API" blocks Task "Deploy to staging"
ontology relate Task "Design UI" related_to Task "Implement API"

# 4. Query project status
ontology query "Task where assignee=alice and status!=completed"
ontology traverse Project "Web App" --depth 2 --relation works_on,blocks
```

### Use Case 2: Knowledge Base
```bash
# 1. Document important concepts
ontology create Concept "Machine Learning" --category "AI"
ontology create Concept "Neural Networks" --category "AI"
ontology create Concept "Supervised Learning" --category "AI"

# 2. Create relationships
ontology relate Concept "Neural Networks" subclass_of Concept "Machine Learning"
ontology relate Concept "Supervised Learning" subclass_of Concept "Machine Learning"

# 3. Link to resources
ontology create Document "ML Tutorial" --path "/docs/ml.md" --type "tutorial"
ontology relate Document "ML Tutorial" explains Concept "Machine Learning"

# 4. Query knowledge graph
ontology query "Concept where category='AI'"
ontology path Concept "Supervised Learning" to Document --via subclass_of,explains
```

### Use Case 3: Personal CRM
```bash
# 1. Track people and interactions
ontology create Person "David Chen" --company "TechCorp" --role "CTO"
ontology create Event "Meeting with David" --date "2026-04-02" --type "business"
ontology relate Event "Meeting with David" has_participant Person "David Chen"

# 2. Record notes and follow-ups
ontology create Note "Discussed API partnership" --date "2026-04-02"
ontology relate Note "Discussed API partnership" about Event "Meeting with David"

ontology create Task "Send partnership proposal" --due "2026-04-03"
ontology relate Task "Send partnership proposal" follows Event "Meeting with David"

# 3. Query contact history
ontology traverse Person "David Chen" --depth 2 --relation has_participant,about,follows
```

## Configuration

```yaml
# ~/.openclaw/workspace/memory/ontology/config.yaml
ontology:
  # Storage settings
  storage:
    directory: "~/.openclaw/workspace/memory/ontology"
    format: "yaml"  # or: json, toml
    compression: true
    backup_count: 7
    
  # Indexing
  indexing:
    auto_index: true
    index_types: ["Person", "Project", "Task", "Event"]
    update_frequency: "on_change"  # or: hourly, daily
    
  # Validation
  validation:
    strict_mode: true
    auto_validate: true
    validate_on_save: true
    
  # Privacy
  privacy:
    encrypt_sensitive: true
    sensitive_fields: ["email", "phone", "address"]
    anonymize_for_export: true
    
  # Integration
  integration:
    memos_sync:
      enabled: true
      sync_entities: ["Person", "Project", "Task"]
      
    clawteam:
      enabled: true
      entity_types: ["Person", "Task", "Project"]
      
    proactive_agent:
      enabled: true
      monitor_changes: true
      
  # Advanced
  advanced:
    graph_traversal_max_depth: 10
    query_timeout: 30
    cache_size: 1000
    auto_cleanup: true
```

## Best Practices

### 1. Start Simple
```bash
# Begin with basic entities
ontology create Person "Test User" --role "tester"
ontology create Project "Test Project" --status "active"

# Add complexity gradually
ontology relate Person "Test User" works_on Project "Test Project"
```

### 2. Use Consistent Naming
```bash
# Good: Consistent, descriptive names
ontology create Person "john_doe" --name "John Doe"
ontology create Project "web_app_2026" --title "Web App 2026"

# Bad: Inconsistent naming
ontology create Person "jdoe"  # Unclear
ontology create Project "wa"   # Too cryptic
```

### 3. Leverage Constraints
```yaml
# Define constraints early
Person:
  email: "must match email regex"
  role: "must be one of: developer, manager, analyst, tester"
  
Task:
  status: "must be: todo, in_progress, blocked, completed"
  priority: "must be 1-5"
```

### 4. Regular Maintenance
```bash
# Weekly cleanup
ontology validate --all --fix
ontology cleanup --orphaned
ontology backup --full

# Monthly optimization
ontology reindex --all
ontology analyze --performance
```

## Troubleshooting

### Common Issues

1. **Entity not found**
   ```bash
   # Check if entity exists
   ontology get Person john_doe
   
   # Search for similar entities
   ontology search "john" --type Person
   
   # Check indexes
   ontology index status
   ```

2. **Constraint violation**
   ```bash
   # See specific violation
   ontology validate Person john_doe --verbose
   
   # List all constraints for type
   ontology constraints Person
   
   # Temporarily disable constraints
   ontology create Person test --email "invalid" --no-validate
   ```

3. **Performance issues**
   ```bash
   # Rebuild indexes
   ontology reindex --all
   
   # Clear cache
   ontology cache clear
   
   # Analyze query performance
   ontology analyze query "Person where role='developer'"
   ```

4. **Import/export problems**
   ```bash
   # Validate import file
   ontology import --file data.json --validate-only
   
   # Export with error checking
   ontology export --format json --validate
   
   # Repair corrupted data
   ontology repair --backup restore_latest
   ```

## Development & Extension

### Adding New Entity Types
```yaml
# 1. Define new type in schema/types.yaml
NewType:
  description: "Description of new type"
  properties:
    required:
      - name
      - category
    optional:
      - description
      - tags
  relations:
    - relates_to
    - part_of

# 2. Add constraints if needed
NewType:
  constraints:
    category: "must be one of: cat1, cat2, cat3"
    tags: "must be array of strings"

# 3. Register type
ontology schema add --file new_type.yaml
```

### Custom Query Functions
```python
# Define custom query function
@ontology.query_function
def find_experts(topic, min_experience_years=3):
    """Find experts on a topic with minimum experience"""
    
    return ontology.query(
        f"Person where skills includes '{topic}' "
        f"and experience_years >= {min_experience_years} "
        f"order by experience_years desc"
    )

# Use custom function
experts = ontology.call("find_experts", "machine_learning", 5)
```

### Plugin System
```python
# Create ontology plugin
class ProjectManagementPlugin:
    def __init__(self, ontology):
        self.ontology = ontology
    
    def calculate_project_health(self, project_id):
        """Calculate health score for project"""
        project = self.ontology.get("Project", project_id)
        tasks = self.ontology.query(f"Task where part_of Project {project_id}")
        
        completed = sum(1 for t in tasks if t.status == "completed")
        total = len(tasks)
        overdue = sum(1 for t in tasks if t.due_date < datetime.now())
        
        health_score = (completed / total * 100) - (overdue * 10)
        return max(0, min(100, health_score))

# Register plugin
ontology.register_plugin("project_management", ProjectManagementPlugin)
```

---

*"Knowledge is of two kinds: we know a subject ourselves, or we know where we can find information upon it." — Samuel Johnson*

**Ontology技能将第二种知识转化为第一种：它创建一个结构化的、可查询的知识图谱，让你真正"知道"你的数据。**