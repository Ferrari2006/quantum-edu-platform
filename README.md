# quantum-edu-platform

量智启学（Quantum Edu Platform）平台总仓：以 FastAPI 为后端、Vite + React 为前端，统一承载接口文档、知识检索（RAG）占位链路，以及已实现的量子计算教育游戏 Demo。

## 功能概览

- **后端服务**：FastAPI，提供健康检查、游戏清单、RAG/量子计算相关接口占位，并自动生成 OpenAPI 文档（Swagger UI）。
- **前端站点**：Vite + React，提供 Home / QA / Game 页面；Game 页面会读取后端的游戏清单并展示一键复制运行命令。
- **games 子项目**：已整合两套 Pygame 量子游戏源码（桌面运行），用于教学演示与玩法验证。

## 项目结构

```
quantum-edu-platform/
  backend/            # FastAPI 后端
  frontend/           # Vite + React 前端
  games/              # 游戏子项目（Pygame / Phaser 等）
  docs/               # 文档与资料
  README.md
```

## 快速开始

### 1) 启动后端（FastAPI）

在项目根目录执行：

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

访问：

- 后端首页：http://127.0.0.1:8001/
- API 文档（可直接 Try it out 测试接口）：http://127.0.0.1:8001/docs
- OpenAPI JSON：http://127.0.0.1:8001/openapi.json

### 2) 启动前端（Vite + React）

前端需要 Node.js（含 npm）。在项目根目录执行：

```bash
cd frontend
npm install
npm run dev
```

访问：

- 前端首页：http://127.0.0.1:5173/#/
- 游戏整合页：http://127.0.0.1:5173/#/game
- 后端文档代理入口：http://127.0.0.1:5173/docs

#### Windows PowerShell 说明

若 PowerShell 禁止运行脚本导致 npm 无法执行，可使用以下任意一种方式：

```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

或直接使用 `npm.cmd`：

```bash
cd frontend
"C:\Program Files\nodejs\npm.cmd" install
"C:\Program Files\nodejs\npm.cmd" run dev
```

## games 子项目（已整合）

当前已整合两套 Pygame 版本的量子游戏源码（桌面运行）：

- **game1：2-qubit 概率匹配版**：`games/game1/quantum_balatro/main.py`
- **game2：Original / easyver 版（含 3→5 qubits、Fidelity 等概念实现）**：`games/game2/quantum_balatro_original/display_engine.py`

前端 Game 页面会展示这两套游戏的目录/入口，并提供一键复制运行命令；数据来源为后端接口 `GET /api/games`。

## 接口占位（后续可直接往里塞实现）

已在后端预留并出现在 `/docs` 中的接口（随版本迭代可能扩展）：

- `GET /api/health`、`GET /api/v1/health-data`
- `POST /api/rag/ingest`、`POST /api/rag/query`、`POST /api/rag/ask`
- `POST /api/quantum/run`、`POST /api/quantum/fidelity`（当前为占位返回 501）
- `GET /api/games`

## 端口约定

- 后端默认：`127.0.0.1:8001`（避免与本机其他服务冲突；需要时可自行改为 8000）
- 前端默认：`127.0.0.1:5173`
