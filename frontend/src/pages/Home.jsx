import { useLanguage } from "../i18n.jsx";
import { HashLink as Link } from "../router.jsx";

export default function Home() {
  const { t } = useLanguage();
  const entryLinks = ["/knowledge", "/oa", "/game", "/progress"];

  return (
    <div className="platform-home">
      <section className="platform-hero">
        <div className="platform-eyebrow">{t.home.eyebrow}</div>
        <h1>{t.home.title}</h1>
        <p>{t.home.intro}</p>
        <div className="platform-actions">
          <Link className="platform-primary" to="/knowledge">
            {t.home.knowledgeAction}
          </Link>
          <Link className="platform-secondary" to="/game">
            {t.home.gameAction}
          </Link>
        </div>
      </section>
      <section className="platform-entry-grid">
        {t.home.entries.map((entry, index) => (
          <Link
            className={`platform-entry ${index === 0 ? "knowledge" : ""}`}
            key={entry.kicker}
            to={entryLinks[index]}
          >
            <span>{entry.kicker}</span>
            <h2>{entry.title}</h2>
            <p>{entry.text}</p>
            <strong>{entry.action}</strong>
          </Link>
        ))}
      </section>
    </div>
  );
}
