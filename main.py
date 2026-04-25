#!/usr/bin/env python3
"""
LinkedIn Jobs Scraper - Main Entry Point
Command-line interface for scraping LinkedIn jobs
"""

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_scraper.auth.authenticator import LinkedInAuthenticator
from linkedin_scraper.scraper.job_scraper import JobScraper
from linkedin_scraper.storage.csv_manager import JobCSVManager
from linkedin_scraper.utils.helpers import load_config, setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='LinkedIn Jobs Scraper - Extract job listings from LinkedIn',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config (will prompt for credentials)
  python main.py
  
  # Scrape only 5 pages
  python main.py --max-pages 5
  
  # Use custom config file
  python main.py --config /path/to/config.yaml
  
  # Run without headless mode (visible browser)
  python main.py --visible
  
  # Refresh session only (validate and update cookies)
  python main.py --refresh-session
  
  # Show CSV stats
  python main.py --stats
  
  # Clear saved cookies (force new login)
  python main.py --clear-cookies
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '-p', '--max-pages',
        type=int,
        default=None,
        help='Maximum number of pages to scrape (default: all pages)'
    )
    
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    
    parser.add_argument(
        '--refresh-session',
        action='store_true',
        help='Refresh session and update cookies without scraping'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics from CSV file'
    )
    
    parser.add_argument(
        '--clear-cookies',
        action='store_true',
        help='Clear saved cookies and force new login'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def clear_cookies():
    """Clear saved cookies file"""
    cookie_file = Path('cookies.json')
    if cookie_file.exists():
        cookie_file.unlink()
        print("✓ Cookies cleared successfully")
    else:
        print("ℹ️ No cookies file found")


def show_stats(config):
    """Display CSV statistics"""
    storage_config = config.get('storage', {})
    filename = storage_config.get('filename', 'linkedin_jobs.csv')
    
    manager = JobCSVManager(filename)
    jobs = manager.read_all_jobs()
    
    print("\n" + "="*60)
    print("LINKEDIN JOBS CSV STATISTICS")
    print("="*60)
    print(f"File: {filename}")
    print(f"Total jobs: {len(jobs)}")
    
    if jobs:
        # Company statistics
        companies = {}
        locations = {}
        for job in jobs:
            company = job.get('company', 'N/A')
            location = job.get('location', 'N/A')
            companies[company] = companies.get(company, 0) + 1
            locations[location] = locations.get(location, 0) + 1
        
        print(f"\n📊 Top 10 companies by job count:")
        for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {company}: {count}")
        
        print(f"\n📍 Top 10 locations:")
        for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {location}: {count}")
        
        # Date range
        dates = [job.get('updatedatetime', '') for job in jobs if job.get('updatedatetime')]
        if dates:
            print(f"\n🕒 Last updated: {max(dates)}")
    
    print("="*60 + "\n")


def refresh_session(config, visible=False):
    """Refresh LinkedIn session"""
    print("🔄 Refreshing LinkedIn session...")
    
    # Temporarily override headless setting
    if visible:
        config['browser']['headless'] = False
    
    authenticator = LinkedInAuthenticator(config)
    driver = None
    
    try:
        driver = authenticator.authenticate()
        success = authenticator.refresh_session(driver)
        
        if success:
            print("✓ Session refreshed successfully!")
            return True
        else:
            print("✗ Failed to refresh session")
            return False
    except Exception as e:
        print(f"✗ Error refreshing session: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Handle clear cookies command (doesn't need config)
    if args.clear_cookies:
        clear_cookies()
        return 0
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override headless mode if visible flag is set
        if args.visible:
            config['browser']['headless'] = False
            print("ℹ️ Running in visible browser mode")
        
        # Setup logging
        if args.verbose:
            config['logging']['level'] = 'DEBUG'
        setup_logging(config)
        
        logger.info("Starting LinkedIn Jobs Scraper")
        
        # Handle stats command
        if args.stats:
            show_stats(config)
            return 0
        
        # Handle session refresh command
        if args.refresh_session:
            success = refresh_session(config, args.visible)
            return 0 if success else 1
        
        # Run scraper
        print("\n" + "="*60)
        print("LINKEDIN JOBS SCRAPER")
        print("="*60)
        print(f"Config: {args.config}")
        if args.max_pages:
            print(f"Max pages: {args.max_pages}")
        if args.visible:
            print("Mode: Visible browser")
        else:
            print("Mode: Headless (background)")
        print("="*60)
        
        authenticator = LinkedInAuthenticator(config)
        scraper = JobScraper(config, authenticator)
        
        # Start scraping
        stats = scraper.scrape_jobs(max_pages=args.max_pages)
        
        # Print results
        print("\n" + "="*60)
        print("SCRAPING RESULTS")
        print("="*60)
        print(f"📊 Total jobs found: {stats['total_jobs_found']}")
        print(f"✅ Jobs added: {stats['jobs_added']}")
        print(f"🔄 Jobs updated: {stats['jobs_updated']}")
        print(f"📄 Pages scraped: {stats['pages_scraped']}")
        print(f"⚠️ Errors: {stats['errors']}")
        
        if stats['jobs_added'] > 0 or stats['jobs_updated'] > 0:
            print(f"\n💾 Data saved to: {config.get('storage', {}).get('filename', 'linkedin_jobs.csv')}")
        
        print("="*60 + "\n")
        
        logger.info("Scraping completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Program interrupted by user")
        logger.warning("Program interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())