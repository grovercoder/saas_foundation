import os
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
from typing import Any

class TemplatingManager:
    def __init__(self, logger: Any, template_dir: str | None = None):
        self.logger = logger
        
        if template_dir is None:
            # Default to a 'templates' directory within the templating package
            # Default to a 'templates' directory at the project root
            # Assuming the project root is two levels up from src/templating/manager.py
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            self.template_dir = os.path.join(project_root, 'templates')
        else:
            self.template_dir = template_dir

        # Ensure the template directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            self.logger.info(f"Created template directory: {self.template_dir}")
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True # Enable async for potential future use
        )
        self.logger.info(f"TemplatingManager initialized with template directory: {self.template_dir}")

    def get_environment(self) -> Environment:
        """Returns the Jinja2 Environment object."""
        return self.env

    def get_package_loader(self, package_name: str, package_path: str = 'templates') -> PackageLoader:
        """
        Returns a Jinja2 PackageLoader for this templating system's templates.
        This is useful for child applications to combine with their own loaders.
        """
        return PackageLoader(package_name, package_path)
