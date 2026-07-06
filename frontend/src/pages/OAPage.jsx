import { useState } from "react";

export default function OAPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onAsk() {
    if (!query.trim()) return;
    setBusy(true);
    setError("");
    try {
      const resp = await fetch("/api/rag/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "请求失败");
      }
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message || "请求失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="title">问答</div>
      <div className="row">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入你的问题"
        />
        <button className="button" onClick={onAsk} disabled={busy || !query.trim()}>
          {busy ? "..." : "Ask"}
        </button>
      </div>
      {error ? <div className="error">{error}</div> : null}
      <pre className="pre">{result ? JSON.stringify(result, null, 2) : ""}</pre>
    </div>
  );
}

