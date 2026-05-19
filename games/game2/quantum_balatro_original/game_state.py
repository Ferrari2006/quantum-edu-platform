import math
import random
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

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
        super().__init__("薛定谔的猫", "每次结算时，每保留1次出牌机会，倍率+5")

    def on_calculate_score(self, current_chips, current_mult, state):
        bonus_mult = state.plays_left * 5
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
    
    def update_preview(self, staged_indices):
        """实时计算预览分数，不消耗实际出牌次数"""
        if not staged_indices:
            self.preview_hand_name, self.preview_score, self.preview_fidelity = "None", 0, 0.0
            return

        gate_types = [self.hand[i].gate_type for i in staged_indices]
        
        # 牌型判定
        if len(gate_types) >= 3 and 'CNOT' in gate_types and 'H' in gate_types: h_name = "GHZ State (同花顺)"
        elif len(gate_types) >= 2 and 'CNOT' in gate_types: h_name = "Bell Pair (纠缠对)"
        elif all(g == 'H' for g in gate_types) and len(gate_types) > 1: h_name = "Flush (均匀叠加)"
        elif 'X' in gate_types and 'H' in gate_types: h_name = "Full House (满堂红)"
        elif len(gate_types) >= 3 and 'X' in gate_types: h_name = "W State (三条)"
        else: h_name = "High Qubit (高牌)"
            
        h_name = self._classify_hand(gate_types)
        self.preview_hand_name = h_name
        base_chips = self.poker_hands[h_name]["chips"]
        base_mult = self.poker_hands[h_name]["mult"]
        
        for joker in self.jokers:
            base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)
            
        target_state = self._target_state_for_hand(h_name)
        fidelity = 1.0
        if self.backend and target_state is not None:
            fidelity = max(0.0, min(1.0, self.backend.calculate_fidelity(target_state)))
            if abs(1.0 - fidelity) < 1e-9:
                fidelity = 1.0
        base_chips, base_mult, fidelity, _ = self.apply_blind_event(gate_types, base_chips, base_mult, fidelity)
        self.preview_fidelity = fidelity
        self.preview_score = int((base_chips * base_mult) * fidelity)

    def _hand_key(self, prefix):
        return next(key for key in self.poker_hands if key.startswith(prefix))

    def _classify_hand(self, gate_types):
        if 'CCX' in gate_types:
            return self._hand_key("Toffoli Cascade")
        if 'SWAP' in gate_types and any(g in gate_types for g in ['CNOT', 'CZ']):
            return self._hand_key("Swap Network")
        if len(gate_types) >= 3 and 'CNOT' in gate_types and 'H' in gate_types:
            return self._hand_key("GHZ State")
        if sum(1 for g in gate_types if g in ['Z', 'CZ', 'RZ']) >= 2:
            return self._hand_key("Phase Lock")
        if len(gate_types) >= 2 and 'CNOT' in gate_types:
            return self._hand_key("Bell Pair")
        if sum(1 for g in gate_types if g in ['RX', 'RY', 'RZ']) >= 2:
            return self._hand_key("Rotation Trio")
        if all(g == 'H' for g in gate_types) and len(gate_types) > 1:
            return self._hand_key("Flush")
        if 'X' in gate_types and 'H' in gate_types:
            return self._hand_key("Full House")
        if len(gate_types) >= 3 and 'X' in gate_types:
            return self._hand_key("W State")
        return self._hand_key("High Qubit")

    def _target_state_for_hand(self, hand_name):
        if self.num_qubits <= 0:
            return None

        if hand_name.startswith("W State") and self.num_qubits >= 3:
            amplitudes = [0.0] * (2 ** self.num_qubits)
            for qubit in range(3):
                amplitudes[1 << qubit] = 1 / (3 ** 0.5)
            return Statevector(amplitudes)

        qc = QuantumCircuit(self.num_qubits)
        if hand_name.startswith("Toffoli Cascade") and self.num_qubits >= 3:
            qc.h(0)
            qc.x(1)
            qc.ccx(0, 1, 2)
        elif hand_name.startswith("Swap Network") and self.num_qubits >= 2:
            qc.h(0)
            qc.swap(0, 1)
            if self.num_qubits >= 3:
                qc.cx(1, 2)
        elif hand_name.startswith("GHZ State"):
            qc.h(0)
            for qubit in range(1, self.num_qubits):
                qc.cx(0, qubit)
        elif hand_name.startswith("Phase Lock") and self.num_qubits >= 2:
            qc.h(0)
            qc.cz(0, 1)
        elif hand_name.startswith("Bell Pair") and self.num_qubits >= 2:
            qc.h(0)
            qc.cx(0, 1)
        elif hand_name.startswith("Rotation Trio"):
            qc.rx(math.pi / 2, 0)
            if self.num_qubits >= 2:
                qc.ry(math.pi / 2, 1)
            if self.num_qubits >= 3:
                qc.rz(math.pi / 2, 2)
        elif hand_name.startswith("Flush"):
            for qubit in range(self.num_qubits):
                qc.h(qubit)
        elif hand_name.startswith("Full House") and self.num_qubits >= 2:
            qc.h(0)
            qc.x(1)
        elif hand_name.startswith("High Qubit"):
            pass
        else:
            return None
        return Statevector.from_instruction(qc)

    def play_hand(self, selected_card_indices, target_qubits_list, theta_list=None):
        """升级版：支持多卡牌插槽同时出牌的安全逻辑"""
        if self.phase != 'PLAYING' or self.plays_left <= 0 or not selected_card_indices:
            return False

        # 基本输入验证：索引合法、目标数与索引一一对应
        if any((not isinstance(i, int) or i < 0 or i >= len(self.hand)) for i in selected_card_indices):
            self.warning = "Invalid card indices"
            return False
        if len(selected_card_indices) != len(target_qubits_list):
            self.warning = "Targets length mismatch"
            return False

        # 去重并按升序排列（保持从左到右的时间顺序）
        unique_indices = sorted(dict.fromkeys(selected_card_indices))
        played_cards = [self.hand[i] for i in unique_indices]
        final_targets = [list(t) for t in target_qubits_list]

        # 记录将要打出的 gate types（用于判定牌型）
        played_gate_types = []

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

                # 自动补全双/三比特门的目标位
                curr_target = final_targets[i]
                if card.gate_type in ['CNOT', 'SWAP', 'CZ'] and len(curr_target) < 2:
                    curr_target.append((curr_target[0] + 1) % self.num_qubits)
                if card.gate_type in ['CCX'] and len(curr_target) < 3:
                    curr_target.extend([
                        (curr_target[0] + 1) % self.num_qubits,
                        (curr_target[0] + 2) % self.num_qubits,
                    ])

                if self.backend:
                    theta = theta_list[i] if theta_list else (math.pi / 2 if card.gate_type in ['RX', 'RY', 'RZ'] else None)
                    try:
                        self.backend.apply_gate(card.gate_type, curr_target, theta)
                    except Exception:
                        # 如果底层模拟失败，记录警告并返回失败（不尝试复杂回滚）
                        self.warning = f"Backend error applying {card.gate_type}"
                        return False

                if not getattr(card, 'is_broken', False):
                    self.discard_pile.append(card)

            # 移除已打出的手牌（按索引）
            remaining = [c for idx, c in enumerate(self.hand) if idx not in unique_indices]
            self.hand = remaining
            self.plays_left -= 1

            # 判定牌型并计分
            hand_name = self._classify_hand(played_gate_types)
            self.last_hand_played = hand_name
            self.current_lesson = self._lesson_for_hand(hand_name, played_gate_types)

            base_chips = self.poker_hands[hand_name]["chips"]
            base_mult = self.poker_hands[hand_name]["mult"]
            original_chips = base_chips
            original_mult = base_mult

            for joker in self.jokers:
                base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)

            target_state = self._target_state_for_hand(hand_name)
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
            hand_score = int((base_chips * base_mult) * fidelity)
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
            }
            self.current_score += hand_score
            cleared = self.current_score >= self.target_score
            self.update_bonus_objective(played_gate_types, hand_name, fidelity, hand_score, cleared)

            # 补牌与进度检查
            self.draw_cards(len(unique_indices))
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
