import { useEffect, useState } from "react";
import BaseMap from "./map/BaseMap";

type Health = { status: string } | null;

export default function App() {
  const [health, setHealth] = useState<Health>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  return (
    <div className="app">
      <header>
        <strong>GramMap</strong>
        <span className={`health ${health?.status === "ok" ? "ok" : "bad"}`}>
          API: {health ? health.status : "checking…"}
        </span>
      </header>
      <BaseMap />
    </div>
  );
}
