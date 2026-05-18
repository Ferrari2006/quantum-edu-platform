import { useEffect, useState } from "react";

export default function GamePage() {
  const [health, setHealth] = useState(null);
  const [games, setGames] = useState([]);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ ok: false }));

    fetch("/api/games")
      .then((r) => r.json())
      .then((data) => setGames(Array.isArray(data) ? data : []))
      .catch(() => setGames([]));
  }, []);

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      window.prompt("复制命令：", text);
    }
  }

  return (
    <div>
      <div className="title">游戏</div>
      <div className="card">
        <div>后端健康检查：{health ? JSON.stringify(health) : "..."}</div>
        <div style={{ marginTop: 10 }}>
          当前游戏以子项目形式整合（Pygame 桌面版），平台页提供一键复制运行命令。
        </div>
      </div>

      <div style={{ height: 14 }} />

      {games.map((g) => {
        const cmd = (g.run || []).join("\n");
        return (
          <div className="card" key={g.id} style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>{g.name}</div>
            <div>目录：{g.path}</div>
            <div>入口：{g.entry}</div>
            <div style={{ marginTop: 10 }} className="row">
              <button className="button" onClick={() => copy(cmd)}>
                复制运行命令
              </button>
              <a className="button" href="/docs" target="_blank" rel="noreferrer">
                打开 API 文档
              </a>
            </div>
            <pre className="pre" style={{ minHeight: 0 }}>
              {cmd}
            </pre>
          </div>
        );
      })}
    </div>
  );
}

