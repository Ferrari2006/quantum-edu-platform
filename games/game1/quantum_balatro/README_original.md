# 🌀 Quantum Balatro: Original Edition

> **"In the quantum realm, the house always loses... if you can maintain coherence."**

**Quantum Balatro** 是一款结合了**量子力学模拟**与 **扑克肉鸽（Roguelike）** 机制的策略游戏。通过 Qiskit 模拟真实的量子叠加与纠缠，玩家需要利用有限的量子门操作，对抗不确定的波函数坍缩。

---

## 🕹️ 核心系统：量化策略

游戏摒弃了传统的纸牌，引入了基于 **Qiskit** 的概率匹配机制。

### 1. 概率匹配系统 (The Matching Engine)
每一关都有一个**目标概率分布**（金色幽灵框）。
- **基础筹码 (Chips)**：计算公式为 $Base = \sum \min(P_{current}, P_{target}) \times 200$。
- **匹配度**：当你的实时概率柱（青色）填满金色框时，即可获得当前关卡的最大基础分。



### 2. 倍率链条 (Multiplier Chain)
- **门增益**：`H` 门提供 $x1.5$ 倍率，`CNOT` 提供 $x2.0$ 倍率。
- **OBSERVE (风险存储)**：点击 OBSERVE 会将当前倍率存入缓存（Stored Mult），且不消耗出牌次数。
- **指数爆发**：通过多次 OBSERVE，你可以实现倍率的指数级增长：
  $1.5 \to 2.25 \to 5.06 \to \dots \to 100x+$。

### 3. 坍缩轮盘 (The Collapse Roulette)
**观测必有代价**。每次点击 OBSERVE 都会强制触发轮盘。
- **安全 (SAFE)**：波函数稳定，成功存储倍率。
- **时间膨胀 (-1 HAND)**：失去一次出牌机会。
- **倍率坍缩 (RESET MULT)**：存储的倍率清零。
- **能量泄漏 (-200 CHIPS)**：直接损失分数。

---

## 🛠️ 技术架构：DSBD 模式

本项目采用 **DSBD (Data-State-Backend-Display)** 解耦架构，确保算法与渲染分离。



[Image of model-view-controller software architecture diagram]


| 模块 | 文件 | 职责 |
| :--- | :--- | :--- |
| **Data (数据层)** | `quantum_core.py` | 关卡配置 (LEVELS)、目标概率 (target_probs) 定义。 |
| **Backend (算法层)** | `quantum_core.py` | 使用 **AerSimulator** 进行量子态演化，计算波函数概率。 |
| **State (状态层)** | `main.py` | 维护 `score`, `hands`, `stored_m` 以及 `ROULETTE` 状态机。 |
| **Display (渲染层)** | `ui_engine.py` | 基于 Pygame 的霓虹赛博 UI，处理发光特效与动态网格。 |

---

## 🚀 进阶连招 (Combos)

* **纠缠流 (The Entangler)**：
    使用 `H(q0)` + `CNOT(q0, q1)` 制造 $\Phi^+$ 态，配合 **Spark Joker** (+100 Chips)，在第二关可以瞬间爆发数千分。
* **相位防御 (Phase Shifter)**：
    激活 **Phase Joker**，此时 `Z` 门将提供额外的 $x1.5$ 倍率，配合 OBSERVE 可以快速堆叠出恐怖的数值。
* **极限跨越 (The Transcendent)**：
    在 Boss 关卡 `DECOHERENCE` (每行限放2门) 中，先用 OBSERVE 存下一部分倍率，清空盘面后再放置新的门，以此绕过硬件限制。

---

## 📦 安装与运行

1. **环境依赖**：
   ```bash
   pip install pygame qiskit qiskit-aer
2. **启动命令**
   ```bash
   python main.py
