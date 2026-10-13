import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth.jsx";
import { useLanguage } from "../i18n.jsx";
import { HashLink as Link } from "../router.jsx";
import "./LearningProgressPage.css";


async function readJson(response) {
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function formatDate(value, language) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function recommendationReason(item, progress) {
  const template = progress.reasons[item.reason_code];
  if (!template) return item.reason;
  return template
    .replace("{score}", String(Math.round((item.mastery_score || 0) * 100)))
    .replace("{concepts}", (item.missing_prerequisite_titles || []).join("、"));
}

function SummaryCard({ label, value, detail }) {
  return (
    <article className="lp-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export default function LearningProgressPage() {
  const { authHeaders, isAuthenticated, user } = useAuth();
  const { language, t } = useLanguage();
  const progress = t.progress;
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [events, setEvents] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) {
      setProfile(null);
      setRecommendations([]);
      setEvents([]);
      return undefined;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const options = { headers: authHeaders(), signal: controller.signal };
    Promise.all([
      fetch("/api/learning/mastery", options).then(readJson),
      fetch("/api/learning/recommendations?limit=6", options).then(readJson),
      fetch("/api/learning/events?limit=50", options).then(readJson),
    ])
      .then(([profileData, recommendationData, eventData]) => {
        setProfile(profileData);
        setRecommendations(recommendationData.items || []);
        setEvents(eventData.items || []);
      })
      .catch((loadError) => {
        if (loadError.name !== "AbortError") setError(loadError.message || progress.error);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [authHeaders, isAuthenticated, progress.error, revision]);

  const filteredConcepts = useMemo(() => {
    const concepts = profile?.concepts || [];
    if (filter === "review") return concepts.filter((item) => item.mastery_score < 0.5);
    if (filter === "mastered") return concepts.filter((item) => item.mastery_score >= 0.75);
    return concepts;
  }, [filter, profile]);

  const exportData = () => {
    const blob = new Blob([
      JSON.stringify({ exported_at: new Date().toISOString(), profile, recommendations, events }, null, 2),
    ], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `quantum-learning-${new Date().toISOString().slice(0, 10)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const summary = profile?.summary || {};

  return (
    <main className="lp-page">
      <section className="lp-hero">
        <div>
          <span>{progress.eyebrow}</span>
          <h1>{progress.title}</h1>
          <p>{progress.subtitle}</p>
        </div>
        {isAuthenticated ? (
          <div className="lp-hero-actions">
            <small>{user?.username}</small>
            <button disabled={loading} onClick={() => setRevision((value) => value + 1)} type="button">
              {progress.refresh}
            </button>
            <button disabled={!profile} onClick={exportData} type="button">{progress.export}</button>
          </div>
        ) : null}
      </section>

      {!isAuthenticated ? (
        <section className="lp-login-card">
          <span>ACCOUNT REQUIRED</span>
          <h2>{progress.loginTitle}</h2>
          <p>{progress.loginHint}</p>
          <Link to="/account">{progress.loginAction} <i>→</i></Link>
        </section>
      ) : loading && !profile ? (
        <div className="lp-state-card">{progress.loading}</div>
      ) : error && !profile ? (
        <div className="lp-state-card is-error">
          <strong>{progress.error}</strong>
          <small>{error}</small>
          <button onClick={() => setRevision((value) => value + 1)} type="button">{progress.retry}</button>
        </div>
      ) : (
        <>
          {error ? <div className="lp-inline-error">{progress.error}：{error}</div> : null}
          <section className="lp-summary-grid">
            <SummaryCard
              detail={`${summary.covered_concepts || 0} / ${summary.total_concepts || 0}`}
              label={progress.summary.average}
              value={`${Math.round((summary.average_mastery || 0) * 100)}%`}
            />
            <SummaryCard
              detail={`${summary.total_concepts || 0}`}
              label={progress.summary.covered}
              value={summary.covered_concepts || 0}
            />
            <SummaryCard
              detail={`${summary.needs_review_concepts || 0} ${progress.filters.review}`}
              label={progress.summary.mastered}
              value={summary.mastered_concepts || 0}
            />
            <SummaryCard
              detail={`${events.length} / 50`}
              label={progress.summary.evidence}
              value={summary.total_evidence || 0}
            />
          </section>

          <section className="lp-section">
            <div className="lp-section-heading">
              <div><span>01</span><div><h2>{progress.recommendationTitle}</h2><p>{progress.recommendationHint}</p></div></div>
            </div>
            {recommendations.length ? (
              <div className="lp-recommendation-grid">
                {recommendations.map((item, index) => (
                  <article className={`lp-recommendation ${item.ready ? "is-ready" : "is-blocked"}`} key={item.concept_id}>
                    <div className="lp-recommendation-top">
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <small>{item.module}</small>
                    </div>
                    <h3>{item.title}</h3>
                    <p>{recommendationReason(item, progress)}</p>
                    <div className="lp-action-row">
                      {(item.actions || []).map((action) => (
                        <Link key={`${item.concept_id}-${action.kind}`} to={action.path}>
                          {progress.actionKinds[action.kind] || action.label}
                        </Link>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : <div className="lp-empty">{progress.noRecommendations}</div>}
          </section>

          <section className="lp-section">
            <div className="lp-section-heading lp-mastery-heading">
              <div><span>02</span><div><h2>{progress.masteryTitle}</h2><p>{progress.masteryHint}</p></div></div>
              <div className="lp-filters">
                {Object.entries(progress.filters).map(([key, label]) => (
                  <button className={filter === key ? "active" : ""} key={key} onClick={() => setFilter(key)} type="button">
                    {label}
                  </button>
                ))}
              </div>
            </div>
            {filteredConcepts.length ? (
              <div className="lp-mastery-list">
                {filteredConcepts.map((item) => (
                  <article key={item.concept_id}>
                    <div className="lp-mastery-copy">
                      <div><strong>{item.title}</strong><small>{item.module} · {item.evidence_count} {progress.evidenceCount}</small></div>
                      <span className={`is-${item.mastery_level}`}>{progress.levels[item.mastery_level]}</span>
                    </div>
                    <div className="lp-mastery-bar">
                      <i style={{ "--mastery": item.mastery_score }} />
                      <strong>{Math.round(item.mastery_score * 100)}%</strong>
                    </div>
                    <Link to={`/knowledge/${item.concept_id}`}>{progress.actionKinds.article} →</Link>
                  </article>
                ))}
              </div>
            ) : <div className="lp-empty">{progress.emptyMastery}</div>}
          </section>

          <section className="lp-section">
            <div className="lp-section-heading">
              <div><span>03</span><div><h2>{progress.timelineTitle}</h2><p>{progress.timelineHint}</p></div></div>
            </div>
            {events.length ? (
              <div className="lp-timeline">
                {events.map((event) => (
                  <article key={event.id}>
                    <div className={`lp-event-mark is-${event.event_type}`}>{(progress.eventTypes[event.event_type] || "E").slice(0, 1)}</div>
                    <div className="lp-event-copy">
                      <span>{progress.eventTypes[event.event_type] || event.event_type}</span>
                      <strong>{event.metadata?.title || event.concept_title || event.concept_id}</strong>
                      <small>{event.source} · {formatDate(event.created_at, language)}</small>
                    </div>
                    <div className="lp-event-score"><small>{progress.score}</small><strong>{Math.round(event.score * 100)}%</strong></div>
                  </article>
                ))}
              </div>
            ) : <div className="lp-empty">{progress.emptyTimeline}</div>}
          </section>
        </>
      )}
    </main>
  );
}
