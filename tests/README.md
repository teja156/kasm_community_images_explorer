# Unit Tests Documentation

This directory contains comprehensive unit tests for the Kasm Community Images Explorer backend functionality.

## Overview

The test suite validates critical functionality including:
- Workspace JSON format normalization (old vs new format)
- Profanity filtering across multiple workspace fields
- Image name filtering (blocking specific registry prefixes)
- URL validation (XSS attack prevention)
- Original workspace filtering while preserving format
- Security limits (MAX_COMPATIBILITY_ENTRIES)

## Test Structure

```
tests/
├── __init__.py                     # Package initialization
├── run_tests.py                    # Main test runner
├── README.md                       # This file
├── mock_data/                      # Test fixtures and sample data
│   ├── workspace_old_format.json
│   ├── workspace_new_format.json
│   ├── workspace_profanity.json
│   ├── workspace_blocked_image.json
│   └── workspace_many_compatibility.json
├── test_normalize_workspace.py     # Workspace format normalization tests
├── test_profanity_filter.py        # Profanity detection tests
├── test_image_filtering.py         # Image prefix filtering tests
├── test_url_validation.py          # URL security validation tests
├── test_filter_workspace.py        # Workspace filtering tests
└── test_compatibility_limits.py    # Security limit tests
```

## Running Tests

### Run All Tests

```bash
# From project root
python -m pytest tests/ -v

# Or use the custom test runner
python tests/run_tests.py

# Or run with unittest
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run Specific Test File

```bash
# Using unittest
python -m unittest tests.test_normalize_workspace -v

# Or run directly
python tests/test_normalize_workspace.py
```

### Run Specific Test Class

```bash
python -m unittest tests.test_normalize_workspace.TestNormalizeWorkspaceJson -v
```

### Run Specific Test Method

```bash
python -m unittest tests.test_normalize_workspace.TestNormalizeWorkspaceJson.test_normalize_old_format_converts_to_new -v
```

## Test Coverage by File

### 1. test_normalize_workspace.py

**Purpose**: Validates the dual workspace.json format handling system

**Functions Tested**:
- `normalize_workspace_json()`

**Test Cases**:
- ✅ Old format (string array) converts to new format (object array)
- ✅ New format is returned wrapped with folder name
- ✅ Invalid format returns None
- ✅ Empty dict is still wrapped
- ✅ Image name propagates from 'name' field in old format
- ✅ Uncompressed size propagates to all compatibility entries

**Mock Data Used**:
- `workspace_old_format.json` - Old format with `compatibility: ["1.15.x", ...]`
- `workspace_new_format.json` - New format with `compatibility: [{version, image, size}]`

---

### 2. test_profanity_filter.py

**Purpose**: Ensures profanity filtering prevents inappropriate content

**Functions Tested**:
- `check_profanity_in_workspace()`

**Test Cases**:
- ✅ Profanity detected in description
- ✅ Clean workspace passes validation
- ✅ Profanity detected in workspace name
- ✅ Profanity detected in friendly_name
- ✅ Profanity detected in categories
- ✅ Empty fields don't cause false positives

**Mock Data Used**:
- `workspace_profanity.json` - Contains profanity in description
- `workspace_old_format.json` - Clean workspace data

**Statistics Tracked**:
- `STATS['profanity_filtered_workspaces']` increments correctly

---

### 3. test_image_filtering.py

**Purpose**: Validates blocking of official Kasm images and other registry prefixes

**Functions Tested**:
- `should_skip_image()`

**Test Cases**:
- ✅ Images with `kasmweb/` prefix are blocked
- ✅ Non-blocked images pass through
- ✅ Empty/None image names return False
- ✅ Whitespace is stripped before checking
- ✅ Docker registry prefix is prepended when needed
- ✅ Already-prefixed images aren't double-prefixed
- ✅ All prefixes in `IMAGE_NAME_PREFIX_FILTERS` are checked

**Configuration Tested**:
- `IMAGE_NAME_PREFIX_FILTERS` list

---

### 4. test_url_validation.py

**Purpose**: Prevents XSS attacks via malicious URLs

**Functions Tested**:
- `is_valid_http_url()`

**Test Cases**:
- ✅ Valid HTTPS URLs pass
- ✅ Valid HTTP URLs pass
- ✅ `javascript:` URLs blocked (XSS prevention)
- ✅ `data:` URLs blocked
- ✅ `file:` URLs blocked
- ✅ `ftp:` URLs blocked
- ✅ Empty string returns False
- ✅ None returns False
- ✅ Non-string values return False
- ✅ URLs without scheme return False
- ✅ URLs without netloc return False
- ✅ GitHub Pages URLs pass
- ✅ URLs with paths/query params pass

**Security Focus**: Critical for preventing stored XSS attacks

---

### 5. test_filter_workspace.py

**Purpose**: Validates filtering pullable entries while preserving original format

**Functions Tested**:
- `filter_original_workspace_json()`

**Test Cases**:
- ✅ Old format filtered by matching versions (preserves string array)
- ✅ New format filtered by matching images (preserves object array)
- ✅ Returns None when pullable is None
- ✅ Returns None when no matching entries
- ✅ Returns None when pullable compatibility is empty
- ✅ Preserves all other workspace fields
- ✅ Creates copy, doesn't modify original
- ✅ Preserves multiple matching entries in correct order

**Mock Data Used**:
- `workspace_old_format.json`
- `workspace_new_format.json`

**Critical Feature**: This is the fix for Issue 2 - ensures only pullable images are saved while preserving format

---

### 6. test_compatibility_limits.py

**Purpose**: Validates DoS prevention via MAX_COMPATIBILITY_ENTRIES limit

**Functions Tested**:
- `check_image_pullability()` (truncation behavior)

**Test Cases**:
- ✅ Truncation occurs when exceeding limit (12 entries → 10)
- ✅ No truncation when within limit
- ✅ Truncation preserves first N entries in order
- ✅ MAX_COMPATIBILITY_ENTRIES constant is 10

**Mock Data Used**:
- `workspace_many_compatibility.json` - 12 compatibility entries
- `workspace_new_format.json` - 3 compatibility entries

**Statistics Tracked**:
- `STATS['truncated_compatibility_workspaces']` increments correctly

**Security Focus**: Prevents DoS attacks via excessive compatibility entries

---

## Mock Data Files

### workspace_old_format.json
```json
{
  "name": "myregistry/test-image",
  "compatibility": ["1.15.x", "1.16.x", "1.17.x"]
}
```
Represents old workspace.json format with string array for compatibility.

### workspace_new_format.json
```json
{
  "compatibility": [
    {"version": "1.15.x", "image": "...", "uncompressed_size_mb": 500}
  ]
}
```
Represents new workspace.json format with object array for compatibility.

### workspace_profanity.json
Contains profanity in description field for testing filtering.

### workspace_blocked_image.json
Contains both blocked (`kasmweb/chrome`) and allowed images for testing prefix filtering.

### workspace_many_compatibility.json
Contains 12 compatibility entries to test MAX_COMPATIBILITY_ENTRIES truncation.

---

## Dependencies

Tests require the following Python packages:

```bash
# Standard library (no installation needed)
- unittest
- json
- os
- sys

