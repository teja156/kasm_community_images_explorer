"""
Unit tests for workspace normalization functionality.
Tests the normalize_workspace_json function which handles both old and new workspace.json formats.
"""

import unittest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import normalize_workspace_json


class TestNormalizeWorkspaceJson(unittest.TestCase):
    """Test cases for normalize_workspace_json function"""
    
    @classmethod
    def setUpClass(cls):
        """Load mock data once for all tests"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), 'mock_data')
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_old_format.json')) as f:
            cls.old_format_data = json.load(f)
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_new_format.json')) as f:
            cls.new_format_data = json.load(f)
    
    def test_normalize_old_format_converts_to_new(self):
        """Test that old format (string array) is converted to new format (object array)"""
        result = normalize_workspace_json(self.old_format_data, "test-workspace")
        
        self.assertIsNotNone(result)
        self.assertIn("test-workspace", result)
        
        workspace = result["test-workspace"]
        compatibility = workspace.get('compatibility', [])
        
        # Should have converted string array to object array
        self.assertTrue(all(isinstance(entry, dict) for entry in compatibility))
        
        # Check first entry structure
        first_entry = compatibility[0]
        self.assertIn('version', first_entry)
        self.assertIn('image', first_entry)
        self.assertIn('uncompressed_size_mb', first_entry)
        
        # Check that versions were preserved
        versions = [entry['version'] for entry in compatibility]
        self.assertEqual(versions, ["1.15.x", "1.16.x", "1.17.x"])
    
    def test_normalize_new_format_returns_as_is(self):
        """Test that new format is returned wrapped with folder name"""
        result = normalize_workspace_json(self.new_format_data, "test-workspace")
        
        self.assertIsNotNone(result)
        self.assertIn("test-workspace", result)
        
        workspace = result["test-workspace"]
        compatibility = workspace.get('compatibility', [])
        
        # Should already be object array
        self.assertTrue(all(isinstance(entry, dict) for entry in compatibility))
        self.assertEqual(len(compatibility), 3)
    
    def test_normalize_invalid_format_returns_none(self):
        """Test that invalid format returns None"""
        invalid_data = "not a dict"
        result = normalize_workspace_json(invalid_data, "test-workspace")
        
        self.assertIsNone(result)
    
    def test_normalize_empty_dict_returns_wrapped(self):
        """Test that empty dict is still wrapped with folder name"""
        empty_data = {}
        result = normalize_workspace_json(empty_data, "test-workspace")
        
        self.assertIsNotNone(result)
        self.assertIn("test-workspace", result)
    
    def test_old_format_image_name_propagation(self):
        """Test that image name from 'name' field propagates to compatibility entries"""
        result = normalize_workspace_json(self.old_format_data, "test-workspace")
        workspace = result["test-workspace"]
        compatibility = workspace.get('compatibility', [])
        
        # All entries should have the same image name from original 'name' field
        expected_image = self.old_format_data['name']
        for entry in compatibility:
            self.assertEqual(entry['image'], expected_image)
    
    def test_old_format_size_propagation(self):
        """Test that uncompressed_size_mb propagates to all compatibility entries"""
        result = normalize_workspace_json(self.old_format_data, "test-workspace")
        workspace = result["test-workspace"]
        compatibility = workspace.get('compatibility', [])
        
        expected_size = self.old_format_data['uncompressed_size_mb']
        for entry in compatibility:
            self.assertEqual(entry['uncompressed_size_mb'], expected_size)


if __name__ == '__main__':
    unittest.main()
