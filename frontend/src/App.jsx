import { AuthProvider } from "./auth.jsx";
import NavBar from "./components/NavBar.jsx";
import { LanguageProvider, useLanguage } from "./i18n.jsx";
import GamePage from "./pages/GamePage.jsx";
import Home from "./pages/Home.jsx";
import KnowledgeBase from "./pages/KnowledgeBase.jsx";
import OAPage from "./pages/OAPage.jsx";
import AccountPage from "./pages/AccountPage.jsx";
import QuantumLab from "./pages/QuantumLab.jsx";
import LearningProgressPage from "./pages/LearningProgressPage.jsx";
import { HashLink as Link, useHashLocation } from "./router.jsx";

function AppContent() {
  const path = useHashLocation();
  const segments = path.split("/").filter(Boolean);
  const { t } = useLanguage();

  let page;
  if (path === "/") {
    page = <Home />;
  } else if (segments[0] === "knowledge" && segments.length <= 2) {
    page = <KnowledgeBase articleId={segments[1] || ""} />;
  } else if (path === "/oa") {
    page = <OAPage />;
  } else if (path === "/game") {
    page = <GamePage />;
  } else if (path === "/lab") {
    page = <QuantumLab />;
  } else if (path === "/account") {
    page = <AccountPage />;
  } else if (path === "/progress") {
    page = <LearningProgressPage />;
  } else {
    page = (
      <div>
        <div className="title">404</div>
        <Link to="/">{t.notFound.back}</Link>
      </div>
    );
  }

  return (
    <>
      <NavBar />
      <div className="container">
        {page}
      </div>
    </>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </LanguageProvider>
  );
}
