# Quantum Edu Platform（量智启学）

> In the quantum realm, the house always loses... if you can maintain coherence.

量智启学（Quantum Edu Platform）是一个面向量子计算启蒙、智能问答与游戏化学习的平台型项目。项目采用前后端分离结构，以 `FastAPI` 作为后端入口，以 `Vite + React` 作为前端承载界面，并将 RAG 智能问答系统、垂直领域量子自己是库、量子计算科普游戏统一整合到同一平台中，便于后续继续扩展知识库、学习路径推荐、量子后端能力以及更多交互式教学模块。

当前版本有两个并行产品方向：一是面向知识学习和课程辅助的 RAG 智能问答系统，二是面向交互体验和概念理解的量子游戏模块。游戏不是平台的全部，而是帮助学生理解抽象概念的一种入口；智能问答、知识检索和学习辅助同样是平台的核心组成部分。

## 项目背景

传统量子计算学习往往存在概念抽象、入门门槛高、资料分散、反馈路径不直观等问题。量智启学希望通过“平台 + 智能问答 + 游戏化学习 + 可扩展知识能力”的方式，一方面帮助学习者快速获得可信的知识解释，另一方面将量子门、电路演化、纠缠、保真度等概念转化为更容易体验、操作与理解的交互内容。

在当前阶段，本仓库主要承担三类职责：

- **平台底座**：提供统一的前后端结构与后续功能接入入口。
- **智能问答**：建设面向量子知识的 RAG 问答链路，为课程学习、概念解释和资料检索提供入口。
- **游戏整合**：沉淀现有量子游戏 Demo，作为平台的交互式学习产品之一。
- **扩展预留**：为后续的知识检索、智能问答、学习路径推荐、游戏模块与量子后端服务化预留清晰边界。

## 功能概览

- **平台后端**：以 FastAPI 作为统一入口，负责承载服务编排、接口组织、RAG 问答、游戏状态桥接与后续能力扩展。
- **平台前端**：以 React 构建平台页面，当前包含首页、问答页、游戏大厅和两个 Web 游戏界面。
- **智能问答系统**：预留 `backend/rag` 与 `docs` 文档目录，当前已提供 ingest、retrieve、answer 的接口骨架，后续可接入文档清洗、向量检索、引用输出和模型回答。
- **游戏整合**：已接入两套量子计算教育游戏 Demo，并通过 `/api/quantum-game` 接口统一管理状态。
- **量子反馈**：Game 1 展示目标概率匹配，Game 2 使用 Qiskit backend 计算真实量子态 fidelity 并参与计分。
- **游戏化学习**：提供规则页、分数拆解、商店、Joker、开包动画、roulette 风险等交互机制。
- **知识扩展**：围绕 docs、RAG、问答页和学习解释层继续沉淀量子知识内容。
- **结构清晰**：以平台仓库为核心，将前端、后端、游戏子项目、文档统一组织，方便团队协作与后续迭代。

## 核心亮点

- **平台化组织**：将前端、后端、游戏原型和文档归拢到同一仓库，降低协作成本。
- **结构先行**：先搭建清晰的模块边界，再逐步向知识库、问答链路和服务能力扩展。
- **智能问答优先级明确**：RAG 系统是平台的重要产品方向，用于承载量子知识解释、资料检索和学习辅助。
- **游戏驱动学习**：以量子游戏作为平台内容的重要组成部分，增强量子概念的可理解性。
- **量子状态可视化**：通过概率柱状图、目标标记、fidelity、score breakdown 等反馈，把抽象概念变成可观察结果。
- **适合持续迭代**：当前版本既能支撑展示，也适合继续补充接口、内容和更稳定的产品形态。

## 技术栈

- **Backend**：FastAPI、Uvicorn
- **Frontend**：Vite、React
- **Quantum / Games**：Python、Qiskit、Qiskit Aer
- **RAG / Knowledge**：项目文档、知识素材、检索、问答链路与学习辅助能力

## 项目结构

```text
quantum-edu-platform/
  backend/
    main.py                 # FastAPI 入口
    api/
      routes.py             # 通用 API 路由
      game_routes.py        # Web 游戏桥接接口
    rag/
      ingest.py             # 文档导入 / 向量化预留
      retriever.py          # 检索逻辑预留
      chain.py              # 问答链路预留
    requirements.txt

  frontend/
    src/
      App.jsx
      main.jsx
      pages/
        Home.jsx            # 首页
        OAPage.jsx          # 问答页面
        GamePage.jsx        # 游戏页面与交互逻辑
        GamePage.css        # 游戏页面样式
      components/
        NavBar.jsx
    package.json

  games/
    game1/
      quantum_balatro/      # Quantum Hacker 源码与 quantum core
    game2/
      quantum_balatro_original/
                            # 卡牌游戏状态机与 quantum backend

  docs/                     # 量子知识库文档 / 项目资料
  README.md
```

## 模块说明

### backend

- `main.py`：平台后端启动入口，负责创建 FastAPI app、挂载 CORS、通用路由和游戏路由。
- `api/routes.py`：通用 API 入口，包含健康检查、RAG 占位接口、量子能力占位接口等。
- `api/game_routes.py`：Web 游戏桥接层，负责游戏列表、启动、状态序列化、Game 1 电路操作、Game 2 卡牌操作等。
- `rag/`：面向知识检索与问答链路的预留目录，当前作为结构占位，后续可逐步完善。
- `requirements.txt`：后端依赖声明文件，包含 FastAPI、Uvicorn、Qiskit、Qiskit Aer。

### frontend

