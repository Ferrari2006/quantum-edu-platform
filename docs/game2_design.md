# Game2 设计与平衡（概要）

目标：将 `game2`（量子卡牌 Roguelike）打磨为教学向可玩原型，保留保真度、噪声、商店与小丑牌机制。

核心要素：
- 比特数：默认 3 qubits，Ante >=3 时扩容至 5 qubits.\
- 牌库类型：普通（blue/normal）、紫（purple 有耐久）、金（gold 成本高，效果强）。
- 核心门：`H`, `X`, `Z`, `CNOT`, `RX/RY/RZ`（旋转门为稀有/教学卡）。
- 小丑牌（Jokers）：一次性或持续的规则修改器（上限 5 张持有，最多同时激活 5 张）。

商店与经济：
- 每关奖励基于目标与剩余出牌机会。\
- 商店每次提供 1-2 个小丑牌或一个包（pack）。\
- Joker 成本范围：4-8 chips，后期稀有 Joker 价格更高。

卡牌平衡要点（建议初始值）：
- 普通卡（H/X/Z/CNOT）：无成本，放置影响保真度与牌型。\
- 蓝卡（RX/CZ）：稀有，提供教学效果与额外 multiplier。\
- 紫卡（耐久 3）：强力效果但有耐久限制。\
- 金卡：消耗 chips 使用，提供瞬时分数溢出或稳定器效果。

代表性 Joker 列表（复用现有）：
- `TOPOLOGY`（Shield）: 每行门数 +1。\
- `ENTANGLE`（Spark）: 使用 CNOT 时 +100 chips。\
- `PHASE`（Phase）: Z 门倍率 x1.5。\
- `COMPRESSION`（Compiler）: 少量门数时 x1.8 multiplier。\

关卡与教学路线：
1. Intro（3 qubits） — 认识 `H` 与 `X`，做简单 GHZ 目标。\
2. Entangle（3 qubits） — 引入 `CNOT`、Bell 对。\
3. Phase（3 qubits） — 相位门与干涉演示。\
4. Boss（扩容至 5 qubits） — 噪声与保真度、包/商店流程。\
5. Challenge（混合） — 多任务评分与策略选择。

测试与可视化要点：
- 提供实时预览（保真度、预估分数）。\
- 商店/开包动画与确认流程（防误买）。\
- 在后端增加轻量日志用于回放与教学视频生成。

下一步行动建议：
1. 在 `backend/api/game_routes.py` 中补强 card-game 相关错误处理与文档注释。\
2. 在 `frontend/src/pages/GamePage.jsx` 的 `CardGame` 区域优化拖拽与开包交互。\
3. 添加后端单元测试覆盖 `GameState.play_hand`, `QuantumBackend.calculate_fidelity`。

作者：自动生成概要（可继续细化）
