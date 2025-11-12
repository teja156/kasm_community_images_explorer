"""
Unit tests for workspace filtering functionality.
Tests the filter_original_workspace_json function which preserves format while filtering pullable entries.
"""

import unittest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import filter_original_workspace_json


class TestFilterOriginalWorkspaceJson(unittest.TestCase):
    """Test cases for filter_original_workspace_json function"""
    
    @classmethod
    def setUpClass(cls):
        """Load mock data once for all tests"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), 'mock_data')
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_old_format.json')) as f:
            cls.old_format_data = json.load(f)
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_new_format.json')) as f:
            cls.new_format_data = json.load(f)
    
    def test_filter_old_format_by_versions(self):
        """Test filtering old format (string array) by matching versions"""
        # Original has ["1.15.x", "1.16.x", "1.17.x"]
        # Pullable only has 1.16.x and 1.17.x
        pullable = {
            'compatibility': [
                {'version': '1.16.x', 'image': 'test/image:1.16', 'uncompressed_size_mb': 500},
                {'version': '1.17.x', 'image': 'test/image:1.17', 'uncompressed_size_mb': 500}
            ]
        }
        
        result = filter_original_workspace_json(self.old_format_data, pullable)
        
        self.assertIsNotNone(result)
        # Should still be string array (old format preserved)
        self.assertTrue(all(isinstance(v, str) for v in result['compatibility']))
        # Should only have 1.16.x and 1.17.x
        self.assertEqual(result['compatibility'], ['1.16.x', '1.17.x'])
    
    def test_filter_new_format_by_images(self):
        """Test filtering new format (object array) by matching images"""
        # Pullable only has one image
        pullable = {
            'compatibility': [
                {'version': '1.16.x', 'image': 'myregistry/test-image:1.16.0', 'uncompressed_size_mb': 510}
            ]
        }
        
        result = filter_original_workspace_json(self.new_format_data, pullable)
        
        self.assertIsNotNone(result)
        # Should still be object array (new format preserved)
        self.assertTrue(all(isinstance(entry, dict) for entry in result['compatibility']))
        # Should only have one entry
        self.assertEqual(len(result['compatibility']), 1)
        self.assertEqual(result['compatibility'][0]['image'], 'myregistry/test-image:1.16.0')
    
    def test_filter_returns_none_when_pullable_is_none(self):
        """Test that None pullable workspace returns None"""
        result = filter_original_workspace_json(self.old_format_data, None)
        self.assertIsNone(result)
    
    def test_filter_returns_none_when_no_matching_entries(self):
        """Test that no matching entries returns None"""
        # Pullable has versions/images not in original
        pullable = {
            'compatibility': [
                {'version': '1.99.x', 'image': 'different/image:1.99', 'uncompressed_size_mb': 500}
            ]
        }
        
        result = filter_original_workspace_json(self.old_format_data, pullable)
        self.assertIsNone(result)
    
    def test_filter_returns_none_when_pullable_compatibility_empty(self):
        """Test that empty pullable compatibility returns None"""
        pullable = {'compatibility': []}
        
        result = filter_original_workspace_json(self.old_format_data, pullable)
        self.assertIsNone(result)
    
    def test_filter_preserves_other_fields(self):
        """Test that filtering preserves all other workspace fields"""
        pullable = {
            'compatibility': [
                {'version': '1.16.x', 'image': 'test/image:1.16', 'uncompressed_size_mb': 500}
            ]
        }
        
        result = filter_original_workspace_json(self.old_format_data, pullable)
        
        # Check that other fields are preserved
        self.assertEqual(result['friendly_name'], self.old_format_data['friendly_name'])
        self.assertEqual(result['description'], self.old_format_data['description'])
        self.assertEqual(result['categories'], self.old_format_data['categories'])
    
    def test_filter_creates_copy_not_modifies_original(self):
        """Test that filtering creates a copy and doesn't modify original"""
        original_compat_len = len(self.old_format_data['compatibility'])
        
        pullable = {
            'compatibility': [
                {'version': '1.16.x', 'image': 'test/image:1.16', 'uncompressed_size_mb': 500}
            ]
        }
        
        result = filter_original_workspace_json(self.old_format_data, pullable)
        
        # Original should be unchanged
        self.assertEqual(len(self.old_format_data['compatibility']), original_compat_len)
        # Result should be filtered
        self.assertEqual(len(result['compatibility']), 1)
    
    def test_filter_multiple_matching_entries_new_format(self):
        """Test filtering preserves multiple matching entries in new format"""
        # Pullable has 2 out of 3 images
        pullable = {
            'compatibility': [
                {'version': '1.15.x', 'image': 'myregistry/test-image:1.15.0', 'uncompressed_size_mb': 500},
                {'version': '1.17.x', 'image': 'myregistry/test-image:1.17.0', 'uncompressed_size_mb': 520}
            ]
        }
        
        result = filter_original_workspace_json(self.new_format_data, pullable)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['compatibility']), 2)
        
        # Check order is preserved
        self.assertEqual(result['compatibility'][0]['version'], '1.15.x')
        self.assertEqual(result['compatibility'][1]['version'], '1.17.x')


if __name__ == '__main__':
    unittest.main()
