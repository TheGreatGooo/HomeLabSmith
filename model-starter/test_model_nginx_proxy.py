# Test file for Model Starter Service
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_starter import ModelStarter

class TestModelStarter(unittest.TestCase):
    
    def setUp(self):
        self.starter = ModelStarter()
        
    def test_setup_routes(self):
        """Test that routes are properly set up"""
        # Check that we have routes for different HTTP methods
        routes = [route for route in self.starter.app.router.routes()]
        self.assertGreater(len(routes), 0)
        
    @patch('aiohttp.ClientSession.get')
    async def test_check_model_running_success(self, mock_get):
        """Test successful model status check"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'running': True})
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.starter.check_model_running()
        self.assertTrue(result)
        
    @patch('aiohttp.ClientSession.get')
    async def test_check_model_running_failure(self, mock_get):
        """Test failed model status check"""
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.starter.check_model_running()
        self.assertFalse(result)
        
    @patch('aiohttp.ClientSession.post')
    async def test_start_model_success(self, mock_post):
        """Test successful model start"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.starter.start_model("test_model")
        self.assertTrue(result)
        
    @patch('aiohttp.ClientSession.post')
    async def test_start_model_failure(self, mock_post):
        """Test failed model start"""
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.starter.start_model("test_model")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()