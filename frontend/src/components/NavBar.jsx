import { NavLink } from "react-router-dom";

export default function NavBar() {
  return (
    <div className="navbar">
      <div className="brand">量智启学</div>
      <div className="links">
        <NavLink className="navlink" to="/">
          Home
        </NavLink>
        <NavLink className="navlink" to="/oa">
          QA
        </NavLink>
        <NavLink className="navlink" to="/game">
          Game
        </NavLink>
      </div>
    </div>
  );
}

