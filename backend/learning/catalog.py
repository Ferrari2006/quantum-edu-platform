from __future__ import annotations

from typing import TypedDict


class Concept(TypedDict):
    id: str
    title: str
    module: str
    difficulty: str


# This mirrors the public knowledge-base route. Article ids deliberately act as the
# first version of concept ids so learning evidence can be traced to a visible lesson.
CONCEPT_CATALOG: list[Concept] = [
    {"id": "what-is-quantum-computing", "title": "什么是量子计算", "module": "起点：先建立地图", "difficulty": "入门"},
    {"id": "classical-bit-and-qubit", "title": "经典比特与量子比特", "module": "起点：先建立地图", "difficulty": "入门"},
    {"id": "learning-map", "title": "量子计算学习地图", "module": "起点：先建立地图", "difficulty": "入门"},
    {"id": "superposition", "title": "叠加态：不是同时处于两个答案", "module": "直觉：理解量子现象", "difficulty": "入门"},
    {"id": "phase-and-interference", "title": "相位与干涉", "module": "直觉：理解量子现象", "difficulty": "基础"},
    {"id": "measurement", "title": "测量：从概率到结果", "module": "直觉：理解量子现象", "difficulty": "基础"},
    {"id": "bloch-sphere", "title": "布洛赫球直觉", "module": "直觉：理解量子现象", "difficulty": "基础"},
    {"id": "single-qubit-gates", "title": "单量子比特门", "module": "线路：从门到电路", "difficulty": "基础"},
    {"id": "multi-qubit-and-cnot", "title": "多比特门与 CNOT", "module": "线路：从门到电路", "difficulty": "基础"},
    {"id": "bell-state", "title": "Bell 态与量子纠缠", "module": "线路：从门到电路", "difficulty": "进阶"},
    {"id": "read-a-circuit", "title": "如何读懂量子线路", "module": "线路：从门到电路", "difficulty": "基础"},
    {"id": "deutsch-jozsa", "title": "Deutsch–Jozsa 算法", "module": "算法：看见干涉的用途", "difficulty": "进阶"},
    {"id": "grover-search", "title": "Grover 搜索", "module": "算法：看见干涉的用途", "difficulty": "进阶"},
    {"id": "variational-algorithms", "title": "变分量子算法", "module": "算法：看见干涉的用途", "difficulty": "进阶"},
    {"id": "shor-overview", "title": "Shor 算法概览", "module": "算法：看见干涉的用途", "difficulty": "进阶"},
    {"id": "qiskit-first-step", "title": "Qiskit 第一步", "module": "实践：把线路运行起来", "difficulty": "入门"},
    {"id": "first-bell-circuit", "title": "动手搭建 Bell 线路", "module": "实践：把线路运行起来", "difficulty": "基础"},
    {"id": "noise-and-fidelity", "title": "噪声与保真度", "module": "实践：把线路运行起来", "difficulty": "进阶"},
    {"id": "quantum-hacker-guide", "title": "《量子小丑牌》知识指南", "module": "游戏实验场", "difficulty": "应用"},
    {"id": "roulette-and-measurement", "title": "轮盘与量子测量", "module": "游戏实验场", "difficulty": "应用"},
    {"id": "quantum-mage-map", "title": "《量子魔法师》概念地图", "module": "游戏实验场", "difficulty": "应用"},
]

CONCEPT_BY_ID = {concept["id"]: concept for concept in CONCEPT_CATALOG}
