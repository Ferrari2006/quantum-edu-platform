# Quantum Edu Platform（量智启学）

> In the quantum realm, the house always loses... if you can maintain coherence.

量智启学（Quantum Edu Platform）是一个面向量子计算启蒙与游戏化学习的平台型项目。项目采用前后端分离结构，以 `FastAPI` 作为后端入口，以 `Vite + React` 作为前端承载界面，并将量子计算教育游戏 Demo 作为 `games` 子项目统一整合到同一平台仓库中，便于后续继续扩展知识库、问答链路、量子后端能力以及更多交互式教学模块。

当前版本重点是把两个量子游戏接入统一 Web 平台：一方面保留原型代码和量子计算核心逻辑，另一方面通过可视化、规则页、分数拆解、量子态 fidelity 反馈和更完整的 UI 流程，让玩家更直观地理解量子门、概率分布、纠缠、保真度等概念。

## 项目背景

传统量子计算学习往往存在概念抽象、入门门槛高、反馈路径不直观等问题。量智启学希望通过“平台 + 游戏化学习 + 可扩展知识能力”的方式，将量子门、电路演化、纠缠、保真度等概念转化为更容易体验、操作与理解的交互内容。

在当前阶段，本仓库主要承担三类职责：

- **平台底座**：提供统一的前后端结构与后续功能接入入口。
- **游戏整合**：沉淀现有量子游戏 Demo，避免原型代码分散、重复维护。
- **扩展预留**：为后续的知识检索、智能问答、学习路径推荐与量子后端服务化预留清晰边界。

## 功能概览

- **平台后端**：以 FastAPI 作为统一入口，负责承载服务编排、接口组织、游戏状态桥接与后续能力扩展。
- **平台前端**：以 React 构建平台页面，当前包含首页、问答页、游戏大厅和两个 Web 游戏界面。
- **游戏整合**：已接入两套量子计算教育游戏 Demo，并通过 `/api/quantum-game` 接口统一管理状态。
- **量子反馈**：Game 1 展示目标概率匹配，Game 2 使用 Qiskit backend 计算真实量子态 fidelity 并参与计分。
- **游戏化学习**：提供规则页、分数拆解、商店、Joker、开包动画、roulette 风险等交互机制。
- **知识扩展**：预留 `backend/rag` 与 `docs` 文档目录，用于后续接入知识库构建、检索与问答链路。
- **结构清晰**：以平台仓库为核心，将前端、后端、游戏子项目、文档统一组织，方便团队协作与后续迭代。

## 核心亮点

- **平台化组织**：将前端、后端、游戏原型和文档归拢到同一仓库，降低协作成本。
- **结构先行**：先搭建清晰的模块边界，再逐步向知识库、问答链路和服务能力扩展。
- **游戏驱动学习**：以量子游戏作为平台内容的重要组成部分，增强量子概念的可理解性。
- **量子状态可视化**：通过概率柱状图、目标标记、fidelity、score breakdown 等反馈，把抽象概念变成可观察结果。
- **适合持续迭代**：当前版本既能支撑展示，也适合继续补充接口、内容和更稳定的产品形态。

## 技术栈

- **Backend**：FastAPI、Uvicorn
- **Frontend**：Vite、React
- **Quantum / Games**：Python、Qiskit、Qiskit Aer
- **Docs / Knowledge**：项目文档、知识素材、后续 RAG 模块预留

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

## 当前游戏说明

### Game 1：Quantum Hacker

入口：前端 Game 页面选择 `Quantum Hacker`。

核心玩法：

- 在 2-qubit circuit 上放置 `H`、`X`、`Z`、`CNOT`。
- 当前线路会生成 `00`、`01`、`10`、`11` 的概率分布。
- 分数来自目标概率匹配度、量子门倍率和 stored multiplier。
- `Play Hand` 会结算当前线路、消耗一次 hand，并清空 stored multiplier。
- `Observe` 会储存当前倍率、不消耗 hand，但会触发 roulette。
- Observe 次数越多、stored multiplier 越高，roulette 负面概率越高。
- 通过 blind 后进入 shop，可购买或切换 joker。
- Boss blind 会加入电路限制，joker 可以改变部分限制或计分方式。

当前 UI 支持：

- 概率柱状图与目标标记。
- 分数拆解。
- Observe 风险概率展示。
- Roulette 动画与结果页。
- Shop / Joker 管理。
- Rules 页面，且返回时不重置游戏状态。

### Game 2：Quantum Balatro Original

入口：前端 Game 页面选择 `Quantum Balatro Original`。

核心玩法：

- 手牌是量子门卡牌，拖入 qubit slots 后组成线路。
- 卡牌组合会识别成量子牌型，例如 Bell Pair、Flush、Full House、W State、GHZ State。
- 后端会用 Qiskit backend 计算当前线路与目标量子态的 fidelity。
- 最终得分由 base chips、base multiplier、joker 修正和 fidelity 共同决定。
- Discard 可以换牌，但次数有限。
- 通过 blind 后进入 shop，可购买 joker 或 quantum pack。
- Quantum pack 有拆包动画，卡牌 reveal 后才能 collect。

当前 UI 支持：

- 手牌拖拽与 staging circuit。
- Last hand 与 score breakdown。
- Fidelity 百分比展示。
- Shop、Joker、Quantum Pack。
- Pack opening 动效。
- Rules 页面，且返回时不重置游戏状态。

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

### Game 1 电路接口

```text
POST /api/quantum-game/circuit/stage
POST /api/quantum-game/circuit/observe
POST /api/quantum-game/circuit/roulette/continue
POST /api/quantum-game/circuit/play
POST /api/quantum-game/circuit/clear
POST /api/quantum-game/circuit/next
POST /api/quantum-game/circuit/shop/buy/{joker_id}
POST /api/quantum-game/circuit/jokers/toggle/{joker_id}
```

### Game 2 卡牌接口

```text
POST /api/quantum-game/play
POST /api/quantum-game/discard
POST /api/quantum-game/cards/shop
POST /api/quantum-game/cards/next
POST /api/quantum-game/cards/buy-joker/{item_index}
POST /api/quantum-game/cards/buy-pack
POST /api/quantum-game/cards/collect-pack
```

## 验证命令

常用检查命令：

```bash
backend/.venv/Scripts/python -m py_compile backend/api/game_routes.py games/game2/quantum_balatro_original/game_state.py
cd frontend
npm.cmd run build
```

## 开发说明

- 前端目前在 `GamePage.jsx` 中使用固定 API base：`http://127.0.0.1:8000/api/quantum-game`，因此后端建议运行在 `8000` 端口。
- 后端游戏状态当前保存在进程内存中，刷新页面后可继续读取当前 active game，但重启后端会丢失状态。
- `games/` 下保留了不同阶段的游戏原型。Web 版主要通过 `backend/api/game_routes.py` 接入核心逻辑。
- `backend/rag/` 目前是知识库问答能力的结构占位，后续可接入文档清洗、向量检索和回答链路。
- 当前仓库仍偏向“平台底座 + 原型整合”，并非最终产品形态。

## Roadmap

- [ ] 完善知识库构建流程：文档清洗、向量化、检索、引用输出。
- [ ] 将量子后端能力抽象为可复用模块或服务：电路执行、fidelity、噪声模型。
- [ ] 打通“游戏卡关 → 智能解释 / 推荐学习路径”的闭环。
- [ ] 为 Game 1 增加更多 Boss 约束、Joker 和目标概率谜题。
- [ ] 为 Game 2 增加更细的 CNOT 目标选择和线路连线可视化。
- [ ] 增加更多牌型、卡牌、pack 类型和教学解释层。
