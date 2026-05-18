# quantum-edu-platform

> "In the quantum realm, the house always loses... if you can maintain coherence."

量智启学（Quantum Edu Platform）是一个面向量子计算启蒙与游戏化学习的平台型项目。仓库采用前后端分离结构，以 `FastAPI` 作为后端入口，以 `Vite + React` 作为前端承载界面，并将量子计算教育游戏 Demo 作为 `games` 子项目统一整合到同一平台仓库中，便于后续继续扩展知识库、问答链路、量子后端能力以及更多交互式教学模块。

## 项目背景

传统量子计算学习往往存在概念抽象、入门门槛高、反馈路径不直观等问题。量智启学希望通过“平台 + 游戏化学习 + 可扩展知识能力”的方式，将量子门、电路演化、纠缠、保真度等概念转化为更容易体验、操作与理解的交互内容。

在当前阶段，本仓库主要承担三类职责：

- **平台底座**：提供统一的前后端结构与后续功能接入入口。
- **游戏整合**：沉淀现有量子游戏 Demo，避免原型代码分散、重复维护。
- **扩展预留**：为后续的知识检索、智能问答、学习路径推荐与量子后端服务化预留清晰边界。

## 功能概览

- **平台后端**：以 FastAPI 作为统一入口，负责承载服务编排、接口组织与后续能力扩展。
- **平台前端**：以 React 构建平台页面，当前包含首页、问答页、游戏页等基础视图。
- **游戏整合**：已接入两套量子计算教育游戏 Demo，用于玩法验证与平台展示。
- **知识扩展**：预留 `rag` 目录与 `docs` 文档目录，用于后续接入知识库构建、检索与问答链路。
- **结构清晰**：以平台仓库为核心，将前端、后端、游戏子项目、文档统一组织，方便团队协作与后续迭代。

## 核心亮点

- **平台化组织**：将前端、后端、游戏原型和文档归拢到同一仓库，降低协作成本。
- **结构先行**：先搭建清晰的模块边界，再逐步向知识库、问答链路和服务能力扩展。
- **游戏驱动学习**：以量子游戏作为平台内容的重要组成部分，增强量子概念的可理解性。
- **适合持续迭代**：当前版本既能支撑展示，也适合继续补充接口、内容和更稳定的产品形态。

## 技术栈

- **Backend**：FastAPI
- **Frontend**：Vite + React
- **Games**：Python + Pygame + Qiskit / Qiskit Aer
- **Docs / Knowledge**：项目文档、知识素材、后续 RAG 模块预留

## 项目结构

```
quantum-edu-platform/
  backend/
    main.py                 # FastAPI 入口
    rag/
      ingest.py             # 文档向量化 / 数据导入预留
      retriever.py          # 检索逻辑预留
      chain.py              # 问答链路预留
    api/
      routes.py             # 统一路由入口
    requirements.txt
  frontend/
    src/
      pages/
        Home.jsx            # 首页
        OAPage.jsx          # 问答页面
        GamePage.jsx        # 游戏页面
      components/           # 公共组件
    package.json
  games/
    game1/                  # 量子游戏 1
    game2/                  # 量子游戏 2
  docs/                     # 量子知识库文档 / 项目资料
  README.md
```

## 模块说明

### backend

- `main.py`：平台后端启动入口，负责挂载服务与统一配置。
- `api/routes.py`：统一组织路由，便于后续继续补充平台能力。
- `rag/`：面向知识检索与问答链路的预留目录，当前作为结构占位，后续可逐步完善。
- `requirements.txt`：后端依赖声明文件。

### frontend

- `pages/Home.jsx`：平台首页，承担项目概览与入口展示。
- `pages/OAPage.jsx`：问答页面，后续承载智能问答、知识检索与学习辅助能力。
- `pages/GamePage.jsx`：游戏整合页，用于展示已接入的游戏项目与运行说明。
- `components/`：前端公共组件目录，便于页面复用与统一风格。

### games

- `game1/`：已整合的 2-qubit 概率匹配版量子游戏 Demo。
- `game2/`：已整合的 Original / easyver 版本量子游戏 Demo，包含更完整的 3→5 qubits 与 Fidelity 概念实现。

### docs

- 用于存放知识库素材、项目文档、说明资料以及后续 RAG 相关文本来源。

## 当前状态

当前仓库已经完成平台基础骨架搭建，并完成以下整合工作：

- 已搭建 FastAPI 后端与 React 前端基础页面。
- 已整合两套量子游戏 Demo 到 `games/` 目录。
- 已补充基础的项目说明、目录结构与运行方式。
- 已为后续知识检索、智能问答与量子计算能力扩展预留结构位置。

## 快速开始（开发环境）

### 1) 启动后端（FastAPI）

在项目根目录执行：

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

启动后，FastAPI 会自动提供文档页（Swagger UI）与 OpenAPI 描述文件，可用于本地调试与接口测试。

### 2) 启动前端（Vite + React）

前端需要 Node.js（含 npm）。在项目根目录执行：

```bash
cd frontend
npm install
npm run dev
```

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

## 架构说明

- **平台层（Platform）**：统一承载站点、文档、后端服务入口与运行说明。
- **游戏层（Games）**：游戏以子项目形式独立演进；现阶段为桌面 Demo，后续可按需要迁移到 Web（Phaser）或拆分核心逻辑为可复用服务。
- **知识层（Docs / RAG）**：文档与知识素材归档于 `docs/`，后续 RAG 的 ingest / retriever / chain 等实现以模块化方式接入。

## 开发说明

- 当前仓库更偏向“平台底座 + 原型整合”，并非最终产品形态。
- `backend/` 与 `frontend/` 的职责已明确划分，便于后续分工协作。
- `games/` 下保留了不同阶段的游戏原型，后续可以选择继续维护桌面版，或将稳定玩法迁移到 Web 版本。

## Roadmap

- [ ] 完善知识库构建流程（文档清洗、向量化、检索、引用输出）
- [ ] 将量子后端能力抽象为可复用模块/服务（电路执行、Fidelity、噪声模型）
- [ ] 打通“游戏卡关 → 智能解释/推荐学习路径”的闭环
- [ ] 增加更多关卡/牌型/可视化与交互（Web 版本或更稳定的桌面版本）
