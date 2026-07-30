import { useEffect, useState } from "react";

import { useAuth } from "../auth.jsx";
import { useLanguage } from "../i18n.jsx";

export default function AccountPage() {
  const { t } = useLanguage();
  const account = t.account;
  const {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchMemories,
    saveMemory,
    deleteMemory,
  } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [memoryForm, setMemoryForm] = useState({ key: "", value: "" });
  const [memories, setMemories] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadMemories() {
    if (!isAuthenticated) {
      setMemories([]);
      return;
    }
    const data = await fetchMemories();
    setMemories(data.items || []);
  }

  useEffect(() => {
    loadMemories().catch((err) => setError(err.message || account.error));
  }, [isAuthenticated]);

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updateMemoryForm(field, value) {
    setMemoryForm((current) => ({ ...current, [field]: value }));
  }

  async function submitAuth(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await login(form);
      } else {
        await register(form);
      }
      setForm({ username: "", email: "", password: "" });
    } catch (err) {
      setError(err.message || account.error);
    } finally {
      setBusy(false);
    }
  }

  async function submitMemory(event) {
    event.preventDefault();
    if (!memoryForm.key.trim() || !memoryForm.value.trim()) return;
    setBusy(true);
    setError("");
    try {
      await saveMemory(memoryForm);
      setMemoryForm({ key: "", value: "" });
      await loadMemories();
    } catch (err) {
      setError(err.message || account.error);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(memoryId) {
    setBusy(true);
    setError("");
    try {
      await deleteMemory(memoryId);
      await loadMemories();
    } catch (err) {
      setError(err.message || account.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="account-page">
      <section className="account-hero">
        <div>
          <div className="account-kicker">PERSONAL LEARNING PROFILE</div>
          <h1>{account.title}</h1>
          <p>{account.subtitle}</p>
        </div>
        {isAuthenticated ? (
          <div className="account-user">
            <span>{account.signedInAs}</span>
            <strong>{user.username}</strong>
            <button
              className="account-secondary"
              onClick={logout}
              type="button"
            >
              {account.logout}
            </button>
          </div>
        ) : null}
      </section>

      {error ? <div className="qa-error">{error}</div> : null}

      {!isAuthenticated ? (
        <section className="account-card auth-card">
          <div className="auth-tabs">
            <button
              className={mode === "login" ? "active" : ""}
              onClick={() => setMode("login")}
              type="button"
            >
              {account.loginTab}
            </button>
            <button
              className={mode === "register" ? "active" : ""}
              onClick={() => setMode("register")}
              type="button"
            >
              {account.registerTab}
            </button>
          </div>
          <form className="account-form" onSubmit={submitAuth}>
            <label>
              <span>{account.username}</span>
              <input
                autoComplete="username"
                onChange={(event) =>
                  updateForm("username", event.target.value)
                }
                required
                value={form.username}
              />
            </label>
            {mode === "register" ? (
              <label>
                <span>{account.email}</span>
                <input
                  autoComplete="email"
                  onChange={(event) =>
                    updateForm("email", event.target.value)
                  }
                  type="email"
                  value={form.email}
                />
              </label>
            ) : null}
            <label>
              <span>{account.password}</span>
              <input
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                minLength={mode === "register" ? 6 : undefined}
                onChange={(event) =>
                  updateForm("password", event.target.value)
                }
                required
                type="password"
                value={form.password}
              />
            </label>
            <button
              className="account-primary"
              disabled={busy}
              type="submit"
            >
              {mode === "login" ? account.login : account.register}
            </button>
          </form>
        </section>
      ) : (
        <section className="account-grid">
          <form
            className="account-card account-form"
            onSubmit={submitMemory}
          >
            <div className="account-section-head">
              <h2>{account.memoryTitle}</h2>
              <p>{account.memoryHint}</p>
            </div>
            <label>
              <span>{account.memoryKey}</span>
              <input
                onChange={(event) =>
                  updateMemoryForm("key", event.target.value)
                }
                placeholder={account.memoryKeyPlaceholder}
                value={memoryForm.key}
              />
            </label>
            <label>
              <span>{account.memoryValue}</span>
              <textarea
                onChange={(event) =>
                  updateMemoryForm("value", event.target.value)
                }
                placeholder={account.memoryValuePlaceholder}
                value={memoryForm.value}
              />
            </label>
            <button
              className="account-primary"
              disabled={
                busy || !memoryForm.key.trim() || !memoryForm.value.trim()
              }
              type="submit"
            >
              {account.saveMemory}
            </button>
          </form>

          <div className="memory-list">
            {memories.length ? (
              memories.map((item) => (
                <article className="memory-item" key={item.id}>
                  <div>
                    <strong>{item.key}</strong>
                    <p>{item.value}</p>
                  </div>
                  <button
                    className="account-secondary"
                    disabled={busy}
                    onClick={() => onDelete(item.id)}
                    type="button"
                  >
                    {account.delete}
                  </button>
                </article>
              ))
            ) : (
              <div className="account-card qa-empty">
                {account.noMemories}
              </div>
            )}
          </div>
        </section>
      )}
    </main>
  );
}
