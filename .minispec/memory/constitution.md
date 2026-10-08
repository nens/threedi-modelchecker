# threedi-modelchecker Constitution

## Core Principles

### I. Correctness
All code and validation logic must be both accurate and bug-free. Validation accuracy is critical—users depend on this tool to identify real schema issues. Implementation must handle edge cases and be thoroughly tested for custom checks.

### II. Clear Patterns
Every check must follow consistent structural patterns. Maintainability comes from clarity and consistency, making it easy for new developers to understand how to add and modify checks. Code clarity is prioritized over extensive documentation.

### III. Performance
Checks must run efficiently on large databases. Query optimization and memory efficiency are important considerations, as users work with substantial schematisation files.

### IV. Compatibility
The project supports Python 3.10–3.14. All code must be compatible across these versions. Dependencies are pinned per Python version in CI.

### V. Integration
The tool integrates with `threedi-schema` for schema validation and the QGIS plugin (ThreediToolbox) for user-facing functionality. Integration points must remain stable and well-documented.

## Testing Standards

### Custom Checks (BaseCheck subclasses)
- Use TDD: Write tests before implementation
- Aim for rigorous test coverage
- Tests verify both correctness and edge cases

### QueryChecks
- Limited automated testing is currently possible
- Focus on clear, well-documented query logic
- Manual verification preferred
- Query intent must be obvious from code

### General Testing
- Minimum coverage for new code
- Tests use in-memory or temporary SpatiaLite databases (fixtures provided)
- Never commit changes to test fixtures (`threedi_modelchecker/tests/data/{empty.sqlite, empty.gpkg}`)

## Documentation Standards

Minimal documentation is preferred. Clarity comes from:
- Consistent patterns and naming conventions
- Self-explanatory code structure
- Inline comments for complex QueryCheck logic
- Decision records for architectural choices (when ambiguity exists)

## Technology Stack

- **Language**: Python 3.10+ (pinned per version in CI)
- **Database**: SQLite/SpatiaLite
- **ORM**: SQLAlchemy 1.4+ (version varies by Python version)
- **CLI Framework**: Click
- **Spatial**: GeoAlchemy2, pyproj
- **Testing**: pytest, factory_boy, pytest-cov
- **Linting**: isort, black, flake8 (pre-commit hooks enforced)
- **Optional**: rasterio (for raster checks; requires GDAL)

## Development Workflow

### Pre-commit Checks
- `isort` for import sorting (Black-compatible profile)
- `black` for code formatting (line length: 88)
- `flake8` for linting (ignores: E203, E266, E501, W503, E711, E712)

### Testing
```bash
pytest                    # All tests
pytest path/to/test.py   # Specific test
pytest -k test_name      # By name
pytest --cov             # Coverage report
```

### CLI Testing
```bash
threedi_modelchecker check -s path/to/model.sqlite -l ERROR
threedi_modelchecker export_checks --format rst
```

### Release
- Version in `threedi_modelchecker/__init__.py`
- Release via `fullrelease` (zest.releaser)
- Changelog in `CHANGES.rst`

---

## MiniSpec Preferences

### Review Chunk Size
**Small**: 20–40 lines per chunk

Code is reviewed in small increments for maximum engagement and early issue detection. This supports the correctness-first philosophy and allows thorough review before proceeding.

### Documentation Review Policy
**Review All**: All documentation changes reviewed by engineer before commit

Architecture decisions, knowledge base updates, and patterns are all reviewed to maintain alignment and ensure documentation quality.

### Autonomy Level
**Always Confirm**: AI pauses after each chunk, waits for explicit approval before proceeding

This ensures alignment on every decision and maintains the deliberate, careful approach that supports correctness.

### Design Evolution Handling
**Always Discuss**: Any deviation from original design is discussed before implementation continues

Design changes—whether in check logic, patterns, or architecture—are collaborative to ensure they serve the project's correctness and clarity goals.

### Walkthrough Depth
**Quick**: 5–10 minute high-level overview

Engineer is familiar with the codebase; quick orientation sufficient for new features or context-setting.

### Change Size Philosophy
**Minimal First**: Show the smallest working change first; expand if needed after review

Start with core functionality, then add robustness, error handling, and edge cases based on feedback.

### Abstraction Threshold
**Conservative**: Extract only when code is duplicated 3+ times or exceeds 50 lines

Avoid over-engineering. Keep abstractions minimal and justified; clarity comes from consistent patterns, not deep abstraction.

### Review Findings Triage
**Your Call**: Present findings; engineer decides whether to address

AI surfaces code review issues (medium-severity and above) and lets engineer prioritize based on project context.

### Deletion Permission
**Yes**: Can suggest removing unnecessary code during features

If code is redundant or no longer needed, it can be proposed for removal. Keeps codebase lean and focused.

---

## Governance

The constitution supersedes all other practices. MiniSpec preferences can be adjusted per-feature if needed, but should be discussed with the engineer first. Core principles remain stable; preferences evolve as the team learns what works best.

**Version**: 1.0.0 | **Ratified**: 2026-04-15 | **Last Amended**: 2026-04-15
