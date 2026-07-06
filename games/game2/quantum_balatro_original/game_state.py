import math
import random
import cmath
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, concurrence, partial_trace, state_fidelity

CARD_BLIND_EVENTS = [
    {
        "id": "CALIBRATION_DRIFT",
        "name": "Calibration Drift",
        "desc": "The first played H this blind grants +2 multiplier.",
    },
    {
        "id": "NOISY_HARDWARE",
        "name": "Noisy Hardware",
        "desc": "Hands with more than 3 cards lose 18% fidelity.",
    },
    {
        "id": "CHEAP_MEASUREMENT",
        "name": "Cheap Measurement",
        "desc": "The first measured hand gains +0.10 fidelity.",
    },
    {
        "id": "PHASE_EXPERIMENT",
        "name": "Phase Experiment",
        "desc": "Z/CZ/RZ cards grant +35 chips each.",
    },
    {
        "id": "ENTANGLEMENT_TAX",
        "name": "Entanglement Tax",
        "desc": "CNOT grants +90 chips, then consumes $2 chips.",
    },
]

CARD_BONUS_OBJECTIVES = [
    {
        "id": "LOW_GATE_CLEAR",
        "name": "Minimal Circuit",
        "desc": "Clear this blind with no more than 3 played cards.",
        "reward": 3,
    },
    {
        "id": "HIGH_FIDELITY",
        "name": "Clean State",
        "desc": "Reach at least 90% fidelity in a scoring hand.",
        "reward": 3,
    },
    {
        "id": "NO_CNOT_CLEAR",
        "name": "No Entangler",
        "desc": "Clear this blind without CNOT in the scoring hand.",
        "reward": 3,
    },
    {
        "id": "Z_SCORE",
        "name": "Phase Marker",
        "desc": "Use Z, CZ, or RZ in a scoring hand.",
        "reward": 2,
    },
    {
        "id": "BELL_PAIR",
        "name": "Bell Trigger",
        "desc": "Trigger a Bell Pair hand.",
        "reward": 3,
    },
    {
        "id": "TWO_HAND_CLIMB",
        "name": "Momentum",
        "desc": "Score higher than the previous hand twice in a row.",
        "reward": 3,
    },
]

# ==========================================
# 1. 实体定义：卡牌系统 (Cards)
# ==========================================
class Card:
    def __init__(self, name, gate_type, rarity='blue', lesson='', target_count=None):
        self.name = name
        self.gate_type = gate_type 
        self.rarity = rarity       
        self.durability = 3 if rarity == 'purple' else -1
        self.is_broken = False
        self.lesson = lesson
        self.target_count = target_count if target_count is not None else (2 if gate_type in ['CNOT', 'CX', 'CZ', 'SWAP'] else 1)
        # --- 新增属性 ---
        self.is_new = False  # 标记是否为刚买的新卡
        
    def use(self, state):
        if self.rarity == 'gold':
            if state.chips >= 5:
                state.chips -= 5
            else:
                return False 
        elif self.rarity == 'purple' and not self.is_broken:
            self.durability -= 1
            if self.durability <= 0:
                self.is_broken = True
                self.name = "退相干的 " + self.name
                if self.gate_type == 'RX':
                    self.gate_type = 'X' 
        elif self.rarity == 'blue':
            state.discard_pile.append(Card("量子噪声", "NOISE", "grey"))
        return True

# ==========================================
# 2. 事件监听：小丑牌系统 (Jokers)
# ==========================================
class Joker:
    def __init__(self, name, desc):
        self.name = name
        self.description = desc

    def on_play_gate(self, gate_type, state):
        pass

    def on_calculate_score(self, current_chips, current_mult, state):
        return current_chips, current_mult

class MaxwellDemonJoker(Joker):
    def __init__(self):
        super().__init__("麦克斯韦妖", "每次打出双比特门(CNOT/SWAP)，筹码+15")

    def on_play_gate(self, gate_type, state):
        if gate_type in ['CNOT', 'SWAP']:
            state.chips += 15

class SchrodingerCatJoker(Joker):
    def __init__(self):
        super().__init__("薛定谔的猫", "每次结算时，每保留1次出牌机会，倍率+0.5")
        self.bonus_per_play = 0.5

    def on_calculate_score(self, current_chips, current_mult, state):
        bonus_mult = state.plays_left * self.bonus_per_play
        return current_chips, current_mult + bonus_mult

class PhaseKickbackJoker(Joker):
    def __init__(self):
        super().__init__("Phase Kickback", "Z/CZ/RZ cards add +12 mult during scoring")

    def on_calculate_score(self, current_chips, current_mult, state):
        phase_count = sum(1 for gate in getattr(state, "last_played_gate_types", []) if gate in ['Z', 'CZ', 'RZ'])
        return current_chips, current_mult + phase_count * 12

class RotationCompilerJoker(Joker):
    def __init__(self):
        super().__init__("Rotation Compiler", "RX/RY/RZ cards add +25 chips")

    def on_calculate_score(self, current_chips, current_mult, state):
        rotation_count = sum(1 for gate in getattr(state, "last_played_gate_types", []) if gate in ['RX', 'RY', 'RZ'])
        return current_chips + rotation_count * 25, current_mult

class TopologyBonusJoker(Joker):
    def __init__(self):
        super().__init__("Topology Bonus", "SWAP/CZ/CCX hands gain x2 mult")

    def on_calculate_score(self, current_chips, current_mult, state):
        if any(gate in ['SWAP', 'CZ', 'CCX'] for gate in getattr(state, "last_played_gate_types", [])):
            return current_chips, current_mult * 2
        return current_chips, current_mult

