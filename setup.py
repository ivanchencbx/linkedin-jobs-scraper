"""
Setup script for LinkedIn Jobs Scraper
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="linkedin-jobs-scraper-cbx",
    version="1.0.2",
    author="Ivan Chen",
    author_email="ivanchen99@gmail.com",
    description="A professional web scraping tool for extracting job listings from LinkedIn",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ivanchencbx/linkedin-jobs-scraper",
    project_urls={
        "Bug Tracker": "https://github.com/ivanchencbx/linkedin-jobs-scraper/issues",
        "Documentation": "https://github.com/ivanchencbx/linkedin-jobs-scraper",
        "Source Code": "https://github.com/ivanchencbx/linkedin-jobs-scraper",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "linkedin-scraper=linkedin_scraper.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "linkedin_scraper": ["config/*.yaml"],
    },
    keywords="linkedin, scraper, jobs, automation, selenium, career",
)