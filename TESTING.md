# Smart Dispatch AI - Testing Guide

Comprehensive testing documentation for the Smart Dispatch AI system.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)

---

## 🎯 Overview

The Smart Dispatch AI test suite provides comprehensive coverage of:

- **Dispatch Search**: Flexible search with multiple filters
- **Availability Logic**: Technician availability and capacity
- **Calendar Generation**: Manual and automated calendar creation
- **Database Maintenance**: Change tracking and rollback
- **Data Integrity**: Validation and consistency checks
- **API Endpoints**: Flask REST API testing

### Test Framework

- **Framework**: pytest
- **Fixtures**: Shared test data and database setup
- **Coverage**: pytest-cov (optional)
- **Isolation**: Each test uses a temporary database

---

## 📁 Test Structure

```
tests/
├── __init__.py                      # Package initialization
├── conftest.py                      # Pytest fixtures and configuration
├── test_dispatch_search.py          # Dispatch search functionality
├── test_availability.py             # Availability and capacity logic
├── test_calendar_generation.py      # Calendar generation features
├── test_database_maintenance.py     # Maintenance operations
├── test_data_integrity.py           # Data validation and integrity
└── test_api_endpoints.py            # Flask API endpoint testing
```

### Test Files

| File | Purpose | Tests |
|------|---------|-------|
| `conftest.py` | Shared fixtures | Database setup, sample data, optimizer instances |
| `test_dispatch_search.py` | Search functionality | Unassigned, filters, date ranges, skills |
| `test_availability.py` | Availability logic | Calendar checks, capacity, workload |
| `test_calendar_generation.py` | Calendar features | Manual/automated generation, duplicates |
| `test_database_maintenance.py` | Maintenance ops | Change logging, rollback, deletion |
| `test_data_integrity.py` | Data validation | Constraints, references, valid values |
| `test_api_endpoints.py` | API testing | All Flask endpoints, error handling |

---

## 🚀 Running Tests

### Prerequisites

```bash
# Install pytest
pip install pytest

# Optional: Install coverage plugin
pip install pytest-cov
```

### Basic Usage

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
pytest

# Verbose output
pytest -v

# Show print statements
pytest -s

# Run specific test file
pytest tests/test_dispatch_search.py

# Run specific test
pytest tests/test_dispatch_search.py::TestDispatchSearch::test_get_unassigned_dispatches

# Run tests matching pattern
pytest -k "search"

# Run tests with marker
pytest -m "unit"
```

### Advanced Options

```bash
# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff

# Parallel execution (requires pytest-xdist)
pytest -n auto

# Generate HTML report
pytest --html=report.html

# Show slowest tests
pytest --durations=10
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html

# Terminal coverage report
pytest --cov=. --cov-report=term

# Coverage for specific module
pytest --cov=dispatch --cov-report=term
```

---

## 📊 Test Coverage

### Current Coverage Areas

#### ✅ Dispatch Search (test_dispatch_search.py)
- [x] Get unassigned dispatches
- [x] Search with date/city/state filters
- [x] Search by dispatch ID
- [x] Search by status
- [x] Search by priority
- [x] Search by skill
- [x] Search assigned only
- [x] Search by date range
- [x] Combined filters
- [x] Get dispatch IDs for autocomplete
- [x] Get unique skills

#### ✅ Availability Logic (test_availability.py)
- [x] Basic availability check
- [x] Calendar max_assignments usage
- [x] Workload consideration
- [x] Unavailable technicians
- [x] No calendar entry handling
- [x] Assigned minutes calculation
- [x] Multiple technicians
- [x] Workload capacity NOT used
- [x] City capacity calculation
- [x] Capacity uses calendar

#### ✅ Calendar Generation (test_calendar_generation.py)
- [x] Manual week generation
- [x] Manual entry flagging
- [x] Automated script skips manual
- [x] No duplicates
- [x] Calendar updates
- [x] Max assignments updates

#### ✅ Database Maintenance (test_database_maintenance.py)
- [x] Log changes
- [x] Get change history
- [x] Filtered history
- [x] Change statistics
- [x] Rollback INSERT
- [x] Rollback UPDATE
- [x] Delete records
- [x] Clear old history
- [x] JSON parsing

#### ✅ Data Integrity (test_data_integrity.py)
- [x] No negative assignments
- [x] Assignments match dispatches
- [x] Valid calendar dates
- [x] Positive max assignments
- [x] Unique dispatch IDs
- [x] Unique technician IDs
- [x] Valid technician references
- [x] Valid calendar references
- [x] Valid coordinates
- [x] Reasonable workload capacity
- [x] Valid appointment times
- [x] Valid priority values
- [x] Valid status values
- [x] No orphaned history

#### ✅ API Endpoints (test_api_endpoints.py)
- [x] /api/init
- [x] /api/dispatches/search
- [x] /api/dispatches/ids
- [x] /api/skills
- [x] /api/unassigned (legacy)
- [x] /api/city/capacity
- [x] /api/technician/availability
- [x] /api/maintenance/stats
- [x] /api/maintenance/history
- [x] /api/technician/generate-week
- [x] Error handling
- [x] /api/cities

### Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Core Logic | 90% | ✅ |
| API Endpoints | 85% | ✅ |
| Database Operations | 95% | ✅ |
| Data Validation | 100% | ✅ |

---

## ✍️ Writing Tests

### Test Structure

```python
import pytest

