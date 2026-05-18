import random

# ==========================================
# 1. 实体定义：卡牌系统 (Cards)
# ==========================================
class Card:
    def __init__(self, name, gate_type, rarity='blue'):
        self.name = name
        self.gate_type = gate_type 
        self.rarity = rarity       
        self.durability = 3 if rarity == 'purple' else -1
        self.is_broken = False
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
        
        # --- 量子牌型定义 (Base Chips x Base Mult) ---
        self.poker_hands = {
            "GHZ State (同花顺)": {"chips": 120, "mult": 12},
            "Full House (满堂红)": {"chips": 90, "mult": 8},
            "W State (三条)": {"chips": 70, "mult": 6},
            "Flush (均匀叠加)": {"chips": 50, "mult": 5},
            "Bell Pair (纠缠对)": {"chips": 30, "mult": 3},
            "High Qubit (高牌)": {"chips": 10, "mult": 2}
        }
        self.last_hand_played = "None"
        
        self.start_new_blind()

    def _init_deck(self):
        deck = []
        for _ in range(5):
            deck.append(Card("哈达玛门 (H)", "H", "normal"))
            deck.append(Card("泡利X门 (X)", "X", "normal"))
        deck.append(Card("受控非门 (CNOT)", "CNOT", "normal"))
        deck.append(Card("粗糙的相位门", "RX", "blue")) 
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

    def start_new_blind(self):
        if self.ante >= 3 and self.num_qubits == 3:
            self.num_qubits = 5
            if self.backend: self.backend.upgrade_qubits(5)
                
        self.plays_left = self.max_plays
        self.discards_left = self.max_discards
        self.current_score = 0
        self.last_hand_played = "None"
        self.last_fidelity = 0.0
        
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
            
        self.preview_hand_name = h_name
        base_chips = self.poker_hands[h_name]["chips"]
        base_mult = self.poker_hands[h_name]["mult"]
        
        for joker in self.jokers:
            base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)
            
        fidelity = 1.0 if not self.backend else 0.85 
        self.preview_fidelity = fidelity
        self.preview_score = int((base_chips * base_mult) * fidelity)

    def play_hand(self, selected_card_indices, target_qubits_list, theta_list=None):
        """升级版：支持多卡牌插槽同时出牌的安全逻辑"""
        if self.phase != 'PLAYING' or self.plays_left <= 0 or not selected_card_indices:
            return False

        # 将索引和目标比特绑定，然后按索引从大到小排序，防止 pop 时越界
        paired = list(zip(selected_card_indices, target_qubits_list))
        paired.sort(key=lambda x: x[0], reverse=True)
        
        played_cards = []
        final_targets = []
        for item in paired:
            played_cards.append(self.hand.pop(item[0]))
            final_targets.append(item[1])
            
        # 恢复成玩家放置的物理时间顺序（从左到右）
        played_cards.reverse()
        final_targets.reverse()
        
        # 记录打出了什么门
        played_gate_types = []

        for i, card in enumerate(played_cards):
            if not card.use(self): continue 
            played_gate_types.append(card.gate_type)
            for joker in self.jokers: joker.on_play_gate(card.gate_type, self)
            
            # === 核心修复：自动补全双比特门的目标位 ===
            curr_target = final_targets[i]
            if card.gate_type in ['CNOT', 'SWAP'] and len(curr_target) < 2:
                # 自动将目标位设定为下一根线 (利用取模运算 % 解决越界)
                curr_target.append((curr_target[0] + 1) % self.num_qubits)

            if self.backend:
                theta = theta_list[i] if theta_list else None
                self.backend.apply_gate(card.gate_type, curr_target, theta)
                
            if not getattr(card, 'is_broken', False): self.discard_pile.append(card)

        self.plays_left -= 1
        
        # === 动态量子牌型判定 ===
        if len(played_gate_types) >= 3 and 'CNOT' in played_gate_types and 'H' in played_gate_types:
            hand_name = "GHZ State (同花顺)"
        elif len(played_gate_types) >= 2 and 'CNOT' in played_gate_types:
            hand_name = "Bell Pair (纠缠对)"
        elif all(g == 'H' for g in played_gate_types) and len(played_gate_types) > 1:
            hand_name = "Flush (均匀叠加)"
        elif 'X' in played_gate_types and 'H' in played_gate_types:
            hand_name = "Full House (满堂红)"
        elif len(played_gate_types) >= 3 and 'X' in played_gate_types:
            hand_name = "W State (三条)"
        else:
            hand_name = "High Qubit (高牌)"
            
        self.last_hand_played = hand_name
        base_chips = self.poker_hands[hand_name]["chips"]
        base_mult = self.poker_hands[hand_name]["mult"]
        
        # 小丑牌算分
        for joker in self.jokers:
            base_chips, base_mult = joker.on_calculate_score(base_chips, base_mult, self)
            
        fidelity = 1.0 if not self.backend else 0.85 

        # 【新增】：把这次出牌的保真度保存到状态机里，供前端读取
        self.last_fidelity = fidelity

        hand_score = int((base_chips * base_mult) * fidelity)
        self.current_score += hand_score
        
        self.draw_cards(len(selected_card_indices))
        self.check_progression()
        return True

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
            
            self.discard_pile.extend(self.hand)
            self.hand.clear()
            self.generate_shop_items()
            
        elif self.plays_left <= 0:
            self.phase = 'GAME_OVER'

    def generate_shop_items(self):
        available_jokers = [MaxwellDemonJoker(), SchrodingerCatJoker()]
        self.shop_jokers = [{"item": j, "cost": 8} for j in random.sample(available_jokers, random.randint(1, 2))]
        self.shop_pack = {"name": "QUANTUM PACK", "cost": 4}

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