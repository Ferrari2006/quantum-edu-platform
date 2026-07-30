import { useAuth } from "../auth.jsx";
import { useLanguage } from "../i18n.jsx";
import { HashLink as Link, HashNavLink as NavLink } from "../router.jsx";

export default function NavBar() {
  const { user } = useAuth();
  const { t, toggleLanguage } = useLanguage();

  return (
    <div className="navbar">
      <Link className="brand" to="/">
        <span className="brand-mark">Q</span>
        <span>
          {t.nav.brand}
          <small>{t.nav.subtitle}</small>
        </span>
      </Link>
      <div className="links">
        <NavLink className="navlink" to="/">
          {t.nav.home}
        </NavLink>
        <NavLink className="navlink" to="/knowledge">
          {t.nav.knowledge}
        </NavLink>
        <NavLink className="navlink" to="/oa">
          {t.nav.qa}
        </NavLink>
        <NavLink className="navlink" to="/game">
          {t.nav.game}
        </NavLink>
        <NavLink className="navlink" to="/account">
          {user ? user.username : t.nav.account}
        </NavLink>
      </div>
      <div className="nav-actions">
        <button
          className="language-toggle"
          onClick={toggleLanguage}
          type="button"
        >
          {t.nav.toggle}
        </button>
        <Link
          className="nav-quick-start"
          to="/knowledge/what-is-quantum-computing"
        >
          {t.nav.quickStart}
        </Link>
      </div>
    </div>
  );
}
