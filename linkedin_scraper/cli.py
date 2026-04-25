#!/usr/bin/env python3
"""
Command-line interface for LinkedIn Jobs Scraper
This file serves as the entry point for the console script.
"""

import argparse
import sys
import logging
from pathlib import Path

# Import from package modules
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
  linkedin-scraper
  
  # Scrape only 5 pages
  linkedin-scraper --max-pages 5
  
  # Override search parameters
  linkedin-scraper --country 103890883 --experience "3,4,5,6" --job-type "F"
  
  # Custom keywords search
  linkedin-scraper --keywords '("Python"OR"Java")AND("Developer")'
  
  # Combine multiple overrides
  linkedin-scraper --max-pages 10 --time-range 2592000 --keywords '("AI"OR"ML")AND("Engineer")'
  
  # Use custom config file
  linkedin-scraper --config /path/to/config.yaml
  
  # Run without headless mode (visible browser)
  linkedin-scraper --visible
  
  # Refresh session only (validate and update cookies)
  linkedin-scraper --refresh-session
  
  # Show CSV stats
  linkedin-scraper --stats
  
  # Clear saved cookies (force new login)
  linkedin-scraper --clear-cookies
        """
    )
    
    # Config file option
    parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    # Scraping options
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
    
    # Search filter overrides
    search_group = parser.add_argument_group('Search Filter Overrides (override config.yaml values)')
    
    search_group.add_argument(
        '--country', '--f-cr',
        dest='f_CR',
        type=str,
        default=None,
        help='Country/Region ID (e.g., 102890883 for China, 103890883 for China Mainland)'
    )
    
    search_group.add_argument(
        '--experience', '--f-e',
        dest='f_E',
        type=str,
        default=None,
        help='Experience level IDs (comma-separated, e.g., 3,4,5,6 where 3=Entry,4=Associate,5=Senior,6=Director)'
    )
    
    search_group.add_argument(
        '--function', '--f-f',
        dest='f_F',
        type=str,
        default=None,
        help='Function area (e.g., it, sales, marketing)'
    )
    
    search_group.add_argument(
        '--job-type', '--f-jt',
        dest='f_JT',
        type=str,
        default=None,
        help='Job type (F=Full-time, C=Contract, P=Part-time, T=Temporary, I=Internship, V=Volunteer)'
    )
    
    search_group.add_argument(
        '--time-range', '--f-tpr',
        dest='f_TPR',
        type=str,
        default=None,
        help='Time range in seconds (e.g., 604800=7 days, 2592000=30 days, 7776000=90 days)'
    )
    
    search_group.add_argument(
        '--work-type', '--f-wt',
        dest='f_WT',
        type=str,
        default=None,
        help='Work type (1=On-site, 2=Remote, 3=Hybrid)'
    )
    
    search_group.add_argument(
        '--keywords', '-k',
        type=str,
        default=None,
        help='Search keywords (use quotes for complex queries)'
    )
    
    search_group.add_argument(
        '--sort-by',
        type=str,
        choices=['R', 'D'],
        default=None,
        help='Sort by: R=Recent, D=Date posted'
    )
    
    # Utility commands
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


def apply_search_overrides(config, args):
    """
    Apply command line search overrides to config
    
    Args:
        config: Configuration dictionary
        args: Parsed command line arguments
        
    Returns:
        Updated config dictionary
    """
    # Ensure search and filters sections exist
    if 'search' not in config:
        config['search'] = {}
    if 'filters' not in config['search']:
        config['search']['filters'] = {}
    
    # Apply overrides (only if provided via CLI)
    overrides_applied = []
    
    if args.f_CR is not None:
        config['search']['filters']['f_CR'] = args.f_CR
        overrides_applied.append(f"  f_CR = {args.f_CR}")
    
    if args.f_E is not None:
        config['search']['filters']['f_E'] = args.f_E
        overrides_applied.append(f"  f_E = {args.f_E}")
    
    if args.f_F is not None:
        config['search']['filters']['f_F'] = args.f_F
        overrides_applied.append(f"  f_F = {args.f_F}")
    
    if args.f_JT is not None:
        config['search']['filters']['f_JT'] = args.f_JT
        overrides_applied.append(f"  f_JT = {args.f_JT}")
    
    if args.f_TPR is not None:
        config['search']['filters']['f_TPR'] = args.f_TPR
        overrides_applied.append(f"  f_TPR = {args.f_TPR}")
    
    if args.f_WT is not None:
        config['search']['filters']['f_WT'] = args.f_WT
        overrides_applied.append(f"  f_WT = {args.f_WT}")
    
    if args.keywords is not None:
        config['search']['keywords'] = args.keywords
        overrides_applied.append(f"  keywords = {args.keywords[:50]}..." if len(args.keywords) > 50 else f"  keywords = {args.keywords}")
    
    if args.sort_by is not None:
        config['search']['sort_by'] = args.sort_by
        overrides_applied.append(f"  sort_by = {args.sort_by}")
    
    # Show applied overrides
    if overrides_applied:
        print("\n" + "="*60)
        print("COMMAND LINE OVERRIDES APPLIED")
        print("="*60)
        for override in overrides_applied:
            print(override)
        print("="*60 + "\n")
    
    return config


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


def print_current_config(config):
    """Print current search configuration"""
    search_config = config.get('search', {})
    filters = search_config.get('filters', {})
    
    print("\n" + "="*60)
    print("CURRENT SEARCH CONFIGURATION")
    print("="*60)
    print(f"  Country (f_CR):      {filters.get('f_CR', 'Not set')}")
    print(f"  Experience (f_E):    {filters.get('f_E', 'Not set')}")
    print(f"  Function (f_F):      {filters.get('f_F', 'Not set')}")
    print(f"  Job Type (f_JT):     {filters.get('f_JT', 'Not set')}")
    print(f"  Time Range (f_TPR):  {filters.get('f_TPR', 'Not set')}")
    print(f"  Work Type (f_WT):    {filters.get('f_WT', 'Not set')}")
    print(f"  Keywords:            {search_config.get('keywords', 'Not set')[:80]}...")
    print(f"  Sort By:             {search_config.get('sort_by', 'Not set')}")
    print(f"  Results per page:    {search_config.get('results_per_page', 25)}")
    print("="*60 + "\n")


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
            if 'logging' not in config:
                config['logging'] = {}
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
        
        # Apply search overrides from command line
        config = apply_search_overrides(config, args)
        
        # Print current configuration
        print_current_config(config)
        
        # Run scraper
        print("\n" + "="*60)
        print("LINKEDIN JOBS SCRAPER")
        print("="*60)
        print(f"Config file: {args.config}")
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