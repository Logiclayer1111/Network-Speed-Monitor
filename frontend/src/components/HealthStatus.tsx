import React, { useState, useEffect } from "react";
import axios from "axios";

interface HealthData {
  status: string;
  samples_collected: number;
  last_update: string;
  uptime_hours: number;
  db_size_mb: number;
}

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await axios.get("http://localhost:8000/api/health");
        setHealth(response.data);
      } catch (error) {
        console.error("Health check failed:", error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (!health) {
    return <div className="health-status offline">Connecting...</div>;
  }

  const isHealthy = health.status === "healthy";

  return (
    <div className={`health-status ${isHealthy ? "online" : "offline"}`}>
      <div className="status-indicator"></div>
      <div className="status-details">
        <span className="status-text">
          {isHealthy ? "● Online" : "○ Offline"}
        </span>
        <span className="status-stats">
          {health.samples_collected} samples • {health.uptime_hours}h uptime
        </span>
      </div>
    </div>
  );
};
