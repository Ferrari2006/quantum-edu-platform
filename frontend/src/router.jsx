import { useEffect, useState } from "react";

function readHashPath() {
  const value = window.location.hash.replace(/^#/, "") || "/";
  const path = value.split("?")[0];
  return path.startsWith("/") ? path : `/${path}`;
}

export function useHashLocation() {
  const [path, setPath] = useState(readHashPath);

  useEffect(() => {
    const updatePath = () => setPath(readHashPath());
    window.addEventListener("hashchange", updatePath);
    return () => window.removeEventListener("hashchange", updatePath);
  }, []);

  return path;
}

export function navigateTo(path, { replace = false } = {}) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (replace) {
    window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${normalized}`);
    window.dispatchEvent(new Event("hashchange"));
    return;
  }
  window.location.hash = normalized;
}

export function HashLink({ to, children, ...props }) {
  const normalized = to.startsWith("/") ? to : `/${to}`;
  return <a href={`#${normalized}`} {...props}>{children}</a>;
}

export function HashNavLink({ to, className = "", children, ...props }) {
  const currentPath = useHashLocation();
  const normalized = to.startsWith("/") ? to : `/${to}`;
  const isActive =
    currentPath === normalized ||
    (normalized !== "/" && currentPath.startsWith(`${normalized}/`));
  const resolvedClassName =
    typeof className === "function" ? className({ isActive }) : `${className}${isActive ? " active" : ""}`;

  return (
    <HashLink className={resolvedClassName.trim()} to={normalized} {...props}>
      {children}
    </HashLink>
  );
}

