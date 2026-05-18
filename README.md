## quantum-edu-platform

量智启学平台总仓：后端 FastAPI + 前端 Web + games 子项目 + docs 文档。

### 目录结构

- backend/：FastAPI 后端与 RAG 占位模块
- frontend/：Web 前端
- games/：游戏子项目（已整合两套 Pygame Demo）
- docs/：文档

### 本地运行（后端）

在项目根目录执行：

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

启动后访问：

- http://127.0.0.1:8001/
- http://127.0.0.1:8001/docs
- http://127.0.0.1:8001/openapi.json

### 本地运行（前端）

前端需要安装 Node.js（含 npm）。在项目根目录执行：

```bash
cd frontend
npm install
npm run dev
```

如遇到 PowerShell 禁止运行脚本导致 npm 无法执行，可以用以下任意一种方式：

```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

或使用 `npm.cmd`：

```bash
cd frontend
"C:\Program Files\nodejs\npm.cmd" install
"C:\Program Files\nodejs\npm.cmd" run dev
```

启动后访问：

- http://127.0.0.1:5173/#/
- http://127.0.0.1:5173/#/game
- http://127.0.0.1:5173/docs

### games 子项目

平台已整合两套 Pygame 版本的量子游戏源码（桌面运行）：

- game1（2-qubit demo）：`games/game1/quantum_balatro/main.py`
- game2（easyver 原版）：`games/game2/quantum_balatro_original/display_engine.py`

前端 Game 页面会展示并提供一键复制运行命令（由后端 `GET /api/games` 提供数据）。
