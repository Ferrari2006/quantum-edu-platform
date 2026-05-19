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

def calculate_score(probs, target_probs, gate_sequence, active_jokers):
    base_chips = 0
    for state, target_p in target_probs.items():
        base_chips += min(probs.get(state, 0), target_p) * 200
        
    gate_names = [g[0] for g in gate_sequence]
    if "ENTANGLE" in active_jokers and "CNOT" in gate_names:
        base_chips += 100
    if "MEASURE" in active_jokers and len(target_probs) == 1:
        base_chips += 80
    if "BALANCER" in active_jokers and len(target_probs) == 4:
        base_chips += 120
        
    mult = 1.0
    for g in gate_names:
        if g == "H": mult *= 1.5
        if g == "Z" and "PHASE" in active_jokers: mult *= 1.5
    if "CNOT" in gate_names: mult *= 2.0
    if "COMPRESSION" in active_jokers and len(gate_sequence) <= 3:
        mult *= 1.8
    return int(base_chips), round(mult, 2)
