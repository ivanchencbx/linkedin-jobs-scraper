"""
LinkedIn Job Scraper Module
Handles job search and extraction
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from linkedin_scraper.auth.authenticator import LinkedInAuthenticator
from linkedin_scraper.storage.csv_manager import JobCSVManager

logger = logging.getLogger(__name__)


class JobScraper:
    """LinkedIn job scraper handler"""
    
    def __init__(self, config: Dict[str, Any], authenticator: LinkedInAuthenticator):
        """
        Initialize job scraper
        
        Args:
            config: Configuration dictionary
            authenticator: LinkedIn authenticator instance
        """
        self.config = config
        self.authenticator = authenticator
        self.search_config = config.get('search', {})
        self.wait_config = config.get('waits', {})
        self.storage_config = config.get('storage', {})
        
        self.driver = None
        self.csv_manager = JobCSVManager(self.storage_config.get('filename', 'linkedin_jobs.csv'))
        
    def _build_search_url(self, start: int = 0) -> str:
        """
        Build job search URL with filters
        
        Args:
            start: Starting index for pagination
            
        Returns:
            Complete search URL
        """
        base_url = self.search_config.get('base_url', 'https://www.linkedin.com/jobs/search/')
        
        # Build query parameters
        params = {
            'f_F': self.search_config.get('filters', {}).get('f_F', 'it'),
            'f_CR': self.search_config.get('filters', {}).get('f_CR', '102890883'),
            'f_E': self.search_config.get('filters', {}).get('f_E', '3,4,5,6'),
            'f_JT': self.search_config.get('filters', {}).get('f_JT', 'F'),
            'f_TPR': self.search_config.get('filters', {}).get('f_TPR', '2592000'),
            'f_WT': self.search_config.get('filters', {}).get('f_WT', '1'),
            'geoId': '92000000',
            'keywords': self.search_config.get('keywords', ''),
            'origin': 'JOB_SEARCH_PAGE_SEARCH_BUTTON',
            'refresh': 'true',
            'sortBy': self.search_config.get('sort_by', 'R'),
            'start': str(start)
        }
        
        return f"{base_url}?{urlencode(params)}"
    
    def _get_total_job_count(self) -> int:
        """
        Get total number of jobs from search results
        
        Returns:
            Total job count
        """
        try:
            wait = WebDriverWait(self.driver, self.wait_config.get('element_wait', 60))
            result_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='main']/div/div[2]/div[1]/header/div[1]/div/small/div/span"))
            )
            count_text = result_element.text.split()[0]
            total_jobs = int(count_text.replace(',', ''))
            logger.info(f"Total jobs found: {total_jobs}")
            print(f"📊 Total jobs found: {total_jobs}")
            return total_jobs
        except Exception as e:
            logger.error(f"Failed to get job count: {e}")
            return 0
    
    def _extract_jobs_from_page(self, page_num: int) -> List[Dict[str, str]]:
        """
        Extract job listings from current page
        
        Args:
            page_num: Current page number (for logging)
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        try:
            # Wait for job list to load
            job_elements = WebDriverWait(self.driver, self.wait_config.get('element_wait', 60)).until(
                EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'ember-view') and contains(@class, 'occludable-update')]"))
            )
            
            logger.info(f"Found {len(job_elements)} jobs on page {page_num}")
            print(f"  📄 Page {page_num}: Found {len(job_elements)} job listings")
            
            for job_element in job_elements:
                try:
                    job_id = job_element.find_element(By.XPATH, ".//div/div").get_attribute("data-job-id")
                    
                    # Extract job details with error handling for each field
                    try:
                        job_title = job_element.find_element(By.XPATH, ".//div/div/div/div/div[2]/div/a/span").text
                    except NoSuchElementException:
                        job_title = "N/A"
                    
                    try:
                        company = job_element.find_element(By.XPATH, ".//div/div/div/div/div[2]/div[2]/span").text
                    except NoSuchElementException:
                        company = "N/A"
                    
                    try:
                        location = job_element.find_element(By.XPATH, ".//div/div/div/div/div[2]/div[3]/ul/li/span").text
                    except NoSuchElementException:
                        location = "N/A"
                    
                    job_data = {
                        'jobid': job_id,
                        'jobtitle': job_title,
                        'company': company,
                        'location': location,
                        'url': f"https://www.linkedin.com/jobs/view/{job_id}",
                        'updatedatetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    jobs.append(job_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract individual job: {e}")
                    continue
                    
        except TimeoutException:
            logger.warning(f"Timeout waiting for job elements on page {page_num}")
            print(f"  ⚠️ Timeout waiting for job elements on page {page_num}")
        except Exception as e:
            logger.error(f"Error extracting jobs from page {page_num}: {e}")
            
        return jobs
    
    def scrape_jobs(self, max_pages: Optional[int] = None) -> Dict[str, int]:
        """
        Main job scraping method
        
        Args:
            max_pages: Maximum number of pages to scrape (None for all)
            
        Returns:
            Dictionary with scraping statistics
        """
        stats = {
            'total_jobs_found': 0,
            'jobs_added': 0,
            'jobs_updated': 0,
            'pages_scraped': 0,
            'errors': 0
        }
        
        try:
            # Authenticate and get driver
            print("\n🚀 Starting LinkedIn Job Scraper")
            print("="*60)
            self.driver = self.authenticator.authenticate()
            
            # Navigate to first page
            first_page_url = self._build_search_url(0)
            logger.info(f"Navigating to search URL: {first_page_url}")
            print(f"\n🔍 Searching for jobs...")
            self.driver.get(first_page_url)
            
            # Wait for page to load
            page_load_wait = self.wait_config.get('page_load', 300)
            logger.info(f"Waiting {page_load_wait} seconds for page to load...")
            print(f"⏳ Waiting {page_load_wait} seconds for page to load...")
            time.sleep(page_load_wait)
            
            # Get total job count
            total_jobs = self._get_total_job_count()
            stats['total_jobs_found'] = total_jobs
            
            if total_jobs == 0:
                logger.warning("No jobs found")
                print("⚠️ No jobs found matching the search criteria")
                return stats
            
            # Calculate number of pages
            results_per_page = self.search_config.get('results_per_page', 25)
            total_pages = (total_jobs + results_per_page - 1) // results_per_page
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
                print(f"📑 Scraping first {total_pages} pages (limited by --max-pages)")
            else:
                print(f"📑 Scraping all {total_pages} pages")
            
            # Scrape each page
            for page_num in range(1, total_pages + 1):
                start_index = (page_num - 1) * results_per_page
                
                if page_num > 1:
                    # Navigate to next page
                    next_page_url = self._build_search_url(start_index)
                    logger.info(f"Navigating to page {page_num}: {next_page_url}")
                    print(f"\n📖 Loading page {page_num}...")
                    self.driver.get(next_page_url)
                    time.sleep(self.wait_config.get('between_pages', 5))
                
                # Extract jobs from current page
                page_jobs = self._extract_jobs_from_page(page_num)
                
                if page_jobs:
                    # Save to CSV
                    added, updated = self.csv_manager.upsert_jobs(page_jobs)
                    stats['jobs_added'] += added
                    stats['jobs_updated'] += updated
                    print(f"  💾 Saved: +{added} new, {updated} updated (Total: {stats['jobs_added']} new, {stats['jobs_updated']} updated)")
                else:
                    logger.warning(f"No jobs extracted from page {page_num}")
                    print(f"  ⚠️ No jobs extracted from page {page_num}")
                    stats['errors'] += 1
                
                stats['pages_scraped'] = page_num
                
                # Add delay between pages (except after last page)
                if page_num < total_pages:
                    time.sleep(self.wait_config.get('between_pages', 5))
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ Scraping interrupted by user")
            logger.warning("Scraping interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            print(f"\n❌ Scraping failed: {e}")
            stats['errors'] += 1
            raise
        finally:
            self.close()
            
        print("\n✅ Scraping completed successfully!")
        logger.info(f"Scraping completed: {stats}")
        return stats
    
    def close(self):
        """Close WebDriver and cleanup"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
            print("🔒 Browser closed")