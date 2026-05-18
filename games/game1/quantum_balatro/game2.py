import pygame
import sys
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

simulator=AerSimulator()

LEVELS=[
    {"name":"Small Blind","target":1500,"boss_type":"NONE","desc":"Standard. H_mult x1.5, CNOT_mult x2.0"},
    {"name":"Big Blind","target":8000,"boss_type":"NONE","desc":"Use OBSERVE to stack multipliers!"},
    {"name":"Boss: Decoherence","target":20000,"boss_type":"DECOHERENCE","desc":"MAX 2 gates/line. Collapse is the only way."}
]

def get_quantum_probs(slots):
    active_slots=[s for s in slots if s.occupied_by]
    active_slots.sort(key=lambda s:s.rect.x)
    qc=QuantumCircuit(2)
    for s in active_slots:
        gate=s.occupied_by.name
        q_idx=s.qubit_idx
        if gate=="H":qc.h(q_idx)
        elif gate=="X":qc.x(q_idx)
        elif gate=="Z":qc.z(q_idx)
        elif gate=="CNOT":qc.cx(q_idx,1-q_idx)
    qc.save_statevector()
    try:
        return simulator.run(qc).result().get_statevector().probabilities_dict()
    except Exception:
        return {"00":1.0}

def check_boss_constraints(slots,boss_type):
    if boss_type=="DECOHERENCE":
        q0_count=len([s for s in slots if s.qubit_idx==0 and s.occupied_by])
        q1_count=len([s for s in slots if s.qubit_idx==1 and s.occupied_by])
        if q0_count>2 or q1_count>2:
            return False,"DECOHERENCE: Max 2 gates per line!"
    return True,""

def calculate_score(probs,target_probs,slots):
    base_chips=0
    for state,target_p in target_probs.items():
        base_chips+=min(probs.get(state,0),target_p)*200
    mult=1.0
    active_gates=[s.occupied_by.name for s in slots if s.occupied_by]
    for g in active_gates:
        if g=="H":mult*=1.5 
    if "CNOT" in active_gates:mult*=2.0
    return int(base_chips),round(mult,2)

WIDTH,HEIGHT=1000,750
BLACK,WHITE,GRAY=(20,20,25),(240,240,240),(60,60,70)
BLUE,PURPLE,ORANGE,RED,GREEN=(51,153,255),(153,51,255),(255,165,0),(255,60,60),(46,204,113)

class Card:
    def __init__(self,name,color,x,y):
        self.name=name; self.color=color
        self.rect=pygame.Rect(x,y,75,95); self.is_dragging=False

class Slot:
    def __init__(self,x,y,qubit_idx):
        self.rect=pygame.Rect(x,y,75,95)
        self.qubit_idx=qubit_idx; self.occupied_by=None

class Button:
    def __init__(self,x,y,w,h,text,color):
        self.rect=pygame.Rect(x,y,w,h); self.text=text; self.color=color
    def draw(self,screen,font):
        pygame.draw.rect(screen,self.color,self.rect,border_radius=8)
        txt=font.render(self.text,True,WHITE)
        screen.blit(txt,txt.get_rect(center=self.rect.center))
    def is_clicked(self,pos):
        return self.rect.collidepoint(pos)

def draw_rules_screen(screen, big_font, font, btn_back):
    """绘制规则讲解页"""
    screen.fill((15, 15, 20)) # 更深的背景色
    pygame.draw.rect(screen, GRAY, (50, 50, 900, 600), 2, border_radius=15)
    
    screen.blit(big_font.render("QUANTUM HACKER MANUAL", True, ORANGE), (300, 80))
    pygame.draw.line(screen, ORANGE, (300, 120), (700, 120), 3)
    
    rules_text = [
        ("1. THE GOAL (CHIPS)", BLUE),
        ("Match the target probabilities (Bell State). Perfect match grants 200 base chips.", WHITE),
        ("", WHITE),
        ("2. QUANTUM GATES (MULTIPLIER)", PURPLE),
        ("[H] Gate: Creates superposition. Grants x1.5 Multiplier per gate.", WHITE),
        ("[CNOT] Gate: Creates entanglement. Grants x2.0 Multiplier to the entire board.", WHITE),
        ("", WHITE),
        ("3. THE EXPLOIT: 'OBSERVE' (COLLAPSE)", GREEN),
        ("Click OBSERVE to instantly store your current multiplier into memory.", WHITE),
        ("This collapses the wave (clears the board) but DOES NOT consume 'Hands'.", WHITE),
        ("Repeat this to chain multipliers exponentially: x1.5 -> x2.25 -> x5.06 -> x100+!", WHITE),
        ("", WHITE),
        ("4. HARDWARE LIMITS (BOSS BLIND)", RED),
        ("Bosses have physical limits (e.g., Max 2 gates per line).", WHITE),
        ("You MUST use the OBSERVE trick to bypass these physical limits and reach", WHITE),
        ("Quantum Supremacy (20,000+ Score)!", WHITE)
    ]
    
    y_offset = 150
    for text, color in rules_text:
        screen.blit(font.render(text, True, color), (80, y_offset))
        y_offset += 28
        
    btn_back.draw(screen, font)

