"""
Unit tests for image name filtering functionality.
Tests the should_skip_image function which blocks certain registry prefixes.
"""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import should_skip_image, IMAGE_NAME_PREFIX_FILTERS


class TestImageFiltering(unittest.TestCase):
    """Test cases for should_skip_image function"""
    
    def test_kasmweb_prefix_is_blocked(self):
        """Test that images with kasmweb/ prefix are blocked"""
        result = should_skip_image("kasmweb/chrome:latest")
        self.assertTrue(result)
    
    def test_non_blocked_image_passes(self):
        """Test that non-blocked images pass through"""
        result = should_skip_image("myregistry/myimage:latest")
        self.assertFalse(result)
    
    def test_empty_image_name_returns_false(self):
        """Test that empty image name returns False"""
        result = should_skip_image("")
        self.assertFalse(result)
    
    def test_none_image_name_returns_false(self):
        """Test that None image name returns False"""
        result = should_skip_image(None)
        self.assertFalse(result)
    
    def test_whitespace_handling(self):
        """Test that whitespace is stripped before checking"""
        result = should_skip_image("  kasmweb/chrome:latest  ")
        self.assertTrue(result)
    
    def test_registry_prefix_addition(self):
        """Test that docker_registry is prepended when checking"""
        # Image without registry prefix, but when combined with registry becomes blocked
        result = should_skip_image("chrome:latest", docker_registry="kasmweb")
        # This should be True because it tries "kasmweb/chrome:latest"
        self.assertTrue(result)
    
    def test_image_already_has_registry(self):
        """Test that image already with registry doesn't get double-prefixed"""
        result = should_skip_image("kasmweb/chrome:latest", docker_registry="kasmweb")
        self.assertTrue(result)
    
    def test_multiple_blocked_prefixes(self):
        """Test that all prefixes in IMAGE_NAME_PREFIX_FILTERS are checked"""
        # Verify kasmweb/ is in the filters
        self.assertIn("kasmweb/", IMAGE_NAME_PREFIX_FILTERS)
        
        for prefix in IMAGE_NAME_PREFIX_FILTERS:
            test_image = f"{prefix}testimage:latest"
            result = should_skip_image(test_image)
            self.assertTrue(result, f"Failed to block {test_image}")


if __name__ == '__main__':
    unittest.main()
