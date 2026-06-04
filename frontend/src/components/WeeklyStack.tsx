import React from "react";
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
  data: Record<string, Array<{ window: number; download: number }>>;
}

export const WeeklyStack: React.FC<WeeklyStackProps> = ({ data }) => {
  // Transform data for stacked display
  const windows = Array.from({ length: 96 }, (_, i) => i);

  const chartData = windows.map((window) => {
    const point: any = { window };
    Object.entries(data).forEach(([date, values]) => {
      const match = values.find((v) => v.window === window);
      point[date] = match?.download || null;
    });
    return point;
  });

  const colors = [
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#ff7300",
    "#0088fe",
    "#00c49f",
    "#ffbb28",
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="window"
          tickFormatter={(val) =>
            `${Math.floor((val * 15) / 60)}:${(val * 15) % 60}`
          }
        />
        <YAxis label={{ value: "Mbps", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend />
        {Object.keys(data).map((date, idx) => (
          <Line
            key={date}
            type="monotone"
            dataKey={date}
            stroke={colors[idx % colors.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};
