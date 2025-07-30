#!/usr/bin/env python3
"""
Setup script for SonicLink package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="soniclink",
    version="1.0.0",
    author="SonicLink Team",
    author_email="contact@soniclink.dev",
    description="High-Speed Ultrasonic Data Communication System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/makalin/SonicLink",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.0",
            "pytest-mock>=3.6.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "soniclink=soniclink.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "ultrasonic",
        "communication",
        "audio",
        "data-transfer",
        "ofdm",
        "encryption",
        "compression",
        "wireless",
        "air-gap",
    ],
    project_urls={
        "Bug Reports": "https://github.com/makalin/SonicLink/issues",
        "Source": "https://github.com/makalin/SonicLink",
        "Documentation": "https://github.com/makalin/SonicLink#readme",
    },
) 