def main():
    pygame.init()
    screen=pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Quantum Balatro - Innovation Edition")
    font=pygame.font.SysFont("Arial",20)
    big_font=pygame.font.SysFont("Arial",32,bold=True)
    
    templates=[
        Card("H",BLUE,50,600),Card("X",PURPLE,150,600), 
        Card("Z",ORANGE,250,600),Card("CNOT",RED,350,600)
    ]
    cards=[]
    slots=[Slot(x,y,q) for q,y in {0:200,1:350}.items() for x in range(300,700,100)]
    
    # 按钮布局优化
    btn_observe=Button(820,510,140,40,"OBSERVE",PURPLE)
    btn_run=Button(820,560,140,50,"PLAY HAND",GREEN)
    btn_clear=Button(820,620,140,40,"CLEAR",GRAY)
    btn_rules=Button(820,670,140,40,"RULES",ORANGE)
    btn_back=Button(430,580,140,50,"BACK TO GAME",GREEN) # 规则页的返回按钮
    
    current_probs={"00":1.0}
    target_probs={"00":0.5,"11":0.5}
    selected_card=None
    
    level_idx=0
    hands_left=4
    total_score=0
    last_chips,last_mult=0,1.0
    stored_mult=1.0 
    game_state="PLAYING" # 新增状态：RULES
    warning_msg=""

    clock=pygame.time.Clock()

    while True:
        if game_state == "RULES":
            draw_rules_screen(screen, big_font, font, btn_back)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:pygame.quit();sys.exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if btn_back.is_clicked(event.pos):
                        game_state="PLAYING"
            pygame.display.flip()
            clock.tick(60)
            continue # 跳过主界面的渲染

        # --- 以下为主界面渲染逻辑 ---
        screen.fill(BLACK)
        cur_level=LEVELS[level_idx]
        target_score=cur_level["target"]
        boss_type=cur_level["boss_type"]

        pygame.draw.rect(screen,(30,30,40),(20,20,960,110),border_radius=10)
        level_color=RED if boss_type!="NONE" else ORANGE
        screen.blit(big_font.render(cur_level["name"],True,level_color),(40,30))
        screen.blit(font.render(cur_level["desc"],True,WHITE),(40,75))
        
        screen.blit(big_font.render(f"SCORE: {total_score} / {target_score}",True,WHITE),(450,30))
        screen.blit(font.render(f"Hands left: {hands_left}",True,WHITE),(450,75))
        
        progress=min(total_score/target_score,1.0)
        pygame.draw.rect(screen,GRAY,(750,50,200,20),border_radius=10)
        pygame.draw.rect(screen,BLUE,(750,50,200*progress,20),border_radius=10)

        if stored_mult>1.0:
            screen.blit(big_font.render(f"STORED MULT: x{round(stored_mult,2)}",True,PURPLE),(450,140))
        elif warning_msg:
            screen.blit(big_font.render(warning_msg,True,RED),(300,140))
        elif last_chips>0 and game_state=="PLAYING":
            screen.blit(font.render(f"Last Hand: {last_chips} X {last_mult} = {int(last_chips*last_mult)}",True,GRAY),(450,140))

        pygame.draw.line(screen,WHITE,(100,247),(800,247),2)
        pygame.draw.line(screen,WHITE,(100,397),(800,397),2)
        screen.blit(font.render("q[0]",True,WHITE),(60,235))
        screen.blit(font.render("q[1]",True,WHITE),(60,385))

        for event in pygame.event.get():
            if event.type==pygame.QUIT:pygame.quit();sys.exit()
            
            if game_state in ["BLIND_CLEARED","GAME_OVER","RUN_WON"]:
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if game_state=="BLIND_CLEARED":
                        level_idx+=1
                        game_state="PLAYING"
                    elif game_state in ["GAME_OVER","RUN_WON"]:
                        level_idx=0
                        game_state="PLAYING"
                    hands_left,total_score,last_chips,last_mult,stored_mult=4,0,0,1.0,1.0
                    warning_msg=""
                    current_probs={"00":1.0}
                    for s in slots:s.occupied_by=None
                    cards.clear()
                continue

            if event.type==pygame.MOUSEBUTTONDOWN:
                if btn_rules.is_clicked(event.pos):
                    game_state="RULES" # 切换到规则页状态
                
                elif btn_observe.is_clicked(event.pos) and hands_left>0:
                    valid,msg=check_boss_constraints(slots,boss_type)
                    if not valid: warning_msg=msg
                    else:
                        c,m=calculate_score(current_probs,target_probs,slots)
                        stored_mult*=m
                        warning_msg=""
                        for s in slots:s.occupied_by=None
                        cards.clear()
                        current_probs={"00":1.0}

                elif btn_run.is_clicked(event.pos) and hands_left>0:
                    valid,msg=check_boss_constraints(slots,boss_type)
                    if not valid: warning_msg=msg
                    else:
                        warning_msg=""
                        c,m=calculate_score(current_probs,target_probs,slots)
                        final_mult=stored_mult*m
                        total_score+=int(c*final_mult)
                        last_chips,last_mult=c,final_mult
                        hands_left-=1
                        stored_mult=1.0
                        for s in slots:s.occupied_by=None
                        cards.clear()
                        current_probs={"00":1.0}
                        
                        if total_score>=target_score:
                            if level_idx==len(LEVELS)-1:game_state="RUN_WON"
                            else:game_state="BLIND_CLEARED"
                        elif hands_left==0:
                            game_state="GAME_OVER"

                elif btn_clear.is_clicked(event.pos):
                    for s in slots:s.occupied_by=None
                    cards.clear()
                    current_probs={"00":1.0}
                    warning_msg=""
                
                for card in cards:
                    if card.rect.collidepoint(event.pos):
                        selected_card=card
                        card.is_dragging=True
                        for s in slots:
                            if s.occupied_by==card:s.occupied_by=None
                        break
                if not selected_card:
                    for temp in templates:
                        if temp.rect.collidepoint(event.pos):
                            new_card=Card(temp.name,temp.color,temp.rect.x,temp.rect.y)
                            new_card.is_dragging=True
                            cards.append(new_card)
                            selected_card=new_card
                            break
            
            if event.type==pygame.MOUSEBUTTONUP and selected_card:
                selected_card.is_dragging=False
                snapped=False
                for s in slots:
                    if s.rect.colliderect(selected_card.rect) and not s.occupied_by:
                        selected_card.rect.topleft=s.rect.topleft
                        s.occupied_by=selected_card
                        snapped=True
                        break
                if not snapped:cards.remove(selected_card)
                current_probs=get_quantum_probs(slots)
                selected_card=None
                warning_msg=""

            if event.type==pygame.MOUSEMOTION and selected_card:
                selected_card.rect.center=event.pos

        for s in slots:
            pygame.draw.rect(screen,(40,40,50),s.rect,border_radius=5)
            pygame.draw.rect(screen,GRAY,s.rect,1,border_radius=5)

        cx,cy=820,200
        pygame.draw.rect(screen,(30,30,40),(cx-10,cy-20,150,300))
        for i,st in enumerate(["00","01","10","11"]):
            p=current_probs.get(st,0)
            bh=int(p*200)
            pygame.draw.rect(screen,BLUE,(cx+i*35,cy+200-bh,25,bh))
            screen.blit(font.render(st,True,WHITE),(cx+i*35,cy+210))

        pygame.draw.rect(screen,GRAY,(20,580,960,140),2,border_radius=10)
        for t in templates:
            pygame.draw.rect(screen,t.color,t.rect,border_radius=8,width=2)
            txt=font.render(t.name,True,t.color)
            screen.blit(txt,txt.get_rect(center=t.rect.center))
        for c in cards:
            pygame.draw.rect(screen,c.color,c.rect,border_radius=8)
            txt=font.render(c.name,True,WHITE)
            screen.blit(txt,txt.get_rect(center=c.rect.center))

        btn_observe.draw(screen,font)
        btn_run.draw(screen,font)
        btn_clear.draw(screen,font)
        btn_rules.draw(screen,font) # 绘制 RULES 按钮

        if game_state=="BLIND_CLEARED":
            pygame.draw.rect(screen,(20,20,25,200),(0,0,WIDTH,HEIGHT))
            screen.blit(big_font.render("BLIND DEFEATED!",True,GREEN),(350,300))
        elif game_state=="RUN_WON":
            pygame.draw.rect(screen,(20,20,25,200),(0,0,WIDTH,HEIGHT))
            screen.blit(big_font.render("CONGRATULATIONS! QUANTUM SUPREMACY REACHED!",True,ORANGE),(100,300))
        elif game_state=="GAME_OVER":
            pygame.draw.rect(screen,(20,20,25,200),(0,0,WIDTH,HEIGHT))
            screen.blit(big_font.render("WAVE COLLAPSED! GAME OVER",True,RED),(280,300))

        pygame.display.flip()
        clock.tick(60)

if __name__=="__main__":
    main()