import { HashRouter, Link, Route, Routes } from "react-router-dom";

import NavBar from "./components/NavBar.jsx";
import GamePage from "./pages/GamePage.jsx";
import Home from "./pages/Home.jsx";
import OAPage from "./pages/OAPage.jsx";

export default function App() {
  return (
    <HashRouter>
      <NavBar />
      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/oa" element={<OAPage />} />
          <Route path="/game" element={<GamePage />} />
          <Route
            path="*"
            element={
              <div>
                <div className="title">404</div>
                <Link to="/">返回首页</Link>
              </div>
            }
          />
        </Routes>
      </div>
    </HashRouter>
  );
}

