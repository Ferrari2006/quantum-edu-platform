import { useState } from "react";

function renderCitations(citations = []) {
  if (!citations.length) return null;
  return (
    <section className="qa-section">
      <h2>引用来源</h2>
      <div className="qa-citations">
        {citations.map((item, index) => (
          <div className="qa-citation" key={`${item.doc_id || "doc"}-${item.chunk_id || index}`}>
            <div className="qa-citation-title">{item.title || item.doc_id || `来源 ${index + 1}`}</div>
            <div className="qa-citation-meta">
              {[item.source, item.doc_id, item.chunk_id].filter(Boolean).join(" · ")}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function renderContexts(contexts = []) {
  if (!contexts.length) return null;
  return (
    <details className="qa-details">
      <summary>检索上下文</summary>
      <div className="qa-context-list">
        {contexts.map((item, index) => (
          <article className="qa-context" key={item.chunk_id || index}>
            <div className="qa-context-head">
              <span>{item.title || item.doc_id || `片段 ${index + 1}`}</span>
              {typeof item.score === "number" ? <span>score {item.score}</span> : null}
            </div>
            <p>{item.content}</p>
          </article>
        ))}
      </div>
    </details>
  );
}

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

  function onSubmit(event) {
    event.preventDefault();
    onAsk();
  }

  return (
    <div className="qa-page">
      <div className="title">问答</div>
      <form className="qa-form" onSubmit={onSubmit}>
        <input
          className="qa-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入你的问题"
        />
        <button className="qa-button" type="submit" disabled={busy || !query.trim()}>
          {busy ? "..." : "Ask"}
        </button>
      </form>
      {error ? <div className="qa-error">{error}</div> : null}
      <div className="qa-result" aria-live="polite">
        {result ? (
          <>
            <section className="qa-section">
              <div className="qa-section-kicker">{result.route || "answer"}</div>
              <h2>回答</h2>
              <div className="qa-answer">{result.answer}</div>
            </section>
            {renderCitations(result.citations)}
            {renderContexts(result.contexts)}
          </>
        ) : (
          <div className="qa-empty">提问后会在这里显示回答。</div>
        )}
      </div>
    </div>
  );
}
