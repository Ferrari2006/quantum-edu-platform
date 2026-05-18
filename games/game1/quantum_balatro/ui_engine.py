"""
ui_engine.py
视图层：负责所有 Pygame 绘图、动画特效、色彩定义以及 UI 组件的封装。
"""
import math
import pygame

# --- 简洁量子调色盘 ---
BLACK = (10, 14, 24)
WHITE = (243, 247, 252)
GRAY = (95, 108, 132)
TEXT_DIM = (164, 176, 196)
PANEL = (20, 26, 39)
PANEL_ALT = (26, 34, 50)
LINE = (57, 73, 105)
CYAN = (38, 225, 233)
MAGENTA = (235, 74, 255)
GOLD = (255, 210, 74)
RED = (255, 94, 106)
GREEN = (70, 239, 177)


def tx(lang, zh, en):
    return zh if lang == "zh" else en


def gate_skin(name):
    skins = {
        "H": ("H", "SUPERPOSITION"),
        "X": ("X", "BIT FLIP"),
        "Z": ("Z", "PHASE SHIFT"),
        "CNOT": ("CX", "ENTANGLE"),
    }
    return skins.get(name, (name, "QUANTUM GATE"))


def fit_card_label(text, max_width, max_size, min_size=8):
    words = text.split(" ")
    for size in range(max_size, min_size - 1, -1):
        font = pygame.font.SysFont("Arial", size, bold=True)
        if font.size(text)[0] <= max_width:
            return font, [text]
        if len(words) > 1:
            split_at = len(words) // 2
            lines = [" ".join(words[:split_at]), " ".join(words[split_at:])]
            if max(font.size(line)[0] for line in lines) <= max_width:
                return font, lines
    fallback = pygame.font.SysFont("Arial", min_size, bold=True)
    if len(words) > 1:
        split_at = len(words) // 2
        return fallback, [" ".join(words[:split_at]), " ".join(words[split_at:])]
    return fallback, [text]


