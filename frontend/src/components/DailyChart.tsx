import React from "react";
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Bar,
} from "recharts";

interface DataPoint {
  timestamp: number;
  download_mbps: number;
  upload_mbps: number;
  latency_ms: number;
}

interface DailyChartProps {
  data: DataPoint[];
}

export const DailyChart: React.FC<DailyChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="no-data">No data available for this date</div>;
  }

  // Format data for Recharts
  const chartData = data.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    download: point.download_mbps,
    upload: point.upload_mbps,
    latency: point.latency_ms,
    fullDate: new Date(point.timestamp),
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">{label}</p>
          <p className="tooltip-download">
            📥 Download: {payload[0]?.value} Mbps
          </p>
          <p className="tooltip-upload">📤 Upload: {payload[1]?.value} Mbps</p>
          <p className="tooltip-latency">⏱️ Latency: {payload[2]?.value} ms</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
        <XAxis
          dataKey="time"
          interval="preserveStartEnd"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          yAxisId="speed"
          label={{
            value: "Mbps",
            angle: -90,
            position: "insideLeft",
            style: { fontSize: 12 },
          }}
          tick={{ fontSize: 11 }}
        />
        <YAxis
          yAxisId="latency"
          orientation="right"
          label={{
            value: "ms",
            angle: 90,
            position: "insideRight",
            style: { fontSize: 12 },
          }}
          tick={{ fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area
          yAxisId="speed"
          type="monotone"
          dataKey="download"
          stroke="#2563eb"
          fill="#2563eb"
          fillOpacity={0.2}
          name="Download (Mbps)"
          strokeWidth={2}
        />
        <Line
          yAxisId="speed"
          type="monotone"
          dataKey="upload"
          stroke="#10b981"
          name="Upload (Mbps)"
          strokeWidth={2}
          dot={false}
        />
        <Bar
          yAxisId="latency"
          dataKey="latency"
          fill="#f59e0b"
          opacity={0.5}
          name="Latency (ms)"
          barSize={3}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};
