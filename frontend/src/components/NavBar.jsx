import { NavLink } from "react-router-dom";

import { useLanguage } from "../i18n.jsx";

export default function NavBar() {
  const { t, toggleLanguage } = useLanguage();

  return (
    <div className="navbar">
      <div className="brand">{t.nav.brand}</div>
      <div className="links">
        <NavLink className="navlink" to="/">
          {t.nav.home}
        </NavLink>
        <NavLink className="navlink" to="/oa">
          {t.nav.qa}
        </NavLink>
        <NavLink className="navlink" to="/game">
          {t.nav.game}
        </NavLink>
        <button className="language-toggle" type="button" onClick={toggleLanguage}>
          {t.nav.toggle}
        </button>
      </div>
    </div>
  );
}
