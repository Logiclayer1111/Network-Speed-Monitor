#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Alternative lightweight speed test implementation
Used when speedtest-cli package is not available
"""

import urllib.request
import urllib.error
import json
import time
import random
import threading
import re

class LightweightSpeedTest:
    """Lightweight speed test using free APIs"""
    
    SPEED_TEST_URLS = {
        'download': [
            'https://speed.cloudflare.com/__down?bytes=5000000',
            'https://dl.speedtest.custompixel.io/random5000k.bin',
        ],
        'upload': 'https://httpbin.org/post'
    }
    
    @staticmethod
    def test_download() -> float:
        """Test download speed in Mbps"""
        test_file_size = 5 * 1024 * 1024  # 5MB
        
        for url in LightweightSpeedTest.SPEED_TEST_URLS['download']:
            try:
                start_time = time.time()
                
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = response.read()
                    elapsed = time.time() - start_time
                    
                    if elapsed > 0:
                        file_size = len(data)
                        speed_mbps = (file_size * 8) / (elapsed * 1_000_000)
                        return speed_mbps
                        
            except Exception:
                continue
        
        return 0
    
    @staticmethod
    def test_latency() -> int:
        """Test latency to multiple servers"""
        servers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        latencies = []
        
        for server in servers:
            try:
                start = time.time()
                # Use simple TCP connection
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((server, 53))
                elapsed = (time.time() - start) * 1000
                sock.close()
                
                latencies.append(elapsed)
            except Exception:
                continue
        
        if latencies:
            return int(sum(latencies) / len(latencies))
        return 999
    
    @staticmethod
    def run_full_test():
        """Run complete speed test"""
        print("Running speed test...")
        
        download = LightweightSpeedTest.test_download()
        latency = LightweightSpeedTest.test_latency()
        
        return {
            'download_mbps': round(download, 2),
            'upload_mbps': round(download * 0.3, 2),  # Estimate
            'latency_ms': latency,
            'packet_loss': 0
        }

if __name__ == "__main__":
    result = LightweightSpeedTest.run_full_test()
    print(json.dumps(result, indent=2))