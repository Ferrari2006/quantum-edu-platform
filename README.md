## quantum-edu-platform

量智启学平台总仓：后端 FastAPI + 前端 Web + games 子项目 + docs 文档。

### 目录结构

- backend/：FastAPI 后端与 RAG 占位模块
- frontend/：Web 前端（需要 Node.js）
- games/：游戏子项目占位（Phaser/Pygame 等）
- docs/：文档

### 本地运行（后端）

在 `backend/` 下创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

启动后访问：

- http://127.0.0.1:8001/
- http://127.0.0.1:8001/docs
- http://127.0.0.1:8001/health
- http://127.0.0.1:8001/api/health

### 本地运行（前端）

前端需要安装 Node.js（含 npm）。

```bash
cd frontend
npm install
npm run dev
```

默认会访问后端 `http://127.0.0.1:8001`，并通过 Vite 代理转发 `/api`。
