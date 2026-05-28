import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface WeeklyStackProps {
  data: Record<
    string,
    Array<{ window: number; download: number; upload: number; latency: number }>
  >;
}

const COLORS = [
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
];

export const WeeklyStack: React.FC<WeeklyStackProps> = ({ data }) => {
  const chartData = useMemo(() => {
    if (!data || Object.keys(data).length === 0) {
      return [];
    }

    // Create 96 windows (24 hours * 4 per hour)
    const windows = Array.from({ length: 96 }, (_, i) => i);

    return windows.map((window) => {
      const point: any = {
        window,
        timeLabel: formatWindowTime(window),
      };

      Object.entries(data).forEach(([date, values]) => {
        const match = values.find((v) => v.window === window);
        point[date] = match?.download || null;
      });

      return point;
    });
  }, [data]);

  function formatWindowTime(window: number): string {
    const hour = Math.floor(window / 4);
    const minute = (window % 4) * 15;
    return `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
  }

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="no-data">
        No weekly data available. Collecting data...
      </div>
    );
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">Time: {label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value?.toFixed(1)} Mbps
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const dates = Object.keys(data).sort();

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="timeLabel"
          interval={11} // Show every ~3 hours
          tick={{ fontSize: 10 }}
        />
        <YAxis
          label={{
            value: "Download Speed (Mbps)",
            angle: -90,
            position: "insideLeft",
          }}
          tick={{ fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11 }}
          formatter={(value) => {
            // Format date for legend
            const date = new Date(value);
            return date.toLocaleDateString();
          }}
        />
        {dates.map((date, index) => (
          <Line
            key={date}
            type="monotone"
            dataKey={date}
            stroke={COLORS[index % COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};
