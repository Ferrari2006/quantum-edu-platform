import pygame
import sys
from game_state import GameState, SchrodingerCatJoker, MaxwellDemonJoker

class DisplayEngine:
    def __init__(self, state):
        pygame.init()
        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Quantum Balatro - Neon Terminal")
        self.clock = pygame.time.Clock()
        
        font_name = "consolas" if pygame.font.match_font("consolas") else "courier new"
        self.font = pygame.font.SysFont(font_name, 18, bold=True)
        self.title_font = pygame.font.SysFont(font_name, 28, bold=True)
        self.small_font = pygame.font.SysFont(font_name, 14)
        self.hud_font = pygame.font.SysFont(font_name, 26, bold=True)
        self.giant_font = pygame.font.SysFont(font_name, 42, bold=True)
        
        self.state = state
        
        # --- 交互系统变量 ---
        self.is_dragging = False
        self.dragging_idx = None
        self.mouse_pos = (0, 0)
        self.staged_cards = {}  # {(qubit, slot_idx): hand_idx}
        self.selected_for_discard = set()
        self.MAX_SLOTS = 4 
        self.confirm_dialog = None
        self.anim_fidelity = 0.0
        
        self.visual_gates = {i: [] for i in range(10)} 
        self.current_ante_blind = (self.state.ante, self.state.blind_index)
        
        # --- 霓虹调色板 ---
        self.COLORS = {
            'bg': (20, 20, 28),
            'grid': (35, 35, 45),
            'line': (0, 200, 255),
            'slot': (45, 45, 55),
            'text': (240, 240, 245),
            'text_dark': (20, 20, 20),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'yellow': (255, 215, 0),
            'red': (255, 80, 80),
            'green': (0, 255, 128),
            'panel_bg': (30, 30, 40),
            'card_bg': (35, 35, 45),
            'rarity': {
                'normal': (150, 150, 150),
                'blue': (50, 150, 255),
                'purple': (200, 50, 255),
                'gold': (255, 200, 50),
                'grey': (60, 60, 60)
            }
        }
        
        self.GATE_COLORS = {
            'H': self.COLORS['cyan'],
            'X': self.COLORS['magenta'],
            'Z': self.COLORS['yellow'],
            'CNOT': self.COLORS['red'],
            'RX': (200, 100, 255)
        }
        
        # --- 翻译字典 (防止乱码) ---
        self.EN_TRANSLATION = {
            "哈达玛门 (H)": "Hadamard",
            "泡利X门 (X)": "Pauli-X",
            "受控非门 (CNOT)": "CNOT Gate",
            "粗糙的相位门": "Phase (RX)",
            "退相干的 粗糙的相位门": "Broken RX",
            "量子噪声": "Thermal Noise",
            "麦克斯韦妖": "Maxwell's Demon",
            "薛定谔的猫": "Schrodinger Cat",
            # 👇 新增这两行技能描述的翻译 👇
            "每次打出双比特门(CNOT/SWAP)，筹码+15": "+15 Chips per CNOT/SWAP played",
            "每次结算时，每保留1次出牌机会，倍率+5": "+5 Mult per remaining Play"
        }

    def draw_grid(self):
        for x in range(0, self.width, 40): pygame.draw.line(self.screen, self.COLORS['grid'], (x, 0), (x, self.height))
        for y in range(0, self.height, 40): pygame.draw.line(self.screen, self.COLORS['grid'], (0, y), (self.width, y))

    def get_card_rect(self, index, total_cards):
        card_w, card_h = 90, 130
        spacing = 15
        total_w = total_cards * card_w + (total_cards - 1) * spacing
        start_x = 240 + (720 - total_w) // 2 
        x = start_x + index * (card_w + spacing)
        y = self.height - card_h - 20
        return pygame.Rect(x, y, card_w, card_h)

    def get_slot_rect(self, q_idx, slot_idx):
        slot_w, slot_h = 80, 110
        base_y = 200 + q_idx * 150
        base_x = 350 + slot_idx * 110
        return pygame.Rect(base_x, base_y - slot_h//2, slot_w, slot_h)

    def trigger_preview_update(self):
        """收集当前插槽里的卡牌索引，通知状态机更新预览"""
        staged_items = sorted(self.staged_cards.items(), key=lambda x: x[0][1])
        indices = [h_idx for _, h_idx in staged_items]
        self.state.update_preview(indices)
    def handle_events(self):
        self.mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # === PLAYING 阶段交互 ===
            if self.state.phase == 'PLAYING':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_staged = False
                    for (q, s), h_idx in list(self.staged_cards.items()):
                        if self.get_slot_rect(q, s).collidepoint(event.pos):
                            del self.staged_cards[(q, s)]
                            self.trigger_preview_update()
                            clicked_staged = True
                            break
                    if clicked_staged: continue

                    for i in range(len(self.state.hand)):
                        if i in self.staged_cards.values(): continue 
                        if self.get_card_rect(i, len(self.state.hand)).collidepoint(event.pos):
                            self.is_dragging = True
                            self.dragging_idx = i
                            if i in self.selected_for_discard: self.selected_for_discard.remove(i)
                            else: self.selected_for_discard.add(i)
                            break
                    
                    play_btn = pygame.Rect(self.width - 250, 480, 200, 60)
                    discard_btn = pygame.Rect(self.width - 250, 560, 200, 60)
                    clear_btn = pygame.Rect(self.width - 250, 640, 200, 60)
                    
                    if clear_btn.collidepoint(event.pos):
                        self.staged_cards.clear()
                    elif discard_btn.collidepoint(event.pos) and self.selected_for_discard and self.state.discards_left > 0:
                        self.state.discard_hand(list(self.selected_for_discard))
                        self.selected_for_discard.clear()
                        self.staged_cards.clear() 
                        self.trigger_preview_update()
                        self.is_dragging = False
                    elif play_btn.collidepoint(event.pos) and self.staged_cards:
                        staged_items = sorted(self.staged_cards.items(), key=lambda x: x[0][1])
                        indices_to_play = [h_idx for _, h_idx in staged_items]
                        targets = [[q] for (q, _), _ in staged_items]
                        self.state.play_hand(indices_to_play, targets)
                        self.staged_cards.clear()
                        self.trigger_preview_update()
                        self.selected_for_discard.clear()
                        self.is_dragging = False

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.is_dragging:
                        dropped = False
                        for q in range(self.state.num_qubits):
                            for s in range(self.MAX_SLOTS):
                                if self.get_slot_rect(q, s).collidepoint(event.pos) and (q, s) not in self.staged_cards:
                                    self.staged_cards[(q, s)] = self.dragging_idx
                                    self.trigger_preview_update()
                                    if self.dragging_idx in self.selected_for_discard:
                                        self.selected_for_discard.remove(self.dragging_idx)
                                    dropped = True
                                    break
                            if dropped: break
                        self.is_dragging = False
                        self.dragging_idx = None
                        
            # === REWARD 阶段交互 ===
            elif self.state.phase == 'REWARD':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pygame.Rect(self.width//2 - 125, self.height//2 + 120, 250, 60).collidepoint(event.pos):
                        self.state.phase = 'SHOP'
                        
            # === SHOP 阶段交互 (含弹窗) ===
            elif self.state.phase == 'SHOP':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.confirm_dialog:
                        confirm_btn = pygame.Rect(self.width//2 - 150, self.height//2 + 50, 130, 50)
                        cancel_btn = pygame.Rect(self.width//2 + 20, self.height//2 + 50, 130, 50)
                        if cancel_btn.collidepoint(event.pos):
                            self.confirm_dialog = None
                        elif confirm_btn.collidepoint(event.pos):
                            item_info = self.confirm_dialog['item_info']
                            if self.state.chips >= item_info['cost']:
                                if self.confirm_dialog['type'] == 'joker' and len(self.state.jokers) < 5:
                                    self.state.chips -= item_info['cost']
                                    self.state.jokers.append(item_info['item'])
                                    self.state.shop_jokers.pop(self.confirm_dialog['index'])
                                elif self.confirm_dialog['type'] == 'pack':
                                    self.state.chips -= item_info['cost']
                                    from game_state import Card
                                    
                                    # 1. 劫持卡牌：放到展示台上，而不是直接进 deck
                                    self.state.opened_card = Card("Phase (RX)", "RX", "purple")
                                    self.state.shop_pack = False
                                    
                                    # 2. 核心跳转：切换到开包动画阶段
                                    self.state.phase = 'OPENING_PACK'
                                    self.pack_reveal = False # 初始状态为没拆开
                                    
                                self.confirm_dialog = None
                                continue
                    
                    if pygame.Rect(self.width - 250, self.height - 100, 200, 60).collidepoint(event.pos):
                        self.state.next_blind_from_shop()
                        continue
                        
                    for i, shop_item in enumerate(self.state.shop_jokers):
                        if pygame.Rect(300 + i * 220, 300, 180, 250).collidepoint(event.pos):
                            self.confirm_dialog = {'type': 'joker', 'index': i, 'item_info': shop_item}
                            break
                    if self.state.shop_pack and pygame.Rect(self.width - 350, 300, 180, 250).collidepoint(event.pos):
                        self.confirm_dialog = {'type': 'pack', 'item_info': self.state.shop_pack}
            # ... 这是上面 SHOP 阶段结束的地方 ...
            
            # === 新增：开包阶段的鼠标点击交互 ===
            elif self.state.phase == 'OPENING_PACK':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not getattr(self, 'pack_reveal', False):
                        # 第一次点击：拆开包！
                        self.pack_reveal = True  
                    else:
                        # 第二次点击：收下卡牌，放回卡组，回到商店
                        self.state.deck.append(self.state.opened_card) 
                        self.state.opened_card = None
                        self.state.phase = 'SHOP'
            # === 重启游戏 ===
            elif self.state.phase in ['GAME_OVER', 'VICTORY']:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pygame.Rect(self.width//2 - 150, self.height//2 + 100, 300, 70).collidepoint(event.pos):
                        self.state.reset_game()
                        self.staged_cards.clear()
                        self.selected_for_discard.clear()

    def check_new_round(self):
        new_tuple = (self.state.ante, self.state.blind_index)
        if new_tuple != self.current_ante_blind:
            self.visual_gates = {i: [] for i in range(10)}
            self.current_ante_blind = new_tuple

    def render(self):
        self.check_new_round()
        self.screen.fill(self.COLORS['bg'])
        self.draw_grid()
        
        # ==========================================
        # 1. 顶部 HUD
        # ==========================================
        pygame.draw.rect(self.screen, self.COLORS['panel_bg'], (20, 20, self.width - 40, 100), border_radius=15)
        blind_str = self.state.blind_sequence[self.state.blind_index].upper() + " BLIND"
        b_color = self.COLORS['cyan'] if "BOSS" not in blind_str else self.COLORS['red']
        
        self.screen.blit(self.giant_font.render(blind_str, True, b_color), (40, 35))
        self.screen.blit(self.small_font.render(f"Target: Ante {self.state.ante}. Shape the quantum state.", True, (150, 150, 160)), (40, 85))
        
        # 【修改点 1：资金文字整体往左平移】
        self.screen.blit(self.font.render(f"FUNDS: ${self.state.chips}", True, self.COLORS['yellow']), (330, 30))
        self.screen.blit(self.font.render(f"HANDS: {self.state.plays_left}", True, self.COLORS['text']), (330, 60))
        self.screen.blit(self.font.render(f"DISCARDS: {self.state.discards_left}", True, self.COLORS['red']), (480, 60))
        
        # === 【核心新增：在顶栏中间绘制小丑牌与悬浮提示】 ===
        for i, joker in enumerate(self.state.jokers):
            # 给每张小丑牌分配一个迷你的槽位
            j_rect = pygame.Rect(620 + i * 55, 35, 45, 65)
            is_hover = j_rect.collidepoint(self.mouse_pos)
            
            if is_hover: j_rect.y -= 5 # 悬停跳动特效
            
            pygame.draw.rect(self.screen, self.COLORS['card_bg'], j_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.COLORS['red'], j_rect, border_radius=6, width=2)
            
            # 画一个大写的 'J' 标识
            j_mark = self.title_font.render("J", True, self.COLORS['red'])
            self.screen.blit(j_mark, (j_rect.centerx - j_mark.get_width()//2, j_rect.centery - j_mark.get_height()//2))
            
            # 渲染 Tooltip 提示框 (置顶显示，防止被其他UI遮挡)
            if is_hover:
                j_name_str = self.EN_TRANSLATION.get(joker.name, joker.name)
                # 读取技能描述的英文翻译
                j_desc_str = self.EN_TRANSLATION.get(joker.description, joker.description)
                tip_txt = self.small_font.render(f"{j_name_str}: {j_desc_str}", True, self.COLORS['text'])
                tip_rect = pygame.Rect(j_rect.centerx - tip_txt.get_width()//2 - 10, j_rect.bottom + 10, tip_txt.get_width() + 20, 30)
                
                pygame.draw.rect(self.screen, (20, 20, 30), tip_rect, border_radius=5)
                pygame.draw.rect(self.screen, self.COLORS['cyan'], tip_rect, border_radius=5, width=1)
                self.screen.blit(tip_txt, (tip_rect.x + 10, tip_rect.y + 7))
        # ===============================================
        
        score_ratio = min(1.0, self.state.current_score / max(1, self.state.target_score))
        pygame.draw.rect(self.screen, (50, 50, 60), (self.width - 350, 70, 300, 15), border_radius=5)
        pygame.draw.rect(self.screen, b_color, (self.width - 350, 70, int(300 * score_ratio), 15), border_radius=5)
        # 先把总分渲染成一个单独的变量
        score_txt = self.giant_font.render(f"{self.state.current_score} / {self.state.target_score}", True, self.COLORS['text'])
        # 画出总分
        self.screen.blit(score_txt, (self.width - 350, 25))
        
        # === 紧接着画出悬浮的预览分数 ===
        if self.state.phase == 'PLAYING' and getattr(self.state, 'preview_score', 0) > 0:
            p_txt = self.hud_font.render(f" (+{self.state.preview_score})", True, self.COLORS['green'])
            self.screen.blit(p_txt, (self.width - 350 + score_txt.get_width(), 35))

        # ==========================================
        # 2. 游玩区域 (PLAYING)
        # ==========================================
        if self.state.phase == 'PLAYING':
            # --- 恢复：左侧牌型图鉴 (Run Info) ---
            dict_rect = pygame.Rect(20, 140, 200, 320 + (self.state.num_qubits-3)*150)
            pygame.draw.rect(self.screen, self.COLORS['panel_bg'], dict_rect, border_radius=15, width=2)
            self.screen.blit(self.font.render("HANDS DICTIONARY", True, self.COLORS['cyan']), (35, 160))
            pygame.draw.line(self.screen, self.COLORS['cyan'], (35, 190), (190, 190), 2)
            
            for i, (h_name, h_stats) in enumerate(self.state.poker_hands.items()):
                eng_name = h_name.split(" ")[0] + (" State" if "GHZ" in h_name or "W" in h_name else "")
                # 读取预览名字决定是否亮起绿灯
                target_name = self.state.preview_hand_name if self.staged_cards else "None"
                color = self.COLORS['green'] if eng_name in target_name else (150, 150, 150)
                self.screen.blit(self.small_font.render(eng_name, True, color), (35, 205 + i * 40))
                self.screen.blit(self.small_font.render(f"{h_stats['chips']} x {h_stats['mult']}", True, self.COLORS['yellow']), (35, 220 + i * 40))

            # --- 量子线路与插槽 ---
            pygame.draw.rect(self.screen, self.COLORS['panel_bg'], (240, 140, 730, dict_rect.height), border_radius=15, width=2)
            for q in range(self.state.num_qubits):
                base_y = 200 + q * 150
                pygame.draw.line(self.screen, self.COLORS['line'], (280, base_y), (900, base_y), 2)
                self.screen.blit(self.title_font.render(f"q[{q}]", True, self.COLORS['text']), (260, base_y - 20))
                
                for s in range(self.MAX_SLOTS):
                    s_rect = self.get_slot_rect(q, s)
                    pygame.draw.rect(self.screen, self.COLORS['slot'], s_rect, border_radius=10)
                    
            # --- 绘制卡牌 (包含稀有度边框和耐久度) ---
            for i, card in enumerate(self.state.hand):
                if i == self.dragging_idx and self.is_dragging:
                    rect = pygame.Rect(0, 0, 90, 130)
                    rect.center = self.mouse_pos
                elif i in self.staged_cards.values():
                    pos = list(self.staged_cards.keys())[list(self.staged_cards.values()).index(i)]
                    rect = self.get_slot_rect(pos[0], pos[1])
                else:
                    rect = self.get_card_rect(i, len(self.state.hand))
                    if rect.collidepoint(self.mouse_pos) and not self.is_dragging: rect.y -= 10
                    
                c_color = self.GATE_COLORS.get(card.gate_type, self.COLORS['card_bg'])
                r_color = self.COLORS['rarity'].get(card.rarity, self.COLORS['rarity']['normal'])
                
                pygame.draw.rect(self.screen, c_color, rect, border_radius=10)
                if card.rarity != 'normal': pygame.draw.rect(self.screen, r_color, rect, border_radius=10, width=3)
                
                if i in self.selected_for_discard and i not in self.staged_cards.values():
                    pygame.draw.rect(self.screen, self.COLORS['text'], rect, border_radius=10, width=4)
                    
                sym_txt = self.giant_font.render(card.gate_type, True, (255, 255, 255))
                self.screen.blit(sym_txt, (rect.centerx - sym_txt.get_width()//2, rect.centery - sym_txt.get_height()//2))
                
                if card.rarity == 'purple':
                    self.screen.blit(self.small_font.render(f"USES:{card.durability}", True, (20,20,20)), (rect.x + 5, rect.y + 5))

            # --- 下方面板 (Library) ---
            lib_rect = pygame.Rect(240, self.height - 180, 730, 160)
            pygame.draw.rect(self.screen, self.COLORS['panel_bg'], lib_rect, border_radius=15, width=2)
            self.screen.blit(self.font.render("CARD LIBRARY", True, self.COLORS['cyan']), (260, self.height - 160))

            # --- 右侧面板 (Controls) ---
            ctrl_rect = pygame.Rect(self.width - 280, 140, 260, 560)
            pygame.draw.rect(self.screen, self.COLORS['panel_bg'], ctrl_rect, border_radius=15, width=2)
            self.screen.blit(self.small_font.render("TARGET MATCH", True, self.COLORS['text']), (self.width - 260, 160))
            # --- 真实的动态保真度柱状图 (TARGET MATCH) ---
            bar_x, bar_y, bar_w, bar_h = self.width - 250, 200, 30, 150
            
            # 1. 画一个暗色的空槽底框
            pygame.draw.rect(self.screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            
            # 2. 获取状态机里的真实保真度，如果没有则默认为 0
            target_fid = self.state.preview_fidelity if self.staged_cards else 0.0
            self.anim_fidelity += (target_fid - self.anim_fidelity) * 0.1
            
            # 3. 平滑动画插值 (Lerp)：让柱子丝滑地涨跌，而不是瞬间突变
            if not hasattr(self, 'anim_fidelity'): 
                self.anim_fidelity = 0.0
            self.anim_fidelity += (target_fid - self.anim_fidelity) * 0.1
            
            # 4. 根据当前的动画进度绘制青色填充条
            fill_h = int(bar_h * self.anim_fidelity)
            if fill_h > 0:
                fill_rect = pygame.Rect(bar_x, bar_y + bar_h - fill_h, bar_w, fill_h)
                pygame.draw.rect(self.screen, self.COLORS['cyan'], fill_rect, border_radius=5)
                
            # 5. 在柱子旁边显示具体的百分比数字
            fid_percent = int(self.anim_fidelity * 100)
            fid_txt = self.small_font.render(f"{fid_percent}%", True, self.COLORS['text'])
            self.screen.blit(fid_txt, (bar_x + 40, bar_y + bar_h - 15))
            
            play_btn = pygame.Rect(self.width - 250, 480, 200, 60)
            disc_btn = pygame.Rect(self.width - 250, 560, 200, 60)
            clear_btn = pygame.Rect(self.width - 250, 640, 200, 60)
            
            can_play = len(self.staged_cards) > 0
            can_disc = len(self.selected_for_discard) > 0 and self.state.discards_left > 0
            
            pygame.draw.rect(self.screen, self.COLORS['green'] if can_play else (40,80,60), play_btn, border_radius=8)
            pygame.draw.rect(self.screen, self.COLORS['red'] if can_disc else (80,40,40), disc_btn, border_radius=8)
            pygame.draw.rect(self.screen, (50, 50, 60), clear_btn, border_radius=8)
            
            p_txt, d_txt, c_txt = self.font.render("PLAY HAND", True, (255,255,255)), self.font.render("DISCARD", True, (255,255,255)), self.font.render("CLEAR", True, (255,255,255))
            self.screen.blit(p_txt, (play_btn.centerx - p_txt.get_width()//2, play_btn.centery - p_txt.get_height()//2))
            self.screen.blit(d_txt, (disc_btn.centerx - d_txt.get_width()//2, disc_btn.centery - d_txt.get_height()//2))
            self.screen.blit(c_txt, (clear_btn.centerx - c_txt.get_width()//2, clear_btn.centery - c_txt.get_height()//2))

        # ==========================================
        # 3. 恢复：结算缓冲界面 (REWARD)
        # ==========================================
        elif self.state.phase == 'REWARD':
            self.screen.blit(self.giant_font.render("BLIND DEFEATED!", True, self.COLORS['green']), (self.width//2 - 180, 200))
            self.screen.blit(self.font.render(f"Base Payout:    + ${self.state.last_payout['base']}", True, (200, 200, 200)), (self.width//2 - 120, 300))
            self.screen.blit(self.font.render(f"Plays Left:     + ${self.state.last_payout['plays']}", True, (200, 200, 200)), (self.width//2 - 120, 340))
            pygame.draw.line(self.screen, (100, 100, 100), (self.width//2 - 140, 380), (self.width//2 + 140, 380), 2)
            self.screen.blit(self.hud_font.render(f"TOTAL EARNED:   + ${self.state.last_payout['total']}", True, self.COLORS['yellow']), (self.width//2 - 160, 410))
            
            btn_rect = pygame.Rect(self.width//2 - 150, self.height//2 + 120, 300, 60)
            btn_hover = btn_rect.collidepoint(self.mouse_pos)
            pygame.draw.rect(self.screen, (0, 200, 150) if btn_hover else (0, 150, 100), btn_rect, border_radius=10)
            next_txt = self.title_font.render("ENTER SHOP ->", True, (255, 255, 255))
            self.screen.blit(next_txt, (btn_rect.centerx - next_txt.get_width()//2, btn_rect.centery - next_txt.get_height()//2))

        # ==========================================
        # 4. 恢复：商店界面 (SHOP & DIALOG)
        # ==========================================
        elif self.state.phase == 'SHOP':
            self.screen.blit(self.giant_font.render("=== QUANTUM SHOP ===", True, self.COLORS['text']), (self.width//2 - 250, 140))
            
            for i, shop_item in enumerate(self.state.shop_jokers):
                joker_rect = pygame.Rect(300 + i * 220, 300, 180, 250)
                is_hover = joker_rect.collidepoint(self.mouse_pos) and not self.confirm_dialog
                if is_hover: joker_rect.y -= 10
                pygame.draw.rect(self.screen, self.COLORS['card_bg'], joker_rect, border_radius=15)
                pygame.draw.rect(self.screen, self.COLORS['red'], joker_rect, border_radius=15, width=3)
                
                j_name_str = self.EN_TRANSLATION.get(shop_item['item'].name, shop_item['item'].name)
                self.screen.blit(self.font.render("JOKER", True, self.COLORS['red']), (joker_rect.centerx - 30, joker_rect.y + 20))
                self.screen.blit(self.small_font.render(j_name_str, True, self.COLORS['text']), (joker_rect.centerx - 60, joker_rect.centery))
                self.screen.blit(self.title_font.render(f"${shop_item['cost']}", True, self.COLORS['yellow']), (joker_rect.centerx - 20, joker_rect.bottom - 40))

            if self.state.shop_pack:
                pack_rect = pygame.Rect(self.width - 350, 300, 180, 250)
                is_hover = pack_rect.collidepoint(self.mouse_pos) and not self.confirm_dialog
                if is_hover: pack_rect.y -= 10
                pygame.draw.rect(self.screen, (40, 40, 55), pack_rect, border_radius=15)
                pygame.draw.rect(self.screen, self.COLORS['line'], pack_rect, border_radius=15, width=3)
                
                self.screen.blit(self.font.render("CARD PACK", True, self.COLORS['line']), (pack_rect.centerx - 45, pack_rect.centery))
                self.screen.blit(self.title_font.render(f"${self.state.shop_pack['cost']}", True, self.COLORS['yellow']), (pack_rect.centerx - 20, pack_rect.bottom - 40))

            next_btn_rect = pygame.Rect(self.width - 250, self.height - 100, 200, 60)
            btn_hover = next_btn_rect.collidepoint(self.mouse_pos) and not self.confirm_dialog
            pygame.draw.rect(self.screen, self.COLORS['green'] if btn_hover else (0, 150, 100), next_btn_rect, border_radius=10)
            next_txt = self.font.render("NEXT BLIND ->", True, (255, 255, 255))
            self.screen.blit(next_txt, (next_btn_rect.centerx - next_txt.get_width()//2, next_btn_rect.centery - next_txt.get_height()//2))

            if self.confirm_dialog:
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                
                dialog_rect = pygame.Rect(self.width//2 - 200, self.height//2 - 120, 400, 240)
                pygame.draw.rect(self.screen, self.COLORS['panel_bg'], dialog_rect, border_radius=15)
                pygame.draw.rect(self.screen, self.COLORS['green'], dialog_rect, border_radius=15, width=3)
                
                item_info = self.confirm_dialog['item_info']
                cost = item_info['cost']
                item_name = self.EN_TRANSLATION.get(item_info['item'].name, item_info['item'].name) if self.confirm_dialog['type'] == 'joker' else item_info['name']
                    
                self.screen.blit(self.font.render("CONFIRM PURCHASE", True, (200, 200, 200)), (dialog_rect.centerx - 80, dialog_rect.y + 20))
                self.screen.blit(self.title_font.render(item_name, True, (255, 255, 255)), (dialog_rect.centerx - 100, dialog_rect.y + 60))
                self.screen.blit(self.hud_font.render(f"Cost: ${cost}", True, self.COLORS['yellow']), (dialog_rect.centerx - 60, dialog_rect.y + 100))
                
                confirm_btn = pygame.Rect(self.width//2 - 150, self.height//2 + 50, 130, 50)
                cancel_btn = pygame.Rect(self.width//2 + 20, self.height//2 + 50, 130, 50)
                
                can_afford = self.state.chips >= cost
                pygame.draw.rect(self.screen, self.COLORS['green'] if confirm_btn.collidepoint(self.mouse_pos) and can_afford else ((100,100,100) if not can_afford else (0,150,100)), confirm_btn, border_radius=8)
                self.screen.blit(self.font.render("BUY", True, (255, 255, 255)), (confirm_btn.centerx - 15, confirm_btn.centery - 10))
                
                pygame.draw.rect(self.screen, self.COLORS['red'] if cancel_btn.collidepoint(self.mouse_pos) else (150, 40, 40), cancel_btn, border_radius=8)
                self.screen.blit(self.font.render("CANCEL", True, (255, 255, 255)), (cancel_btn.centerx - 30, cancel_btn.centery - 10))
        # ==========================================
        # ★ 新增：拆包动画界面 (OPENING_PACK)
        # ==========================================
        elif self.state.phase == 'OPENING_PACK':
            # 画一个半透明的黑色遮罩，聚焦视线
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            self.screen.blit(overlay, (0, 0))
            
            center_x, center_y = self.width // 2, self.height // 2
            
            if not getattr(self, 'pack_reveal', False):
                # 状态 1：还没拆开，显示巨大的卡包
                pack_rect = pygame.Rect(0, 0, 260, 360)
                pack_rect.center = (center_x, center_y)
                
                # 鼠标悬停时会微微向上浮动
                if pack_rect.collidepoint(self.mouse_pos): pack_rect.y -= 10
                
                pygame.draw.rect(self.screen, (40, 40, 55), pack_rect, border_radius=20)
                pygame.draw.rect(self.screen, self.COLORS['line'], pack_rect, border_radius=20, width=5)
                
                p_txt = self.giant_font.render("QUANTUM PACK", True, self.COLORS['line'])
                sub_txt = self.title_font.render("CLICK TO OPEN", True, (200, 200, 200))
                self.screen.blit(p_txt, (pack_rect.centerx - p_txt.get_width()//2, pack_rect.centery - 20))
                self.screen.blit(sub_txt, (pack_rect.centerx - sub_txt.get_width()//2, pack_rect.bottom + 40))
                
            else:
                # 状态 2：拆开了！展示那张卡牌！
                card = self.state.opened_card
                c_rect = pygame.Rect(0, 0, 260, 360)
                c_rect.center = (center_x, center_y)
                
                # 画两层发光的光晕（青色边框）
                pygame.draw.rect(self.screen, self.COLORS['cyan'], c_rect.inflate(40, 40), border_radius=25)
                pygame.draw.rect(self.screen, self.COLORS['bg'], c_rect.inflate(20, 20), border_radius=20)
                
                # 画巨大化的卡牌本体
                c_color = self.GATE_COLORS.get(card.gate_type, self.COLORS['card_bg'])
                pygame.draw.rect(self.screen, c_color, c_rect, border_radius=15)
                r_color = self.COLORS['rarity'].get(card.rarity, self.COLORS['rarity']['normal'])
                pygame.draw.rect(self.screen, r_color, c_rect, border_radius=15, width=6)
                
                # 巨大化的文字
                f_name = "consolas" if pygame.font.match_font("consolas") else "courier new"
                sym_font = pygame.font.SysFont(f_name, 80, bold=True)
                sym_txt = sym_font.render(card.gate_type, True, (255, 255, 255))
                name_txt = self.title_font.render(self.EN_TRANSLATION.get(card.name, card.name), True, self.COLORS['text'])
                
                self.screen.blit(sym_txt, (c_rect.centerx - sym_txt.get_width()//2, c_rect.centery - 40))
                self.screen.blit(name_txt, (c_rect.centerx - name_txt.get_width()//2, c_rect.centery + 60))
                
                if card.rarity == 'purple':
                    dur_txt = self.title_font.render(f"USES: {card.durability}", True, (20, 20, 20))
                    self.screen.blit(dur_txt, (c_rect.x + 20, c_rect.y + 20))
                    
                sub_txt = self.title_font.render("CLICK TO COLLECT", True, self.COLORS['yellow'])
                self.screen.blit(sub_txt, (c_rect.centerx - sub_txt.get_width()//2, c_rect.bottom + 40))
        # ==========================================
        # 5. 结束与重启界面
        # ==========================================
        elif self.state.phase in ['GAME_OVER', 'VICTORY']:
            m_color = self.COLORS['red'] if self.state.phase == 'GAME_OVER' else self.COLORS['green']
            self.screen.blit(self.giant_font.render("GAME OVER" if self.state.phase == 'GAME_OVER' else "SUPREMACY", True, m_color), (self.width//2 - 130, 250))
            self.screen.blit(self.title_font.render("INSUFFICIENT FIDELITY." if self.state.phase == 'GAME_OVER' else "YOU BEAT THE GAME!", True, self.COLORS['text']), (self.width//2 - 170, 320))
            
            btn_rect = pygame.Rect(self.width//2 - 150, self.height//2 + 100, 300, 70)
            pygame.draw.rect(self.screen, self.COLORS['yellow'] if btn_rect.collidepoint(self.mouse_pos) else (180, 150, 0), btn_rect, border_radius=15)
            self.screen.blit(self.title_font.render("RESTART RUN", True, (20, 20, 20)), (btn_rect.centerx - 80, btn_rect.centery - 15))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.render()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        from quantum_backend import QuantumBackend
        backend = QuantumBackend(num_qubits=3)
    except ImportError:
        backend = None
    state = GameState(backend=backend)
    state.jokers.append(SchrodingerCatJoker())
    game = DisplayEngine(state)
    game.run()