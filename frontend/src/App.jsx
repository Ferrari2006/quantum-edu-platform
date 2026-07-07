import { HashRouter, Link, Route, Routes } from "react-router-dom";

import NavBar from "./components/NavBar.jsx";
import { LanguageProvider, useLanguage } from "./i18n.jsx";
import GamePage from "./pages/GamePage.jsx";
import Home from "./pages/Home.jsx";
import OAPage from "./pages/OAPage.jsx";

function NotFound() {
  const { t } = useLanguage();

  return (
    <div>
      <div className="title">404</div>
      <Link to="/">{t.notFound.back}</Link>
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <HashRouter>
        <NavBar />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/oa" element={<OAPage />} />
            <Route path="/game" element={<GamePage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </HashRouter>
    </LanguageProvider>
  );
}
