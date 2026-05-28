import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { DailyChart } from "./components/DailyChart";
import { WeeklyStack } from "./components/WeeklyStack";
import { WorstTimes } from "./components/WorstTimes";
import { HealthStatus } from "./components/HealthStatus";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

interface SpeedDataPoint {
  timestamp: number;
  download_mbps: number;
  upload_mbps: number;
  latency_ms: number;
}

interface Stats {
  total_samples: number;
  avg_download: number;
  avg_upload: number;
  avg_latency: number;
  days_of_data: number;
}

function App() {
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0],
  );
  const [dailyData, setDailyData] = useState<SpeedDataPoint[]>([]);
  const [weekData, setWeekData] = useState<Record<string, any>>({});
  const [worstTimes, setWorstTimes] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setError(null);

      const [daily, week, worst, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/daily/${selectedDate}`),
        axios.get(`${API_BASE}/week`),
        axios.get(`${API_BASE}/worst-times?days=7`),
        axios.get(`${API_BASE}/stats`),
      ]);

      setDailyData(daily.data);
      setWeekData(week.data);
      setWorstTimes(worst.data.worst_periods || worst.data);
      setStats(statsRes.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch data:", err);
      setError("Failed to connect to API. Make sure the backend is running.");
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchData, 60000); // Refresh every minute
    }
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-title">
          <h1>🌐 Network Speed Monitor</h1>
          <p>Real speed, not tunnel speed</p>
        </div>
        <HealthStatus />
      </header>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={() => fetchData()}>Retry</button>
        </div>
      )}

      <main className="app-main">
        {/* Stats Cards */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Samples</span>
              <span className="stat-value">{stats.total_samples}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg Download</span>
              <span className="stat-value">{stats.avg_download} Mbps</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg Upload</span>
              <span className="stat-value">{stats.avg_upload} Mbps</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Avg Latency</span>
              <span className="stat-value">{stats.avg_latency} ms</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Days of Data</span>
              <span className="stat-value">{stats.days_of_data}</span>
            </div>
          </div>
        )}

        {/* Daily View */}
        <section className="daily-section">
          <div className="section-header">
            <h2>📊 Daily Speed</h2>
            <div className="date-controls">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
              <label className="auto-refresh">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                Auto-refresh
              </label>
            </div>
          </div>
          <div className="chart-container">
            <DailyChart data={dailyData} />
          </div>
        </section>

        {/* Weekly View */}
        <section className="weekly-section">
          <h2>📈 Weekly Trend (Last 7 Days)</h2>
          <div className="chart-container large">
            <WeeklyStack data={weekData} />
          </div>
        </section>

        {/* Insights */}
        <section className="insights-section">
          <h2>🔍 Worst Performance Windows</h2>
          <WorstTimes data={worstTimes} />
        </section>
      </main>

      <footer className="app-footer">
        <p>Data updates every 3-5 minutes • VPN-aware filtering active</p>
      </footer>
    </div>
  );
}

export default App;
