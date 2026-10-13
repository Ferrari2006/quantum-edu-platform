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

# The first prerequisite graph is intentionally small and acyclic. A concept is
# considered ready when every listed prerequisite has at least developing mastery.
CONCEPT_PREREQUISITES: dict[str, list[str]] = {
    "classical-bit-and-qubit": ["what-is-quantum-computing"],
    "superposition": ["classical-bit-and-qubit"],
    "phase-and-interference": ["superposition"],
    "measurement": ["classical-bit-and-qubit"],
    "bloch-sphere": ["classical-bit-and-qubit"],
    "single-qubit-gates": ["superposition"],
    "multi-qubit-and-cnot": ["single-qubit-gates"],
    "bell-state": ["superposition", "multi-qubit-and-cnot"],
    "read-a-circuit": ["single-qubit-gates"],
    "deutsch-jozsa": ["phase-and-interference", "read-a-circuit"],
    "grover-search": ["phase-and-interference", "read-a-circuit"],
    "variational-algorithms": ["bloch-sphere", "read-a-circuit"],
    "shor-overview": ["phase-and-interference", "read-a-circuit"],
    "qiskit-first-step": ["read-a-circuit"],
    "first-bell-circuit": ["qiskit-first-step", "bell-state"],
    "noise-and-fidelity": ["qiskit-first-step"],
    "quantum-hacker-guide": ["single-qubit-gates"],
    "roulette-and-measurement": ["measurement"],
    "quantum-mage-map": ["multi-qubit-and-cnot", "bloch-sphere"],
}

LAB_CONCEPTS = {
    "superposition",
    "phase-and-interference",
    "measurement",
    "bloch-sphere",
    "single-qubit-gates",
    "multi-qubit-and-cnot",
    "bell-state",
    "read-a-circuit",
    "qiskit-first-step",
    "first-bell-circuit",
    "noise-and-fidelity",
}

# Concepts with a guided circuit task should open a concrete experiment instead of
# dropping the learner onto an empty canvas. Other lab-capable concepts still use
# the generic lab route until a reviewed task is available.
LAB_TASK_BY_CONCEPT = {
    "superposition": "hadamard-superposition",
    "phase-and-interference": "phase-interference",
    "single-qubit-gates": "bit-flip",
    "multi-qubit-and-cnot": "ghz-chain",
    "bell-state": "bell-pair",
    "first-bell-circuit": "bell-pair",
}

GUIDED_LAB_TASKS = [
    {"id": "hadamard-superposition", "concept_id": "superposition"},
    {"id": "bit-flip", "concept_id": "single-qubit-gates"},
    {"id": "phase-interference", "concept_id": "phase-and-interference"},
    {"id": "bell-pair", "concept_id": "bell-state"},
    {"id": "ghz-chain", "concept_id": "multi-qubit-and-cnot"},
]

GAME_CONCEPTS = {
    "quantum-hacker-guide",
    "roulette-and-measurement",
    "quantum-mage-map",
}

AI_PRACTICE_CONCEPTS = {
    "deutsch-jozsa",
    "grover-search",
    "variational-algorithms",
    "shor-overview",
}
