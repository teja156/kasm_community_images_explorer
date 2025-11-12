"""
Unit tests for URL validation functionality.
Tests the is_valid_http_url function which prevents XSS attacks.
"""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_github import is_valid_http_url


class TestUrlValidation(unittest.TestCase):
    """Test cases for is_valid_http_url function"""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URLs pass"""
        url = "https://example.com/registry"
        self.assertTrue(is_valid_http_url(url))
    
    def test_valid_http_url(self):
        """Test that valid HTTP URLs pass"""
        url = "http://example.com/registry"
        self.assertTrue(is_valid_http_url(url))
    
    def test_javascript_url_blocked(self):
        """Test that javascript: URLs are blocked (XSS prevention)"""
        url = "javascript:alert('XSS')"
        self.assertFalse(is_valid_http_url(url))
    
    def test_data_url_blocked(self):
        """Test that data: URLs are blocked"""
        url = "data:text/html,<script>alert('XSS')</script>"
        self.assertFalse(is_valid_http_url(url))
    
    def test_file_url_blocked(self):
        """Test that file: URLs are blocked"""
        url = "file:///etc/passwd"
        self.assertFalse(is_valid_http_url(url))
    
    def test_ftp_url_blocked(self):
        """Test that ftp: URLs are blocked"""
        url = "ftp://example.com/file"
        self.assertFalse(is_valid_http_url(url))
    
    def test_empty_string_returns_false(self):
        """Test that empty string returns False"""
        self.assertFalse(is_valid_http_url(""))
    
    def test_none_returns_false(self):
        """Test that None returns False"""
        self.assertFalse(is_valid_http_url(None))
    
    def test_non_string_returns_false(self):
        """Test that non-string values return False"""
        self.assertFalse(is_valid_http_url(12345))
        self.assertFalse(is_valid_http_url(['http://example.com']))
    
    def test_url_without_scheme_returns_false(self):
        """Test that URLs without scheme return False"""
        self.assertFalse(is_valid_http_url("example.com"))
    
    def test_url_without_netloc_returns_false(self):
        """Test that URLs without network location return False"""
        self.assertFalse(is_valid_http_url("http://"))
    
    def test_github_pages_url(self):
        """Test that typical GitHub Pages URLs pass"""
        url = "https://username.github.io/repo-name/"
        self.assertTrue(is_valid_http_url(url))
    
    def test_url_with_path(self):
        """Test that URLs with paths pass"""
        url = "https://example.com/path/to/resource"
        self.assertTrue(is_valid_http_url(url))
    
    def test_url_with_query_params(self):
        """Test that URLs with query parameters pass"""
        url = "https://example.com/page?param=value&other=123"
        self.assertTrue(is_valid_http_url(url))


if __name__ == '__main__':
    unittest.main()
