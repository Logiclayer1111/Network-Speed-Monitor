"""
Background Aggregator Service
Runs daily to aggregate data into 15-minute windows
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DataAggregator:
    """Background service that aggregates raw data into summary tables"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.running = False
        self.thread = None
    
    def aggregate_daily(self):
        """Aggregate yesterday's data"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Aggregating data for {yesterday}")
        
        try:
            self.db.aggregate_15min_windows(yesterday)
            logger.info(f"Successfully aggregated {yesterday}")
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
    
    def cleanup_old_data(self):
        """Remove data older than 30 days"""
        logger.info("Running data cleanup...")
        try:
            self.db.cleanup_old_data(days_to_keep=30)
            self.db.vacuum()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def update_system_health(self):
        """Record system health metrics"""
        import psutil
        
        try:
            stats = self.db.get_stats()
            
            metrics = {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'uptime_seconds': int(time.time() - getattr(self, 'start_time', time.time())),
                'total_samples': stats['total_samples'],
                'last_poll': stats['last_sample']['timestamp'] if stats['last_sample'] else 0,
                'memory_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                'cpu_percent': psutil.Process().cpu_percent(),
                'adapter_count': 1  # Will be updated by poller
            }
            
            self.db.insert_health_metrics(metrics)
        except Exception as e:
            logger.error(f"Health metrics failed: {e}")
    
    def run_once(self):
        """Run a single aggregation cycle"""
        self.aggregate_daily()
        self.update_system_health()
        self.cleanup_old_data()
    
    def start_daemon(self):
        """Start aggregator in background thread"""
        self.running = True
        self.start_time = time.time()
        
        def run_loop():
            logger.info("Aggregator daemon started")
            
            while self.running:
                # Run at 2 AM daily
                now = datetime.now()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                sleep_seconds = (next_run - now).total_seconds()
                
                if sleep_seconds > 0:
                    # Sleep in small increments to check running flag
                    for _ in range(int(sleep_seconds)):
                        if not self.running:
                            break
                        time.sleep(1)
                
                if self.running:
                    self.run_once()
            
            logger.info("Aggregator daemon stopped")
        
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the aggregator"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

# Global instance
_aggregator = None

def start_aggregator():
    """Start the aggregator service"""
    global _aggregator
    if _aggregator is None:
        _aggregator = DataAggregator()
        _aggregator.start_daemon()
    return _aggregator

def stop_aggregator():
    """Stop the aggregator service"""
    global _aggregator
    if _aggregator:
        _aggregator.stop()
        _aggregator = None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Starting aggregator in foreground...")
    aggregator = DataAggregator()
    
    # Run once immediately
    aggregator.run_once()
    
    # Then start daemon
    aggregator.start_daemon()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping...")
        aggregator.stop()