class TestFeatureName:
    """Test feature description."""
    
    def test_specific_behavior(self, optimizer):
        """Test specific behavior description."""
        # Arrange
        input_data = {...}
        
        # Act
        result = optimizer.some_method(input_data)
        
        # Assert
        assert result is not None
        assert result['key'] == expected_value
```

### Using Fixtures

```python
def test_with_fixtures(self, optimizer, tomorrow_date, sample_data):
    """Test using multiple fixtures."""
    # optimizer: SmartDispatchAI instance with test database
    # tomorrow_date: Tomorrow's date as string
    # sample_data: Dictionary of test data
    
    result = optimizer.get_unassigned_dispatches(date=tomorrow_date)
    assert result is not None
```

### Available Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `test_db_path` | Path | Temporary database file path |
| `sample_data` | dict | Sample technicians, dispatches, calendar |
| `test_database` | Path | Populated test database |
| `optimizer` | SmartDispatchAI | Optimizer instance |
| `maintenance` | DatabaseMaintenance | Maintenance instance |
| `tomorrow_date` | str | Tomorrow's date (YYYY-MM-DD) |
| `next_week_monday` | str | Next Monday's date (YYYY-MM-DD) |

### Best Practices

#### ✅ DO

```python
# Clear test names
def test_unassigned_dispatches_filtered_by_state(self, optimizer):
    """Test that unassigned dispatches can be filtered by state."""
    pass

# Test one thing per test
def test_availability_uses_calendar_max_assignments(self, optimizer):
    """Test that availability calculation uses calendar max_assignments."""
    pass

# Use descriptive assertions
assert result['available'] is True, "Technician should be available"

# Clean up test data
def test_with_cleanup(self, optimizer):
    # Create test data
    optimizer.db.execute("INSERT INTO ...")
    
    try:
        # Test logic
        pass
    finally:
        # Cleanup
        optimizer.db.execute("DELETE FROM ...")
```

#### ❌ DON'T

```python
# Vague test names
def test_search(self):
    pass

# Test multiple things
def test_everything(self):
    # Tests search, availability, and calendar
    pass

# Silent assertions
assert result  # What are we checking?

# Leave test data
def test_no_cleanup(self, optimizer):
    optimizer.db.execute("INSERT INTO ...")
    # No cleanup - affects other tests!
```

### Parameterized Tests

```python
@pytest.mark.parametrize("status,expected_count", [
    ("Pending", 5),
    ("In Progress", 3),
    ("Completed", 10),
])
def test_search_by_status(self, optimizer, status, expected_count):
    """Test searching by different status values."""
    result = optimizer.db.query(
        "SELECT * FROM current_dispatches WHERE Status = ?",
        (status,)
    )
    assert len(result) == expected_count
```

### Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset(self):
    pass

# Mark integration tests
@pytest.mark.integration
def test_full_workflow(self):
    pass

# Skip test conditionally
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature(self):
    pass
```

---

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running tests..."
pytest -x
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## 🐛 Debugging Tests

### Print Debugging

```python
def test_with_debug(self, optimizer):
    result = optimizer.some_method()
    print(f"Result: {result}")  # Use pytest -s to see
    assert result is not None
```

### Breakpoint Debugging

```python
def test_with_breakpoint(self, optimizer):
    result = optimizer.some_method()
    breakpoint()  # Drops into pdb
    assert result is not None
```

### Pytest Debugging

```bash
# Drop into pdb on failure
pytest --pdb

# Drop into pdb on first failure
pytest -x --pdb

# Show local variables on failure
pytest -l
```

---

## 📈 Test Metrics

### Running Test Metrics

```bash
# Count tests
pytest --collect-only | grep "test session starts"

# Show test durations
pytest --durations=0

# Show slowest 10 tests
pytest --durations=10

# Generate JUnit XML report
pytest --junitxml=report.xml
```

### Coverage Metrics

```bash
# Coverage summary
pytest --cov=. --cov-report=term-missing

# Coverage by file
pytest --cov=. --cov-report=term:skip-covered

# Fail if coverage below threshold
pytest --cov=. --cov-fail-under=80
```

---

## 🎓 Additional Resources

### Pytest Documentation
- [Pytest Official Docs](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)

### Testing Best Practices
- [Test-Driven Development (TDD)](https://en.wikipedia.org/wiki/Test-driven_development)
- [Arrange-Act-Assert Pattern](https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/)
- [Testing Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

---

## 📝 Test Checklist

Before committing code, ensure:

- [ ] All tests pass (`pytest`)
- [ ] New features have tests
- [ ] Bug fixes have regression tests
- [ ] Coverage is maintained or improved
- [ ] Tests are documented
- [ ] No skipped tests without reason
- [ ] Test names are descriptive
- [ ] Fixtures are used appropriately
- [ ] Test data is cleaned up

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: Tests fail with "database is locked"
```bash
# Solution: Ensure no other process is using the database
rm dispatch.db
pytest
```

**Issue**: Fixtures not found
```bash
# Solution: Ensure conftest.py is in tests/ directory
ls tests/conftest.py
```

**Issue**: Import errors
```bash
# Solution: Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**Issue**: Tests pass locally but fail in CI
```bash
# Solution: Check Python version and dependencies
python --version
pip list
```

---

## 📞 Support

For test-related questions or issues:

1. Check this documentation
2. Review test examples in `tests/`
3. Check pytest documentation
4. Open an issue on GitHub

---

**Last Updated**: 2025-11-19
**Version**: 1.0.0

