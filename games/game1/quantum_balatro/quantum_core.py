"""
quantum_core.py
核心算法层：负责 Qiskit 量子线路演化、Boss 规则约束以及分数计算。
"""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

simulator = AerSimulator()

LEVELS = [
    {
        "name": "Small Blind",
        "target": 1500,
        "boss_type": "NONE",
        "desc": "Target: Pure State |00>. Simple and clean.",
        "target_probs": {"00": 1.0},
        "reward": 3  # 基础奖励 3 块钱
    },
    {
        "name": "Big Blind",
        "target": 8000,
        "boss_type": "NONE",
        "desc": "Target: Phi+ Bell State. Requires H + CNOT.",
        "target_probs": {"00": 0.5, "11": 0.5},
        "reward": 5  # 基础奖励 5 块钱
    },
    {
        "name": "Boss: Decoherence",
        "target": 20000,
        "boss_type": "DECOHERENCE",
        "desc": "Target: Psi+ State (Anti-correlated). Try H -> CNOT -> X(q1).",
        "target_probs": {"01": 0.5, "10": 0.5},
        "reward": 8
    },
    {
        "name": "Boss: Phase Lock",
        "target": 26000,
        "boss_type": "PHASE_LOCK",
        "desc": "Target: |01>. At least one Z gate must be staged before scoring.",
        "target_probs": {"01": 1.0},
        "reward": 9
    },
    {
        "name": "Boss: Entangler",
        "target": 34000,
        "boss_type": "ENTANGLER",
        "desc": "Target: uniform anti-noise. You must use CNOT exactly once.",
        "target_probs": {"00": 0.25, "01": 0.25, "10": 0.25, "11": 0.25},
        "reward": 10
    },
    {
        "name": "Boss: Sparse Memory",
        "target": 42000,
        "boss_type": "SPARSE_MEMORY",
        "desc": "Target: mostly |10>. No more than 4 gates may be staged.",
        "target_probs": {"10": 0.75, "11": 0.25},
        "reward": 12
    }
]

def get_quantum_probs(gate_sequence):
    qc = QuantumCircuit(2)
    for gate, qubit_idx in gate_sequence:
        if gate == "H": qc.h(qubit_idx)
        elif gate == "X": qc.x(qubit_idx)
        elif gate == "Z": qc.z(qubit_idx)
        elif gate == "CNOT": qc.cx(qubit_idx, 1 - qubit_idx)
    qc.save_statevector()
    try:
        result = simulator.run(qc).result()
        return result.get_statevector().probabilities_dict()
    except Exception: return {"00": 1.0}

def check_boss_constraints(gate_sequence, boss_type, active_jokers):
    limit = 3 if "TOPOLOGY" in active_jokers else 2
    gate_names = [g[0] for g in gate_sequence]
    if boss_type == "DECOHERENCE":
        q0_count = sum(1 for g in gate_sequence if g[1] == 0)
        q1_count = sum(1 for g in gate_sequence if g[1] == 1)
        if q0_count > limit or q1_count > limit:
            return False, f"HARDWARE LIMIT: Max {limit} gates per line!"
    if boss_type == "PHASE_LOCK" and "Z" not in gate_names and "PHASE_BYPASS" not in active_jokers:
        return False, "PHASE LOCK: Stage at least one Z gate, or activate Phase Key."
    if boss_type == "ENTANGLER" and gate_names.count("CNOT") != 1 and "ENTANGLE_STABILIZER" not in active_jokers:
        return False, "ENTANGLER: Use CNOT exactly once, or activate Stabilizer."
    max_gates = 5 if "COMPRESSION" in active_jokers else 4
    if boss_type == "SPARSE_MEMORY" and len(gate_sequence) > max_gates:
        return False, f"SPARSE MEMORY: Max {max_gates} staged gates."
    return True, ""

def calculate_score_details(probs, target_probs, gate_sequence, active_jokers, circuit_depth=None):
    """以目标匹配质量为主、线路深度为成本计算得分。"""
    match_quality = sum(
        min(float(probs.get(state, 0.0)), float(target_probability))
        for state, target_probability in target_probs.items()
    )
    match_quality = max(0.0, min(1.0, match_quality))
    gate_names = [g[0] for g in gate_sequence]
    joker_chips = 0
    if "ENTANGLE" in active_jokers and "CNOT" in gate_names:
        joker_chips += 100
    if "MEASURE" in active_jokers and len(target_probs) == 1:
        joker_chips += 80
    if "BALANCER" in active_jokers and len(target_probs) == 4:
        joker_chips += 120

    # 奖励也受匹配质量约束，避免靠 Joker 在错误线路上硬刷分。
    chips = int((300 + joker_chips) * match_quality)
    quality_mult = 1.0 + 4.0 * (match_quality ** 2)
    depth = len(gate_sequence) if circuit_depth is None else max(0, int(circuit_depth))
    depth_decay = 0.93 if "COMPRESSION" in active_jokers else 0.85
    depth_efficiency = depth_decay ** depth
    joker_mult = 1.0
    if "PHASE" in active_jokers and "Z" in gate_names:
        joker_mult *= 1.25
    if "COMPRESSION" in active_jokers and depth <= 3:
        joker_mult *= 1.15
    mult = quality_mult * depth_efficiency * joker_mult
    return {
        "chips": chips,
        "mult": round(mult, 3),
        "match_quality": round(match_quality, 4),
        "quality_mult": round(quality_mult, 3),
        "circuit_depth": depth,
        "depth_efficiency": round(depth_efficiency, 3),
    }


def calculate_score(probs, target_probs, gate_sequence, active_jokers, circuit_depth=None):
    details = calculate_score_details(
        probs,
        target_probs,
        gate_sequence,
        active_jokers,
        circuit_depth,
    )
    return details["chips"], details["mult"]
