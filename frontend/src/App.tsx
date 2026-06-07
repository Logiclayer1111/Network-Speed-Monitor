import React, { useState, useEffect } from "react";
import axios from "axios";
import { DailyChart } from "./components/DailyChart";
import { WeeklyStack } from "./components/WeeklyStack";
import { WorstTimes } from "./components/WorstTimes";
import { HealthStatus } from "./components/HealthStatus";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

interface SpeedData {
  timestamp: number;
  download_mbps: number;
  upload_mbps: number;
  latency_ms: number;
}

function App() {
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0],
  );
  const [dailyData, setDailyData] = useState<SpeedData[]>([]);
  const [weekData, setWeekData] = useState<Record<string, any[]>>({});
  const [worstTimes, setWorstTimes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [selectedDate]);

  const fetchAllData = async () => {
    try {
      const [daily, week, worst, health] = await Promise.all([
        axios.get(`${API_BASE}/daily/${selectedDate}`),
        axios.get(`${API_BASE}/week`),
        axios.get(`${API_BASE}/worst-times?days=7`),
        axios.get(`${API_BASE}/health`),
      ]);

      setDailyData(daily.data);
      setWeekData(week.data);
      setWorstTimes(worst.data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="app">
      <header>
        <h1>🌐 Network Speed Monitor</h1>
        <HealthStatus />
      </header>

      <main>
        <section className="daily-view">
          <h2>Today's Speed</h2>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          <DailyChart data={dailyData} />
        </section>

        <section className="weekly-view">
          <h2>Weekly Trend</h2>
          <WeeklyStack data={weekData} />
        </section>

        <section className="insights">
          <h2>🔍 Worst Performance Windows</h2>
          <WorstTimes data={worstTimes} />
        </section>
      </main>
    </div>
  );
}

export default App;
