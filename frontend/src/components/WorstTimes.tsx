import React from "react";

interface WorstPeriod {
  day: string;
  time_range: string;
  avg_download: number;
  min_download: number;
  max_download: number;
  samples: number;
}

interface WorstTimesProps {
  data: WorstPeriod[];
}

export const WorstTimes: React.FC<WorstTimesProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="no-data">
        Not enough data to identify worst times. Collecting...
      </div>
    );
  }

  // Helper to get severity class
  const getSeverityClass = (speed: number) => {
    if (speed < 10) return "severity-critical";
    if (speed < 25) return "severity-poor";
    if (speed < 50) return "severity-fair";
    return "severity-good";
  };

  return (
    <div className="worst-times">
      <div className="worst-header">
        <p className="insight-note">
          Based on the last 7 days of data. Lower download speeds indicate worse
          performance.
        </p>
      </div>

      <div className="worst-table">
        <table>
          <thead>
            <tr>
              <th>Day</th>
              <th>Time Window</th>
              <th>Avg Download</th>
              <th>Range</th>
              <th>Samples</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(data) &&
              data.map((period, index) => (
                <tr
                  key={index}
                  className={getSeverityClass(period.avg_download)}
                >
                  <td>{formatDay(period.day)}</td>
                  <td>{period.time_range}</td>
                  <td className="speed-value">
                    <strong>{period.avg_download} Mbps</strong>
                  </td>
                  <td className="speed-range">
                    {period.min_download} - {period.max_download} Mbps
                  </td>
                  <td>{period.samples}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="recommendation">
        <h4>💡 Recommendation</h4>
        {data.length > 0 && (
          <p>
            Your worst performance is typically on{" "}
            <strong>{formatDay(data[0].day)}</strong>
            between <strong>{data[0].time_range}</strong> with average speeds of
            <strong> {data[0].avg_download} Mbps</strong>.
            {data[0].avg_download < 25
              ? " Consider scheduling bandwidth-intensive tasks outside this window."
              : " Performance is generally good, but monitor for anomalies."}
          </p>
        )}
      </div>
    </div>
  );
};

function formatDay(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return "Today";
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
