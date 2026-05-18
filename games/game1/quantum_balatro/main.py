"""
main.py
控制器层：游戏主循环，负责状态机流转、事件监听以及连接前后端模块。
在此文件下运行代码：python main.py
"""
import random
import sys

import pygame

from quantum_core import LEVELS, calculate_score, check_boss_constraints, get_quantum_probs
from ui_engine import *

BASE_W, BASE_H = 1280, 900
GATE_COLORS = {"H": CYAN, "X": MAGENTA, "Z": GOLD, "CNOT": RED}
GATE_GUIDE = {
    "H": {
        "zh_title": "叠加",
        "zh_tip": "把单一路径拆成概率分布",
        "en_title": "Superpose",
        "en_tip": "Split one path into multiple outcomes",
    },
    "X": {
        "zh_title": "翻转",
        "zh_tip": "把 0 和 1 的结果对调",
        "en_title": "Bit Flip",
        "en_tip": "Swap the 0 and 1 outcomes",
    },
    "Z": {
        "zh_title": "相位",
        "zh_tip": "改变相位，常配合 H 使用",
        "en_title": "Phase",
        "en_tip": "Shift phase and combo with H",
    },
    "CNOT": {
        "zh_title": "纠缠",
        "zh_tip": "控制两比特联动，生成 Bell 态",
        "en_title": "Entangle",
        "en_tip": "Link two qubits to create Bell states",
    },
}
LEVEL_META = [
    {
        "zh_name": "小盲注",
        "zh_desc": "目标：纯态 |00>，先熟悉基础门的摆放。",
        "en_desc": "Target: pure state |00>. A warm-up for basic gate placement.",
    },
    {
        "zh_name": "大盲注",
        "zh_desc": "目标：Phi+ Bell 态，需要 H 与 CNOT 配合。",
        "en_desc": "Target: Phi+ Bell state. Requires H + CNOT.",
    },
    {
        "zh_name": "Boss：去相干",
        "zh_desc": "目标：Psi+ 态。每条线路门数受限，考验布局策略。",
        "en_desc": "Target: Psi+ state. Gate count is limited on each line.",
    },
]

ALL_JOKER_BLUEPRINTS = [
    {"id": "TOPOLOGY", "name": "Shield", "zh_name": "护盾", "color": CYAN, "desc": "+1 Limit", "zh_desc": "每行门数 +1", "price": 4},
    {"id": "ENTANGLE", "name": "Spark", "zh_name": "火花", "color": RED, "desc": "+100 Chips", "zh_desc": "+100 筹码", "price": 5},
    {"id": "PHASE", "name": "Phase", "zh_name": "相位", "color": GOLD, "desc": "Z:x1.5", "zh_desc": "Z 门倍率 x1.5", "price": 6},
]


def extract_gate_sequence(slots):
    active_slots = [s for s in slots if s.occupied_by]
    active_slots.sort(key=lambda s: s.rect.x)
    return [(s.occupied_by.name, s.qubit_idx) for s in active_slots]


def get_level_display(level_idx, lang):
    level = LEVELS[level_idx]
    meta = LEVEL_META[level_idx]
    if lang == "zh":
        return meta["zh_name"], meta["zh_desc"]
    return level["name"], meta["en_desc"]


def label(lang, zh, en):
    return zh if lang == "zh" else en


def gate_guide(name, lang):
    info = GATE_GUIDE[name]
    if lang == "zh":
        return info["zh_title"], info["zh_tip"]
    return info["en_title"], info["en_tip"]


def wrap_text(text, font, max_width):
    words = text.split(" ")
    if len(words) <= 1:
        return [text]

    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def clear_board(slots, cards):
    for slot in slots:
        slot.occupied_by = None
    cards.clear()


