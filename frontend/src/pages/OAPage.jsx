import { useState } from "react";

import { useAuth } from "../auth.jsx";
import { useLanguage } from "../i18n.jsx";

function Citations({ citations = [], labels }) {
  if (!citations.length) return null;
  return (
    <section className="qa-section">
      <h2>{labels.citations}</h2>
      <div className="qa-citations">
        {citations.map((item, index) => (
          <div className="qa-citation" key={`${item.doc_id || "doc"}-${item.chunk_id || index}`}>
            <div className="qa-citation-title">
              {item.title || item.doc_id || `${labels.source} ${index + 1}`}
            </div>
            <div className="qa-citation-meta">
              {[item.source, item.doc_id, item.chunk_id].filter(Boolean).join(" · ")}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Contexts({ contexts = [], labels }) {
  if (!contexts.length) return null;
  return (
    <details className="qa-details">
      <summary>{labels.contexts}</summary>
      <div className="qa-context-list">
        {contexts.map((item, index) => (
          <article className="qa-context" key={item.chunk_id || index}>
            <div className="qa-context-head">
              <span>
                {item.title || item.doc_id || `${labels.chunk} ${index + 1}`}
              </span>
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
  const { t } = useLanguage();
  const { authHeaders, isAuthenticated } = useAuth();
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
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ query })
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || t.qa.requestFailed);
      }
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message || t.qa.requestFailed);
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
      <div className="title">{t.qa.title}</div>
      <div className="qa-auth-hint">
        {isAuthenticated ? t.qa.authHint : t.qa.guestHint}
      </div>
      <form className="qa-form" onSubmit={onSubmit}>
        <input
          className="qa-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t.qa.placeholder}
        />
        <button className="qa-button" type="submit" disabled={busy || !query.trim()}>
          {busy ? t.qa.asking : t.qa.ask}
        </button>
      </form>
      {error ? <div className="qa-error">{error}</div> : null}
      <div className="qa-result" aria-live="polite">
        {result ? (
          <>
            <section className="qa-section">
              <div className="qa-section-kicker">{result.route || "answer"}</div>
              <h2>{t.qa.answer}</h2>
              <div className="qa-answer">{result.answer}</div>
            </section>
            <Citations citations={result.citations} labels={t.qa} />
            <Contexts contexts={result.contexts} labels={t.qa} />
          </>
        ) : (
          <div className="qa-empty">{t.qa.empty}</div>
        )}
      </div>
    </div>
  );
}
