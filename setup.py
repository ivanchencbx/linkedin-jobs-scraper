"""
Setup script for LinkedIn Jobs Scraper
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="linkedin-jobs-scraper",
    version="1.0.0",
    author="Ivan Chen",
    description="LinkedIn Jobs Scraper - Extract job listings from LinkedIn",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ivanchencbx/linkedin-jobs-scraper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.15.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.2",
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "linkedin-scraper=main:main",
        ],
    },
)