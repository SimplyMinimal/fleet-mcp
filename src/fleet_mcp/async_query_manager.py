"""Async query job manager for Fleet MCP.

This module provides storage and management for asynchronous query execution,
allowing queries to run beyond the 60-second MCP client timeout limitation.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QueryStatus(str, Enum):
    """Status of an async query job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncQueryJob:
    """Represents an asynchronous query job."""

    campaign_id: int
    query: str
    status: QueryStatus
    created_at: float
    updated_at: float
    started_at: float | None = None
    completed_at: float | None = None
    total_hosts: int = 0
    results_count: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "query": self.query,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_hosts": self.total_hosts,
            "results_count": self.results_count,
            "results": self.results,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AsyncQueryJob":
        """Create job from dictionary."""
        return cls(
            campaign_id=data["campaign_id"],
            query=data["query"],
            status=QueryStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            total_hosts=data.get("total_hosts", 0),
            results_count=data.get("results_count", 0),
            results=data.get("results", []),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class AsyncQueryManager:
    """Manager for asynchronous query jobs with disk-based storage."""

    def __init__(self, storage_dir: str | Path, retention_hours: int = 24):
        """Initialize the async query manager.

        Args:
            storage_dir: Directory for storing query results
            retention_hours: Hours to retain completed queries before cleanup
        """
        self.storage_dir = Path(storage_dir)
        self.retention_hours = retention_hours
        self._jobs: dict[int, AsyncQueryJob] = {}
        self._background_tasks: dict[int, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Load existing jobs from disk
        self._load_jobs()

    def _get_job_file(self, campaign_id: int) -> Path:
        """Get the file path for a job."""
        return self.storage_dir / f"job_{campaign_id}.json"

    def _load_jobs(self) -> None:
        """Load all jobs from disk."""
        for job_file in self.storage_dir.glob("job_*.json"):
            try:
                with open(job_file) as f:
                    data = json.load(f)
                    job = AsyncQueryJob.from_dict(data)
                    self._jobs[job.campaign_id] = job
                    logger.debug(f"Loaded job {job.campaign_id} from disk")
            except Exception as e:
                logger.error(f"Failed to load job from {job_file}: {e}")

    def _save_job(self, job: AsyncQueryJob) -> None:
        """Save a job to disk."""
        job_file = self._get_job_file(job.campaign_id)
        try:
            with open(job_file, "w") as f:
                json.dump(job.to_dict(), f, indent=2)
            logger.debug(f"Saved job {job.campaign_id} to disk")
        except Exception as e:
            logger.error(f"Failed to save job {job.campaign_id}: {e}")

    def _delete_job_file(self, campaign_id: int) -> None:
        """Delete a job file from disk."""
        job_file = self._get_job_file(campaign_id)
        try:
            if job_file.exists():
                job_file.unlink()
                logger.debug(f"Deleted job file for {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to delete job file {campaign_id}: {e}")

    async def create_job(
        self,
        campaign_id: int,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncQueryJob:
        """Create a new async query job.

        Args:
            campaign_id: Fleet campaign ID
            query: SQL query string
            metadata: Optional metadata about the query

        Returns:
            Created AsyncQueryJob
        """
        async with self._lock:
            now = time.time()
            job = AsyncQueryJob(
                campaign_id=campaign_id,
                query=query,
                status=QueryStatus.PENDING,
                created_at=now,
                updated_at=now,
                metadata=metadata or {},
            )
            self._jobs[campaign_id] = job
            self._save_job(job)
            logger.info(f"Created async query job {campaign_id}")
            return job

    async def get_job(self, campaign_id: int) -> AsyncQueryJob | None:
        """Get a job by campaign ID.

        Args:
            campaign_id: Fleet campaign ID

        Returns:
            AsyncQueryJob if found, None otherwise
        """
        job = self._jobs.get(campaign_id)
        if job:
            logger.debug(f"Found job {campaign_id} in memory cache")
        else:
            logger.warning(
                f"Job {campaign_id} not found in memory cache. "
                f"Available jobs: {list(self._jobs.keys())}"
            )
        return job

    async def update_job_status(
        self,
        campaign_id: int,
        status: QueryStatus,
        error: str | None = None,
    ) -> None:
        """Update job status.

        Args:
            campaign_id: Fleet campaign ID
            status: New status
            error: Optional error message
        """
        async with self._lock:
            job = self._jobs.get(campaign_id)
            if not job:
                logger.warning(f"Job {campaign_id} not found for status update")
                return

            job.status = status
            job.updated_at = time.time()

            if status == QueryStatus.RUNNING and job.started_at is None:
                job.started_at = time.time()
            elif status in (
                QueryStatus.COMPLETED,
                QueryStatus.FAILED,
                QueryStatus.CANCELLED,
            ):
                job.completed_at = time.time()

            if error:
                job.error = error

            self._save_job(job)
            logger.debug(f"Updated job {campaign_id} status to {status}")

    async def add_result(
        self,
        campaign_id: int,
        result: dict[str, Any],
    ) -> None:
        """Add a result to a job.

        Args:
            campaign_id: Fleet campaign ID
            result: Query result to add
        """
        async with self._lock:
            job = self._jobs.get(campaign_id)
            if not job:
                logger.warning(f"Job {campaign_id} not found for adding result")
                return

            job.results.append(result)
            job.results_count = len(job.results)
            job.updated_at = time.time()
            self._save_job(job)

    async def set_total_hosts(self, campaign_id: int, total_hosts: int) -> None:
        """Set the total number of hosts for a job.

        Args:
            campaign_id: Fleet campaign ID
            total_hosts: Total number of hosts targeted
        """
        async with self._lock:
            job = self._jobs.get(campaign_id)
            if not job:
                logger.warning(f"Job {campaign_id} not found for setting total hosts")
                return

            job.total_hosts = total_hosts
            job.updated_at = time.time()
            self._save_job(job)

    async def list_jobs(
        self,
        status_filter: QueryStatus | None = None,
        limit: int | None = None,
    ) -> list[AsyncQueryJob]:
        """List all jobs, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by
            limit: Optional maximum number of jobs to return

        Returns:
            List of AsyncQueryJob objects
        """
        jobs = list(self._jobs.values())

        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]

        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        if limit:
            jobs = jobs[:limit]

        return jobs

    async def cancel_job(self, campaign_id: int) -> bool:
        """Cancel a running job.

        Args:
            campaign_id: Fleet campaign ID

        Returns:
            True if job was cancelled, False if not found or already completed
        """
        async with self._lock:
            job = self._jobs.get(campaign_id)
            if not job:
                return False

            if job.status in (
                QueryStatus.COMPLETED,
                QueryStatus.FAILED,
                QueryStatus.CANCELLED,
            ):
                return False

            # Cancel background task if it exists
            task = self._background_tasks.get(campaign_id)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            job.status = QueryStatus.CANCELLED
            job.updated_at = time.time()
            job.completed_at = time.time()
            self._save_job(job)
            logger.info(f"Cancelled job {campaign_id}")
            return True

    def register_background_task(
        self, campaign_id: int, task: asyncio.Task[None]
    ) -> None:
        """Register a background task for a job.

        Args:
            campaign_id: Fleet campaign ID
            task: Asyncio task running the query
        """
        self._background_tasks[campaign_id] = task

    async def cleanup_old_jobs(self) -> int:
        """Clean up old completed jobs based on retention policy.

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = time.time() - (self.retention_hours * 3600)
        cleaned = 0

        async with self._lock:
            jobs_to_delete = []
            for campaign_id, job in self._jobs.items():
                if (
                    job.status
                    in (
                        QueryStatus.COMPLETED,
                        QueryStatus.FAILED,
                        QueryStatus.CANCELLED,
                    )
                    and job.completed_at
                    and job.completed_at < cutoff_time
                ):
                    jobs_to_delete.append(campaign_id)

            for campaign_id in jobs_to_delete:
                del self._jobs[campaign_id]
                self._delete_job_file(campaign_id)
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old jobs")

        return cleaned


# Global manager instance
_async_query_manager: AsyncQueryManager | None = None


def get_async_query_manager(config: Any) -> AsyncQueryManager:
    """Get or create the global async query manager instance.

    Args:
        config: Fleet configuration object with async_query_storage_dir and async_query_retention_hours

    Returns:
        Global AsyncQueryManager instance
    """
    global _async_query_manager
    if _async_query_manager is None:
        logger.info(
            f"Creating new AsyncQueryManager instance with storage_dir={config.async_query_storage_dir}"
        )
        _async_query_manager = AsyncQueryManager(
            storage_dir=config.async_query_storage_dir,
            retention_hours=config.async_query_retention_hours,
        )
    else:
        logger.debug(
            f"Reusing existing AsyncQueryManager instance (id={id(_async_query_manager)})"
        )
    return _async_query_manager
