#!/usr/bin/env python
"""
Main Poller Process - Collects speed samples at randomized intervals
Runs as Windows service or standalone process
"""

import os
import sys
import time
import random
import logging
import signal
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from poller.adapter_detector import AdapterDetector
from poller.speed_tester import SpeedTester
from db.db_manager import DatabaseManager

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# Ensure log directory exists (tests import this module directly)
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(log_dir / 'poller.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NetworkSpeedPoller:
    """Main polling service that collects network speed data"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.detector = AdapterDetector()
        self.current_adapter = None
        self.running = True
        self.poll_count = 0
        
    def setup_signal_handlers(self):
        """Handle shutdown signals gracefully"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def get_random_interval(self):
        """Return random interval between 3-5 minutes (180-300 seconds)"""
        return random.randint(180, 300)
    
    def refresh_adapter_if_needed(self):
        """Refresh adapter every 10 polls or if invalid"""
        if not self.current_adapter or self.poll_count % 10 == 0:
            self.current_adapter = self.detector.get_active_physical_adapter()
            if self.current_adapter:
                logger.info(f"Using adapter: {self.current_adapter['name']}")
            else:
                logger.warning("No physical adapter found")
        return self.current_adapter is not None
    
    def poll_once(self):
        """Execute a single polling iteration"""
        try:
            # Check if we have a valid adapter
            if not self.refresh_adapter_if_needed():
                logger.warning("Skipping poll - no valid adapter")
                return
            
            logger.info(f"Starting speed test (poll #{self.poll_count})")
            
            # Run speed test
            tester = SpeedTester(self.current_adapter)
            result = tester.run_test()
            
            if result:
                # Save to database
                self.db.insert_speed_sample(result)
                logger.info(
                    f"Speed test complete - "
                    f"↓{result['download_mbps']:.1f} Mbps, "
                    f"↑{result['upload_mbps']:.1f} Mbps, "
                    f"latency: {result['latency_ms']}ms"
                )
                self.poll_count += 1
            else:
                logger.error("Speed test failed")
                
        except Exception as e:
            logger.exception(f"Error during polling: {e}")
    
    def run(self):
        """Main polling loop"""
        logger.info("Network Speed Poller starting...")
        self.setup_signal_handlers()
        
        # Create logs directory if needed
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Run initial poll immediately
        self.poll_once()
        
        # Main loop
        while self.running:
            interval = self.get_random_interval()
            logger.debug(f"Next poll in {interval} seconds")
            
            # Sleep in small increments to check running flag
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)
            
            if self.running:
                self.poll_once()
        
        logger.info("Network Speed Poller stopped")

def main():
    """Entry point for poller"""
    poller = NetworkSpeedPoller()
    poller.run()

if __name__ == "__main__":
    main()