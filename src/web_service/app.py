from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.templating.manager import TemplatingManager
from src.logging_system.manager import LogManager
from typing import Any, Optional

class WebService:
    def __init__(self, logger: Any, templating_manager: TemplatingManager, mode: str):
        self.logger = logger
        self.app = FastAPI()
        self.templates = Jinja2Templates(directory=templating_manager.template_dir) # Use the root templates directory
        self.templating_manager = templating_manager
        self.server = None # To store the uvicorn.Server instance
        self.mode = mode # Store the application mode

        # Add a global dependency to inject the templating manager
        @self.app.middleware("http")
        async def add_templating_manager_to_request(request: Request, call_next):
            request.state.templating_manager = self.templating_manager
            response = await call_next(request)
            return response

        self.logger.info("WebService initialized.")

    def get_app(self) -> FastAPI:
        return self.app

    def set_server(self, server):
        self.server = server

# Global instance for easy access in routes
# This will be initialized in main.py
web_service_instance: Optional[WebService] = None

def get_web_service() -> WebService:
    if web_service_instance is None:
        raise Exception("WebService not initialized. Call WebService.initialize() first.")
    return web_service_instance

    def set_server(self, server):
        self.server = server

def initialize_web_service(logger: Any, templating_manager: TemplatingManager, server: Any, mode: str):
    global web_service_instance
    web_service_instance = WebService(logger, templating_manager, mode)
    web_service_instance.set_server(server)
    return web_service_instance
