#!/usr/bin/env python3
"""Setup script for TestForge."""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="testforge",
    version="1.0.0",
    description="Comprehensive mutation testing framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TestForge Team",
    author_email="dev@testforge.io",
    url="https://github.com/moggan1337/TestForge",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "astor>=0.8.1",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "isort>=5.12",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "testforge=testforge.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="mutation-testing test-quality coverage testing",
    project_urls={
        "Bug Reports": "https://github.com/moggan1337/TestForge/issues",
        "Source": "https://github.com/moggan1337/TestForge",
    },
)