# ==========================================
# 3. 核心中枢：游戏状态机 (GameState)
# ==========================================
class GameState:
    def __init__(self, backend=None):
        self.backend = backend 
        
        # --- 基础资源 ---
        self.chips = 0             
        self.deck = self._init_deck()
        self.hand = []
        self.discard_pile = []
        self.jokers = []           
        
        # --- 关卡进度控制 ---
        self.ante = 1              
        self.blind_sequence = ['Small', 'Big', 'Boss']
        self.blind_index = 0       
        self.num_qubits = 3        
        self.phase = 'PLAYING'     
        
        # --- 商店与结算记录 ---
        self.shop_jokers = []  
        self.shop_pack = False 
        self.shop_joker_pack = False
        self.opened_card = None
        self.opened_joker_choices = []
        self.last_payout = {'base': 0, 'plays': 0, 'total': 0}
        self.last_score_breakdown = {
            'hand': 'None',
            'base_chips': 0,
            'base_mult': 0,
            'fidelity': 0.0,
            'joker_chips_delta': 0,
            'joker_mult_delta': 0,
            'score': 0,
            'event_note': ''
        }
        
        # --- 当前游玩状态 ---
        self.max_plays = 4
        self.max_discards = 3
        self.plays_left = self.max_plays
        self.discards_left = self.max_discards
        self.current_score = 0
        self.target_score = 0
        # --- 新增：实时预览数据 ---
        self.preview_hand_name = "None"
        self.preview_score = 0
        self.preview_fidelity = 0.0
        self.last_played_gate_types = []
        self.blind_event = random.choice(CARD_BLIND_EVENTS)
        self.event_used = False
        self.last_event_result = ""
        self.bonus_objective = random.choice(CARD_BONUS_OBJECTIVES)
        self.bonus_complete = False
        self.bonus_reward_claimed = False
        self.last_hand_score_value = 0
        self.score_climb_streak = 0
        self.recommendation_used = False
        self.recommendation_text = ""
        self.recommendation_gates = []
        
        # --- 量子牌型定义 (Base Chips x Base Mult) ---
        self.poker_hands = {
            "GHZ State (同花顺)": {"chips": 120, "mult": 12},
            "Full House (满堂红)": {"chips": 90, "mult": 8},
            "W State (三条)": {"chips": 70, "mult": 6},
            "Flush (均匀叠加)": {"chips": 50, "mult": 5},
            "Bell Pair (纠缠对)": {"chips": 30, "mult": 3},
            "High Qubit (高牌)": {"chips": 10, "mult": 2}
        }
        self.poker_hands.update({
            "Toffoli Cascade": {"chips": 180, "mult": 16},
            "Swap Network": {"chips": 150, "mult": 13},
            "Phase Lock": {"chips": 105, "mult": 10},
            "Rotation Trio": {"chips": 80, "mult": 7},
        })
        self.hand_catalog = [
            {"name": name, "chips": stats["chips"], "mult": stats["mult"]}
            for name, stats in self.poker_hands.items()
        ]
        self.pack_catalog = [
            {"type": "phase", "name": "Phase Pack", "desc": "Adds Z/CZ/RZ cards for phase-interference hands."},
            {"type": "rotation", "name": "Rotation Pack", "desc": "Adds RX/RY/RZ cards that teach continuous rotations."},
            {"type": "entangle", "name": "Entangle Pack", "desc": "Adds CNOT/CZ/SWAP cards for explicit two-qubit targeting."},
            {"type": "control", "name": "Control Pack", "desc": "Adds a rare CCX card for late-game control logic."},
        ]
        self.current_lesson = {
            "title": "Stage a quantum poker hand",
            "body": "Drag cards into time slots. Controlled gates use the source row plus the selected target row, so CNOT direction matters.",
        }
        self.last_hand_played = "None"
        
        self.start_new_blind()
        # 新手教程标记：第一次进入游戏时展示
        self.seen_tutorial = False

    def _init_deck(self):
        deck = []
        for _ in range(5):
            deck.append(Card("哈达玛门 (H)", "H", "normal"))
            deck.append(Card("泡利X门 (X)", "X", "normal"))
        deck.append(Card("受控非门 (CNOT)", "CNOT", "normal"))
        deck.append(Card("粗糙的相位门", "RX", "blue")) 
        for _ in range(2):
            deck.append(Card("Pauli-Z Gate (Z)", "Z", "normal", "Changes phase without changing measurement probability."))
        deck.append(Card("Controlled-Z (CZ)", "CZ", "blue", "Adds a conditional phase between two selected qubits.", 2))
        random.shuffle(deck)
        return deck

    def reset_game(self):
        """完全重置游戏，用于 RESTART"""
        self.chips = 0
        self.deck = self._init_deck()
        self.hand = []
        self.discard_pile = []
        self.jokers = []
        self.ante = 1
        self.blind_index = 0
        self.num_qubits = 3
        self.last_fidelity = 0.0
        self.blind_event = random.choice(CARD_BLIND_EVENTS)
        self.event_used = False
        self.last_event_result = ""
        self.bonus_objective = random.choice(CARD_BONUS_OBJECTIVES)
        self.bonus_complete = False
        self.bonus_reward_claimed = False
        self.last_hand_score_value = 0
        self.score_climb_streak = 0
        self.recommendation_used = False
        self.recommendation_text = ""
        self.recommendation_gates = []
        if self.backend: self.backend.upgrade_qubits(3)
        self.start_new_blind()

    def draw_cards(self, num):
        for _ in range(num):
            if not self.deck:
                if not self.discard_pile: break 
                self.deck = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.deck)
            self.hand.append(self.deck.pop())

    def ensure_blind_event(self):
        if not hasattr(self, "blind_event") or not self.blind_event:
            self.blind_event = random.choice(CARD_BLIND_EVENTS)
        if not hasattr(self, "event_used"):
            self.event_used = False
        if not hasattr(self, "last_event_result"):
            self.last_event_result = ""

    def ensure_bonus_objective(self):
        if not hasattr(self, "bonus_objective") or not self.bonus_objective:
            self.bonus_objective = random.choice(CARD_BONUS_OBJECTIVES)
        if not hasattr(self, "bonus_complete"):
            self.bonus_complete = False
        if not hasattr(self, "bonus_reward_claimed"):
            self.bonus_reward_claimed = False
        if not hasattr(self, "last_hand_score_value"):
            self.last_hand_score_value = 0
        if not hasattr(self, "score_climb_streak"):
            self.score_climb_streak = 0

    def ensure_recommendation(self):
        if not hasattr(self, "recommendation_used"):
            self.recommendation_used = False
        if not hasattr(self, "recommendation_text"):
            self.recommendation_text = ""
        if not hasattr(self, "recommendation_gates"):
            self.recommendation_gates = []

    def recommend_play(self):
        self.ensure_recommendation()
        if self.phase != 'PLAYING':
            return {"text": self.recommendation_text, "gates": self.recommendation_gates}
        if self.recommendation_used:
            return {"text": self.recommendation_text, "gates": self.recommendation_gates}

        gates = [card.gate_type for card in self.hand]
        shadow_gates = []
        if "H" in gates and "CNOT" in gates:
            shadow_gates = [
                {"gate": "H", "qubit": 0, "slot": 0},
                {"gate": "CNOT", "qubit": 0, "slot": 1, "targets": [0, 1]},
            ]
            text = "想触发 Bell Pair：先把 H 放进 q0 的前面插槽，再把 CNOT 放在后面，让它控制另一条线。"
        elif "H" in gates:
            shadow_gates = [{"gate": "H", "qubit": 0, "slot": 0}]
            text = "想让多个测量结果出现：先把 H 放在 q0。它会把确定态拆成叠加态。"
        elif any(gate in gates for gate in ["Z", "CZ", "RZ"]):
            gate = next(gate for gate in ["Z", "CZ", "RZ"] if gate in gates)
            shadow_gates = [{"gate": gate, "qubit": 0, "slot": 0}]
            text = "手里有相位门：如果有相位事件或 Phase 牌型目标，可以先放 Z/CZ/RZ 争取额外奖励。"
        elif "X" in gates:
            shadow_gates = [{"gate": "X", "qubit": 0, "slot": 0}]
            text = "目标需要出现 1 时：把 X 放在对应量子比特上，它会把 |0> 翻成 |1>。"
        else:
            shadow_gates = [{"gate": "KEEP", "qubit": 0, "slot": 0}]
            text = "这手先保守：少放牌、保持线路干净，等抽到 H 或 CNOT 再做更强牌型。"

        self.recommendation_used = True
        self.recommendation_text = text
        self.recommendation_gates = shadow_gates
        return {"text": text, "gates": shadow_gates}

    def update_bonus_objective(self, gate_types, hand_name, fidelity, hand_score, cleared):
        self.ensure_bonus_objective()
        objective_id = self.bonus_objective["id"]
        if self.last_hand_score_value and hand_score > self.last_hand_score_value:
            self.score_climb_streak += 1
        elif self.last_hand_score_value:
            self.score_climb_streak = 0
        self.last_hand_score_value = hand_score

        if objective_id == "LOW_GATE_CLEAR" and cleared and len(gate_types) <= 3:
            self.bonus_complete = True
        elif objective_id == "HIGH_FIDELITY" and fidelity >= 0.9:
            self.bonus_complete = True
        elif objective_id == "NO_CNOT_CLEAR" and cleared and "CNOT" not in gate_types:
            self.bonus_complete = True
        elif objective_id == "Z_SCORE" and hand_score > 0 and any(gate in ["Z", "CZ", "RZ"] for gate in gate_types):
            self.bonus_complete = True
        elif objective_id == "BELL_PAIR" and hand_name.startswith("Bell Pair"):
            self.bonus_complete = True
        elif objective_id == "TWO_HAND_CLIMB" and self.score_climb_streak >= 2:
            self.bonus_complete = True

    def claim_bonus_reward(self):
        self.ensure_bonus_objective()
        if not self.bonus_complete or self.bonus_reward_claimed:
            return 0
        reward = int(self.bonus_objective.get("reward", 0))
        self.chips += reward
        self.bonus_reward_claimed = True
        return reward

    def apply_blind_event(self, gate_types, chips, mult, fidelity, commit=False):
        self.ensure_blind_event()
        event_id = self.blind_event["id"]
        note = ""
        chip_cost = 0

        if event_id == "CALIBRATION_DRIFT" and "H" in gate_types and not self.event_used:
            mult += 2
            note = "+2 mult from first H"
            if commit:
                self.event_used = True
        elif event_id == "NOISY_HARDWARE" and len(gate_types) > 3:
            fidelity = max(0.0, fidelity * 0.82)
            note = "-18% fidelity after 3 cards"
        elif event_id == "CHEAP_MEASUREMENT" and not self.event_used:
            fidelity = min(1.0, fidelity + 0.10)
            note = "+0.10 fidelity from cheap measurement"
            if commit:
                self.event_used = True
        elif event_id == "PHASE_EXPERIMENT":
            phase_count = sum(1 for gate in gate_types if gate in ["Z", "CZ", "RZ"])
            if phase_count:
                chips += 35 * phase_count
                note = f"+{35 * phase_count} chips from phase cards"
        elif event_id == "ENTANGLEMENT_TAX" and "CNOT" in gate_types:
            cnot_count = gate_types.count("CNOT")
            chips += 90 * cnot_count
            chip_cost = 2
            note = f"+{90 * cnot_count} chips from CNOT, -$2 chips"

        if commit and chip_cost:
            self.chips = max(0, self.chips - chip_cost)
        return chips, mult, fidelity, note

    def start_new_blind(self):
        if self.ante >= 3 and self.num_qubits == 3:
            self.num_qubits = 5
            if self.backend: self.backend.upgrade_qubits(5)
                
        self.plays_left = self.max_plays
        self.discards_left = self.max_discards
        self.current_score = 0
        self.last_hand_played = "None"
        self.last_fidelity = 0.0
        self.last_played_gate_types = []
        self.blind_event = random.choice(CARD_BLIND_EVENTS)
        self.event_used = False
        self.last_event_result = ""
        self.bonus_objective = random.choice(CARD_BONUS_OBJECTIVES)
        self.bonus_complete = False
        self.bonus_reward_claimed = False
        self.last_hand_score_value = 0
        self.score_climb_streak = 0
        self.recommendation_used = False
        self.recommendation_text = ""
        self.recommendation_gates = []
        self.last_score_breakdown = {
            'hand': 'None',
            'base_chips': 0,
            'base_mult': 0,
            'fidelity': 0.0,
            'joker_chips_delta': 0,
            'joker_mult_delta': 0,
            'score': 0,
            'event_note': ''
        }
        
        base = 300
        multiplier = 1.5 ** (self.ante - 1)
        if self.blind_index == 1: multiplier *= 1.5
        if self.blind_index == 2: multiplier *= 2.0
        self.target_score = int(base * multiplier)
        
        if self.backend: self.backend.reset_circuit()
            
        self.discard_pile.extend(self.hand)
        self.hand.clear()
        
        self.draw_cards(5)
        self.phase = 'PLAYING'
    
    def update_preview(self, staged_indices, target_qubits_list=None, slot_indices=None):
        """实时计算预览分数，不消耗实际出牌次数"""
        if not staged_indices:
            self.preview_hand_name, self.preview_score, self.preview_fidelity = "None", 0, 0.0
            return
        if target_qubits_list is None:
            target_qubits_list = [[0] for _ in staged_indices]
        preview = self.preview_hand(staged_indices, target_qubits_list, slot_indices=slot_indices)
        self.preview_hand_name = preview.get('hand', 'None')
        self.preview_score = preview.get('score', 0)
        self.preview_fidelity = preview.get('fidelity', 0.0)

    def _hand_key(self, prefix):
        return next(key for key in self.poker_hands if key.startswith(prefix))

    def _normalize_operations(self, operations):
        normalized = []
        for operation in operations:
            if isinstance(operation, str):
                normalized.append({'gate': operation.upper(), 'targets': []})
            else:
                normalized.append({
                    'gate': str(operation.get('gate', '')).upper(),
                    'targets': list(operation.get('targets', [])),
                })
        return normalized

    def _state_probabilities(self, state):
        if state is None:
            return []
        return [float(abs(amplitude) ** 2) for amplitude in state.data]

    def _qubit_one_probability(self, probabilities, qubit):
        return sum(
            probability
            for basis_index, probability in enumerate(probabilities)
            if (basis_index >> qubit) & 1
        )

    def _single_qubit_purity(self, state, qubit):
        if state is None:
            return 1.0
        rho00 = 0.0
        rho11 = 0.0
        rho01 = 0j
        step = 1 << qubit
        for basis_index in range(len(state.data)):
            if basis_index & step:
                continue
            zero_amplitude = state.data[basis_index]
            one_amplitude = state.data[basis_index | step]
            rho00 += abs(zero_amplitude) ** 2
            rho11 += abs(one_amplitude) ** 2
            rho01 += zero_amplitude * one_amplitude.conjugate()
        return float(rho00 ** 2 + rho11 ** 2 + 2 * abs(rho01) ** 2)

    def _has_relative_phase(self, state):
        if state is None:
            return False
        nonzero = [amplitude for amplitude in state.data if abs(amplitude) > 1e-7]
        if len(nonzero) < 2:
            return False
        reference_phase = cmath.phase(nonzero[0])
        return any(
            abs(math.sin(cmath.phase(amplitude) - reference_phase)) > 1e-5
            or math.cos(cmath.phase(amplitude) - reference_phase) < 0.999
            for amplitude in nonzero[1:]
        )

    def _bell_candidate(self, operations, final_state=None):
        superposed = set()
        for operation in operations:
            gate = operation['gate']
            targets = operation['targets']
            if gate in ['H', 'RX', 'RY'] and targets:
                superposed.add(targets[0])
                continue
            if gate not in ['CNOT', 'CX', 'CZ'] or len(targets) < 2:
                continue
            source, target = targets[:2]
            prepared = source in superposed if gate in ['CNOT', 'CX'] else source in superposed and target in superposed
            if not prepared:
                continue
            if final_state is None:
                return operation
            try:
                traced_out = [
                    qubit
                    for qubit in range(self.num_qubits)
                    if qubit not in [source, target]
                ]
                pair_state = partial_trace(final_state, traced_out)
                if float(concurrence(pair_state)) > 0.1:
                    return operation
            except Exception:
                if self._single_qubit_purity(final_state, source) < 0.98 and self._single_qubit_purity(final_state, target) < 0.98:
                    return operation
        return None

    def _is_ghz_circuit(self, operations, final_state):
        if self.num_qubits < 3 or final_state is None:
            return False
        for h_index, h_operation in enumerate(operations):
            if h_operation['gate'] != 'H' or not h_operation['targets']:
                continue
            reached = {h_operation['targets'][0]}
            for operation in operations[h_index + 1:]:
                if operation['gate'] not in ['CNOT', 'CX'] or len(operation['targets']) < 2:
                    continue
                control, target = operation['targets'][:2]
                if control in reached:
                    reached.add(target)
            if len(reached) != self.num_qubits:
                continue
            probabilities = self._state_probabilities(final_state)
            endpoint_probability = probabilities[0] + probabilities[-1]
            if endpoint_probability > 0.98 and 0.4 <= probabilities[0] <= 0.6 and 0.4 <= probabilities[-1] <= 0.6:
                return True
        return False

    def _is_w_state(self, final_state):
        probabilities = self._state_probabilities(final_state)
        if not probabilities:
            return False
        populated = [
            probability
            for basis_index, probability in enumerate(probabilities)
            if basis_index.bit_count() == 1 and probability > 0.05
        ]
        single_excitation_total = sum(
            probability
            for basis_index, probability in enumerate(probabilities)
            if basis_index.bit_count() == 1
        )
        return len(populated) >= 3 and single_excitation_total > 0.98 and max(populated) - min(populated) < 0.08

    def _is_uniform_superposition(self, final_state):
        probabilities = self._state_probabilities(final_state)
        if not probabilities:
            return False
        expected = 1 / len(probabilities)
        return all(abs(probability - expected) < 0.015 for probability in probabilities)

    def _classify_hand(self, operations, final_state=None):
        operations = self._normalize_operations(operations)
        gates = [operation['gate'] for operation in operations]
        probabilities = self._state_probabilities(final_state)

        for index, operation in enumerate(operations):
            if operation['gate'] not in ['CCX', 'TOFFOLI'] or len(operation['targets']) < 3 or not probabilities:
                continue
            controls = operation['targets'][:2]
            target = operation['targets'][2]
            prepared_controls = {
                earlier['targets'][0]
                for earlier in operations[:index]
                if earlier['gate'] in ['X', 'H', 'RX', 'RY'] and earlier['targets']
            }
            if set(controls) <= prepared_controls and self._qubit_one_probability(probabilities, target) > 0.05:
                return self._hand_key("Toffoli Cascade")

        if self._is_ghz_circuit(operations, final_state):
            return self._hand_key("GHZ State")
        if self._is_w_state(final_state) and len(operations) >= 3:
            return self._hand_key("W State")

        has_swap = any(operation['gate'] == 'SWAP' for operation in operations)
        has_entangler = any(operation['gate'] in ['CNOT', 'CX', 'CZ'] for operation in operations)
        if has_swap and has_entangler and any(
            self._single_qubit_purity(final_state, qubit) < 0.98
            for qubit in range(self.num_qubits)
        ):
            return self._hand_key("Swap Network")

        phase_operations = [operation for operation in operations if operation['gate'] in ['Z', 'CZ', 'RZ']]
        if len(phase_operations) >= 2 and self._has_relative_phase(final_state):
            return self._hand_key("Phase Lock")

        if self._bell_candidate(operations, final_state) is not None:
            return self._hand_key("Bell Pair")

        rotation_operations = [operation for operation in operations if operation['gate'] in ['RX', 'RY', 'RZ']]
        if len(rotation_operations) >= 3 and len({operation['gate'] for operation in rotation_operations}) >= 2:
            if probabilities and max(probabilities) < 0.98:
                return self._hand_key("Rotation Trio")

        if len(operations) > 1 and gates and all(gate == 'H' for gate in gates) and self._is_uniform_superposition(final_state):
            return self._hand_key("Flush")

        h_targets = {
            operation['targets'][0]
            for operation in operations
            if operation['gate'] == 'H' and operation['targets']
        }
        x_targets = {
            operation['targets'][0]
            for operation in operations
            if operation['gate'] == 'X' and operation['targets']
        }
        if probabilities and h_targets and x_targets and any(h_target != x_target for h_target in h_targets for x_target in x_targets):
            has_balanced = any(0.45 <= self._qubit_one_probability(probabilities, qubit) <= 0.55 for qubit in h_targets)
            has_deterministic_one = any(self._qubit_one_probability(probabilities, qubit) >= 0.98 for qubit in x_targets)
            if has_balanced and has_deterministic_one:
                return self._hand_key("Full House")

        return self._hand_key("High Qubit")

    def _apply_operation_to_circuit(self, circuit, operation):
        gate = operation['gate']
        targets = operation['targets']
        if not targets:
            return
        if gate == 'H': circuit.h(targets[0])
        elif gate == 'X': circuit.x(targets[0])
        elif gate == 'Y': circuit.y(targets[0])
        elif gate == 'Z': circuit.z(targets[0])
        elif gate == 'RX': circuit.rx(math.pi / 2, targets[0])
        elif gate == 'RY': circuit.ry(math.pi / 2, targets[0])
        elif gate == 'RZ': circuit.rz(math.pi / 2, targets[0])
        elif gate in ['CNOT', 'CX'] and len(targets) >= 2: circuit.cx(targets[0], targets[1])
        elif gate == 'CZ' and len(targets) >= 2: circuit.cz(targets[0], targets[1])
        elif gate == 'SWAP' and len(targets) >= 2: circuit.swap(targets[0], targets[1])
        elif gate in ['CCX', 'TOFFOLI'] and len(targets) >= 3: circuit.ccx(targets[0], targets[1], targets[2])

    def _target_state_for_hand(self, hand_name, operations=None, final_state=None):
        if self.num_qubits <= 0:
            return None

        operations = self._normalize_operations(operations or [])

        if hand_name.startswith("W State") and self.num_qubits >= 3:
            amplitudes = [0.0] * (2 ** self.num_qubits)
            probabilities = self._state_probabilities(final_state)
            active_qubits = [
                basis_index.bit_length() - 1
                for basis_index, probability in enumerate(probabilities)
                if basis_index.bit_count() == 1 and probability > 0.05
            ] or list(range(3))
            for qubit in active_qubits:
                amplitudes[1 << qubit] = 1 / (len(active_qubits) ** 0.5)
            return Statevector(amplitudes)

        qc = QuantumCircuit(self.num_qubits)
        if hand_name.startswith("Toffoli Cascade") and self.num_qubits >= 3:
            for operation in operations:
                self._apply_operation_to_circuit(qc, operation)
        elif hand_name.startswith("Swap Network") and self.num_qubits >= 2:
            for operation in operations:
                self._apply_operation_to_circuit(qc, operation)
        elif hand_name.startswith("GHZ State"):
            root = next(
                (operation['targets'][0] for operation in operations if operation['gate'] == 'H' and operation['targets']),
                0,
            )
            qc.h(root)
            for qubit in range(self.num_qubits):
                if qubit != root:
                    qc.cx(root, qubit)
        elif hand_name.startswith("Phase Lock") and self.num_qubits >= 2:
            for operation in operations:
                self._apply_operation_to_circuit(qc, operation)
        elif hand_name.startswith("Bell Pair") and self.num_qubits >= 2:
            entangler = self._bell_candidate(operations, final_state)
            source, target = entangler['targets'][:2] if entangler else (0, 1)
            if entangler and entangler['gate'] == 'CZ':
                qc.h(source)
                qc.h(target)
                qc.cz(source, target)
            else:
                qc.h(source)
                qc.cx(source, target)
        elif hand_name.startswith("Rotation Trio"):
            for operation in operations:
                if operation['gate'] in ['RX', 'RY', 'RZ']:
                    self._apply_operation_to_circuit(qc, operation)
        elif hand_name.startswith("Flush"):
            for qubit in range(self.num_qubits):
                qc.h(qubit)
        elif hand_name.startswith("Full House") and self.num_qubits >= 2:
            h_target = next(operation['targets'][0] for operation in operations if operation['gate'] == 'H' and operation['targets'])
            x_target = next(
                operation['targets'][0]
                for operation in operations
                if operation['gate'] == 'X' and operation['targets'] and operation['targets'][0] != h_target
            )
            qc.h(h_target)
            qc.x(x_target)
        elif hand_name.startswith("High Qubit"):
            pass
        else:
            return None
        return Statevector.from_instruction(qc)

    def _ideal_hand_shape(self, hand_name):
        if hand_name.startswith("GHZ State"):
            return self.num_qubits, self.num_qubits
        if hand_name.startswith("W State"):
            return max(3, self.num_qubits), max(2, self.num_qubits - 1)
        if hand_name.startswith("Bell Pair"):
            return 2, 2
        if hand_name.startswith("Flush"):
            return self.num_qubits, 1
        if hand_name.startswith("Full House"):
            return 2, 1
        if hand_name.startswith("Phase Lock"):
            return 3, 3
        if hand_name.startswith("Rotation Trio"):
            return 3, 3
        if hand_name.startswith("Swap Network"):
            return 3, 3
        if hand_name.startswith("Toffoli Cascade"):
            return 3, 2
        return 1, 1

    def _score_quantum_hand(
        self,
        base_chips,
        base_mult,
        fidelity,
        hand_name,
        operations,
        circuit_depth,
        ineffective_gates,
    ):
        ideal_gates, ideal_depth = self._ideal_hand_shape(hand_name)
        extra_gates = max(0, len(operations) - ideal_gates)
        depth_overrun = max(0, circuit_depth - ideal_depth)
        redundant_units = max(extra_gates, depth_overrun, ineffective_gates)
        depth_efficiency = 0.82 ** redundant_units
        fidelity_weight = max(0.0, min(1.0, fidelity)) ** 2
        score = int(base_chips * base_mult * fidelity_weight * depth_efficiency)
        return score, {
            'fidelity_weight': round(fidelity_weight, 4),
            'gate_count': len(operations),
            'ideal_gate_count': ideal_gates,
            'circuit_depth': circuit_depth,
            'ideal_depth': ideal_depth,
            'ineffective_gates': ineffective_gates,
            'redundant_gates': redundant_units,
            'depth_efficiency': round(depth_efficiency, 3),
        }

    def _resolve_circuit_depth(self, slot_indices, operation_count):
        if slot_indices is None:
            return operation_count
        if len(slot_indices) != operation_count or any(not isinstance(slot, int) or slot < 0 for slot in slot_indices):
            raise ValueError("Invalid slot sequence")
        return len(set(slot_indices))

    def _prepare_ordered_play(self, selected_card_indices, target_qubits_list):
        """按请求顺序绑定卡牌与目标；请求顺序即线路从左到右的执行顺序。"""
        if len(selected_card_indices) != len(target_qubits_list):
            return None, None, "Targets length mismatch"
        if len(set(selected_card_indices)) != len(selected_card_indices):
            return None, None, "A card cannot be played twice"
        if any((not isinstance(i, int) or i < 0 or i >= len(self.hand)) for i in selected_card_indices):
            return None, None, "Invalid card indices"

        played_cards = [self.hand[i] for i in selected_card_indices]
        final_targets = []
        for card, raw_targets in zip(played_cards, target_qubits_list):
            targets = list(raw_targets)
            if not targets:
                return None, None, f"Missing target for {card.gate_type}"
            if card.gate_type in ['CNOT', 'SWAP', 'CZ'] and len(targets) < 2:
                targets.append((targets[0] + 1) % self.num_qubits)
            if card.gate_type in ['CCX'] and len(targets) < 3:
                targets.extend([
                    (targets[0] + 1) % self.num_qubits,
                    (targets[0] + 2) % self.num_qubits,
                ])
            if any(not isinstance(target, int) or target < 0 or target >= self.num_qubits for target in targets):
                return None, None, f"Invalid target for {card.gate_type}"
            required_targets = getattr(card, 'target_count', 1)
            if len(targets) < required_targets or len(set(targets[:required_targets])) < required_targets:
                return None, None, f"Invalid target layout for {card.gate_type}"
            final_targets.append(targets)
        return played_cards, final_targets, ""

    def preview_hand(self, selected_card_indices, target_qubits_list, theta_list=None, slot_indices=None):
        """在当前线路副本上计算牌型、保真度与得分，不修改游戏状态。"""
        if self.phase != 'PLAYING' or not selected_card_indices:
            return {
                'valid': False,
                'hand': 'None',
                'base_chips': 0,
                'base_mult': 0,
                'fidelity': 0.0,
                'joker_chips_delta': 0,
                'joker_mult_delta': 0,
                'score': 0,
                'event_note': '',
                'warning': 'Stage at least one card',
            }

        played_cards, final_targets, warning = self._prepare_ordered_play(
            selected_card_indices,
            target_qubits_list,
        )
        if warning:
            return {
                'valid': False,
                'hand': 'None',
                'base_chips': 0,
                'base_mult': 0,
                'fidelity': 0.0,
                'joker_chips_delta': 0,
                'joker_mult_delta': 0,
                'score': 0,
                'event_note': '',
                'warning': warning,
            }

        gate_types = [card.gate_type for card in played_cards]
        operations = [
            {'gate': card.gate_type, 'targets': targets}
            for card, targets in zip(played_cards, final_targets)
        ]
        fidelity = 1.0
        preview_backend = None
        ineffective_gates = 0
        try:
            if self.backend:
                preview_backend = self.backend.clone() if hasattr(self.backend, 'clone') else None
                if preview_backend is None:
                    raise RuntimeError("Backend preview is unavailable")
                for index, (card, targets) in enumerate(zip(played_cards, final_targets)):
                    state_before = preview_backend.get_statevector()
                    theta = theta_list[index] if theta_list else (
                        math.pi / 2 if card.gate_type in ['RX', 'RY', 'RZ'] else None
                    )
                    preview_backend.apply_gate(card.gate_type, targets, theta)
                    if state_before is not None and state_fidelity(state_before, preview_backend.get_statevector()) > 1 - 1e-9:
                        ineffective_gates += 1
            final_state = preview_backend.get_statevector() if preview_backend else None
            hand_name = self._classify_hand(operations, final_state)
            target_state = self._target_state_for_hand(hand_name, operations, final_state)
            if preview_backend and target_state is not None:
                fidelity = max(0.0, min(1.0, preview_backend.calculate_fidelity(target_state)))
                if abs(1.0 - fidelity) < 1e-9:
                    fidelity = 1.0
        except Exception as exc:
            return {
                'valid': False,
                'hand': 'None',
                'base_chips': 0,
                'base_mult': 0,
                'fidelity': 0.0,
                'joker_chips_delta': 0,
                'joker_mult_delta': 0,
                'score': 0,
                'event_note': '',
                'warning': f"Preview failed: {str(exc)}",
            }

        original_chips = self.poker_hands[hand_name]["chips"]
        original_mult = self.poker_hands[hand_name]["mult"]
        base_chips, base_mult = original_chips, original_mult

        previous_gate_types = self.last_played_gate_types
        self.last_played_gate_types = gate_types[:]
        try:
            for joker in self.jokers:
                base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)
        finally:
            self.last_played_gate_types = previous_gate_types

        base_chips, base_mult, fidelity, event_note = self.apply_blind_event(
            gate_types,
            base_chips,
            base_mult,
            fidelity,
        )
        try:
            circuit_depth = self._resolve_circuit_depth(slot_indices, len(operations))
        except ValueError as exc:
            return {
                'valid': False,
                'hand': hand_name,
                'base_chips': original_chips,
                'base_mult': original_mult,
                'fidelity': round(fidelity, 3),
                'joker_chips_delta': base_chips - original_chips,
                'joker_mult_delta': base_mult - original_mult,
                'score': 0,
                'event_note': event_note,
                'warning': str(exc),
            }
        score, efficiency_details = self._score_quantum_hand(
            base_chips,
            base_mult,
            fidelity,
            hand_name,
            operations,
            circuit_depth,
            ineffective_gates,
        )
        return {
            'valid': True,
            'hand': hand_name,
            'base_chips': original_chips,
            'base_mult': original_mult,
            'fidelity': round(fidelity, 3),
            'joker_chips_delta': base_chips - original_chips,
            'joker_mult_delta': base_mult - original_mult,
            'score': score,
            'event_note': event_note,
            'warning': '',
            'gate_sequence': operations,
            **efficiency_details,
        }

    def play_hand(self, selected_card_indices, target_qubits_list, theta_list=None, slot_indices=None):
        """升级版：支持多卡牌插槽同时出牌的安全逻辑"""
        if self.phase != 'PLAYING' or self.plays_left <= 0 or not selected_card_indices:
            return False

        played_cards, final_targets, warning = self._prepare_ordered_play(
            selected_card_indices,
            target_qubits_list,
        )
        if warning:
            self.warning = warning
            return False

        # 记录将要打出的 gate types（用于判定牌型）
        played_gate_types = []
        played_operations = []
        ineffective_gates = 0

        try:
            for i, card in enumerate(played_cards):
                # card.use 可能会修改 state（例如扣除 chips），但不会移除手牌——移除在成功后统一处理
                ok = card.use(self)
                if not ok:
                    # 使用失败（例如费用不足） => 该卡被跳过
                    continue

                played_gate_types.append(card.gate_type)
                self.last_played_gate_types = played_gate_types[:]
                for joker in self.jokers:
                    joker.on_play_gate(card.gate_type, self)

                curr_target = final_targets[i]
                played_operations.append({'gate': card.gate_type, 'targets': curr_target})

                if self.backend:
                    state_before = self.backend.get_statevector()
                    theta = theta_list[i] if theta_list else (math.pi / 2 if card.gate_type in ['RX', 'RY', 'RZ'] else None)
                    try:
                        self.backend.apply_gate(card.gate_type, curr_target, theta)
                        if state_before is not None and state_fidelity(state_before, self.backend.get_statevector()) > 1 - 1e-9:
                            ineffective_gates += 1
                    except Exception:
                        # 如果底层模拟失败，记录警告并返回失败（不尝试复杂回滚）
                        self.warning = f"Backend error applying {card.gate_type}"
                        return False

                if not getattr(card, 'is_broken', False):
                    self.discard_pile.append(card)

            # 移除已打出的手牌（按索引）
            selected_index_set = set(selected_card_indices)
            remaining = [c for idx, c in enumerate(self.hand) if idx not in selected_index_set]
            self.hand = remaining
            self.plays_left -= 1

            # 判定牌型并计分
            final_state = self.backend.get_statevector() if self.backend else None
            hand_name = self._classify_hand(played_operations, final_state)
            self.last_hand_played = hand_name
            self.current_lesson = self._lesson_for_hand(hand_name, played_gate_types)

            base_chips = self.poker_hands[hand_name]["chips"]
            base_mult = self.poker_hands[hand_name]["mult"]
            original_chips = base_chips
            original_mult = base_mult

            for joker in self.jokers:
                base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)

            target_state = self._target_state_for_hand(hand_name, played_operations, final_state)
            fidelity = 1.0
            if self.backend and target_state is not None:
                fidelity = max(0.0, min(1.0, self.backend.calculate_fidelity(target_state)))
                if abs(1.0 - fidelity) < 1e-9:
                    fidelity = 1.0

            base_chips, base_mult, fidelity, event_note = self.apply_blind_event(
                played_gate_types,
                base_chips,
                base_mult,
                fidelity,
                commit=True,
            )
            self.last_fidelity = fidelity
            circuit_depth = self._resolve_circuit_depth(slot_indices, len(played_operations))
            hand_score, efficiency_details = self._score_quantum_hand(
                base_chips,
                base_mult,
                fidelity,
                hand_name,
                played_operations,
                circuit_depth,
                ineffective_gates,
            )
            self.last_event_result = event_note
            self.last_score_breakdown = {
                'hand': hand_name,
                'base_chips': original_chips,
                'base_mult': original_mult,
                'fidelity': round(fidelity, 3),
                'joker_chips_delta': base_chips - original_chips,
                'joker_mult_delta': base_mult - original_mult,
                'score': hand_score,
                'event_note': event_note,
                **efficiency_details,
            }
            self.current_score += hand_score
            cleared = self.current_score >= self.target_score
            self.update_bonus_objective(played_gate_types, hand_name, fidelity, hand_score, cleared)

            # 每一手都是独立线路；UI 清空出牌区后，底层量子态也必须同步重置。
            if self.backend:
                self.backend.reset_circuit()

            # 补牌与进度检查
            self.draw_cards(len(selected_card_indices))
            self.check_progression()
            return True

        except Exception as e:
            # 捕获非预期异常并提供提示
            self.warning = f"Play failed: {str(e)}"
            return False

    def discard_hand(self, selected_card_indices):
        if self.discards_left <= 0: return False
        self.discards_left -= 1
        selected_card_indices.sort(reverse=True)
        for i in selected_card_indices:
            self.discard_pile.append(self.hand.pop(i))
        self.draw_cards(len(selected_card_indices))
        return True

    def check_progression(self):
        """带 REWARD 阶段和奖金结算"""
        if self.current_score >= self.target_score:
            self.phase = 'REWARD'
            base_reward = 3 if self.blind_index == 0 else (4 if self.blind_index == 1 else 5)
            plays_reward = self.plays_left
            total_reward = base_reward + plays_reward
            
            self.last_payout = {'base': base_reward, 'plays': plays_reward, 'total': total_reward}
            self.chips += total_reward
            bonus_reward = self.claim_bonus_reward()
            if bonus_reward:
                self.last_payout['bonus'] = bonus_reward
            
            self.discard_pile.extend(self.hand)
            self.hand.clear()
            self.generate_shop_items()
            
        elif self.plays_left <= 0:
            self.phase = 'GAME_OVER'

    def generate_shop_items(self):
        available_jokers = [
            MaxwellDemonJoker(),
            SchrodingerCatJoker(),
            PhaseKickbackJoker(),
            RotationCompilerJoker(),
            TopologyBonusJoker(),
        ]
        self.shop_jokers = [{"item": j, "cost": 8} for j in random.sample(available_jokers, random.randint(1, 2))]
        pack = random.choice(self.pack_catalog)
        self.shop_pack = {"name": pack["name"], "type": pack["type"], "desc": pack["desc"], "cost": 4}
        self.shop_joker_pack = {
            "name": "Joker Pack",
            "type": "joker",
            "desc": "Open to reveal two random Jokers. Pick one to add to your build.",
            "cost": 8,
        }

    def create_joker_pack_choices(self):
        pool = [
            MaxwellDemonJoker(),
            SchrodingerCatJoker(),
            PhaseKickbackJoker(),
            RotationCompilerJoker(),
            TopologyBonusJoker(),
        ]
        owned_names = {joker.name for joker in self.jokers}
        fresh_pool = [joker for joker in pool if joker.name not in owned_names]
        if len(fresh_pool) < 2:
            fresh_pool = pool
        return random.sample(fresh_pool, min(2, len(fresh_pool)))

    def create_pack_card(self, pack_type):
        pools = {
            "phase": [
                Card("Phase Kick (RZ)", "RZ", "purple", "RZ changes relative phase and helps Phase Lock hands."),
                Card("Controlled Phase (CZ)", "CZ", "purple", "CZ connects two selected qubits through phase.", 2),
                Card("Sharp Z", "Z", "gold", "A paid Z card with strong phase-hand synergy."),
            ],
            "rotation": [
                Card("Rotation X (RX)", "RX", "purple", "RX rotates around the X axis by pi/2."),
                Card("Rotation Y (RY)", "RY", "purple", "RY rotates around the Y axis by pi/2."),
                Card("Rotation Z (RZ)", "RZ", "purple", "RZ rotates around the Z axis by pi/2."),
            ],
            "entangle": [
                Card("Controlled-NOT Plus", "CNOT", "purple", "Choose source and target to decide entanglement direction.", 2),
                Card("Swap Link", "SWAP", "purple", "SWAP exchanges the states of two selected qubits.", 2),
                Card("Controlled-Z Link", "CZ", "blue", "CZ is a phase entangler with explicit target choice.", 2),
            ],
            "control": [
                Card("Toffoli Gate (CCX)", "CCX", "gold", "Two controls flip one target; a rare late-game logic card.", 3),
                Card("Swap Link", "SWAP", "purple", "SWAP exchanges the states of two selected qubits.", 2),
            ],
        }
        return random.choice(pools.get(pack_type, pools["rotation"]))

    def _lesson_for_hand(self, hand_name, gate_types):
        if hand_name.startswith("Bell Pair") or hand_name.startswith("GHZ"):
            body = "Entanglement comes from a superposition source followed by controlled gates. Change CNOT targets to see fidelity move."
        elif hand_name.startswith("Phase"):
            body = "Phase gates may not change bar probabilities immediately, but they change interference and target-state overlap."
        elif hand_name.startswith("Rotation"):
            body = "Rotation cards use a fixed pi/2 angle here, introducing continuous gates without needing a slider yet."
        elif hand_name.startswith("Swap"):
            body = "SWAP changes where quantum information lives, so line routing becomes part of the puzzle."
        elif hand_name.startswith("Toffoli"):
            body = "CCX is a reversible three-qubit control gate: two controls decide whether the target flips."
        else:
            body = "This is a simple hand. Add H, CNOT, phase, or rotation cards to reach richer target states."
        return {"title": hand_name, "body": body, "gates": gate_types}

    def next_blind_from_shop(self):
        if self.phase != 'SHOP': return
        self.blind_index += 1
        if self.blind_index >= len(self.blind_sequence): 
            self.blind_index = 0
            self.ante += 1
            
        if self.ante > 3:
            self.phase = 'VICTORY'
        else:
            self.start_new_blind()
