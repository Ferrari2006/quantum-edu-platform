from quantum_core import LEVELS, calculate_score, get_quantum_probs


def run():
    gate_sequence = [("H", 0), ("CNOT", 0)]
    probs = get_quantum_probs(gate_sequence)
    probs = {str(k): float(v) for k, v in probs.items()}
    level = LEVELS[1]
    chips, mult = calculate_score(probs, level["target_probs"], gate_sequence, active_jokers=set())
    return {"probs": probs, "chips": chips, "mult": mult}


if __name__ == "__main__":
    print(run())
