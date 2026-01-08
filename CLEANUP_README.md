# Cleaning Up Test Data

## Problem

Running tests creates fnords with "Test" in their summary in your actual database (not the temporary test database). This pollutes your real fnord collection.

## Solution 1: Tests Now Use Temporary Database

Tests have been updated to use the `initialized_db` fixture from `conftest.py`. This fixture:

- Creates a temporary database for each test
- Automatically cleans up the temporary database after each test runs
- Uses `FNORD_DB_PATH` environment variable to isolate test data

**Result**: Tests should no longer pollute your real database!

## Solution 2: Manual Cleanup Script

If you already have test pollution, run:

```bash
python scripts/cleanup_test_fnords.py
```

This script:
- Opens your real database (from `~/.config/fnord/fnord.db`)
- Finds all fnords with "Test" in summary or source
- Prompts for confirmation before deleting
- Removes the test records

### Example Usage

```bash
$ python scripts/cleanup_test_fnords.py

🍎 Cleaning up test fnords... 🍎

This will DELETE all fnords with 'Test' in summary. Continue? [y/N]: y
Opening database: /Users/talimoreno/.config/fnord/fnord.db
Found 12 test fnords to remove
Deleted 12 test fnords!
Database cleaned up. The fnords are pleased.
```

## Verifying Clean Database

After running tests or the cleanup script, verify your real fnords are intact:

```bash
fnord list
```

You should only see your actual fnords, not test records.

## Prevention Going Forward

- The test fixtures now use temporary databases by default
- Tests use isolated temporary databases
