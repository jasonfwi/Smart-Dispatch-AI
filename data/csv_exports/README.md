# CSV Exports Directory

This directory contains CSV exports of Databricks tables imported by `import_to_local.py`.

## File Naming Convention

### Timestamped Files
- Format: `{table_name}_{YYYYMMDD_HHMMSS}.csv`
- Example: `current_dispatches_20251118_214530.csv`
- Purpose: Historical record of each import

### Latest Files
- Format: `{table_name}_latest.csv`
- Example: `current_dispatches_latest.csv`
- Purpose: Always points to the most recent import (overwritten on each import)

## Usage

### Import with CSV Export (default)
```bash
python import_to_local.py
```

### Import without CSV Export
```bash
python import_to_local.py --no-csv
```

## Tables Exported

By default, the following tables are exported:
- `current_dispatches`
- `technicians`
- `technician_calendar`
- `dispatch_history`

## Notes

- CSV files are excluded from version control (see `.gitignore`)
- Each import creates both a timestamped version and updates the `_latest` version
- Use the `_latest` files for quick access to current data
- Timestamped files provide a history of imports for comparison