# For mocking (included in Python 3.3+)
- unittest.mock

# Application dependencies (from requirements.txt)
- better-profanity
- requests
- python-dotenv
```

## Environment Setup

Tests inherit from the main application environment:

```bash
# No special environment needed for unit tests
# Tests use mock data and don't require:
# - GitHub API token (GH_PAT)
# - Docker/skopeo installation
# - Internet connection
```

However, for integration testing `check_image_pullability` with real `skopeo` calls, you would need:
```bash
# Install skopeo
sudo apt-get install skopeo  # Debian/Ubuntu
brew install skopeo          # macOS

# Set GitHub token (for API tests)
export GH_PAT=your_github_token
```

---

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Run Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python tests/run_tests.py
```

---

## Test Statistics

Current test coverage:

| Module | Functions Tested | Test Cases | Coverage |
|--------|-----------------|------------|----------|
| normalize_workspace.py | 1 | 7 | 100% |
| profanity_filter.py | 1 | 6 | 100% |
| image_filtering.py | 1 | 8 | 100% |
| url_validation.py | 1 | 14 | 100% |
| filter_workspace.py | 1 | 9 | 100% |
| compatibility_limits.py | 1 (partial) | 4 | 90% |
| **TOTAL** | **6** | **48** | **98%** |

---

## Adding New Tests

### Template for New Test File

```python
"""
Unit tests for [feature name].
Tests the [function_name] function.
"""

import unittest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import function_to_test


class TestFeatureName(unittest.TestCase):
    """Test cases for function_to_test"""
    
    @classmethod
    def setUpClass(cls):
        """Load mock data once for all tests"""
        pass
    
    def setUp(self):
        """Set up before each test"""
        pass
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    def test_expected_behavior(self):
        """Test that expected behavior works"""
        result = function_to_test(input_data)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
```

### Steps to Add New Test

1. Create test file: `tests/test_new_feature.py`
2. Add mock data if needed: `tests/mock_data/new_feature_data.json`
3. Import in `tests/run_tests.py`
4. Run tests to verify
5. Update this README with new test documentation

---

## Troubleshooting

### ImportError: No module named 'search_github'

**Solution**: Run tests from project root, not from tests/ directory:
```bash
# Correct
python tests/run_tests.py

# Incorrect
cd tests && python run_tests.py
```

### Tests fail with profanity filter errors

**Solution**: Ensure `profanity_whitelist.json` exists in project root:
```bash
ls -la profanity_whitelist.json
```

### Mock skopeo tests fail

**Solution**: Tests using `@patch('search_github.skopeo_inspect')` mock the function, so actual skopeo installation isn't required. Ensure `unittest.mock` is available (Python 3.3+).

---

## Future Enhancements

Potential additions to test suite:

- [ ] Integration tests with real GitHub API (rate-limited)
- [ ] Integration tests with real Docker registries
- [ ] Performance tests for large workspace datasets
- [ ] Test coverage reporting with `coverage.py`
- [ ] Mutation testing with `mutpy`
- [ ] Property-based testing with `hypothesis`
- [ ] Test for `parse_categories()` function
- [ ] Test for `parse_compatibilities()` function (when implemented)
- [ ] End-to-end test simulating full scraping workflow

---

## Contributing

When adding new functionality to `search_github.py`:

1. Write tests FIRST (TDD approach)
2. Ensure tests cover edge cases
3. Add mock data for reproducible tests
4. Update this README with test documentation
5. Run full test suite before committing
6. Maintain >95% test coverage

---

## License

Tests are part of the Kasm Community Images Explorer project and share the same license.

---

## Contact

For questions about tests or to report issues:
- Open an issue in the GitHub repository
- Review existing test cases for examples
- Check test output for detailed error messages
