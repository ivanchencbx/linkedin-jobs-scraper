"""
LinkedIn Jobs Scraper Package
"""

__version__ = "1.0.0"
__author__ = "Ivan Chen"

from linkedin_scraper.auth.authenticator import LinkedInAuthenticator
from linkedin_scraper.scraper.job_scraper import JobScraper
from linkedin_scraper.storage.csv_manager import JobCSVManager

__all__ = [
    'LinkedInAuthenticator',
    'JobScraper', 
    'JobCSVManager'
]