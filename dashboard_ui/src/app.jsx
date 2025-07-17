import React, { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState({ status: "loading...", tasks: [] });
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch("/api/status")
      .then((res) => res.json())
      .then(setStatus);

    fetch("/api/logs")
      .then((res) => res.json())
      .then(setLogs);
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>Marina Dashboard</h1>
      <h2>Status: {status.status}</h2>

      <h3>Active Tasks</h3>
      <ul>
        {status.tasks.length === 0 && <li>No active tasks</li>}
        {status.tasks.map((task, i) => (
          <li key={i}>{task}</li>
        ))}
      </ul>

      <h3>Recent Logs</h3>
      <ul>
        {logs.length === 0 && <li>No logs found</li>}
        {logs.map((log, i) => (
          <li key={i}>
            <strong>{log.file}</strong>
            <pre
              style={{
                backgroundColor: "#eee",
                padding: 10,
                overflowX: "auto",
                maxHeight: 150,
              }}
            >
              {log.content}
            </pre>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
