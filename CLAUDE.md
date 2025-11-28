# CLAUDE.md - AI Assistant Guidelines for data-sourcer

## Project Overview

**Repository:** data-sourcer
**Organization:** free-plinko-game
**Status:** New/Initial Development

This project is a data sourcing utility designed to collect, process, and manage data for the free-plinko-game ecosystem.

## Repository Structure

```
data-sourcer/
├── CLAUDE.md           # AI assistant guidelines (this file)
├── src/                # Source code (to be created)
│   ├── collectors/     # Data collection modules
│   ├── processors/     # Data processing/transformation
│   ├── exporters/      # Data export utilities
│   └── utils/          # Shared utilities
├── tests/              # Test files
├── config/             # Configuration files
└── docs/               # Documentation
```

## Development Conventions

### Language & Framework Preferences

When building out this project, prefer:
- **TypeScript** for type safety and maintainability
- **Node.js** as the runtime environment
- **ESM modules** over CommonJS
- **Async/await** patterns for asynchronous operations

### Code Style

- Use meaningful, descriptive variable and function names
- Keep functions small and focused (single responsibility)
- Document public APIs with JSDoc comments
- Use strict TypeScript settings (`strict: true`)
- Prefer `const` over `let`, avoid `var`

### File Naming

- Use **kebab-case** for file names: `data-collector.ts`
- Use **PascalCase** for class names: `DataCollector`
- Use **camelCase** for functions and variables: `fetchData()`
- Test files: `*.test.ts` or `*.spec.ts`

### Git Workflow

1. **Branch naming:** `feature/`, `fix/`, `docs/`, `refactor/` prefixes
2. **Commit messages:** Use conventional commits format:
   - `feat: add new data collector`
   - `fix: resolve parsing error`
   - `docs: update README`
   - `refactor: simplify data processing`
3. **Keep commits atomic:** One logical change per commit

## Development Commands

```bash
# Install dependencies (when package.json exists)
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint

# Type check
npm run typecheck
```

## Key Technical Decisions

### Error Handling

- Use custom error classes for domain-specific errors
- Always handle promise rejections
- Log errors with appropriate context
- Return meaningful error messages to callers

### Data Processing

- Validate all external data inputs
- Use streaming for large datasets when possible
- Implement rate limiting for external API calls
- Cache results where appropriate

### Testing

- Write unit tests for all utility functions
- Integration tests for data collectors
- Mock external dependencies in tests
- Aim for >80% code coverage on critical paths

## AI Assistant Guidelines

### When Working on This Codebase

1. **Read before modifying:** Always read existing files before making changes
2. **Understand context:** Check related files and imports
3. **Preserve patterns:** Follow existing code conventions
4. **Test changes:** Run tests after modifications
5. **Document decisions:** Add comments for non-obvious logic

### Common Tasks

#### Adding a New Data Collector

1. Create file in `src/collectors/`
2. Implement the collector interface
3. Add configuration options to `config/`
4. Write tests in `tests/collectors/`
5. Update exports in `src/index.ts`

#### Processing Data

1. Use existing utility functions when available
2. Validate input data structure
3. Handle edge cases (empty data, malformed input)
4. Return consistent output format

### What to Avoid

- Don't commit sensitive data (API keys, credentials)
- Don't add unnecessary dependencies
- Don't break existing functionality without discussion
- Don't ignore TypeScript errors
- Don't skip writing tests for new features

## Environment Setup

### Required Environment Variables

```bash
# Example .env structure (create .env.local for local development)
NODE_ENV=development
LOG_LEVEL=debug
DATA_OUTPUT_DIR=./output
```

### Prerequisites

- Node.js >= 18.x
- npm >= 9.x

## Project Roadmap

This is a new project. Initial setup should include:

1. Initialize package.json with TypeScript configuration
2. Set up ESLint and Prettier
3. Configure Jest for testing
4. Create basic project structure
5. Implement core data sourcing functionality

## Useful Resources

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

*Last updated: 2025-11-28*
