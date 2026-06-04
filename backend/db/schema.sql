-- Network Speed Monitor Database Schema
-- SQLite 3

-- Table: physical network adapters
CREATE TABLE IF NOT EXISTS adapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    mac_address TEXT UNIQUE,
    manufacturer TEXT,
    speed INTEGER,
    is_active BOOLEAN DEFAULT 1,
    first_seen INTEGER,  -- Unix timestamp ms
    last_seen INTEGER,   -- Unix timestamp ms
    UNIQUE(name, mac_address)
);

-- Table: speed test samples
CREATE TABLE IF NOT EXISTS speed_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,  -- Unix timestamp (milliseconds)
    adapter_id INTEGER,
    download_mbps REAL,
    upload_mbps REAL,
    latency_ms INTEGER,
    packet_loss REAL,
    data_usage_bytes INTEGER,
    server_location TEXT,
    FOREIGN KEY(adapter_id) REFERENCES adapters(id)
);

-- Table: 15-minute aggregated windows
CREATE TABLE IF NOT EXISTS daily_aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,  -- YYYY-MM-DD
    window_start INTEGER NOT NULL,  -- 0-95 (96 windows of 15 minutes)
    avg_download REAL,
    avg_upload REAL,
    avg_latency REAL,
    max_latency INTEGER,
    min_download REAL,
    max_download REAL,
    sample_count INTEGER,
    packet_loss_avg REAL,
    UNIQUE(date, window_start)
);

-- Table: weekly insights
CREATE TABLE IF NOT EXISTS weekly_insights (
    week_start TEXT PRIMARY KEY,  -- YYYY-WW format
    worst_15min_window INTEGER,
    worst_avg_download REAL,
    best_15min_window INTEGER,
    best_avg_download REAL,
    total_samples INTEGER,
    avg_weekly_download REAL
);

-- Table: system health metrics
CREATE TABLE IF NOT EXISTS system_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    poller_uptime_seconds INTEGER,
    total_samples INTEGER,
    last_successful_poll INTEGER,
    memory_usage_mb REAL,
    cpu_percent REAL,
    adapter_count INTEGER
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_samples_timestamp ON speed_samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_samples_adapter ON speed_samples(adapter_id);
CREATE INDEX IF NOT EXISTS idx_aggregates_date ON daily_aggregates(date);
CREATE INDEX IF NOT EXISTS idx_health_timestamp ON system_health(timestamp);

-- View: last 24 hours of data
CREATE VIEW IF NOT EXISTS v_last_24h AS
SELECT 
    datetime(timestamp/1000, 'unixepoch', 'localtime') as sample_time,
    download_mbps,
    upload_mbps,
    latency_ms
FROM speed_samples
WHERE timestamp >= strftime('%s', 'now', '-1 day') * 1000
ORDER BY timestamp;

-- View: daily summary statistics
CREATE VIEW IF NOT EXISTS v_daily_stats AS
SELECT 
    date(timestamp/1000, 'unixepoch') as day,
    COUNT(*) as samples,
    AVG(download_mbps) as avg_download,
    MAX(download_mbps) as max_download,
    MIN(download_mbps) as min_download,
    AVG(latency_ms) as avg_latency,
    AVG(packet_loss) as avg_packet_loss
FROM speed_samples
GROUP BY day
ORDER BY day DESC;