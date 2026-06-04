"""
Database Manager - Handles all database operations
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

class DatabaseManager:
    """Manages SQLite database operations for speed monitoring"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to user's AppData directory for Windows
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            db_dir = Path(app_data) / 'NetworkSpeedMonitor'
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / 'speedmon.db'
        
        self.db_path = str(db_path)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with schema"""
        schema_path = Path(__file__).parent / 'schema.sql'
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema)
        
        print(f"Database initialized at {self.db_path}")
    
    # ============ Adapter Operations ============
    
    def get_or_create_adapter(self, adapter_info: Dict) -> int:
        """Get existing adapter ID or create new one"""
        with self.get_connection() as conn:
            # Try to find existing adapter
            cursor = conn.execute("""
                SELECT id FROM adapters 
                WHERE mac_address = ? OR (name = ? AND mac_address IS NULL)
            """, (adapter_info.get('mac'), adapter_info.get('name')))
            
            row = cursor.fetchone()
            if row:
                # Update last_seen
                conn.execute("""
                    UPDATE adapters 
                    SET last_seen = ?, is_active = 1
                    WHERE id = ?
                """, (int(datetime.now().timestamp() * 1000), row['id']))
                return row['id']
            
            # Insert new adapter
            cursor = conn.execute("""
                INSERT INTO adapters 
                (name, description, mac_address, manufacturer, speed, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                adapter_info.get('name'),
                adapter_info.get('description'),
                adapter_info.get('mac'),
                adapter_info.get('manufacturer'),
                adapter_info.get('speed'),
                int(datetime.now().timestamp() * 1000),
                int(datetime.now().timestamp() * 1000)
            ))
            return cursor.lastrowid
    
    # ============ Speed Sample Operations ============
    
    def insert_speed_sample(self, data: Dict) -> int:
        """Insert a speed test sample"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO speed_samples 
                (timestamp, adapter_id, download_mbps, upload_mbps, latency_ms, packet_loss)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['timestamp'],
                data.get('adapter_id'),
                data.get('download_mbps'),
                data.get('upload_mbps'),
                data.get('latency_ms'),
                data.get('packet_loss', 0)
            ))
            return cursor.lastrowid
    
    def get_samples_by_date(self, date: str, resolution: str = 'minute') -> List[Dict]:
        """Get samples for a specific date"""
        with self.get_connection() as conn:
            if resolution == 'minute':
                cursor = conn.execute("""
                    SELECT 
                        timestamp,
                        download_mbps,
                        upload_mbps,
                        latency_ms,
                        packet_loss
                    FROM speed_samples
                    WHERE date(timestamp/1000, 'unixepoch') = ?
                    ORDER BY timestamp
                """, (date,))
            else:  # 15-minute aggregates
                cursor = conn.execute("""
                    SELECT 
                        window_start as period,
                        avg_download as download_mbps,
                        avg_upload as upload_mbps,
                        avg_latency as latency_ms
                    FROM daily_aggregates
                    WHERE date = ?
                    ORDER BY window_start
                """, (date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_week_data(self, start_date: str = None) -> Dict[str, List]:
        """Get data for last 7 days"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    date,
                    window_start,
                    avg_download,
                    avg_upload,
                    avg_latency
                FROM daily_aggregates
                WHERE date >= date(?, '-7 days') 
                    AND date <= date('now')
                ORDER BY date, window_start
            """, (start_date,))
            
            weekly_data = {}
            for row in cursor:
                date = row['date']
                if date not in weekly_data:
                    weekly_data[date] = []
                weekly_data[date].append({
                    'window': row['window_start'],
                    'download': row['avg_download'],
                    'upload': row['avg_upload'],
                    'latency': row['avg_latency']
                })
            
            return weekly_data    
    def get_worst_times(self, days: int = 7, window_minutes: int = 15) -> List[Dict]:
        """Identify worst performing time windows"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    date(timestamp/1000, 'unixepoch') as day,
                    (strftime('%H', datetime(timestamp/1000, 'unixepoch')) * 60 + 
                     strftime('%M', datetime(timestamp/1000, 'unixepoch'))) / ? as window,
                    AVG(download_mbps) as avg_download,
                    COUNT(*) as samples,
                    MIN(download_mbps) as min_download,
                    MAX(download_mbps) as max_download
                FROM speed_samples
                WHERE timestamp >= strftime('%s', 'now', ? || ' days') * 1000
                    AND download_mbps > 0
                GROUP BY day, window
                HAVING samples >= 2
                ORDER BY avg_download ASC
                LIMIT 10
            """, (window_minutes, f'-{days}'))
            
            results = []
            for row in cursor.fetchall():
                # Calculate time range for display
                start_hour = (row['window'] * window_minutes) // 60
                start_minute = (row['window'] * window_minutes) % 60
                end_hour = ((row['window'] + 1) * window_minutes) // 60
                end_minute = ((row['window'] + 1) * window_minutes) % 60
                
                results.append({
                    'day': row['day'],
                    'time_range': f"{start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}",
                    'avg_download': round(row['avg_download'], 1),
                    'min_download': round(row['min_download'], 1),
                    'max_download': round(row['max_download'], 1),
                    'samples': row['samples']
                })
            
            return results
    
    # ============ Aggregate Operations ============
    
    def aggregate_15min_windows(self, date: str = None):
        """Aggregate minute data into 15-minute windows"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        with self.get_connection() as conn:
            # Clear old aggregates for this day
            conn.execute("DELETE FROM daily_aggregates WHERE date = ?", (date,))
            
            # Generate aggregates for each 15-minute window
            for window in range(96):  # 24 hours * 4 (15-min windows)
                start_min = window * 15
                end_min = start_min + 14
                
                conn.execute("""
                    INSERT INTO daily_aggregates 
                    (date, window_start, avg_download, avg_upload, avg_latency, 
                     max_latency, min_download, max_download, sample_count, packet_loss_avg)
                    SELECT 
                        ?,
                        ?,
                        AVG(download_mbps),
                        AVG(upload_mbps),
                        AVG(latency_ms),
                        MAX(latency_ms),
                        MIN(download_mbps),
                        MAX(download_mbps),
                        COUNT(*),
                        AVG(packet_loss)
                    FROM speed_samples
                    WHERE date(timestamp/1000, 'unixepoch') = ?
                        AND (strftime('%H', datetime(timestamp/1000, 'unixepoch')) * 60 +
                             strftime('%M', datetime(timestamp/1000, 'unixepoch'))) BETWEEN ? AND ?
                        AND download_mbps > 0
                """, (date, window, date, start_min, end_min))
    
    # ============ Statistics Operations ============
    
    def get_stats(self) -> Dict:
        """Get overall statistics"""
        with self.get_connection() as conn:
            # Total samples
            total = conn.execute("SELECT COUNT(*) as count FROM speed_samples").fetchone()
            
            # Last sample
            last = conn.execute("""
                SELECT timestamp, download_mbps, upload_mbps, latency_ms
                FROM speed_samples 
                ORDER BY timestamp DESC 
                LIMIT 1
            """).fetchone()
            
            # Average speeds
            avg = conn.execute("""
                SELECT 
                    AVG(download_mbps) as avg_download,
                    AVG(upload_mbps) as avg_upload,
                    AVG(latency_ms) as avg_latency,
                    COUNT(DISTINCT date(timestamp/1000, 'unixepoch')) as days_of_data
                FROM speed_samples
                WHERE download_mbps > 0
            """).fetchone()
            
            return {
                'total_samples': total['count'],
                'last_sample': dict(last) if last else None,
                'avg_download': round(avg['avg_download'], 1) if avg['avg_download'] else 0,
                'avg_upload': round(avg['avg_upload'], 1) if avg['avg_upload'] else 0,
                'avg_latency': round(avg['avg_latency'], 1) if avg['avg_latency'] else 0,
                'days_of_data': avg['days_of_data'] or 0
            }
    
    def get_health_metrics(self) -> Dict:
        """Get system health metrics"""
        with self.get_connection() as conn:
            # Get latest health entry
            cursor = conn.execute("""
                SELECT * FROM system_health 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return {}
    
    def insert_health_metrics(self, metrics: Dict):
        """Insert system health metrics"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_health 
                (timestamp, poller_uptime_seconds, total_samples, last_successful_poll, 
                 memory_usage_mb, cpu_percent, adapter_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.get('timestamp', int(datetime.now().timestamp() * 1000)),
                metrics.get('uptime_seconds', 0),
                metrics.get('total_samples', 0),
                metrics.get('last_poll', 0),
                metrics.get('memory_mb', 0),
                metrics.get('cpu_percent', 0),
                metrics.get('adapter_count', 0)
            ))
    
    # ============ Maintenance ============
    
    def vacuum(self):
        """Optimize database"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove old data to keep database size manageable"""
        cutoff = (datetime.now() - timedelta(days=days_to_keep)).timestamp() * 1000
        
        with self.get_connection() as conn:
            conn.execute("DELETE FROM speed_samples WHERE timestamp < ?", (cutoff,))
            conn.execute("DELETE FROM system_health WHERE timestamp < ?", (cutoff,))
            conn.execute("DELETE FROM daily_aggregates WHERE date < date('now', ?)", (f'-{days_to_keep} days',))
    
    def export_to_csv(self, start_date: str, end_date: str, filepath: str):
        """Export data to CSV file"""
        import csv
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    datetime(timestamp/1000, 'unixepoch') as datetime,
                    download_mbps,
                    upload_mbps,
                    latency_ms,
                    packet_loss
                FROM speed_samples
                WHERE date(timestamp/1000, 'unixepoch') BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Datetime', 'Download (Mbps)', 'Upload (Mbps)', 'Latency (ms)', 'Packet Loss (%)'])
                
                for row in rows:
                    writer.writerow([row['datetime'], row['download_mbps'], row['upload_mbps'], row['latency_ms'], row['packet_loss']])
            
            return len(rows)