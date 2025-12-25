from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import logging
from dataclasses import dataclass


@dataclass
class ProcessingMetrics:
    """Data class to hold processing metrics"""
    start_time: datetime
    end_time: Optional[datetime] = None
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    total_time_seconds: Optional[float] = None
    success_rate: Optional[float] = None

    def calculate_totals(self):
        """Calculate derived metrics after processing is complete"""
        if self.end_time:
            self.total_time_seconds = (self.end_time - self.start_time).total_seconds()

        if self.items_processed > 0:
            self.success_rate = (self.items_successful / self.items_processed) * 100


class ProgressTracker:
    """Utility class for tracking progress and collecting metrics"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = {}
        self.start_times = {}

    def start_task(self, task_name: str, total_items: int = None):
        """Start tracking a task"""
        self.start_times[task_name] = time.time()

        self.metrics[task_name] = ProcessingMetrics(
            start_time=datetime.utcnow(),
            items_processed=0,
            items_successful=0,
            items_failed=0
        )

        if total_items:
            if self.logger:
                self.logger.info(f"Starting task '{task_name}' with {total_items} items")
        else:
            if self.logger:
                self.logger.info(f"Starting task '{task_name}'")

    def update_progress(self, task_name: str, successful: bool = True, increment: int = 1):
        """Update progress for a task"""
        if task_name not in self.metrics:
            self.start_task(task_name)

        metrics = self.metrics[task_name]
        metrics.items_processed += increment

        if successful:
            metrics.items_successful += increment
        else:
            metrics.items_failed += increment

    def complete_task(self, task_name: str):
        """Complete tracking for a task"""
        if task_name not in self.metrics:
            if self.logger:
                self.logger.warning(f"Task '{task_name}' was not started before completing")
            return

        metrics = self.metrics[task_name]
        metrics.end_time = datetime.utcnow()
        metrics.calculate_totals()

        # Calculate elapsed time
        if task_name in self.start_times:
            elapsed = time.time() - self.start_times[task_name]
            metrics.total_time_seconds = elapsed

        if self.logger:
            success_rate = metrics.success_rate or 0
            self.logger.info(
                f"Task '{task_name}' completed: "
                f"{metrics.items_processed} items processed, "
                f"{metrics.items_successful} successful, "
                f"{metrics.items_failed} failed, "
                f"{success_rate:.2f}% success rate, "
                f"{metrics.total_time_seconds:.2f}s total time"
            )

    def get_metrics(self, task_name: str) -> Optional[ProcessingMetrics]:
        """Get metrics for a specific task"""
        return self.metrics.get(task_name)

    def get_all_metrics(self) -> Dict[str, ProcessingMetrics]:
        """Get metrics for all tasks"""
        return self.metrics.copy()

    def reset_task(self, task_name: str):
        """Reset metrics for a specific task"""
        if task_name in self.metrics:
            del self.metrics[task_name]
        if task_name in self.start_times:
            del self.start_times[task_name]


class MetricsAggregator:
    """Utility to aggregate metrics across multiple operations"""

    def __init__(self):
        self.aggregated_metrics = {}

    def add_metric(self, category: str, name: str, value: Any):
        """Add a metric to the aggregator"""
        if category not in self.aggregated_metrics:
            self.aggregated_metrics[category] = {}

        self.aggregated_metrics[category][name] = value

    def get_aggregated(self) -> Dict[str, Dict[str, Any]]:
        """Get all aggregated metrics"""
        return self.aggregated_metrics

    def get_category(self, category: str) -> Dict[str, Any]:
        """Get metrics for a specific category"""
        return self.aggregated_metrics.get(category, {})

    def calculate_rate(self, category: str, success_key: str, total_key: str) -> float:
        """Calculate a success rate from two metrics"""
        category_metrics = self.aggregated_metrics.get(category, {})
        success = category_metrics.get(success_key, 0)
        total = category_metrics.get(total_key, 0)

        if total == 0:
            return 0.0

        return (success / total) * 100

    def reset(self):
        """Reset all aggregated metrics"""
        self.aggregated_metrics = {}