# Model Starter Service
# This service starts and manages model inference endpoints, automatically starting models when they are requested

import asyncio
import aiohttp
import logging
from aiohttp import web
import sys
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/model-starter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
INFERENCE_SERVER_HOST = os.getenv('INFERENCE_SERVER_HOST', 'localhost')
INFERENCE_SERVER_PORT = os.getenv('INFERENCE_SERVER_PORT', '5002')
INFERENCE_SERVER_URL = f"http://{INFERENCE_SERVER_HOST}:{INFERENCE_SERVER_PORT}"

class ModelStarter:
    def __init__(self):
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        # Register all HTTP methods for the model endpoint
        self.app.router.add_route('*', '/{model_name}/', self.handle_model_request)
        self.app.router.add_route('*', '/{model_name}/{path:.*}', self.handle_model_request)
        
    async def check_model_running(self) -> bool:
        """Check if any models are currently running on the inference server"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{INFERENCE_SERVER_URL}/models/running") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('running', False)
                    else:
                        logger.warning(f"Unexpected status code checking model status: {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.error("Timeout while checking model status")
            return False
        except Exception as e:
            logger.error(f"Error checking model status: {e}")
            return False
        
    async def start_model(self, model_name: str) -> bool:
        """Start a specific model on the inference server"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(f"{INFERENCE_SERVER_URL}/models/{model_name}/start") as response:
                    if response.status == 200:
                        logger.info(f"Model {model_name} started successfully")
                        return True
                    else:
                        logger.error(f"Failed to start model {model_name}: HTTP {response.status}")
                        return False
        except asyncio.TimeoutError:
            logger.error(f"Timeout while starting model {model_name}")
            return False
        except Exception as e:
            logger.error(f"Error starting model {model_name}: {e}")
            return False
            
    async def wait_for_model_ready(self, model_name: str, timeout: int = 60) -> bool:
        """Wait for a model to become ready"""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{INFERENCE_SERVER_URL}/models/running") as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('running', False):
                                logger.info(f"Model {model_name} is now running")
                                return True
                        else:
                            logger.warning(f"Unexpected status code checking model status: {response.status}")
            except asyncio.TimeoutError:
                logger.debug(f"Timeout checking model status for {model_name}")
            except Exception as e:
                logger.debug(f"Error checking model status during wait: {e}")
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
            
        logger.error(f"Timeout waiting for model {model_name} to start")
        return False
        
    async def handle_model_request(self, request: web.Request) -> web.Response:
        """Handle incoming requests to model endpoints"""
        model_name = request.match_info.get('model_name', '')
        path = request.match_info.get('path', '')
        
        if not model_name:
            logger.warning("No model name provided in request")
            return web.Response(status=400, text="Model name required")
            
        logger.info(f"Request for model: {model_name}, path: {path}")
        
        # Check if model is running
        is_running = await self.check_model_running()
        
        if not is_running:
            logger.info(f"Model {model_name} not running, starting it now...")
            success = await self.start_model(model_name)
            
            if not success:
                logger.error(f"Failed to start model {model_name}")
                return web.Response(status=500, text=f"Failed to start model {model_name}")
                
            # Wait for model to be ready
            ready = await self.wait_for_model_ready(model_name)
            if not ready:
                logger.error(f"Model {model_name} failed to become ready")
                return web.Response(status=500, text=f"Model {model_name} failed to start")
        
        # Return 504 to indicate to nginx that it should retry the upstream
        # This is because we've ensured the model is ready, but we want nginx to 
        # retry the actual request to the real model service
        logger.info(f"Model {model_name} is ready, returning 504 to trigger nginx retry")
        return web.Response(status=504, text="Service Unavailable - Model ready, retry upstream")

    def run(self, host='0.0.0.0', port=8080):
        """Run the starter server"""
        web.run_app(self.app, host=host, port=port)

if __name__ == '__main__':
    starter = ModelStarter()
    starter.run()