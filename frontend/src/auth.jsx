import { createContext, useCallback, useContext, useMemo, useState } from "react";

const TOKEN_KEY = "quantum_edu_access_token";
const USER_KEY = "quantum_edu_user";
const AuthContext = createContext(null);

function readStoredUser() {
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }
  return data;
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(
    () => window.localStorage.getItem(TOKEN_KEY) || "",
  );
  const [user, setUser] = useState(readStoredUser);

  const authHeaders = useCallback(
    (extra = {}) => ({
      ...extra,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const saveSession = useCallback((payload) => {
    setToken(payload.access_token);
    setUser(payload.user);
    window.localStorage.setItem(TOKEN_KEY, payload.access_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  }, []);

  const login = useCallback(
    async ({ username, password }) => {
      const payload = await requestJson("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      saveSession(payload);
      return payload;
    },
    [saveSession],
  );

  const register = useCallback(
    async ({ username, password, email }) => {
      const payload = await requestJson("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, email: email || null }),
      });
      saveSession(payload);
      return payload;
    },
    [saveSession],
  );

  const logout = useCallback(() => {
    setToken("");
    setUser(null);
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  }, []);

  const fetchMemories = useCallback(
    () => requestJson("/api/memories", { headers: authHeaders() }),
    [authHeaders],
  );

  const saveMemory = useCallback(
    ({ key, value }) =>
      requestJson("/api/memories", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ key, value, source: "manual" }),
      }),
    [authHeaders],
  );

  const deleteMemory = useCallback(
    async (memoryId) => {
      const response = await fetch(`/api/memories/${memoryId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!response.ok) {
        throw new Error("Delete memory failed");
      }
    },
    [authHeaders],
  );

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      authHeaders,
      login,
      register,
      logout,
      fetchMemories,
      saveMemory,
      deleteMemory,
    }),
    [
      authHeaders,
      deleteMemory,
      fetchMemories,
      login,
      logout,
      register,
      saveMemory,
      token,
      user,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
