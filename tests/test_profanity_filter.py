"""
Unit tests for profanity filtering functionality.
Tests the check_profanity_in_workspace function.
"""

import unittest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import check_profanity_in_workspace, STATS


class TestProfanityFiltering(unittest.TestCase):
    """Test cases for check_profanity_in_workspace function"""
    
    @classmethod
    def setUpClass(cls):
        """Load mock data once for all tests"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), 'mock_data')
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_profanity.json')) as f:
            cls.profanity_data = json.load(f)
        
        with open(os.path.join(cls.mock_data_dir, 'workspace_old_format.json')) as f:
            cls.clean_data = json.load(f)
    
    def setUp(self):
        """Reset profanity stats before each test"""
        STATS['profanity_filtered_workspaces'] = 0
    
    def test_detect_profanity_in_description(self):
        """Test that profanity in description is detected"""
        result = check_profanity_in_workspace(self.profanity_data, "test-workspace")
        
        self.assertTrue(result)
        self.assertEqual(STATS['profanity_filtered_workspaces'], 1)
    
    def test_clean_workspace_passes(self):
        """Test that workspace without profanity passes"""
        result = check_profanity_in_workspace(self.clean_data, "test-workspace")
        
        self.assertFalse(result)
        self.assertEqual(STATS['profanity_filtered_workspaces'], 0)
    
    def test_profanity_in_workspace_name(self):
        """Test that profanity in workspace name is detected"""
        result = check_profanity_in_workspace(self.clean_data, "damn-workspace")
        
        self.assertTrue(result)
        self.assertEqual(STATS['profanity_filtered_workspaces'], 1)
    
    def test_profanity_in_friendly_name(self):
        """Test that profanity in friendly_name is detected"""
        data = self.clean_data.copy()
        data['friendly_name'] = "Damn Good Workspace"
        
        result = check_profanity_in_workspace(data, "test-workspace")
        
        self.assertTrue(result)
    
    def test_profanity_in_categories(self):
        """Test that profanity in categories is detected"""
        data = self.clean_data.copy()
        data['categories'] = ["Development", "Damn Tools"]
        
        result = check_profanity_in_workspace(data, "test-workspace")
        
        self.assertTrue(result)
    
    def test_empty_fields_no_false_positives(self):
        """Test that empty/missing fields don't cause false positives"""
        minimal_data = {
            'friendly_name': 'Clean Workspace',
            'description': '',
            'categories': []
        }
        
        result = check_profanity_in_workspace(minimal_data, "test-workspace")
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
