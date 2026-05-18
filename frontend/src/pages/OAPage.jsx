import { useState } from "react";

export default function OAPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onAsk() {
    setBusy(true);
    try {
      const resp = await fetch("/api/rag/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      setResult(await resp.json());
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
        <button className="button" onClick={onAsk} disabled={busy}>
          {busy ? "..." : "Ask"}
        </button>
      </div>
      <pre className="pre">{result ? JSON.stringify(result, null, 2) : ""}</pre>
    </div>
  );
}

