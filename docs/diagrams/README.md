# Architecture Diagrams

This directory contains architecture diagrams for the AI Search Engine in Mermaid format.

## Viewing Diagrams

### GitHub/GitLab
The `system_overview.md` file contains Mermaid diagrams that render automatically in:
- GitHub (native support)
- GitLab (native support)
- Gitea (with plugin)

### Local Viewing

**Option 1: VS Code**
Install the "Markdown Preview Mermaid Support" extension:
```bash
code --install-extension bierner.markdown-mermaid
```

**Option 2: Mermaid Live Editor**
1. Copy diagram code
2. Go to https://mermaid.live/
3. Paste and view

**Option 3: Command Line**
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i system_overview.md -o output.png

# Generate SVG
mmdc -i system_overview.md -o output.svg
```

## Diagrams Included

1. **System Overview** - High-level architecture
2. **Routing System** - Query routing with strategies
3. **Research Agent Flow** - Step-by-step research process
4. **Code Execution Security** - 3-layer security model
5. **RAG System Architecture** - Vector store and retrieval
6. **Web Application** - FastAPI structure
7. **LLM Manager Fallback** - Provider failover
8. **Workflow Execution Modes** - Sequential, Parallel, DAG
9. **Caching Strategy** - Multi-level caching
10. **Data Flow** - Complete query lifecycle
11. **Module Dependencies** - Component relationships
12. **Deployment Architecture** - Production setup

## Embedding in Documentation

### Sphinx (RST)
```rst
.. mermaid:: diagrams/system_overview.md
```

### Markdown
```markdown
![System Overview](diagrams/system_overview.md)
```

### HTML
```html
<div class="mermaid">
  <!-- Paste mermaid code here -->
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
```

## Exporting Diagrams

### To PNG/SVG
```bash
# Using mermaid-cli
mmdc -i system_overview.md -o diagrams/png/system_overview.png
mmdc -i system_overview.md -o diagrams/svg/system_overview.svg
```

### To PDF
```bash
# Using mermaid-cli with puppeteer
mmdc -i system_overview.md -o diagrams/pdf/system_overview.pdf
```

## Diagram Types

- **Flowchart**: `graph TB` (top to bottom)
- **Sequence**: `sequenceDiagram`
- **Graph**: `graph LR` (left to right)

## Styling

Mermaid supports custom styling:
```mermaid
style NodeName fill:#f9f,stroke:#333,stroke-width:4px
```

## ASCII Diagrams

For text-only environments, see `../../ARCHITECTURE_DIAGRAMS.md` for ASCII art versions of all diagrams.

## Contributing

When adding new diagrams:
1. Use consistent styling
2. Add descriptive comments
3. Test rendering in GitHub
4. Update this README

## Tools

- **Mermaid Live Editor**: https://mermaid.live/
- **Mermaid CLI**: https://github.com/mermaid-js/mermaid-cli
- **VS Code Extension**: Markdown Preview Mermaid Support
- **Draw.io**: https://app.diagrams.net/ (alternative)

## Resources

- **Mermaid Documentation**: https://mermaid.js.org/
- **Mermaid Syntax**: https://mermaid.js.org/intro/syntax-reference.html
- **Examples**: https://mermaid.js.org/syntax/examples.html