def build_fonts(scale):
    base = max(14, int(18 * scale))
    small = max(11, int(13 * scale))
    title = max(22, int(30 * scale))
    huge = max(34, int(46 * scale))
    section = max(17, int(22 * scale))
    return (
        pygame.font.SysFont("Microsoft YaHei UI", title, bold=True),
        pygame.font.SysFont("Microsoft YaHei UI", section, bold=True),
        pygame.font.SysFont("Microsoft YaHei UI", base, bold=True),
        pygame.font.SysFont("Microsoft YaHei UI", small),
    )


def compute_layout(width, height, temps, slots, cards, btns, btn_back, btn_next_blind, btn_buy, btn_cancel, top_btns):
    scale = min(width / BASE_W, height / BASE_H)
    margin = int(24 * scale)
    gap = int(18 * scale)

    top_rect = pygame.Rect(margin, margin, width - margin * 2, int(height * 0.17))
    left_width = int(width * 0.68)
    board_rect = pygame.Rect(margin, top_rect.bottom + gap, left_width, int(height * 0.41))
    deck_rect = pygame.Rect(margin, board_rect.bottom + gap, left_width, height - board_rect.bottom - gap - margin)
    side_rect = pygame.Rect(board_rect.right + gap, top_rect.bottom + gap, width - board_rect.right - gap - margin, height - top_rect.bottom - gap - margin)

    slot_w, slot_h = int(88 * scale), int(120 * scale)
    x_start = board_rect.x + int(200 * scale)
    x_gap = int(120 * scale)
    y_positions = [board_rect.y + int(110 * scale), board_rect.y + int(280 * scale)]
    for index, slot in enumerate(slots):
        row = 0 if slot.qubit_idx == 0 else 1
        col = index if index < 4 else index - 4
        if slot.qubit_idx == 1:
            col = index - 4
        slot.rect.update(x_start + col * x_gap, y_positions[row], slot_w, slot_h)
        if slot.occupied_by and not slot.occupied_by.dragging:
            slot.occupied_by.rect = slot.rect.copy()

    card_w, card_h = int(90 * scale), int(118 * scale)
    deck_card_y = deck_rect.y + int(88 * scale)
    deck_card_x = deck_rect.x + int(26 * scale)
    deck_gap = int(110 * scale)
    for index, temp in enumerate(temps):
        temp.rect.update(deck_card_x + index * deck_gap, deck_card_y, card_w, card_h)

    for card in cards:
        if not card.dragging and all(slot.occupied_by != card for slot in slots):
            card.rect.size = (card_w, card_h)

    action_w = side_rect.width - int(32 * scale)
    action_x = side_rect.x + int(16 * scale)
    action_y = side_rect.y + int(350 * scale)
    btn_gap = int(14 * scale)
    btns["obs"].rect.update(action_x, action_y, action_w, int(46 * scale))
    btns["run"].rect.update(action_x, btns["obs"].rect.bottom + btn_gap, action_w, int(52 * scale))
    btns["clr"].rect.update(action_x, btns["run"].rect.bottom + btn_gap, action_w, int(42 * scale))
    btns["rule"].rect.update(action_x, btns["clr"].rect.bottom + btn_gap, action_w, int(38 * scale))

    top_btns["lang"].rect.update(top_rect.right - int(210 * scale), top_rect.y + int(18 * scale), int(90 * scale), int(34 * scale))
    top_btns["help"].rect.update(top_rect.right - int(106 * scale), top_rect.y + int(18 * scale), int(86 * scale), int(34 * scale))

    btn_back.rect.update(width // 2 - int(95 * scale), height - margin - int(52 * scale), int(190 * scale), int(46 * scale))
    btn_next_blind.rect.update(width - margin - int(220 * scale), height - margin - int(56 * scale), int(200 * scale), int(48 * scale))
    btn_buy.rect.update(width // 2 - int(140 * scale), height // 2 + int(60 * scale), int(120 * scale), int(42 * scale))
    btn_cancel.rect.update(width // 2 + int(20 * scale), height // 2 + int(60 * scale), int(120 * scale), int(42 * scale))

    return {
        "scale": scale,
        "top": top_rect,
        "board": board_rect,
        "deck": deck_rect,
        "side": side_rect,
    }


def make_shop_items(owned_jokers):
    pool = [bp for bp in ALL_JOKER_BLUEPRINTS if bp["id"] not in [oj.id for oj in owned_jokers]]
    return [Joker(p["id"], p["name"], p["color"], p["desc"], p["price"]) for p in random.sample(pool, min(2, len(pool)))]


def main():
    pygame.init()
    screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
    pygame.display.set_caption("Quantum Hacker")

    temps = [Card("H", CYAN, 0, 0), Card("X", MAGENTA, 0, 0), Card("Z", GOLD, 0, 0), Card("CNOT", RED, 0, 0)]
    cards = []
    slots = [Slot(0, 0, 0) for _ in range(4)] + [Slot(0, 0, 1) for _ in range(4)]
    btns = {
        "obs": Button(0, 0, 0, 0, "OBSERVE", MAGENTA),
        "run": Button(0, 0, 0, 0, "PLAY HAND", GREEN),
        "clr": Button(0, 0, 0, 0, "CLEAR", GRAY),
        "rule": Button(0, 0, 0, 0, "RULES", GOLD),
    }
    top_btns = {
        "lang": Button(0, 0, 0, 0, "EN / 中", PANEL_ALT),
        "help": Button(0, 0, 0, 0, "HELP", PANEL_ALT),
    }
    btn_back = Button(0, 0, 0, 0, "BACK", CYAN)
    btn_next_blind = Button(0, 0, 0, 0, "NEXT BLIND", GREEN)
    btn_buy = Button(0, 0, 0, 0, "CONFIRM", GREEN)
    btn_cancel = Button(0, 0, 0, 0, "CANCEL", RED)

    state = "PLAY"
    lang = "zh"
    show_help = True
    lv_idx, hands, score = 0, 4, 0
    money = 3
    owned_jokers = []
    shop_items = []
    selected_shop_item = None
    shop_warning = ""

    last_c, last_m, stored_m = 0, 1.0, 1.0
    sel_card, warning, probs = None, "", {"00": 1.0}
    roulette_items = [
        {"name": "SAFE", "color": GREEN, "msg": "Waveform Stable"},
        {"name": "-1 HAND", "color": RED, "msg": "Time Dilation!"},
        {"name": "RESET MULT", "color": MAGENTA, "msg": "Multiplier Collapsed!"},
        {"name": "-200 CHIPS", "color": GOLD, "msg": "Energy Leak!"},
    ]
    roulette_angle, roulette_speed, roulette_timer, roulette_result = 0.0, 0.0, 0, None

    clock = pygame.time.Clock()

    while True:
        width, height = screen.get_size()
        layout = compute_layout(width, height, temps, slots, cards, btns, btn_back, btn_next_blind, btn_buy, btn_cancel, top_btns)
        fonts = build_fonts(layout["scale"])
        title_font, section_font, body_font, small_font = fonts
        guide_font = pygame.font.SysFont("Microsoft YaHei UI", max(10, int(13 * layout["scale"])), bold=True)
        guide_tip_font = pygame.font.SysFont("Microsoft YaHei UI", max(9, int(11 * layout["scale"])))
        t = pygame.time.get_ticks() / 1000
        m_pos = pygame.mouse.get_pos()
        cur_lv = LEVELS[lv_idx]
        level_name, level_desc = get_level_display(lv_idx, lang)
        target_probs = cur_lv["target_probs"]
        active_js = [j.id for j in owned_jokers if j.active]

        btns["obs"].text = label(lang, "观测 OBSERVE", "OBSERVE")
        btns["run"].text = label(lang, "结算 PLAY", "PLAY HAND")
        btns["clr"].text = label(lang, "清空", "CLEAR")
        btns["rule"].text = label(lang, "规则", "RULES")
        btn_back.text = label(lang, "返回游戏", "BACK TO GAME")
        btn_next_blind.text = label(lang, "进入商店", "ENTER SHOP")
        btn_buy.text = label(lang, "确认购买", "CONFIRM")
        btn_cancel.text = label(lang, "取消", "CANCEL")
        top_btns["lang"].text = "EN / 中"
        top_btns["help"].text = label(lang, "提示", "HELP")

        if state == "RULES":
            draw_rules_screen(screen, fonts, btn_back, t, lang)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((max(1040, event.w), max(760, event.h)), pygame.RESIZABLE)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "PLAY"
                if event.type == pygame.MOUSEBUTTONDOWN and btn_back.rect.collidepoint(m_pos):
                    state = "PLAY"
            pygame.display.flip()
            clock.tick(60)
            continue

        if state == "SHOP":
            draw_shop_screen(screen, fonts, money, shop_items, btn_next_blind, selected_shop_item, btn_buy, btn_cancel, t, shop_warning, lang)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((max(1040, event.w), max(760, event.h)), pygame.RESIZABLE)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "PLAY"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    shop_warning = ""
                    if not selected_shop_item and btn_next_blind.rect.collidepoint(m_pos):
                        lv_idx += 1
                        state, hands, score = "PLAY", 4, 0
                        last_c, last_m, stored_m = 0, 1.0, 1.0
                        clear_board(slots, cards)
                        probs = {"00": 1.0}
                    elif selected_shop_item:
                        if btn_buy.rect.collidepoint(m_pos):
                            if money >= selected_shop_item.price:
                                money -= selected_shop_item.price
                                owned_jokers.append(selected_shop_item)
                                shop_items.remove(selected_shop_item)
                                selected_shop_item = None
                            else:
                                shop_warning = label(lang, "资金不足", "NOT ENOUGH FUNDS!")
                        elif btn_cancel.rect.collidepoint(m_pos):
                            selected_shop_item = None
                    else:
                        for joker in shop_items:
                            if joker.rect.collidepoint(m_pos):
                                if len(owned_jokers) >= 2:
                                    shop_warning = label(lang, "最多装备 2 个插件", "MAX JOKERS REACHED!")
                                else:
                                    selected_shop_item = joker
                                break
            pygame.display.flip()
            clock.tick(60)
            continue

        if state == "ROULETTE":
            if roulette_speed > 0:
                roulette_angle = (roulette_angle + roulette_speed) % 360
                roulette_speed -= 0.08
                if roulette_speed <= 0:
                    roulette_speed = 0
                    hit_idx = int(((360 - roulette_angle) % 360) // (360 / len(roulette_items)))
                    roulette_result = roulette_items[hit_idx]
                    roulette_timer = pygame.time.get_ticks()
                    if roulette_result["name"] == "-1 HAND":
                        hands -= 1
                    elif roulette_result["name"] == "RESET MULT":
                        stored_m = 1.0
                    elif roulette_result["name"] == "-200 CHIPS":
                        score = max(0, score - 200)

            draw_roulette_screen(screen, fonts, roulette_items, roulette_angle, roulette_speed, roulette_result, t, lang)
            if roulette_speed <= 0 and roulette_result and pygame.time.get_ticks() - roulette_timer > 2200:
                state = "LOSE" if hands <= 0 else "PLAY"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((max(1040, event.w), max(760, event.h)), pygame.RESIZABLE)
            pygame.display.flip()
            clock.tick(60)
            continue

        screen.fill(BLACK)
        draw_grid(screen, t)

        draw_panel(screen, layout["top"], border_color=CYAN)
        draw_panel(screen, layout["board"], border_color=LINE)
        draw_panel(screen, layout["side"], border_color=LINE)
        draw_panel(screen, layout["deck"], border_color=LINE)

        screen.blit(title_font.render(level_name, True, RED if cur_lv["boss_type"] != "NONE" else CYAN), (layout["top"].x + 28, layout["top"].y + 22))
        desc_max_w = int(layout["top"].width * 0.48)
        for i, line in enumerate(wrap_text(level_desc, body_font, desc_max_w)[:2]):
            screen.blit(body_font.render(line, True, TEXT_DIM), (layout["top"].x + 30, layout["top"].y + 66 + i * int(22 * layout["scale"])))
        boss_label = label(lang, "普通关", "STANDARD") if cur_lv["boss_type"] == "NONE" else label(lang, "Boss 机制", "BOSS RULE")
        top_tags = [
            (label(lang, f"关卡 {lv_idx + 1}/{len(LEVELS)}", f"BLIND {lv_idx + 1}/{len(LEVELS)}"), CYAN),
            (label(lang, f"插件 {len(owned_jokers)}/2", f"JOKERS {len(owned_jokers)}/2"), GREEN),
            (boss_label, RED if cur_lv["boss_type"] != "NONE" else LINE),
        ]
        tag_x = layout["top"].x + 30
        tag_y = layout["top"].y + int(124 * layout["scale"])
        for text, color in top_tags:
            tag_w = max(int(92 * layout["scale"]), small_font.size(text)[0] + int(18 * layout["scale"]))
            tag_rect = pygame.Rect(tag_x, tag_y, tag_w, int(24 * layout["scale"]))
            pygame.draw.rect(screen, PANEL_ALT, tag_rect, border_radius=12)
            pygame.draw.rect(screen, color, tag_rect, 2, border_radius=12)
            screen.blit(small_font.render(text, True, WHITE), small_font.render(text, True, WHITE).get_rect(center=tag_rect.center))
            tag_x += tag_w + int(10 * layout["scale"])

        funds_label = f"{label(lang, '资金', 'FUNDS')}: ${money}"
        hands_label = f"{label(lang, '手数', 'HANDS')}: {hands}"
        stats_x = layout["top"].right - int(layout["top"].width * 0.32)
        screen.blit(body_font.render(funds_label, True, GOLD), (stats_x, layout["top"].y + 26))
        screen.blit(body_font.render(hands_label, True, WHITE if hands > 1 else RED), (stats_x, layout["top"].y + 58))

        progress_x = layout["top"].right - int(layout["top"].width * 0.24)
        progress_y = layout["top"].y + 92
        screen.blit(section_font.render(f"{score} / {cur_lv['target']}", True, WHITE), (progress_x, progress_y))
        bar_rect = pygame.Rect(progress_x, progress_y + 40, int(layout["top"].width * 0.22), int(12 * layout["scale"]))
        pygame.draw.rect(screen, PANEL_ALT, bar_rect, border_radius=12)
        pygame.draw.rect(screen, CYAN, (bar_rect.x, bar_rect.y, int(bar_rect.width * min(score / cur_lv["target"], 1.0)), bar_rect.height), border_radius=12)

        top_btns["lang"].draw(screen, small_font, hover=top_btns["lang"].rect.collidepoint(m_pos))
        top_btns["help"].draw(screen, small_font, hover=top_btns["help"].rect.collidepoint(m_pos))

        for i, joker in enumerate(owned_jokers):
            joker_x = layout["board"].x + int(16 * layout["scale"]) + i * int(146 * layout["scale"])
            joker_y = layout["board"].y + int(14 * layout["scale"])
            joker.draw(screen, body_font, small_font, joker_x, joker_y)

        line_y = [layout["board"].y + int(150 * layout["scale"]), layout["board"].y + int(320 * layout["scale"])]
        line_x1 = layout["board"].x + int(90 * layout["scale"])
        line_x2 = layout["board"].right - int(26 * layout["scale"])
        for idx, y in enumerate(line_y):
            pygame.draw.line(screen, (50, 64, 93), (line_x1, y), (line_x2, y), 4)
            pygame.draw.line(screen, CYAN, (line_x1, y), (line_x2, y), 1)
            screen.blit(body_font.render(f"q[{idx}]", True, WHITE), (layout["board"].x + 24, y - int(18 * layout["scale"])))

        hover_slot = None
        if sel_card:
            for slot in slots:
                if slot.rect.colliderect(sel_card.rect) and not slot.occupied_by:
                    hover_slot = slot
                    break

        for slot in slots:
            slot_fill = PANEL_ALT if not slot.occupied_by else (32, 49, 74)
            pygame.draw.rect(screen, slot_fill, slot.rect, border_radius=16)
            border = CYAN if hover_slot == slot else LINE
            pygame.draw.rect(screen, border, slot.rect, 2, border_radius=16)
            if slot.occupied_by:
                draw_glow_rect(screen, slot.rect, slot.occupied_by.color, glow_range=5)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((max(1040, event.w), max(760, event.h)), pygame.RESIZABLE)
            if state in ["WIN", "LOSE", "NEXT_BLIND"]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if state == "NEXT_BLIND":
                        state = "SHOP"
                        selected_shop_item = None
                        shop_items = make_shop_items(owned_jokers)
                    else:
                        lv_idx, money = 0, 3
                        state, hands, score = "PLAY", 4, 0
                        last_c, last_m, stored_m = 0, 1.0, 1.0
                        clear_board(slots, cards)
                        owned_jokers.clear()
                        warning = ""
                        probs = {"00": 1.0}
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l:
                    lang = "en" if lang == "zh" else "zh"
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_r:
                    clear_board(slots, cards)
                    warning = ""
                    probs = {"00": 1.0}
                elif event.key == pygame.K_SPACE:
                    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": btns["obs"].rect.center})
                    pygame.event.post(event)
                elif event.key == pygame.K_RETURN:
                    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": btns["run"].rect.center})
                    pygame.event.post(event)
                elif event.key == pygame.K_ESCAPE:
                    state = "RULES"

            if event.type == pygame.MOUSEBUTTONDOWN:
                gate_sequence = extract_gate_sequence(slots)
                if top_btns["lang"].rect.collidepoint(m_pos):
                    lang = "en" if lang == "zh" else "zh"
                    continue
                if top_btns["help"].rect.collidepoint(m_pos):
                    show_help = not show_help
                    continue
                if btns["rule"].rect.collidepoint(m_pos):
                    state = "RULES"
                elif btns["clr"].rect.collidepoint(m_pos):
                    clear_board(slots, cards)
                    warning = ""
                    probs = {"00": 1.0}
                elif btns["run"].rect.collidepoint(m_pos):
                    valid, msg = check_boss_constraints(gate_sequence, cur_lv["boss_type"], active_js)
                    if not valid:
                        warning = msg
                    else:
                        c, m = calculate_score(probs, target_probs, gate_sequence, active_js)
                        score += int(c * m * stored_m)
                        last_c, last_m, hands, stored_m = c, m * stored_m, hands - 1, 1.0
                        clear_board(slots, cards)
                        if score >= cur_lv["target"]:
                            money += cur_lv.get("reward", 4) + hands
                            state = "WIN" if lv_idx == len(LEVELS) - 1 else "NEXT_BLIND"
                        elif hands <= 0:
                            state = "LOSE"
                elif btns["obs"].rect.collidepoint(m_pos):
                    valid, msg = check_boss_constraints(gate_sequence, cur_lv["boss_type"], active_js)
                    if not valid:
                        warning = msg
                    else:
                        _, m = calculate_score(probs, target_probs, gate_sequence, active_js)
                        stored_m *= m
                        clear_board(slots, cards)
                        probs = {"00": 1.0}
                        state = "ROULETTE"
                        roulette_speed, roulette_angle, roulette_result = random.uniform(18.0, 30.0), 0.0, None

                for joker in owned_jokers:
                    if joker.rect.collidepoint(m_pos):
                        joker.active = not joker.active

                for card in reversed(cards):
                    if card.rect.collidepoint(m_pos):
                        sel_card = card
                        card.dragging = True
                        for slot in slots:
                            if slot.occupied_by == card:
                                slot.occupied_by = None
                        break

                if not sel_card:
                    for template in temps:
                        if template.rect.collidepoint(m_pos):
                            new_card = Card(template.name, template.color, template.rect.x, template.rect.y)
                            new_card.rect.size = template.rect.size
                            new_card.dragging = True
                            cards.append(new_card)
                            sel_card = new_card
                            break

            if event.type == pygame.MOUSEBUTTONUP and sel_card:
                sel_card.dragging = False
                snapped = False
                for slot in slots:
                    if slot.rect.colliderect(sel_card.rect) and not slot.occupied_by:
                        sel_card.rect = slot.rect.copy()
                        slot.occupied_by = sel_card
                        snapped = True
                        break
                if not snapped and sel_card in cards:
                    cards.remove(sel_card)
                sel_card = None
                warning = ""
                probs = get_quantum_probs(extract_gate_sequence(slots))

            if event.type == pygame.MOUSEMOTION and sel_card:
                sel_card.rect.center = pygame.mouse.get_pos()

        for card in cards:
            card.draw(screen, body_font, small_font)

        screen.blit(section_font.render(label(lang, "量子门卡库", "CARD LIBRARY"), True, CYAN), (layout["deck"].x + 24, layout["deck"].y + 18))
        screen.blit(small_font.render(label(lang, "拖拽量子门到量子线路中，尝试逼近目标态。", "Drag gates onto the quantum lines and shape the target state."), True, TEXT_DIM), (layout["deck"].x + 26, layout["deck"].y + 48))
        pygame.draw.line(screen, LINE, (layout["deck"].x + 24, layout["deck"].y + 70), (layout["deck"].right - 24, layout["deck"].y + 70), 1)
        for template in temps:
            template.draw(screen, body_font, small_font)
            title_text, tip_text = gate_guide(template.name, lang)
            desc_y = template.rect.bottom + int(10 * layout["scale"])
            title_surface = guide_font.render(title_text, True, template.color)
            screen.blit(title_surface, title_surface.get_rect(center=(template.rect.centerx, desc_y)))
            tip_lines = wrap_text(tip_text, guide_tip_font, template.rect.width + int(12 * layout["scale"]))[:2]
            for idx, line in enumerate(tip_lines):
                line_surface = guide_tip_font.render(line, True, TEXT_DIM)
                line_y = desc_y + int(16 * layout["scale"]) + idx * int(14 * layout["scale"])
                screen.blit(line_surface, line_surface.get_rect(center=(template.rect.centerx, line_y)))

        chart_rect = pygame.Rect(layout["side"].x + 18, layout["side"].y + 24, layout["side"].width - 36, int(layout["side"].height * 0.42))
        draw_panel(screen, chart_rect, border_color=CYAN, fill_color=PANEL_ALT, radius=18)
        screen.blit(section_font.render(label(lang, "目标匹配", "TARGET MATCH"), True, WHITE), (chart_rect.x + 18, chart_rect.y + 14))
        screen.blit(small_font.render(label(lang, "金框表示目标，青柱表示当前概率", "Gold frame = target, cyan bars = current probability"), True, TEXT_DIM), (chart_rect.x + 18, chart_rect.y + 42))

        states = ["00", "01", "10", "11"]
        plot_left = chart_rect.x + int(24 * layout["scale"])
        plot_right = chart_rect.right - int(24 * layout["scale"])
        legend_y = chart_rect.bottom - int(40 * layout["scale"])
        bar_base_y = legend_y - int(22 * layout["scale"])
        bar_top_y = chart_rect.y + int(88 * layout["scale"])
        bar_max_h = bar_base_y - bar_top_y
        group_w = (plot_right - plot_left) / len(states)
        bar_w = max(18, min(int(34 * layout["scale"]), int(group_w * 0.52)))
        grid_labels = [0.25, 0.5, 0.75, 1.0]
        for mark in grid_labels:
            y = bar_base_y - int(mark * bar_max_h)
            pygame.draw.line(screen, (45, 58, 82), (plot_left, y), (plot_right, y), 1)
            pct = f"{int(mark * 100)}%"
            pct_surface = small_font.render(pct, True, TEXT_DIM)
            screen.blit(pct_surface, (plot_right - pct_surface.get_width(), y - 10))
        for i, st in enumerate(states):
            target = target_probs.get(st, 0)
            current = probs.get(st, 0)
            bar_x = int(plot_left + i * group_w + (group_w - bar_w) / 2)
            pygame.draw.rect(screen, PANEL, (bar_x, bar_top_y, bar_w, bar_max_h), border_radius=8)
            if target > 0:
                th = int(target * bar_max_h)
                pygame.draw.rect(screen, GOLD, (bar_x, bar_base_y - th, bar_w, th), 2, border_radius=8)
            bh = int(current * bar_max_h)
            bar_rect = pygame.Rect(bar_x, bar_base_y - bh, bar_w, bh)
            pygame.draw.rect(screen, CYAN, bar_rect, border_radius=8)
            if bh > 0:
                draw_glow_rect(screen, bar_rect, CYAN, glow_range=5)
            pct_text = small_font.render(f"{int(current * 100)}%", True, WHITE)
            screen.blit(pct_text, pct_text.get_rect(center=(bar_x + bar_w // 2, bar_top_y - 12)))
            screen.blit(small_font.render(st, True, WHITE), (bar_x - 2, bar_base_y + 12))

        gold_legend = small_font.render(label(lang, "金色轮廓 = 目标", "Gold outline = target"), True, GOLD)
        cyan_legend = small_font.render(label(lang, "青色柱 = 当前", "Cyan bar = current"), True, CYAN)
        screen.blit(gold_legend, (chart_rect.x + 18, legend_y))
        screen.blit(cyan_legend, (chart_rect.x + 18, legend_y + int(18 * layout["scale"])))

        for button in btns.values():
            button.draw(screen, body_font, hover=button.rect.collidepoint(m_pos))

        info_y = btns["rule"].rect.bottom + int(24 * layout["scale"])
        if stored_m > 1.0:
            msg = label(lang, f"存储倍率 x{stored_m:.2f}", f"Stored Mult x{stored_m:.2f}")
            screen.blit(section_font.render(msg, True, MAGENTA), (layout["side"].x + 18, info_y))
        elif warning:
            screen.blit(body_font.render(warning, True, RED), (layout["side"].x + 18, info_y))
        elif last_c > 0:
            msg = label(lang, f"上次结算 {last_c} x {last_m:.2f}", f"Last hand {last_c} x {last_m:.2f}")
            screen.blit(body_font.render(msg, True, WHITE), (layout["side"].x + 18, info_y))

        if show_help:
            help_y = max(info_y + int(34 * layout["scale"]), layout["side"].bottom - int(96 * layout["scale"]))
            screen.blit(small_font.render(label(lang, "快捷键", "SHORTCUTS"), True, TEXT_DIM), (layout["side"].x + 18, help_y))
            hints = [
                label(lang, "L 切换中英", "L Toggle language"),
                label(lang, "H 开关帮助", "H Toggle help"),
                label(lang, "R 清空线路", "R Clear board"),
                label(lang, "Enter 结算 / Space 观测", "Enter Play / Space Observe"),
            ]
            for i, hint in enumerate(hints):
                screen.blit(small_font.render(hint, True, TEXT_DIM), (layout["side"].x + 18, help_y + 18 + i * 18))

        if state in ["WIN", "LOSE", "NEXT_BLIND"]:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            msg = {
                "WIN": label(lang, "突破成功，点击重新开始", "FIREWALL BREACHED. CLICK TO RESTART"),
                "LOSE": label(lang, "波函数坍缩，点击重开", "WAVE COLLAPSED. CLICK TO RESTART"),
                "NEXT_BLIND": label(lang, "当前关卡完成，点击进入商店", "BLIND DEFEATED. CLICK TO ENTER SHOP"),
            }[state]
            color = GREEN if state != "LOSE" else RED
            text = title_font.render(msg, True, color)
            screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
