import { Link } from "react-router-dom";

import { useLanguage } from "../i18n.jsx";

const actionMeta = [
  { to: "/oa", accent: "cyan" },
  { to: "/game", accent: "green" },
  { to: "/oa", accent: "amber" }
];

const progressValues = [80, 56, 34, 18];

export default function Home() {
  const { t } = useLanguage();
  const home = t.home;

  return (
    <main className="home-page">
      <section className="home-hero">
        <div className="hero-copy">
          <div className="eyebrow">{home.eyebrow}</div>
          <h1>{home.title}</h1>
          <p>{home.intro}</p>
          <div className="hero-actions">
            <Link className="primary-action" to="/oa">
              {home.ask}
            </Link>
            <Link className="secondary-action" to="/game">
              {home.game}
            </Link>
          </div>
        </div>
        <div className="quantum-panel" aria-label={home.statusLabel}>
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="qubit-core">Q</div>
          <div className="signal-card signal-a">RAG</div>
          <div className="signal-card signal-b">Game</div>
          <div className="signal-card signal-c">API</div>
        </div>
      </section>

      <section className="metric-strip" aria-label={home.modulesLabel}>
        {home.metrics.map(([value, label]) => (
          <div className="metric-item" key={value}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </section>

      <section className="home-grid">
        <div className="quick-actions">
          <div className="section-head">
            <h2>{home.quickTitle}</h2>
            <span>{home.quickHint}</span>
          </div>
          <div className="action-grid">
            {home.quickActions.map((item, index) => (
              <Link
                className={`action-card accent-${actionMeta[index].accent}`}
                to={actionMeta[index].to}
                key={item.title}
              >
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        </div>

        <aside className="study-panel">
          <div className="section-head">
            <h2>{home.progressTitle}</h2>
            <span>{home.progressHint}</span>
          </div>
          <div className="step-list">
            {home.learningSteps.map((step, index) => (
              <div className="step-item" key={step.name}>
                <div className="step-meta">
                  <strong>{step.name}</strong>
                  <span>{step.status}</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${progressValues[index]}%` }} />
                </div>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="lab-band">
        <div>
          <h2>{home.extendTitle}</h2>
          <p>{home.extendText}</p>
        </div>
        <Link className="secondary-action" to="/oa">
          {home.plan}
        </Link>
      </section>
    </main>
  );
}
