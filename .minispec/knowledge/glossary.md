# Glossary

Domain-specific terms and definitions for threedi-modelchecker.

## 3Di Concepts

- **Schematisation**: A user-built database defining a 3Di model structure (what is being checked)
- **3Di Model**: A schematisation converted into a simulation-ready model
- **3Di Schema**: The versioned database schema that defines valid schematisation structure

## Validation Concepts

- **Check**: A declarative validation rule (subclass of BaseCheck)
- **QueryCheck**: A check based on SQL queries (limited test coverage)
- **Check Level**: Severity classification (ERROR, FUTURE_ERROR, WARNING, INFO)
- **Check Result**: An error or issue found by a check

## System Components

- **LocalContext**: Default context; reads rasters from local `data/rasters/` directory
- **ServerContext**: Context for remote raster access (used in testing)
- **ModelChecker**: Main class orchestrating check execution

*Additional domain terms will be added as development continues.*
