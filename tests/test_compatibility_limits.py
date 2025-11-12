"""
Unit tests for compatibility entry limits and security controls.
Tests MAX_COMPATIBILITY_ENTRIES limit and related statistics tracking.
"""

import unittest
import json
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import check_image_pullability, MAX_COMPATIBILITY_ENTRIES, STATS


class TestCompatibilityLimits(unittest.TestCase):
    """Test cases for MAX_COMPATIBILITY_ENTRIES security limit"""
    
    @classmethod
    def setUpClass(cls):
        """Load mock data once for all tests"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), 'mock_data')
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_many_compatibility.json')) as f:
            cls.many_compat_data = json.load(f)
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_new_format.json')) as f:
            cls.normal_data = json.load(f)
    
    def setUp(self):
        """Reset stats before each test"""
        STATS['truncated_compatibility_workspaces'] = 0
    
    @patch('search_github.skopeo_inspect')
    def test_truncation_occurs_when_exceeding_limit(self, mock_skopeo):
        """Test that compatibility entries are truncated when exceeding MAX_COMPATIBILITY_ENTRIES"""
        mock_skopeo.return_value = True
        
        # This data has 12 entries, should be truncated to 10
        result = check_image_pullability(self.many_compat_data)
        
        self.assertIsNotNone(result)
        # Should be truncated to MAX_COMPATIBILITY_ENTRIES
        self.assertEqual(len(result['compatibility']), MAX_COMPATIBILITY_ENTRIES)
        self.assertEqual(STATS['truncated_compatibility_workspaces'], 1)
    
    @patch('search_github.skopeo_inspect')
    def test_no_truncation_when_within_limit(self, mock_skopeo):
        """Test that no truncation occurs when within limit"""
        mock_skopeo.return_value = True
        
        # This data has 3 entries, within limit
        result = check_image_pullability(self.normal_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['compatibility']), 3)
        self.assertEqual(STATS['truncated_compatibility_workspaces'], 0)
    
    @patch('search_github.skopeo_inspect')
    def test_truncation_preserves_first_entries(self, mock_skopeo):
        """Test that truncation preserves the first N entries in order"""
        mock_skopeo.return_value = True
        
        result = check_image_pullability(self.many_compat_data)
        
        # Check that first 10 versions are preserved
        expected_versions = [f"1.{10+i}.x" for i in range(MAX_COMPATIBILITY_ENTRIES)]
        actual_versions = [entry['version'] for entry in result['compatibility']]
        
        self.assertEqual(actual_versions, expected_versions)
    
    def test_max_compatibility_entries_constant(self):
        """Test that MAX_COMPATIBILITY_ENTRIES is set to expected value"""
        self.assertEqual(MAX_COMPATIBILITY_ENTRIES, 10)


if __name__ == '__main__':
    unittest.main()
