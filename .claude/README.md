# .claude Directory Guide

This directory contains configuration and context files for Claude Code CLI to provide better assistance with the AI Portfolio Optimization project.

## Directory Structure

```
.claude/
├── README.md                    # This file
├── config.yaml                  # Claude CLI configuration
├── project-context.md           # Project overview and architecture
├── coding-guidelines.md         # Code style and development patterns
├── commands/                    # Pre-defined command templates
│   ├── optimize.md             # Portfolio optimization commands
│   └── quality.md              # Code quality and maintenance commands
└── templates/                   # Code templates
    ├── module-template.py      # Standard module structure
    └── test-template.py        # Standard test structure
```

## Purpose and Benefits

### 1. **Enhanced Context Understanding**
- Provides Claude with deep understanding of your project structure
- Includes domain knowledge about portfolio optimization and financial mathematics
- Documents current implementation status and priorities

### 2. **Consistent Code Generation**
- Templates ensure new code follows existing patterns
- Coding guidelines maintain style consistency
- Pre-defined commands for common tasks

### 3. **Improved Development Workflow**
- Quick access to project-specific prompts
- Standardized approaches to common development tasks
- Integration with existing tools and patterns

## How to Use

### Using Pre-defined Commands

The `commands/` directory contains ready-to-use Claude Code CLI commands:

```bash
# Create portfolio optimizer module
claude code "$(cat .claude/commands/optimize.md | grep -A 20 'Create Complete Portfolio Optimizer')"

# Fix technical debt
claude code "$(cat .claude/commands/quality.md | grep -A 15 'Fix Technical Debt')"

# Add comprehensive testing
claude code "$(cat .claude/commands/optimize.md | grep -A 15 'Enhance Testing')"
```

### Using Templates

Reference templates when creating new modules:

```bash
# Create new module based on template
claude code "Create a new risk management module in src/risk/ following the patterns in .claude/templates/module-template.py"

# Create tests for existing module
claude code "Create comprehensive tests for src/optimizer/mean_variance.py following .claude/templates/test-template.py"
```

### Custom Prompts

Leverage project context for custom requests:

```bash
claude code "Add mathematical formula validation to the existing math detector, ensuring it integrates with the current Settings and logging systems"

claude code "Implement a new Black-Litterman optimizer that uses insights from the knowledge management system"
```

## Configuration Files

### config.yaml
- Project metadata and preferences
- Context files to include
- Language-specific settings
- AI assistant preferences

### project-context.md
- Current implementation status
- Architecture overview
- Technology stack
- Development priorities

### coding-guidelines.md
- Code style standards
- Documentation requirements
- Error handling patterns
- Testing guidelines

## Best Practices

### 1. **Keep Context Updated**
- Update project-context.md when architecture changes
- Modify coding-guidelines.md when standards evolve
- Add new command templates for recurring tasks

### 2. **Use Specific Prompts**
- Reference existing code patterns and modules
- Specify integration requirements
- Include error handling and testing requirements

### 3. **Leverage Domain Knowledge**
- Use financial and mathematical terminology correctly
- Reference existing mathematical detection capabilities
- Consider portfolio optimization best practices

## Integration with Existing Documentation

The `.claude` directory complements your existing documentation:

- **docs/Claude.md**: Technical implementation details
- **docs/Mathematical_Detection_Improvements.md**: Algorithm specifics
- **docs/OCR_Configuration.md**: API integration guides
- **README.md**: User-facing documentation

## Maintenance

### Regular Updates
- Review and update context files monthly
- Add new command templates for recurring tasks
- Update coding guidelines as patterns evolve

### Version Control
- Commit `.claude` directory changes with code changes
- Document significant context updates in commit messages
- Keep templates synchronized with actual code patterns

## Examples

### Creating a New Optimizer
```bash
claude code "Create a new RiskParityOptimizer in src/optimizer/risk_parity.py that:
1. Inherits from BaseOptimizer (following existing patterns)
2. Implements equal risk contribution optimization
3. Uses the existing Settings class for configuration
4. Includes comprehensive error handling and logging
5. Follows the module template structure
6. Includes type hints and Google-style docstrings"
```

### Adding API Endpoints
```bash
claude code "Add FastAPI endpoints to src/frontend/api/ for portfolio optimization:
1. POST /api/optimize - run optimization with parameters
2. GET /api/portfolios - list saved portfolios
3. GET /api/performance/{portfolio_id} - get performance metrics
4. Follow existing authentication and error handling patterns
5. Include OpenAPI documentation
6. Add comprehensive tests"
```

### Enhancing Existing Features
```bash
claude code "Enhance the mathematical detection system to:
1. Support LaTeX formula validation
2. Add confidence scoring improvements
3. Integrate with the knowledge management system
4. Maintain backward compatibility
5. Follow existing error handling patterns
6. Include performance benchmarks"
```

This `.claude` directory setup will significantly improve Claude's ability to understand your project and provide relevant, consistent assistance.
