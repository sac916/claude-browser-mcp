"""
Setup configuration for Browser MCP Server

This setup.py file configures the installation and distribution of the
browser MCP server package. It defines dependencies, entry points,
and package metadata.
"""

from setuptools import setup, find_packages
import os

# Read README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Browser automation MCP server using Playwright"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Remove version constraints for basic parsing
                    package = line.split('>=')[0].split('==')[0].split('<=')[0]
                    requirements.append(line)
    
    return requirements

setup(
    name="claude-browser-mcp",
    version="0.1.0",
    description="Browser automation MCP server using Playwright",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Claude Assistant",
    author_email="claude@anthropic.com",
    url="https://github.com/anthropic/claude-browser-mcp",
    
    # Package configuration
    packages=find_packages(),
    package_dir={'': '.'},
    include_package_data=True,
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points for command line usage
    entry_points={
        "console_scripts": [
            "browser-mcp=src.server:main",
            "claude-browser-mcp=src.server:main",
        ],
    },
    
    # Package classification
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
    ],
    
    # Keywords for package discovery
    keywords=[
        "mcp", "browser", "automation", "playwright", "web", "scraping",
        "claude", "ai", "assistant", "model-context-protocol"
    ],
    
    # Additional metadata
    project_urls={
        "Documentation": "https://github.com/anthropic/claude-browser-mcp/blob/main/README.md",
        "Source": "https://github.com/anthropic/claude-browser-mcp",
        "Tracker": "https://github.com/anthropic/claude-browser-mcp/issues",
    },
    
    # Package data
    package_data={
        "src": ["*.py"],
    },
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0", 
            "black>=23.0.0",
            "mypy>=1.5.0",
            "flake8>=6.0.0",
        ],
        "full": [
            "beautifulsoup4>=4.12.0",
            "lxml>=4.9.0",
            "httpx>=0.25.0",
            "pyyaml>=6.0",
        ]
    },
    
    # Zip safety
    zip_safe=False,
)