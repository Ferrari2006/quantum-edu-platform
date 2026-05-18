# quantum-edu-platform

> "In the quantum realm, the house always loses... if you can maintain coherence."

量智启学（Quantum Edu Platform）平台总仓：以 FastAPI 为后端、Vite + React 为前端，统一承载平台页面、自动生成的 API 文档（Swagger UI）、以及已实现的量子计算教育游戏 Demo（games 子项目）。

## 功能概览

- **平台后端**：FastAPI（自动生成 OpenAPI / Swagger UI，可在页面内直接测试请求）。
- **平台前端**：Vite + React，提供 Home / QA / Game 页面。
- **游戏 Demo**：已整合两套 Pygame 量子游戏源码（桌面运行），用于教学演示与玩法验证。
- **可扩展性**：为后续接入知识检索（RAG）、量子计算能力服务化、学习数据记录等模块预留结构位置。

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

前端 Game 页面会展示这两套游戏的目录/入口，并提供一键复制运行命令（便于组内协作与演示复现）。

## 架构说明（概念）

- **平台层（Platform）**：统一承载站点、文档、后端服务入口与运行说明。
- **游戏层（Games）**：游戏以子项目形式独立演进；现阶段为桌面 Demo，后续可按需要迁移到 Web（Phaser）或拆分核心逻辑为可复用服务。
- **知识层（Docs / RAG）**：文档与知识素材归档于 `docs/`，后续 RAG 的 ingest / retriever / chain 等实现以模块化方式接入。

## Roadmap

- [ ] 完善知识库构建流程（文档清洗、向量化、检索、引用输出）
- [ ] 将量子后端能力抽象为可复用模块/服务（电路执行、Fidelity、噪声模型）
- [ ] 打通“游戏卡关 → 智能解释/推荐学习路径”的闭环
- [ ] 增加更多关卡/牌型/可视化与交互（Web 版本或更稳定的桌面版本）

## 端口约定

- 后端默认：`127.0.0.1:8001`（避免与本机其他服务冲突；需要时可自行改为 8000）
- 前端默认：`127.0.0.1:5173`