def draw_glow_rect(surf, rect, color, width=2, glow_range=8):
    """渲染多层发光特效"""
    for i in range(glow_range):
        alpha = max(0, 120 - i * (120 // max(glow_range, 1)))
        s = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
        pygame.draw.rect(
            s,
            (*color[:3], alpha),
            (0, 0, rect.width + i * 2, rect.height + i * 2),
            width,
            border_radius=10 + i,
        )
        surf.blit(s, (rect.x - i, rect.y - i))


def draw_grid(screen, t):
    """绘制背景量子网格"""
    width, height = screen.get_size()
    step = max(36, int(min(width, height) / 24))
    for i in range(0, width + step, step):
        offset = math.sin(t + i / 120) * 6
        pygame.draw.line(screen, (16, 24, 40), (i + offset, 0), (i + offset, height), 1)
    for j in range(0, height + step, step):
        offset = math.cos(t * 0.8 + j / 110) * 4
        pygame.draw.line(screen, (14, 21, 34), (0, j + offset), (width, j + offset), 1)


def draw_panel(screen, rect, border_color=LINE, fill_color=PANEL, radius=20):
    shadow = rect.move(0, 6)
    pygame.draw.rect(screen, (8, 11, 18), shadow, border_radius=radius)
    pygame.draw.rect(screen, fill_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=radius)


def draw_rules_screen(screen, fonts, btn_back, t, lang):
    title_font, section_font, body_font, small_font = fonts
    width, height = screen.get_size()
    screen.fill(BLACK)
    draw_grid(screen, t)

    panel = pygame.Rect(int(width * 0.08), int(height * 0.08), int(width * 0.84), int(height * 0.78))
    draw_panel(screen, panel, border_color=CYAN)

    title = tx(lang, "量子黑客手册", "QUANTUM HACKER MANUAL")
    screen.blit(title_font.render(title, True, GOLD), (panel.x + 36, panel.y + 28))
    pygame.draw.line(screen, GOLD, (panel.x + 36, panel.y + 82), (panel.right - 36, panel.y + 82), 2)

    rules = [
        (tx(lang, "[ 核心目标 ]", "[ CORE OBJECTIVE ]"), CYAN),
        (tx(lang, "拖拽量子门改变量子态概率分布，让青色柱尽量贴近金色目标框。", "Place gates to alter probabilities. Match the cyan bars to the gold target boxes."), WHITE),
        (tx(lang, "每个完全匹配的目标态最多可获得 200 基础 Chips。", "Each fully matched state grants up to 200 base chips."), TEXT_DIM),
        (tx(lang, "[ 量子门与倍率 ]", "[ GATES & MULTIPLIER ]"), CYAN),
        (tx(lang, "- H（Hadamard）：制造叠加，倍率 x1.5。", "- H (Hadamard): Creates superposition. Grants x1.5 mult."), WHITE),
        (tx(lang, "- CNOT：制造纠缠，Bell 态核心门，倍率 x2.0。", "- CNOT: Creates entanglement. Essential for Bell states. Grants x2.0 mult."), WHITE),
        (tx(lang, "- Z（Phase）：改变量子相位，激活 Phase 插件后倍率 x1.5。", "- Z (Phase): Shifts phase. Grants x1.5 mult if PHASE plugin is active."), WHITE),
        (tx(lang, "[ OBSERVE 机制 ]", "[ THE 'OBSERVE' EXPLOIT ]"), MAGENTA),
        (tx(lang, "- OBSERVE 不消耗 Hands。", "- OBSERVE does not consume Hands."), WHITE),
        (tx(lang, "- 它会保存当前倍率并清空盘面，适合继续连锁叠倍率。", "- It stores your current mult and clears the board."), WHITE),
        (tx(lang, "[ 坍缩轮盘 ]", "[ COLLAPSE ROULETTE ]"), RED),
        (tx(lang, "- 每次观测都会触发风险轮盘，可能损失 Hands、Chips 或倍率。", "- Every observation spins the roulette and may cost Hands, Chips or your mult."), WHITE),
        (tx(lang, "[ 经济与插件 ]", "[ ECONOMY & DARK WEB ]"), GREEN),
        (tx(lang, "- 过关奖励 = 关卡奖励 + 剩余 Hands 奖励。", "- Reward = Blind payout + bonus for remaining Hands."), WHITE),
        (tx(lang, "- 最多装备 2 个插件，用来突破规则或强化得分。", "- Buy up to 2 plugins (Jokers) to bend the rules."), WHITE),
    ]

    y = panel.y + 110
    for text, color in rules:
        font = section_font if text.startswith("[") else body_font
        if text.startswith("["):
            y += 10
        screen.blit(font.render(text, True, color), (panel.x + 40, y))
        y += 34 if font == section_font else 28

    btn_back.draw(screen, body_font, hover=btn_back.rect.collidepoint(pygame.mouse.get_pos()))
    screen.blit(small_font.render(tx(lang, "按 Esc 返回游戏", "Press Esc to return"), True, TEXT_DIM), (panel.x + 42, panel.bottom - 54))


def draw_shop_screen(screen, fonts, money, shop_items, btn_next, selected_item, btn_buy, btn_cancel, t, warning_msg="", lang="en"):
    title_font, section_font, body_font, small_font = fonts
    width, height = screen.get_size()
    screen.fill(BLACK)
    draw_grid(screen, t)

    header = pygame.Rect(int(width * 0.05), int(height * 0.05), int(width * 0.9), int(height * 0.16))
    shelf = pygame.Rect(int(width * 0.05), int(height * 0.25), int(width * 0.9), int(height * 0.5))
    draw_panel(screen, header, border_color=GREEN)
    draw_panel(screen, shelf, border_color=LINE)

    screen.blit(title_font.render(tx(lang, "暗网商店", "DARK WEB SHOP"), True, GREEN), (header.x + 28, header.y + 28))
    screen.blit(section_font.render(f"{tx(lang, '资金', 'FUNDS')}: ${money}", True, GOLD), (header.right - 220, header.y + 34))
    screen.blit(body_font.render(tx(lang, "选择插件强化下一关策略。", "Choose a plugin to power up the next blind."), True, TEXT_DIM), (header.x + 30, header.y + 84))

    screen.blit(section_font.render(tx(lang, "可购买插件", "AVAILABLE PLUGINS"), True, WHITE), (shelf.x + 24, shelf.y + 18))
    card_y = shelf.y + 78
    gap = min(200, max(150, (shelf.width - 120) // max(len(shop_items), 1)))
    for i, joker in enumerate(shop_items):
        joker.draw(screen, body_font, small_font, shelf.x + 30 + i * gap, card_y, show_price=True)
        if selected_item == joker:
            draw_glow_rect(screen, joker.rect, GREEN, glow_range=12)

    if warning_msg:
        screen.blit(body_font.render(warning_msg, True, RED), (shelf.x + 28, shelf.bottom - 50))

    btn_next.draw(screen, body_font, hover=btn_next.rect.collidepoint(pygame.mouse.get_pos()))

    if selected_item:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(int(width * 0.32), int(height * 0.29), int(width * 0.36), int(height * 0.32))
        draw_panel(screen, box, border_color=CYAN, fill_color=PANEL_ALT, radius=18)

        screen.blit(section_font.render(tx(lang, f"购买 {selected_item.name} ?", f"BUY {selected_item.name}?"), True, WHITE), (box.x + 30, box.y + 26))
        screen.blit(body_font.render(f"{tx(lang, '价格', 'Cost')}: ${selected_item.price}", True, GOLD), (box.x + 30, box.y + 76))
        screen.blit(body_font.render(selected_item.desc, True, WHITE), (box.x + 30, box.y + 116))

        btn_buy.draw(screen, body_font, hover=btn_buy.rect.collidepoint(pygame.mouse.get_pos()))
        btn_cancel.draw(screen, body_font, hover=btn_cancel.rect.collidepoint(pygame.mouse.get_pos()))


def draw_roulette_screen(screen, fonts, items, angle, speed, result, t, lang):
    title_font, section_font, body_font, _ = fonts
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((8, 12, 20, 230))
    screen.blit(overlay, (0, 0))
    draw_grid(screen, t)

    cx, cy = width // 2, int(height * 0.48)
    r = int(min(width, height) * 0.22)
    screen.blit(title_font.render(tx(lang, "波函数坍缩", "WAVE COLLAPSE"), True, WHITE), (cx - 220, int(height * 0.08)))

    num_items = len(items)
    step = 360 / num_items
    for i, item in enumerate(items):
        start_deg = angle + i * step
        end_deg = angle + (i + 1) * step
        points = [(cx, cy)]
        for deg in range(int(start_deg), int(end_deg) + 1):
            rad = math.radians(deg)
            points.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
        pygame.draw.polygon(screen, item["color"], points, 0)
        pygame.draw.polygon(screen, BLACK, points, 2)

        text_rad = math.radians(start_deg + step / 2)
        tx_pos = cx + (r * 0.7) * math.cos(text_rad)
        ty_pos = cy + (r * 0.7) * math.sin(text_rad)
        txt = body_font.render(item["name"], True, BLACK)
        screen.blit(txt, txt.get_rect(center=(tx_pos, ty_pos)))

    pygame.draw.polygon(screen, WHITE, [(cx + r + 16, cy), (cx + r + 50, cy - 22), (cx + r + 50, cy + 22)])

    if speed <= 0 and result:
        msg = result["msg"]
        res_txt = section_font.render(msg, True, result["color"])
        screen.blit(res_txt, res_txt.get_rect(center=(cx, int(height * 0.84))))


class Joker:
    def __init__(self, id_str, name, color, desc, price):
        self.id = id_str
        self.name = name
        self.color = color
        self.desc = desc
        self.price = price
        self.rect = pygame.Rect(0, 0, 128, 92)
        self.active = False

    def draw(self, screen, font, small_font, x, y, show_price=False):
        self.rect.topleft = (x, y)
        border = self.color if self.active else LINE
        draw_panel(screen, self.rect, border_color=border, fill_color=PANEL_ALT, radius=16)
        if self.active:
            draw_glow_rect(screen, self.rect, self.color, glow_range=8)
        screen.blit(font.render(self.name, True, self.color), (x + 12, y + 10))
        screen.blit(small_font.render(self.desc, True, WHITE), (x + 12, y + 42))
        if show_price:
            pygame.draw.line(screen, LINE, (x + 10, y + 66), (x + self.rect.width - 10, y + 66), 1)
            screen.blit(small_font.render(f"Cost: ${self.price}", True, GOLD), (x + 12, y + 72))


class Card:
    def __init__(self, name, color, x, y):
        self.name = name
        self.color = color
        self.rect = pygame.Rect(x, y, 84, 112)
        self.dragging = False

    def draw(self, screen, font, small_font=None):
        shadow = self.rect.move(0, 6)
        pygame.draw.rect(screen, (8, 12, 18), shadow, border_radius=18)
        draw_panel(screen, self.rect, border_color=self.color, fill_color=PANEL_ALT, radius=18)
        inner = self.rect.inflate(-10, -10)
        pygame.draw.rect(screen, self.color, inner, border_radius=14)

        core = inner.inflate(-10, -10)
        pygame.draw.rect(screen, PANEL, core, border_radius=12)
        glow = pygame.Surface((core.width, core.height), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*self.color, 52),
            (core.width // 2, int(core.height * 0.46)),
            max(16, min(core.width, core.height) // 3),
        )
        screen.blit(glow, core.topleft)

        symbol, effect = gate_skin(self.name)
        icon_font = pygame.font.SysFont("Arial", max(18, int(self.rect.height * 0.28)), bold=True)
        badge_font = pygame.font.SysFont("Arial", max(10, int(self.rect.height * 0.11)), bold=True)

        badge = pygame.Rect(core.x + 8, core.y + 8, core.width - 16, max(18, int(self.rect.height * 0.14)))
        pygame.draw.rect(screen, (*self.color, 255), badge, border_radius=10)
        screen.blit(
            badge_font.render("Q-GATE", True, BLACK),
            badge_font.render("Q-GATE", True, BLACK).get_rect(center=badge.center),
        )

        icon = icon_font.render(symbol, True, WHITE)
        screen.blit(icon, icon.get_rect(center=(self.rect.centerx, self.rect.centery - 10)))

        txt = font.render(self.name, True, WHITE)
        screen.blit(txt, txt.get_rect(center=(self.rect.centerx, self.rect.centery + 18)))
        if small_font:
            effect_font, effect_lines = fit_card_label(
                effect,
                core.width - 8,
                max(8, int(self.rect.height * 0.10)),
            )
            effect_base_y = self.rect.bottom - (24 if len(effect_lines) == 1 else 30)
            for idx, line in enumerate(effect_lines):
                tag = effect_font.render(line, True, (235, 240, 246))
                screen.blit(tag, tag.get_rect(center=(self.rect.centerx, effect_base_y + idx * 12)))
        if self.dragging:
            draw_glow_rect(screen, self.rect, self.color, glow_range=10)


class Slot:
    def __init__(self, x, y, idx):
        self.rect = pygame.Rect(x, y, 84, 112)
        self.qubit_idx = idx
        self.occupied_by = None


class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color

    def draw(self, screen, font, hover=False):
        shadow = self.rect.move(0, 5)
        pygame.draw.rect(screen, (8, 12, 18), shadow, border_radius=14)
        fill = tuple(min(255, c + 20) for c in self.color) if hover else self.color
        pygame.draw.rect(screen, fill, self.rect, border_radius=14)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=14)
        if hover:
            draw_glow_rect(screen, self.rect, fill, glow_range=8)
        txt = font.render(self.text, True, WHITE)
        screen.blit(txt, txt.get_rect(center=self.rect.center))
