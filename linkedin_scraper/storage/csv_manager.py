"""
CSV Storage Manager for LinkedIn Jobs
Handles reading, writing, and upserting job data
"""

import csv
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class JobCSVManager:
    """CSV file manager for job listings"""
    
    def __init__(self, filename: str = 'linkedin_jobs.csv', encoding: str = 'utf-8-sig'):
        """
        Initialize CSV manager
        
        Args:
            filename: CSV file name
            encoding: File encoding
        """
        self.filename = Path(filename)
        self.encoding = encoding
        self.fieldnames = ['jobid', 'jobtitle', 'company', 'location', 'url', 'updatedatetime']
        
    def _ensure_file_exists(self) -> None:
        """Create CSV file with header if it doesn't exist"""
        if not self.filename.exists():
            with open(self.filename, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
            logger.info(f"Created new CSV file: {self.filename}")
    
    def read_all_jobs(self) -> List[Dict[str, str]]:
        """
        Read all jobs from CSV file
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        if not self.filename.exists():
            return jobs
        
        try:
            with open(self.filename, 'r', newline='', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    jobs.append(row)
            logger.debug(f"Read {len(jobs)} jobs from {self.filename}")
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            
        return jobs
    
    def write_all_jobs(self, jobs: List[Dict[str, str]]) -> None:
        """
        Write all jobs to CSV file
        
        Args:
            jobs: List of job dictionaries
        """
        try:
            self._ensure_file_exists()
            with open(self.filename, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(jobs)
            logger.info(f"Saved {len(jobs)} jobs to {self.filename}")
        except Exception as e:
            logger.error(f"Failed to write CSV file: {e}")
            raise
    
    def upsert_job(self, job_data: Dict[str, str]) -> bool:
        """
        Insert or update a single job
        
        Args:
            job_data: Job dictionary containing jobid
            
        Returns:
            True if inserted, False if updated
        """
        existing_jobs = self.read_all_jobs()
        jobid = job_data['jobid']
        
        found = False
        for i, job in enumerate(existing_jobs):
            if job['jobid'] == jobid:
                existing_jobs[i] = job_data
                found = True
                logger.info(f"Updated job: {jobid} - {job_data.get('jobtitle', '')}")
                break
        
        if not found:
            existing_jobs.append(job_data)
            logger.info(f"Added new job: {jobid} - {job_data.get('jobtitle', '')}")
        
        self.write_all_jobs(existing_jobs)
        return not found
    
    def upsert_jobs(self, new_jobs: List[Dict[str, str]]) -> Tuple[int, int]:
        """
        Batch insert or update jobs
        
        Args:
            new_jobs: List of job dictionaries
            
        Returns:
            Tuple of (added_count, updated_count)
        """
        if not new_jobs:
            return 0, 0
        
        existing_jobs = self.read_all_jobs()
        existing_dict = {job['jobid']: job for job in existing_jobs}
        
        added = 0
        updated = 0
        
        for new_job in new_jobs:
            jobid = new_job['jobid']
            if jobid in existing_dict:
                existing_dict[jobid] = new_job
                updated += 1
                logger.debug(f"Updated: {jobid}")
            else:
                existing_dict[jobid] = new_job
                added += 1
                logger.debug(f"Added: {jobid}")
        
        all_jobs = list(existing_dict.values())
        self.write_all_jobs(all_jobs)
        
        logger.info(f"Batch upsert complete: +{added} added, {updated} updated")
        return added, updated
    
    def get_job_count(self) -> int:
        """
        Get total number of jobs in CSV
        
        Returns:
            Number of jobs
        """
        return len(self.read_all_jobs())
    
    def get_job_by_id(self, jobid: str) -> Optional[Dict[str, str]]:
        """
        Get a specific job by ID
        
        Args:
            jobid: Job ID to look up
            
        Returns:
            Job dictionary or None if not found
        """
        jobs = self.read_all_jobs()
        for job in jobs:
            if job['jobid'] == jobid:
                return job
        return None
    
    def delete_job(self, jobid: str) -> bool:
        """
        Delete a job by ID
        
        Args:
            jobid: Job ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        jobs = self.read_all_jobs()
        original_count = len(jobs)
        jobs = [job for job in jobs if job['jobid'] != jobid]
        
        if len(jobs) < original_count:
            self.write_all_jobs(jobs)
            logger.info(f"Deleted job: {jobid}")
            return True
        
        logger.warning(f"Job not found for deletion: {jobid}")
        return False