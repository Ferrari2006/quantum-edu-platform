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
    if boss_type == "DECOHERENCE":
        q0_count = sum(1 for g in gate_sequence if g[1] == 0)
        q1_count = sum(1 for g in gate_sequence if g[1] == 1)
        if q0_count > limit or q1_count > limit:
            return False, f"HARDWARE LIMIT: Max {limit} gates per line!"
    return True, ""

def calculate_score(probs, target_probs, gate_sequence, active_jokers):
    base_chips = 0
    for state, target_p in target_probs.items():
        base_chips += min(probs.get(state, 0), target_p) * 200
        
    gate_names = [g[0] for g in gate_sequence]
    if "ENTANGLE" in active_jokers and "CNOT" in gate_names:
        base_chips += 100
        
    mult = 1.0
    for g in gate_names:
        if g == "H": mult *= 1.5
        if g == "Z" and "PHASE" in active_jokers: mult *= 1.5
    if "CNOT" in gate_names: mult *= 2.0
    return int(base_chips), round(mult, 2)