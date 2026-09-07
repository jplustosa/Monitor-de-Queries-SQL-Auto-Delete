# SQL Query Monitor & Auto-Delete

> Python automation for controlled Oracle SQL processing, CSV export and operational file management.

**Python · Oracle · oracledb · Pandas · Logging · Automation**

## Problem

Operational teams often receive SQL scripts as files that must be executed, validated and returned as structured output. Manual processing increases repetitive work and makes failures harder to track.

This project automates that workflow while preserving failed scripts for investigation.

## Workflow

```text
SQL file (.txt)
      ↓
File detection
      ↓
Encoding detection
      ↓
Oracle execution
      ↓
CSV export
      ↓
Success? ───── No ───→ Keep script + log error
   |
  Yes
   ↓
Delete processed script
   ↓
Record operation
```

## Features

- Automatic monitoring of `./scripts/`.
- Oracle SQL execution.
- CSV result export.
- Multiple text encodings.
- Automatic deletion only after successful processing.
- Connection testing.
- Processing and monitoring controls.
- Operational logging.
- Failed scripts retained for troubleshooting.

## Security

**Do not place Oracle credentials directly in source code.**

Use environment variables or a local `.env` file excluded by `.gitignore`:

```text
ORACLE_USER=...
ORACLE_PASSWORD=...
ORACLE_DSN=...
```

If credentials were ever committed to a repository, rotate them and remove them from Git history before treating the repository as clean.

## Quick start

Install the required dependencies:

```bash
pip install oracledb pandas chardet
```

Create a `scripts/` directory and place SQL files using the expected `.txt` format. Then run:

```bash
python monitor_queries.py
```

## Processing rules

| Result | CSV | Original SQL file |
| --- | --- | --- |
| Success with rows | Generated | Deleted |
| Success without rows | Processed | Deleted |
| Execution error | Not generated | Preserved |
| Connection error | Not generated | Preserved |

Preserving failed inputs is intentional: an operational automation should not destroy evidence needed for troubleshooting.

## Repository structure

```text
.
├── monitor_queries.py
├── scripts/              # Input SQL files
├── resultados/           # Generated CSVs
└── README.md
```

## Engineering improvements recommended

- Move application code into `src/`.
- Add unit tests for file detection, encoding and processing rules.
- Add integration tests using an Oracle test environment.
- Replace GUI-driven configuration with environment-based configuration where appropriate.
- Add structured logging.
- Add retry and timeout policies.
- Add a dry-run mode.
- Add metrics/health checks.
- Containerize the worker where Oracle connectivity permits.
- Add CI with linting, tests and secret scanning.

## Portfolio case

This project demonstrates a practical automation mindset: **detect → execute → validate → persist output → clean up → audit**.

The important behavior is that automation does not treat every execution as success. Failures remain available for diagnosis, making the process safer for operational use.
