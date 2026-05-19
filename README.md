# Quantum Edu Platform

> In the quantum realm, the house always loses... if you can maintain coherence.

Quantum Edu Platform 是一个面向量子计算启蒙与游戏化学习的平台原型。项目采用前后端分离结构：后端使用 FastAPI 提供统一 API，前端使用 Vite + React 承载平台页面和 Web 游戏界面，`games/` 目录保留量子游戏核心逻辑与原型代码。

当前版本重点是把两个量子游戏接入统一平台，并通过可视化、规则页、分数拆解和量子态反馈，让玩家更直观地理解量子门、概率分布、纠缠、保真度等概念。

## Features

- FastAPI 后端，统一提供健康检查、RAG 占位接口、游戏状态接口。
- React 前端，包含首页、问答页、游戏大厅和两个可玩的量子游戏。
- Game 1: Quantum Hacker，2-qubit 电路谜题，围绕目标概率、倍率、Observe 风险和 Boss 约束展开。
- Game 2: Quantum Balatro Original，卡牌驱动的量子 roguelike，使用真实量子态 fidelity 参与计分。
- 两个游戏都内置 Rules 页面，支持从当前局返回，不会重置游戏状态。
- Game 2 开包页包含拆包动画，不再直接显示结果。
- UI 已包含进度条、概率图、分数拆解、商店、Joker 和响应式布局。

## Tech Stack

- Backend: FastAPI, Uvicorn
- Frontend: Vite, React
- Quantum / Games: Python, Qiskit, Qiskit Aer
- Docs / Future Knowledge Layer: local markdown docs and reserved RAG modules

## Project Structure

```text
quantum-edu-platform/
  backend/
    main.py                 # FastAPI app entry
    api/
      routes.py             # General API routes
      game_routes.py        # Web game bridge routes
    rag/                    # Reserved RAG modules
    requirements.txt

  frontend/
    src/
      App.jsx
      main.jsx
      pages/
        Home.jsx
        OAPage.jsx
        GamePage.jsx
        GamePage.css
      components/
        NavBar.jsx
    package.json

  games/
    game1/
      quantum_balatro/      # Quantum Hacker source and quantum core
    game2/
      quantum_balatro_original/
                            # Card game state and quantum backend

  docs/
    README.md

  README.md
```

## Quick Start

需要分别启动后端和前端。

### 1. Start Backend

在项目根目录执行：

```bash
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后：

- Backend home: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Game API base: `http://127.0.0.1:8000/api/quantum-game`

### 2. Start Frontend

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

如果 Windows PowerShell 禁止执行 npm 脚本，可以改用：

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

## Build Frontend

```bash
cd frontend
npm.cmd run build
```

构建产物会输出到：

```text
frontend/dist/
```

## Web Games

### Game 1: Quantum Hacker

入口：前端 Game 页面选择 `Quantum Hacker`。

核心机制：

- 在 2-qubit circuit 上放置 `H`, `X`, `Z`, `CNOT`。
- 当前线路会生成 `00`, `01`, `10`, `11` 的概率分布。
- 分数来自目标概率匹配度、量子门倍率和 stored multiplier。
- `Play Hand` 会结算当前线路并消耗一次 hand。
- `Observe` 会储存当前倍率、不消耗 hand，但会触发 roulette。
- Observe 次数越多、stored multiplier 越高，roulette 负面概率越高。
- 通过 blind 后进入 shop，可购买或切换 joker。
- Boss blind 会加入电路限制，joker 可以改变部分限制或计分方式。

UI 支持：

- 概率柱状图和目标标记。
- 分数拆解。
- Observe 风险概率展示。
- Roulette 动画和结果页。
- Rules 页面。

### Game 2: Quantum Balatro Original

入口：前端 Game 页面选择 `Quantum Balatro Original`。

核心机制：

- 手牌是量子门卡牌，拖入 qubit slots 后组成线路。
- 卡牌组合会识别成量子牌型，例如 Bell Pair, Flush, Full House, W State, GHZ State。
- 后端会用 Qiskit backend 计算当前线路与目标量子态的 fidelity。
- 最终得分由 base chips、base multiplier、joker 修正和 fidelity 共同决定。
- Discard 可以换牌，但次数有限。
- 通过 blind 后进入 shop，可购买 joker 或 quantum pack。
- Pack opening 有拆包动画，卡牌 reveal 后才能 collect。

UI 支持：

- 手牌拖拽和 staging circuit。
- Last hand 和 score breakdown。
- Fidelity 百分比展示。
- Shop、joker、pack opening。
- Rules 页面。

## Main API Routes

General:

```text
GET  /health
GET  /api/health
GET  /api/v1/health-data
POST /api/rag/ingest
POST /api/rag/query
POST /api/rag/ask
```

Game bridge:

```text
GET  /api/quantum-game/list
GET  /api/quantum-game/state
POST /api/quantum-game/start/{game_id}
POST /api/quantum-game/clear
```

Game 1 circuit routes:

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

Game 2 card routes:

```text
POST /api/quantum-game/play
POST /api/quantum-game/discard
POST /api/quantum-game/cards/shop
POST /api/quantum-game/cards/next
POST /api/quantum-game/cards/buy-joker/{item_index}
POST /api/quantum-game/cards/buy-pack
POST /api/quantum-game/cards/collect-pack
```

## Development Notes

- 前端目前在 `GamePage.jsx` 中使用固定 API base: `http://127.0.0.1:8000/api/quantum-game`，因此后端建议运行在 `8000` 端口。
- 后端游戏状态当前保存在进程内存中，刷新页面后可继续读取当前 active game，但重启后端会丢失状态。
- `games/game1/quantum_balatro/game2.py` 和部分原型文件仍保留 Pygame 版本代码，Web 版主要通过 `backend/api/game_routes.py` 和 quantum core 接入。
- `backend/rag/` 目前是知识库问答能力的结构占位，后续可接入文档清洗、向量检索和回答链路。

## Verification

常用检查命令：

```bash
backend/.venv/Scripts/python -m py_compile backend/api/game_routes.py games/game2/quantum_balatro_original/game_state.py
cd frontend
npm.cmd run build
```

## Roadmap

- 完善 RAG 文档 ingest、retriever、answer chain。
- 将量子线路执行、fidelity、噪声模型抽象为更稳定的服务模块。
- 增加更多关卡、Boss 约束、Joker 和卡牌类型。
- 为 Game 2 增加更细的 CNOT 目标选择和线路连线可视化。
- 增加学习解释层，把游戏行为连接到具体量子概念。
