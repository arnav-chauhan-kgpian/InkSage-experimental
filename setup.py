"""
Setup script for InkSage Context Engine.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="inksage",
    version="1.0.0",
    author="InkSage Team",
    author_email="dev@inksage.local",
    description="A privacy-first, context-aware local AI writing assistant.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/inksage",
    
    # Automatically find packages under src/
    packages=find_packages(),
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: General",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: X11 Applications :: Qt",
    ],
    
    # PySide6 and modern async features usually require 3.10+
    python_requires=">=3.10",
    
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        # Optional RAG dependencies for future expansion
        "rag": [
            "chromadb>=0.4.0",
            "sentence-transformers>=2.2.0"
        ]
    },
    
    # Creates the 'inksage' command line tool
    entry_points={
        "console_scripts": [
            "inksage=src.main:main",
        ],
    },
    
    include_package_data=True,
    package_data={
        # Ensure config and assets are bundled
        "": ["config/*.yaml", "assets/*"],
    },
    
    zip_safe=False,
    # Updated keywords for the PyTorch/Transformers stack
    keywords="ai writing-assistant local-llm pytorch transformers pyside6 privacy",
    
    project_urls={
        "Bug Reports": "https://github.com/your-username/inksage/issues",
        "Source": "https://github.com/your-username/inksage",
    },
)