- `pages/Home.jsx`：平台首页，承担项目概览与入口展示。
- `pages/OAPage.jsx`：问答页面，后续承载智能问答、知识检索与学习辅助能力。
- `pages/GamePage.jsx`：游戏整合页，包含游戏大厅、两个游戏的主要界面、规则页、商店、开包动画和状态刷新逻辑。
- `pages/GamePage.css`：游戏页面样式，包含工作台布局、卡牌、概率图、规则页、roulette、pack opening 等视觉效果。
- `components/NavBar.jsx`：前端公共导航组件。

### games

- `game1/quantum_balatro/`：2-qubit 概率匹配类量子游戏。Web 版主要复用 `quantum_core.py` 中的概率计算、Boss 约束和计分逻辑。
- `game2/quantum_balatro_original/`：卡牌驱动的量子 roguelike。当前 Web 版复用 `game_state.py` 和 `quantum_backend.py`，并使用 Qiskit 计算目标态 fidelity。

### docs

- 用于存放知识库素材、项目文档、说明资料以及后续 RAG 相关文本来源。

## 智能问答与知识系统

RAG 智能问答系统是量智启学的重要产品方向之一。它的目标不是简单做一个聊天入口，而是围绕量子计算学习场景，提供可检索、可解释、可扩展的知识辅助能力。

当前仓库已经预留了基础结构：

- `docs/`：用于沉淀量子知识文档、课程资料、项目说明和后续知识库来源。
- `backend/rag/ingest.py`：文档导入与清洗流程的接口位置。
- `backend/rag/retriever.py`：检索逻辑的接口位置。
- `backend/rag/chain.py`：问答生成链路的接口位置。
- `frontend/src/pages/OAPage.jsx`：前端问答页面入口。
- `/api/rag/ingest`、`/api/rag/query`、`/api/rag/ask`：后端问答相关 API 入口。

后续可以在这个方向上继续扩展：

- 文档清洗、分块、向量化和索引构建。
- 基于问题的知识检索和引用返回。
- 面向量子概念的分层解释，例如初学者解释、公式解释、实验/游戏关联解释。
- 与游戏模块联动，在玩家卡关或结算后给出概念提示和学习路径建议。

## 当前游戏说明

### Game 1：Quantum Hacker

`Quantum Hacker` 是一个 2-qubit 电路谜题游戏，玩家通过放置量子门来匹配目标概率分布，并在分数、倍率、Observe 风险和 Boss 约束之间做取舍。当前 Web 版已经提供概率可视化、分数拆解、roulette、shop、joker 和规则页等基础体验。

### Game 2：Quantum Balatro Original

`Quantum Balatro Original` 是一个卡牌驱动的量子 roguelike 原型，玩家用量子门卡牌构造线路，并通过牌型、joker 和量子态 fidelity 完成计分。当前 Web 版已经提供手牌拖拽、staging circuit、shop、quantum pack、开包动效、分数拆解和规则页等基础体验。

## 快速开始（开发环境）

需要分别启动后端和前端。建议先启动后端，再启动前端。

### 1. 启动后端（FastAPI）

在项目根目录执行：

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后可访问：

- 后端首页：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`
- 游戏 API：`http://127.0.0.1:8000/api/quantum-game`

### 2. 启动前端（Vite + React）

新开一个终端，在项目根目录执行：

```bash
cd frontend
npm install
npm run dev
```

前端默认地址通常是：

```text
http://127.0.0.1:5173
```

### Windows PowerShell 说明

如果 PowerShell 禁止执行 npm 脚本，可以使用 `npm.cmd`：

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

也可以调整当前用户的脚本执行策略：

```bash
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 构建前端

```bash
cd frontend
npm.cmd run build
```

构建产物会输出到：

```text
frontend/dist/
```

## 主要 API

### 通用接口

```text
GET  /health
GET  /api/health
GET  /api/v1/health-data
POST /api/rag/ingest
POST /api/rag/query
POST /api/rag/ask
```

### 游戏桥接接口

```text
GET  /api/quantum-game/list
GET  /api/quantum-game/state
POST /api/quantum-game/start/{game_id}
POST /api/quantum-game/clear
```

## 验证命令

常用检查命令：

```bash
backend/.venv/Scripts/python -m py_compile backend/api/game_routes.py games/game2/quantum_balatro_original/game_state.py
cd frontend
npm.cmd run build
```

## 开发说明

- 前端游戏页使用相对 API base：`/api/quantum-game`；本地开发时由 Vite proxy 转发到后端默认 `8000` 端口。
- 后端游戏状态当前保存在进程内存中，刷新页面后可继续读取当前 active game，但重启后端会丢失状态。
- `games/` 下保留了不同阶段的游戏原型。Web 版主要通过 `backend/api/game_routes.py` 接入核心逻辑。
- `backend/rag/` 是智能问答系统的核心预留模块，目前提供最小接口骨架，后续重点是补齐文档处理、检索和回答链路。
- 当前仓库仍偏向“平台底座 + RAG 骨架 + 游戏原型整合”，并非最终产品形态。

## Roadmap

- [ ] 完善 RAG 知识库构建流程：文档清洗、分块、向量化、检索、引用输出。
- [ ] 完善智能问答体验：问题改写、上下文引用、分层解释、前端问答交互。
- [ ] 建立量子知识内容体系：基础概念、量子门、电路、纠缠、测量、算法入门等。
- [ ] 打通“知识问答 ↔ 游戏反馈”的闭环，让游戏中的操作和卡关点能够触发学习解释。
- [ ] 将量子后端能力抽象为可复用模块或服务：电路执行、fidelity、噪声模型。
- [ ] 为 Game 1 增加更多 Boss 约束、Joker 和目标概率谜题。
- [ ] 为 Game 2 增加更细的 CNOT 目标选择和线路连线可视化。
- [ ] 增加更多牌型、卡牌、pack 类型和教学解释层。
