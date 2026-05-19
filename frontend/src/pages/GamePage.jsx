import { useEffect, useMemo, useRef, useState } from "react";
import "./GamePage.css";

const API_BASE = "/api/quantum-game";
const GATES = ["H", "X", "Z", "CNOT"];
const GATE_DETAILS = {
  H: {
    name: "Hadamard",
    role: "Superposition",
    text: "Split one line into 50/50 probability.",
  },
  X: {
    name: "Pauli-X",
    role: "Bit Flip",
    text: "Flip |0> into |1> on one line.",
  },
  Z: {
    name: "Pauli-Z",
    role: "Phase",
    text: "Phase tool for boss locks and joker combos.",
  },
  CNOT: {
    name: "CNOT",
    role: "Entangle",
    text: "Control one line and flip the other.",
  },
};
const STATES = ["00", "01", "10", "11"];
const DRAG_TYPE = "application/quantum-game";
const CIRCUIT_TUTORIAL_STORAGE_KEY = "quantum-hacker-tutorial-complete";
const CONCEPT_CODEX_STORAGE_KEY = "quantum-concept-codex";
const CONTROLLED_GATES = new Set(["CNOT", "CZ", "SWAP"]);
const CIRCUIT_TUTORIAL_STEPS = [
  {
    key: "circuit-intro",
    title: "欢迎来到 Quantum Hacker",
    body: "这是一局两比特线路谜题。每个盲注都有目标概率分布，你要搭出尽量接近目标的量子线路来得分。",
    cue: "点击继续",
  },
  {
    key: "circuit-target",
    title: "先看右侧目标",
    body: "柱状图里蓝色是当前线路概率，黄色标记是目标概率。越贴近目标，基础筹码越高。",
    cue: "看目标概率",
  },
  {
    key: "circuit-gates",
    title: "选择并打出门卡",
    body: "H、X、Z、CNOT 现在是门卡。先点一张卡选中，再点线路插槽打出；也可以直接把门卡拖进插槽。",
    cue: "看门和插槽",
  },
  {
    key: "circuit-risk",
    title: "Observe 是风险按钮",
    body: "Observe 会保存当前倍数，但会触发轮盘事件。用得越多、存的倍数越高，风险越大。",
    cue: "看 Observe",
  },
  {
    key: "circuit-score",
    title: "准备好就 Play Hand",
    body: "Play Hand 会结算当前线路、消耗一次出手机会，并在达标后进入商店。Boss 关还会限制线路规则。",
    cue: "开始破解",
  },
];
const CARD_TUTORIAL_STEPS = [
  {
    key: "intro",
    title: "欢迎来到量子卡牌局",
    body: "这一局的目标是在出牌次数用完前达到盲注分数。你会把手牌变成一段量子线路，然后按保真度结算分数。",
    cue: "点击继续",
  },
  {
    key: "hand",
    title: "先看底部手牌",
    body: "每张牌是一种量子门。点击手牌可以选中并弃牌，拖拽手牌可以放进上方线路。",
    cue: "看手牌",
  },
  {
    key: "stage",
    title: "拖到线路插槽",
    body: "横向插槽代表时间顺序，纵向行代表作用在哪个量子比特上。也可以把鼠标移到空插槽上，直接点弹出的门名。",
    cue: "看线路",
  },
  {
    key: "control",
    title: "受控门要选目标",
    body: "CNOT、CZ、SWAP 这类多比特门会显示目标选择器。源比特和目标比特的方向会影响纠缠结果。",
    cue: "看目标选择",
  },
  {
    key: "score",
    title: "出牌并观察结算",
    body: "右侧会显示最近一次牌型、分数拆解和教学提示。准备好后按 Play Hand；不想要的牌可以选中后 Discard。",
    cue: "开始游戏",
  },
];

const CONCEPT_LIBRARY = [
  { id: "gate-h", group: "Gates", title: "H gate", desc: "Creates superposition: one basis state can split into multiple measurement outcomes." },
  { id: "gate-x", group: "Gates", title: "X gate", desc: "A bit flip. It maps |0> to |1> and |1> to |0>." },
  { id: "gate-z", group: "Gates", title: "Z gate", desc: "A phase flip. It may not change measurement probability immediately, but it changes interference." },
  { id: "gate-cnot", group: "Gates", title: "CNOT gate", desc: "A controlled operation. On superposition, it can create entanglement." },
  { id: "gate-cz", group: "Gates", title: "CZ gate", desc: "A controlled phase gate. It links qubits through phase rather than a visible bit flip." },
  { id: "gate-swap", group: "Gates", title: "SWAP gate", desc: "Exchanges the states of two qubits, making routing part of the puzzle." },
  { id: "gate-rx", group: "Gates", title: "RX gate", desc: "A continuous rotation around the X axis of the Bloch sphere." },
  { id: "gate-ry", group: "Gates", title: "RY gate", desc: "A continuous rotation around the Y axis of the Bloch sphere." },
  { id: "gate-rz", group: "Gates", title: "RZ gate", desc: "A continuous rotation around the Z axis, changing relative phase." },
  { id: "gate-ccx", group: "Gates", title: "CCX gate", desc: "The Toffoli gate: two controls decide whether a target qubit flips." },
  { id: "formula-probability", group: "Formulas", title: "Measurement probability", desc: "P(s) = |amplitude(s)|^2. Game1 scores by matching measured probabilities." },
  { id: "formula-fidelity", group: "Formulas", title: "State fidelity", desc: "F = |<target|current>|^2. Game2 scores how close your circuit state is to a target state." },
  { id: "formula-score", group: "Formulas", title: "Score formula", desc: "Score combines base chips, multipliers, and either probability overlap or fidelity." },
  { id: "state-bell", group: "States", title: "Bell pair", desc: "A two-qubit entangled state with strong correlation between measurement outcomes." },
  { id: "state-ghz", group: "States", title: "GHZ state", desc: "A multi-qubit entangled state where all qubits share one global correlation." },
  { id: "state-w", group: "States", title: "W state", desc: "A multi-qubit state with one excitation shared across several qubits." },
  { id: "state-phase", group: "States", title: "Phase lock", desc: "A situation where probabilities may look close, but relative phase controls fidelity." },
  { id: "state-rotation", group: "States", title: "Rotation trio", desc: "A hand that introduces continuous rotations instead of only discrete flips." },
  { id: "system-measurement", group: "Systems", title: "Measurement collapse", desc: "Observation extracts information, then the prepared circuit no longer stays untouched." },
  { id: "system-overlap", group: "Systems", title: "Target overlap", desc: "A circuit can be evaluated by how much of its output distribution overlaps the target." },
  { id: "system-boss", group: "Systems", title: "Hardware constraints", desc: "Boss rules represent limits like depth, routing, phase requirements, and gate count." },
  { id: "system-clear", group: "Systems", title: "Blind cleared", desc: "Clearing a blind means your quantum strategy met the scoring target." },
  { id: "system-failure", group: "Systems", title: "Run failed", desc: "Failure is a useful diagnostic: compare gates, targets, and the recap to plan the next circuit." },
];

const CONCEPT_BY_ID = Object.fromEntries(CONCEPT_LIBRARY.map((concept) => [concept.id, concept]));

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

function loadConceptIds() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(CONCEPT_CODEX_STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.filter((id) => CONCEPT_BY_ID[id]) : [];
  } catch {
    return [];
  }
}

function saveConceptIds(ids) {
  window.localStorage.setItem(CONCEPT_CODEX_STORAGE_KEY, JSON.stringify(ids));
}

function collectConceptIds(state) {
  const ids = new Set(["formula-score"]);
  if (state.kind === "circuit") {
    ["gate-h", "gate-x", "gate-z", "gate-cnot", "formula-probability", "system-overlap"].forEach((id) => ids.add(id));
    (state.hand_cards || []).forEach((card) => ids.add(gateConceptId(card.gate)));
    (state.gates || []).forEach((gate) => ids.add(gateConceptId(gate.gate)));
    (state.last_recap?.gates || []).forEach((gate) => ids.add(gateConceptId(gate.gate)));
    if (state.phase === "ROULETTE" || state.last_roulette) ids.add("system-measurement");
    if (["SHOP", "WIN"].includes(state.phase)) ids.add("system-clear");
    if (state.phase === "GAME_OVER") ids.add("system-failure");
    if (state.level?.boss_type && state.level.boss_type !== "NONE") ids.add("system-boss");
  }

  if (state.kind === "cards") {
    ids.add("formula-fidelity");
    (state.hand_cards || []).forEach((card) => ids.add(gateConceptId(card.gate)));
    (state.last_recap?.gates || []).forEach((gate) => ids.add(gateConceptId(gate)));
    handConceptIds(state.last_hand_played).forEach((id) => ids.add(id));
    if (["REWARD", "SHOP", "VICTORY"].includes(state.phase)) ids.add("system-clear");
    if (state.phase === "GAME_OVER") ids.add("system-failure");
  }

  return [...ids].filter((id) => CONCEPT_BY_ID[id]);
}

function gateConceptId(gate) {
  const key = String(gate || "").toLowerCase();
  return key ? `gate-${key === "cx" ? "cnot" : key}` : "";
}

function handConceptIds(handName = "") {
  const ids = [];
  if (handName.includes("Bell")) ids.push("state-bell");
  if (handName.includes("GHZ")) ids.push("state-ghz");
  if (handName.includes("W State")) ids.push("state-w");
  if (handName.includes("Phase")) ids.push("state-phase");
  if (handName.includes("Rotation")) ids.push("state-rotation");
  return ids;
}

const BUILD_ARCHETYPES = {
  Entanglement: {
    label: "Entanglement",
    hint: "CNOT and Bell-style hands turn correlation into bonus chips.",
    gates: ["CNOT", "CX"],
    wants: ["CNOT", "Bell Pair", "Stabilizer"],
  },
  Phase: {
    label: "Phase",
    hint: "Z/CZ effects convert invisible phase into multiplier value.",
    gates: ["Z", "CZ", "RZ"],
    wants: ["Z", "CZ", "Phase Key"],
  },
  Compiler: {
    label: "Compiler",
    hint: "Short circuits and lean gate paths score harder.",
    gates: [],
    wants: ["Shield", "low gate count", "clean target overlap"],
  },
  Topology: {
    label: "Topology",
    hint: "Routing and constraint tools make awkward boss rules playable.",
    gates: ["SWAP", "CCX"],
    wants: ["SWAP", "CCX", "Shield"],
  },
  Measurement: {
    label: "Measurement",
    hint: "Pure-state or uniform targets become reliable chip engines.",
    gates: ["H"],
    wants: ["H", "pure targets", "uniform targets"],
  },
  Rotation: {
    label: "Rotation",
    hint: "RX/RY/RZ clusters build a rotation-focused scoring lane.",
    gates: ["RX", "RY", "RZ"],
    wants: ["RX", "RY", "RZ"],
  },
  Tempo: {
    label: "Tempo",
    hint: "Safety and recovery picks keep a run alive after bad measurements.",
    gates: [],
    wants: ["survival", "extra attempts", "fallback scoring"],
  },
  Wildcard: {
    label: "Wildcard",
    hint: "Flexible picks support mixed quantum hands.",
    gates: [],
    wants: ["any high-value hand"],
  },
};

function normalizeGateName(gate) {
  if (!gate) return "";
  const name = typeof gate === "string" ? gate : gate.gate;
  return String(name || "").toUpperCase();
}

function jokerArchetype(joker) {
  if (joker?.archetype) return joker.archetype;
  const text = `${joker?.name || ""} ${joker?.desc || ""}`.toLowerCase();
  if (text.includes("cnot") || text.includes("bell") || text.includes("entang")) return "Entanglement";
  if (text.includes("phase") || text.includes(" z ")) return "Phase";
  if (text.includes("compiler") || text.includes("sparse")) return "Compiler";
  if (text.includes("topology") || text.includes("swap") || text.includes("ccx")) return "Topology";
  if (text.includes("projector") || text.includes("uniform") || text.includes("single-state")) return "Measurement";
  if (text.includes("rotation") || text.includes("rx") || text.includes("ry") || text.includes("rz")) return "Rotation";
  if (text.includes("cat") || text.includes("survive")) return "Tempo";
  return "Wildcard";
}

function buildSynergySummary(jokers = [], gates = []) {
  const counts = {};
  jokers.forEach((joker) => {
    const archetype = jokerArchetype(joker);
    counts[archetype] = (counts[archetype] || 0) + 2;
  });

  gates.map(normalizeGateName).forEach((gate) => {
    Object.entries(BUILD_ARCHETYPES).forEach(([key, archetype]) => {
      if (archetype.gates.includes(gate)) counts[key] = (counts[key] || 0) + 1;
    });
  });

  const entries = Object.keys(BUILD_ARCHETYPES)
    .map((key) => ({ key, score: counts[key] || 0, ...BUILD_ARCHETYPES[key] }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.label.localeCompare(b.label));

  return entries.length ? entries : [{ key: "Wildcard", score: 0, ...BUILD_ARCHETYPES.Wildcard }];
}

export default function GamePage() {
  const [gamesList, setGamesList] = useState([]);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState("");
  const [codexOpen, setCodexOpen] = useState(false);
  const [conceptIds, setConceptIds] = useState(loadConceptIds);
  const [newConceptCount, setNewConceptCount] = useState(0);

  const refreshState = () =>
    api("/state")
      .then(setGameState)
      .catch((err) => setError(err.message));

  useEffect(() => {
    api("/list").then(setGamesList).catch((err) => setError(err.message));
    refreshState();
  }, []);

  useEffect(() => {
    if (!gameState?.active) return;
    const foundIds = collectConceptIds(gameState).filter((id) => !conceptIds.includes(id));
    if (!foundIds.length) return;
    const nextIds = [...conceptIds, ...foundIds];
    setConceptIds(nextIds);
    saveConceptIds(nextIds);
    setNewConceptCount(foundIds.length);
    const timeoutId = window.setTimeout(() => setNewConceptCount(0), 2200);
    return () => window.clearTimeout(timeoutId);
  }, [gameState, conceptIds]);

  const startGame = async (gameId) => {
    setError("");
    await api(`/start/${gameId}`, { method: "POST" });
    await refreshState();
  };

  const exitGame = async () => {
    setError("");
    await api("/clear", { method: "POST" });
    await refreshState();
  };

  if (!gameState) {
    return <div className="quantum-game">Loading quantum workspace...</div>;
  }

  return (
    <div className="quantum-game">
      <button className="codex-toggle" onClick={() => setCodexOpen(true)}>
        Concept Codex <span>{conceptIds.length}/{CONCEPT_LIBRARY.length}</span>
      </button>
      {newConceptCount > 0 && <div className="codex-toast">+{newConceptCount} concept unlocked</div>}
      {codexOpen && (
        <ConceptCodexModal
          unlockedIds={conceptIds}
          onClose={() => setCodexOpen(false)}
        />
      )}
      {error && <div className="game-error">{error}</div>}
      {!gameState.active ? (
        <GameLobby gamesList={gamesList} onStart={startGame} />
      ) : gameState.kind === "circuit" ? (
        <CircuitGame state={gameState} onRefresh={refreshState} onExit={exitGame} />
      ) : (
        <CardGame state={gameState} onRefresh={refreshState} onExit={exitGame} />
      )}
    </div>
  );
}

function GameLobby({ gamesList, onStart }) {
  return (
    <main className="selection-screen">
      <h1 className="main-title">Quantum Games</h1>
      <p className="subtitle">Choose a game. Both run inside the platform through the FastAPI game bridge.</p>
      <div className="games-grid">
        {gamesList.map((game) => (
          <article key={game.id} className="game-entry-card">
            <span className="game-badge">{game.kind}</span>
            <h2>{game.name}</h2>
            <p>{game.desc}</p>
            <code>{game.dir}</code>
            <button className="btn-enter" onClick={() => onStart(game.id)}>
              Enter Game
            </button>
          </article>
        ))}
      </div>
    </main>
  );
}

function CircuitGame({ state, onRefresh, onExit }) {
  const [selectedCardId, setSelectedCardId] = useState(null);
  const [showRules, setShowRules] = useState(false);
  const [showTutorialLocal, setShowTutorialLocal] = useState(false);
  const [tutorialStep, setTutorialStep] = useState(0);
  const [playAnimating, setPlayAnimating] = useState(false);
  const legacyHandCards = GATES.map((gate, index) => ({ id: `legacy-${gate}-${index}`, gate, ...GATE_DETAILS[gate] }));
  const handCards = Array.isArray(state.hand_cards) ? state.hand_cards : legacyHandCards;
  const selectedCard = handCards.find((card) => card.id === selectedCardId) || handCards[0];
  const usesLegacyCards = !Array.isArray(state.hand_cards);
  const selectedGate = selectedCard?.gate || "H";
  const gatesBySlot = useMemo(() => {
    const map = new Map();
    state.gates.forEach((gate) => map.set(`${gate.qubit}_${gate.slot}`, gate));
    return map;
  }, [state.gates]);
  const stagedEvolutionGates = useMemo(() => {
    const activeGates = (state.gates || [])
      .slice()
      .sort((a, b) => a.slot - b.slot || a.qubit - b.qubit)
      .map((gate) => ({ gate: gate.gate, qubit: gate.qubit }));
    if (activeGates.length) return activeGates;
    return (state.last_recap?.gates || []).map((gate) => ({ gate: gate.gate, qubit: gate.qubit }));
  }, [state.gates, state.last_recap]);
  const tutorial = CIRCUIT_TUTORIAL_STEPS[tutorialStep] || CIRCUIT_TUTORIAL_STEPS[0];

  useEffect(() => {
    const tutorialDone = window.localStorage.getItem(CIRCUIT_TUTORIAL_STORAGE_KEY) === "1";
    const shouldShow = state.phase === "PLAYING" && state.level_index === 0 && !tutorialDone;
    setShowTutorialLocal(shouldShow);
    if (shouldShow) {
      setTutorialStep(0);
    }
  }, [state.phase, state.level_index]);

  useEffect(() => {
    if (!handCards.length) {
      setSelectedCardId(null);
      return;
    }
    if (!handCards.some((card) => card.id === selectedCardId)) {
      setSelectedCardId(handCards[0].id);
    }
  }, [handCards, selectedCardId]);

  const setGate = async (qubit, slot) => {
    if (!selectedCard) return;
    const key = `${qubit}_${slot}`;
    const withoutSlot = state.gates.filter((gate) => `${gate.qubit}_${gate.slot}` !== key);
    const placement = { gate: selectedCard.gate, qubit, slot };
    if (!usesLegacyCards) placement.card_id = selectedCard.id;
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({ gates: [...withoutSlot, placement] }),
    });
    await onRefresh();
  };

  const setGateByCard = async (card, qubit, slot) => {
    const key = `${qubit}_${slot}`;
    const withoutSlot = state.gates.filter((gate) => `${gate.qubit}_${gate.slot}` !== key);
    const placement = { gate: card.gate, qubit, slot };
    if (!String(card.id).startsWith("legacy-")) placement.card_id = card.id;
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({ gates: [...withoutSlot, placement] }),
    });
    await onRefresh();
  };

  const startGateDrag = (event, card) => {
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData(DRAG_TYPE, JSON.stringify({ type: "gate", card }));
  };

  const dropGate = async (event, qubit, slot) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData(DRAG_TYPE);
    if (!raw) return;
    const payload = JSON.parse(raw);
    if (payload.type === "gate" && payload.card) {
      await setGateByCard(payload.card, qubit, slot);
    }
  };

  const removeGate = async (qubit, slot) => {
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({
        gates: state.gates.filter((gate) => gate.qubit !== qubit || gate.slot !== slot),
      }),
    });
    await onRefresh();
  };

  const action = async (path) => {
    await api(path, { method: "POST" });
    await onRefresh();
  };

  const playCircuitHand = async () => {
    setPlayAnimating(true);
    window.setTimeout(() => setPlayAnimating(false), 920);
    await action("/circuit/play");
  };

  const finishTutorial = () => {
    window.localStorage.setItem(CIRCUIT_TUTORIAL_STORAGE_KEY, "1");
    setShowTutorialLocal(false);
  };

  const advanceTutorial = () => {
    if (tutorialStep >= CIRCUIT_TUTORIAL_STEPS.length - 1) {
      finishTutorial();
      return;
    }
    setTutorialStep((current) => current + 1);
  };

  if (showRules) {
    return <CircuitRulesPage onBack={() => setShowRules(false)} onExit={onExit} />;
  }

  if (state.phase === "ROULETTE") {
    return <CircuitRoulette state={state} onAction={action} onExit={onExit} onRules={() => setShowRules(true)} />;
  }

  if (state.phase === "SHOP") {
    return <CircuitShop state={state} onAction={action} onExit={onExit} onRules={() => setShowRules(true)} />;
  }

  return (
    <main className={`board-screen ${playAnimating ? "play-animating" : ""} ${showTutorialLocal ? `tutorial-active tutorial-step-${tutorial.key}` : ""}`}>
      {showTutorialLocal && (
        <div className="tutorial-overlay" onClick={advanceTutorial}>
          <div className="tutorial-box" role="dialog" aria-modal="true" aria-labelledby="circuit-tutorial-title">
            <div className="tutorial-progress" aria-label={`Tutorial step ${tutorialStep + 1} of ${CIRCUIT_TUTORIAL_STEPS.length}`}>
              {CIRCUIT_TUTORIAL_STEPS.map((step, index) => (
                <span key={step.key} className={index <= tutorialStep ? "active" : ""} />
              ))}
            </div>
            <span className="tutorial-kicker">Step {tutorialStep + 1} / {CIRCUIT_TUTORIAL_STEPS.length}</span>
            <h2 id="circuit-tutorial-title">{tutorial.title}</h2>
            <p>{tutorial.body}</p>
            <div className="tutorial-actions">
              <button className="btn btn-clear" onClick={(event) => { event.stopPropagation(); finishTutorial(); }}>
                跳过
              </button>
              <button className="btn btn-play-hand" onClick={(event) => { event.stopPropagation(); advanceTutorial(); }}>
                {tutorialStep >= CIRCUIT_TUTORIAL_STEPS.length - 1 ? "开始游戏" : "继续"}
              </button>
            </div>
            <small>{tutorial.cue}</small>
          </div>
        </div>
      )}
      <TopBar onExit={onExit} onRules={() => setShowRules(true)} />
      <header className="hud">
        <div>
          <h2>Quantum Hacker</h2>
          <p>{state.level.desc}</p>
          <ProgressMeter current={state.score} target={state.level.target} />
        </div>
        <div className="stats">
          <span>Blind {state.level_index + 1}/{state.level_count}</span>
          <span>Score {state.score} / {state.level.target}</span>
          <span>Hands {state.hands_left}</span>
          <span>Funds ${state.money}</span>
          <span>Deck {state.deck_count} / Discard {state.discard_count}</span>
        </div>
      </header>

      <section className="main-layout">
        {playAnimating && <MeasurementBurst label="Measuring circuit" />}
        <div className="circuit-board">
          <div className="section-head">
            <h3>Quantum Circuit</h3>
            <span className="selected-gate-readout">Selected {selectedCard ? `${selectedCard.gate} #${selectedCard.id}` : "No card"}</span>
          </div>

          <div className="gate-palette circuit-card-hand" aria-label="Gate card hand">
            {handCards.map((card) => {
              const detail = GATE_DETAILS[card.gate] || card;
              return (
                <button
                  key={card.id}
                  className={`gate-card gate-card-${card.gate.toLowerCase()} ${selectedCard?.id === card.id ? "active" : ""}`}
                  onClick={() => setSelectedCardId(card.id)}
                  draggable
                  onDragStart={(event) => startGateDrag(event, card)}
                  aria-pressed={selectedCard?.id === card.id}
                >
                  <span className="gate-card-role">{detail.role}</span>
                  <strong>{card.gate}</strong>
                  <span>{detail.name}</span>
                  <small>{detail.text}</small>
                </button>
              );
            })}
            {!handCards.length && <p className="empty-hand-note">No gate cards in hand.</p>}
          </div>

          {[0, 1].map((qubit) => (
            <div key={qubit} className="circuit-row">
              <span className="qubit-label">q[{qubit}]</span>
              <div className="slots-container">
                {[0, 1, 2, 3].map((slot) => {
                  const gate = gatesBySlot.get(`${qubit}_${slot}`);
                  return (
                    <button
                      key={slot}
                      className={`circuit-slot ${gate ? "occupied" : ""}`}
                      onClick={() => (gate ? removeGate(qubit, slot) : setGate(qubit, slot))}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={(event) => dropGate(event, qubit, slot)}
                      title={gate ? "Click to return card to hand" : selectedCard ? `Play ${selectedCard.gate}` : "No card selected"}
                    >
                      {gate?.gate || "+"}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <aside className="control-panel">
          <ProbabilityChart probabilities={state.probabilities} targets={state.level.target_probs} />
          <StateEvolutionTimeline gates={stagedEvolutionGates} qubits={2} />
          <JokerBuildPanel jokers={state.owned_jokers} gates={stagedEvolutionGates} compact />
          <div className="preview-box">
            <span>Preview</span>
            <strong>{state.preview.chips} x {state.preview.mult} = {state.preview.total}</strong>
          </div>
          <CircuitScoreBreakdown state={state} />
          <QuantumRecapPanel recap={state.last_recap} />
          {state.stored_mult > 1 && <div className="notice">Stored multiplier x{state.stored_mult}</div>}
          {state.warning && <div className="warning">{state.warning}</div>}
          <button className="btn btn-observe" onClick={() => action("/circuit/observe")}>Observe</button>
          <button className="btn btn-play-hand" onClick={playCircuitHand}>Play Hand</button>
          <button className="btn btn-clear" onClick={() => action("/circuit/clear")}>Clear Circuit</button>
        </aside>
      </section>

      {state.phase !== "PLAYING" && (
        <div className="game-overlay">
          <h2>{state.phase === "GAME_OVER" ? "Wave Collapsed" : state.phase === "WIN" ? "Run Won" : "Blind Defeated"}</h2>
          <CircuitFormulaSummary state={state} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          <button className="btn btn-play-hand" onClick={() => action("/start/game1")}>Restart</button>
        </div>
      )}
    </main>
  );
}

function CircuitRoulette({ state, onAction, onExit, onRules }) {
  const [revealed, setRevealed] = useState(false);
  const hitIndex = Math.max(
    0,
    state.roulette_items.findIndex((item) => item.name === state.last_roulette?.name),
  );
  const segmentCenter = hitIndex * 90 + 45;
  const rotation = 360 * 4 - segmentCenter;

  useEffect(() => {
    setRevealed(false);
    const timeoutId = window.setTimeout(() => setRevealed(true), 1650);
    return () => window.clearTimeout(timeoutId);
  }, [state.last_roulette?.name]);

  return (
    <main className="board-screen roulette-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <header className="hud">
        <div>
          <h2>Wave Collapse Roulette</h2>
          <p>Observation stored the multiplier, then collapsed the circuit into a random event.</p>
        </div>
        <div className="stats">
          <span>Score {state.score} / {state.level.target}</span>
          <span>Hands {state.hands_left}</span>
          <span>Stored x{state.stored_mult}</span>
        </div>
      </header>

      <section className="roulette-stage">
        <div className="roulette-pointer" />
        <div
          key={state.last_roulette?.name}
          className="roulette-wheel spinning"
          style={{ "--spin": `${rotation}deg` }}
          onAnimationEnd={() => setRevealed(true)}
        >
          {state.roulette_items.map((item, index) => (
            <span key={item.name} className={`roulette-label roulette-label-${index}`}>
              {item.name}
            </span>
          ))}
        </div>
        {revealed ? (
          <div className={`roulette-result result-${state.last_roulette?.color || "green"}`}>
            <strong>{state.last_roulette?.name}</strong>
            <span>{state.last_roulette?.message}</span>
          </div>
        ) : (
          <div className="roulette-result roulette-pending">
            <strong>Spinning...</strong>
            <span>Collapsing the waveform</span>
          </div>
        )}
        <RouletteChances chances={state.roulette_chances} />
        {revealed ? (
          <button className="btn btn-play-hand" onClick={() => onAction("/circuit/roulette/continue")}>
            Continue
          </button>
        ) : (
          <button className="btn btn-clear" disabled>
            Spinning
          </button>
        )}
      </section>
    </main>
  );
}

function CircuitShop({ state, onAction, onExit, onRules }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <header className="hud">
        <div>
          <h2>Quantum Hacker Shop</h2>
          <p>Buy up to two jokers. Active jokers change circuit scoring and boss constraints.</p>
        </div>
        <div className="stats">
          <span>Funds ${state.money}</span>
          <span>Blind {state.level_index + 1}/{state.level_count}</span>
          <span>Jokers {state.owned_jokers.length}/2</span>
        </div>
      </header>

      <section className="shop-layout">
        <div className="shop-shelf">
          <h3>Jokers</h3>
          <div className="shop-items">
            {state.shop_jokers.length ? (
              state.shop_jokers.map((joker) => (
                <article key={joker.id} className={`shop-card joker-${joker.color}`}>
                  <span className="shop-type">JOKER</span>
                  <span className="archetype-badge">{joker.archetype || jokerArchetype(joker)}</span>
                  <h4>{joker.name}</h4>
                  <p>{joker.desc}</p>
                  <small>{joker.synergy || BUILD_ARCHETYPES[jokerArchetype(joker)]?.hint}</small>
                  <strong>${joker.cost}</strong>
                  <button
                    className="btn btn-play-hand"
                    onClick={() => onAction(`/circuit/shop/buy/${joker.id}`)}
                    disabled={state.money < joker.cost || state.owned_jokers.length >= 2}
                  >
                    Buy Joker
                  </button>
                </article>
              ))
            ) : (
              <p className="empty-hand-note">No jokers left in this shop.</p>
            )}
          </div>
        </div>

        <aside className="shop-side">
          <JokerBuildPanel jokers={state.owned_jokers} gates={state.last_recap?.gates || []} />
          <CircuitFormulaSummary state={state} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          <h3>Owned Jokers</h3>
          {state.owned_jokers.length ? (
            state.owned_jokers.map((joker) => {
              const active = state.active_jokers.includes(joker.id);
              return (
                <button
                  key={joker.id}
                  className={`owned-joker owned-joker-button ${active ? "active" : ""}`}
                  onClick={() => onAction(`/circuit/jokers/toggle/${joker.id}`)}
                >
                  <strong>{joker.name}</strong>
                  <em>{joker.archetype || jokerArchetype(joker)}</em>
                  <span>{active ? "Active" : "Inactive"} - {joker.desc}</span>
                </button>
              );
            })
          ) : (
            <p className="empty-hand-note">No owned jokers yet.</p>
          )}
          <button className="btn btn-play-hand" onClick={() => onAction("/circuit/next")}>
            Next Blind
          </button>
        </aside>
      </section>
    </main>
  );
}

function CardGame({ state, onRefresh, onExit }) {
  const [selectedCardIds, setSelectedCardIds] = useState([]);
  const [stagedCards, setStagedCards] = useState({});
  const [draggingCardId, setDraggingCardId] = useState(null);
  const [showRules, setShowRules] = useState(false);
  const [showTutorialLocal, setShowTutorialLocal] = useState(false);
  const [tutorialStep, setTutorialStep] = useState(0);
  const [playAnimating, setPlayAnimating] = useState(false);

  useEffect(() => {
    setSelectedCardIds([]);
    setStagedCards({});
    setShowTutorialLocal(Boolean(state.show_tutorial));
    if (state.show_tutorial) {
      setTutorialStep(0);
    }
  }, [state.phase, state.hand_cards.length, state.current_score, state.plays_left, state.discards_left, state.show_tutorial]);

  const tutorial = CARD_TUTORIAL_STEPS[tutorialStep] || CARD_TUTORIAL_STEPS[0];

  const visibleStagedCards = useMemo(() => {
    return Object.fromEntries(
      Object.entries(stagedCards).filter((entry) => state.hand_cards[entry[1].cardIndex]),
    );
  }, [stagedCards, state.hand_cards]);
  const stagedEvolutionGates = useMemo(() => {
    const pairs = Object.entries(visibleStagedCards);
    if (pairs.length) {
      return pairs
        .sort((a, b) => Number(a[0].split("_")[1]) - Number(b[0].split("_")[1]))
        .map(([key, staged]) => {
          const qubit = Number(key.split("_")[0]);
          const card = state.hand_cards[staged.cardIndex];
          return { gate: card?.gate || "?", qubit, targets: staged.targets };
        });
    }
    return (state.last_recap?.gates || []).map((gate) => ({ gate, qubit: null }));
  }, [visibleStagedCards, state.hand_cards, state.last_recap]);

  const stageCard = (cardIndex, qubit, slot) => {
    setStagedCards((current) => {
      const card = state.hand_cards[cardIndex];
      const next = Object.fromEntries(
        Object.entries(current).filter((entry) => entry[1].cardIndex !== cardIndex),
      );
      next[`${qubit}_${slot}`] = {
        cardIndex,
        targets: CONTROLLED_GATES.has(card?.gate) ? [qubit, (qubit + 1) % state.num_qubits] : [qubit],
      };
      return next;
    });
  };

  const setControlledTarget = (qubit, slot, target) => {
    const key = `${qubit}_${slot}`;
    setStagedCards((current) => {
      const staged = current[key];
      if (!staged) return current;
      return {
        ...current,
        [key]: {
          ...staged,
          targets: [qubit, Number(target)],
        },
      };
    });
  };

  const unstageSlot = (qubit, slot) => {
    setStagedCards((current) => {
      const next = { ...current };
      delete next[`${qubit}_${slot}`];
      return next;
    });
  };

  const startCardDrag = (event, cardIndex, source = "hand") => {
    setDraggingCardId(cardIndex);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData(DRAG_TYPE, JSON.stringify({ type: "card", cardIndex, source }));
  };

  const dropCard = (event, qubit, slot) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData(DRAG_TYPE);
    if (!raw) return;
    const payload = JSON.parse(raw);
    if (payload.type === "card") {
      stageCard(payload.cardIndex, qubit, slot);
    }
    setDraggingCardId(null);
  };

  const playHand = async () => {
    const pairs = Object.entries(visibleStagedCards);
    if (!pairs.length) return;
    pairs.sort((a, b) => Number(a[0].split("_")[1]) - Number(b[0].split("_")[1]));
    setPlayAnimating(true);
    window.setTimeout(() => setPlayAnimating(false), 920);
    await api("/play", {
      method: "POST",
      body: JSON.stringify({
        selected_indices: pairs.map((pair) => pair[1].cardIndex),
        targets: pairs.map((pair) => pair[1].targets || [Number(pair[0].split("_")[0])]),
      }),
    });
    await onRefresh();
  };

  const discard = async () => {
    if (!selectedCardIds.length) return;
    await api("/discard", { method: "POST", body: JSON.stringify(selectedCardIds) });
    await onRefresh();
  };

  const action = async (path) => {
    await api(path, { method: "POST" });
    await onRefresh();
  };

  const finishTutorial = async () => {
    try {
      await api("/cards/tutorial/complete", { method: "POST" });
    } catch (err) {
      console.error("Failed to complete tutorial", err);
    }
    setShowTutorialLocal(false);
    await onRefresh();
  };

  const advanceTutorial = async () => {
    if (tutorialStep >= CARD_TUTORIAL_STEPS.length - 1) {
      await finishTutorial();
      return;
    }
    setTutorialStep((current) => current + 1);
  };

  if (showRules) {
    return <CardRulesPage onBack={() => setShowRules(false)} onExit={onExit} />;
  }

  if (state.phase === "SHOP") {
    return <CardShop state={state} onAction={action} onExit={onExit} onRules={() => setShowRules(true)} />;
  }

  if (state.phase === "OPENING_PACK") {
    return <PackOpening state={state} onAction={action} onExit={onExit} onRules={() => setShowRules(true)} />;
  }

  return (
    <main className={`board-screen ${playAnimating ? "play-animating" : ""} ${showTutorialLocal ? `tutorial-active tutorial-step-${tutorial.key}` : ""}`}>
      {showTutorialLocal && (
        <div className="tutorial-overlay" onClick={advanceTutorial}>
          <div className="tutorial-box" role="dialog" aria-modal="true" aria-labelledby="card-tutorial-title">
            <div className="tutorial-progress" aria-label={`Tutorial step ${tutorialStep + 1} of ${CARD_TUTORIAL_STEPS.length}`}>
              {CARD_TUTORIAL_STEPS.map((step, index) => (
                <span key={step.key} className={index <= tutorialStep ? "active" : ""} />
              ))}
            </div>
            <span className="tutorial-kicker">Step {tutorialStep + 1} / {CARD_TUTORIAL_STEPS.length}</span>
            <h2 id="card-tutorial-title">{tutorial.title}</h2>
            <p>{tutorial.body}</p>
            <div className="tutorial-actions">
              <button className="btn btn-clear" onClick={(event) => { event.stopPropagation(); finishTutorial(); }}>
                跳过
              </button>
              <button className="btn btn-play-hand" onClick={(event) => { event.stopPropagation(); advanceTutorial(); }}>
                {tutorialStep >= CARD_TUTORIAL_STEPS.length - 1 ? "开始游戏" : "继续"}
              </button>
            </div>
            <small>{tutorial.cue}</small>
          </div>
        </div>
      )}
      <TopBar onExit={onExit} onRules={() => setShowRules(true)} />
      <header className="hud">
        <div>
          <h2>Quantum Balatro Original</h2>
          <p>Build a hand by placing gate cards into qubit slots.</p>
          <ProgressMeter current={state.current_score} target={state.target_score} />
        </div>
        <div className="stats">
          <span>Chips ${state.chips}</span>
          <span>Score {state.current_score} / {state.target_score}</span>
          <span>Plays {state.plays_left}</span>
          <span>Discards {state.discards_left}</span>
        </div>
      </header>

      <section className="main-layout">
        {playAnimating && <MeasurementBurst label="Measuring hand" />}
        <div className="circuit-board">
          <h3>Card Staging Circuit</h3>
          <div className="circuit-grid">
          {Array.from({ length: state.num_qubits }, (_, qubit) => (
            <div key={qubit} className="circuit-row">
              <span className="qubit-label">q[{qubit}]</span>
              <div className="slots-container">
                {[0, 1, 2, 3].map((slot) => {
                  const staged = visibleStagedCards[`${qubit}_${slot}`];
                  const stagedCardIdx = staged?.cardIndex;
                  const card = state.hand_cards[stagedCardIdx];
                  const isControlled = CONTROLLED_GATES.has(card?.gate);
                  const targetQubit = staged?.targets?.[1] ?? (qubit + 1) % state.num_qubits;
                  const targetOffset = targetQubit - qubit;
                  return (
                    <div
                      key={slot}
                      className={`circuit-slot ${card ? "occupied draggable-card-slot" : ""} ${isControlled ? "controlled-gate" : ""}`}
                      draggable={Boolean(card)}
                      onDragStart={(event) => card && startCardDrag(event, stagedCardIdx, "stage")}
                      onDragEnd={() => setDraggingCardId(null)}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={(event) => dropCard(event, qubit, slot)}
                      onClick={() => card && unstageSlot(qubit, slot)}
                      title={card ? "Drag to another slot or click to remove" : "Drop a card here"}
                    >
                      {isControlled && (
                        <span
                          className={`gate-connector ${targetOffset < 0 ? "target-up" : "target-down"}`}
                          style={{ "--connector-span": Math.max(1, Math.abs(targetOffset)) }}
                          aria-hidden="true"
                        />
                      )}
                      {card?.gate || "+"}
                      {isControlled && (
                        <label className="target-picker" onClick={(event) => event.stopPropagation()}>
                          <span>to</span>
                          <select
                            value={targetQubit}
                            onChange={(event) => setControlledTarget(qubit, slot, event.target.value)}
                          >
                            {Array.from({ length: state.num_qubits }, (_, option) => (
                              <option key={option} value={option} disabled={option === qubit}>
                                q{option}
                              </option>
                            ))}
                          </select>
                        </label>
                      )}
                      {!card && (
                        <div className="slot-selector">
                          {state.hand_cards.map((handCard, index) =>
                            Object.values(visibleStagedCards).some((item) => item.cardIndex === index) ? null : (
                              <button key={handCard.id} onClick={() => stageCard(index, qubit, slot)}>
                                {handCard.gate}
                              </button>
                            ),
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
          </div>
        </div>

        <aside className="control-panel">
          <div className="preview-box">
            <span>Last hand</span>
            <strong>{state.last_hand_played}</strong>
          </div>
          <CardScoreBreakdown breakdown={state.last_score_breakdown} />
          <TeachingPanel lesson={state.lesson} />
          <StateEvolutionTimeline gates={stagedEvolutionGates} qubits={state.num_qubits} />
          <JokerBuildPanel jokers={state.jokers} gates={stagedEvolutionGates} compact />
          <QuantumRecapPanel recap={state.last_recap} />
          <button className="btn btn-play-hand" onClick={playHand} disabled={!Object.keys(visibleStagedCards).length}>
            Play Hand
          </button>
          <button className="btn btn-discard" onClick={discard} disabled={!selectedCardIds.length}>
            Discard Selected
          </button>
          <button className="btn btn-clear" onClick={() => setStagedCards({})}>
            Clear Stage
          </button>
        </aside>
      </section>

      <section className="hand-area">
        <h3>Hand Cards</h3>
        {state.phase !== "PLAYING" && (
          <p className="empty-hand-note">
            {state.phase === "REWARD"
              ? "Blind cleared. Your hand was scored and moved to the discard pile."
              : "This run is no longer in the playing phase."}
          </p>
        )}
        <div className="cards-container">
          {state.hand_cards.map((card, index) => {
            if (Object.values(visibleStagedCards).some((item) => item.cardIndex === index)) return null;
            const selected = selectedCardIds.includes(index);
            return (
              <button
                key={card.id}
                className={`q-card rarity-${card.rarity} ${selected ? "selected" : ""}`}
                draggable
                onDragStart={(event) => startCardDrag(event, index)}
                onDragEnd={() => setDraggingCardId(null)}
                onClick={() =>
                  draggingCardId === index
                    ? undefined
                    :
                  setSelectedCardIds((current) =>
                    current.includes(index) ? current.filter((id) => id !== index) : [...current, index],
                  )
                }
              >
                <strong>{card.gate}</strong>
                <span>{card.name}</span>
                {card.targets > 1 && <small>{card.targets}-qubit</small>}
              </button>
            );
          })}
        </div>
      </section>

      <LearningCatalog state={state} />

      {state.phase !== "PLAYING" && (
        <div className="game-overlay">
          <h2>
            {state.phase === "REWARD"
              ? "Blind Cleared"
              : state.phase === "VICTORY"
                ? "Run Won"
                : "Game Over"}
          </h2>
          {state.phase === "REWARD" && <p>Reward added. Chips: ${state.chips}</p>}
          <CardFormulaSummary breakdown={state.last_score_breakdown} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          {state.phase === "REWARD" ? (
            <button className="btn btn-play-hand" onClick={() => action("/cards/shop")}>Enter Shop</button>
          ) : (
            <button className="btn btn-play-hand" onClick={() => action("/start/game2")}>Restart</button>
          )}
        </div>
      )}
    </main>
  );
}

function CardShop({ state, onAction, onExit, onRules }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <header className="hud">
        <div>
          <h2>Quantum Shop</h2>
          <p>Spend chips on jokers or add a quantum card pack to the deck.</p>
        </div>
        <div className="stats">
          <span>Chips ${state.chips}</span>
          <span>Ante {state.ante}</span>
          <span>{state.blind_index + 1} / 3</span>
          <span>Jokers {state.jokers.length} / 5</span>
        </div>
      </header>

      <section className="shop-layout">
        <div className="shop-shelf">
          <h3>Jokers</h3>
          <div className="shop-items">
            {state.shop_jokers.length ? (
              state.shop_jokers.map((joker) => (
                <article key={`${joker.name}-${joker.index}`} className="shop-card joker-shop-card">
                  <span className="shop-type">JOKER</span>
                  <span className="archetype-badge">{joker.archetype || jokerArchetype(joker)}</span>
                  <h4>{joker.name}</h4>
                  <p>{joker.desc}</p>
                  <small>{joker.synergy || BUILD_ARCHETYPES[jokerArchetype(joker)]?.hint}</small>
                  <strong>${joker.cost}</strong>
                  <button
                    className="btn btn-play-hand"
                    onClick={() => onAction(`/cards/buy-joker/${joker.index}`)}
                    disabled={state.chips < joker.cost || state.jokers.length >= 5}
                  >
                    Buy Joker
                  </button>
                </article>
              ))
            ) : (
              <p className="empty-hand-note">No jokers left in this shop.</p>
            )}
          </div>
        </div>

        <aside className="shop-side">
          <JokerBuildPanel jokers={state.jokers} gates={state.last_recap?.gates || []} />
          <h3>Pack</h3>
          {state.shop_pack ? (
            <article className="shop-card pack-shop-card">
              <span className="shop-type">PACK</span>
              <h4>{state.shop_pack.name}</h4>
              <p>{state.shop_pack.desc || "Open to reveal a quantum gate card, then collect it into your deck."}</p>
              <strong>${state.shop_pack.cost}</strong>
              <button
                className="btn btn-observe"
                onClick={() => onAction("/cards/buy-pack")}
                disabled={state.chips < state.shop_pack.cost}
              >
                Buy Pack
              </button>
            </article>
          ) : (
            <p className="empty-hand-note">Pack sold out.</p>
          )}

          <div className="owned-jokers">
            <h3>Owned Jokers</h3>
            {state.jokers.map((joker, index) => (
              <div key={`${joker.name}-${index}`} className="owned-joker">
                <strong>{joker.name}</strong>
                <em>{joker.archetype || jokerArchetype(joker)}</em>
                <span>{joker.desc}</span>
              </div>
            ))}
          </div>

          <button className="btn btn-play-hand" onClick={() => onAction("/cards/next")}>
            Next Blind
          </button>
        </aside>
      </section>
    </main>
  );
}

function PackOpening({ state, onAction, onExit, onRules }) {
  const card = state.opened_card;
  const [revealStep, setRevealStep] = useState("sealed");
  const revealTimer = useRef(null);

  useEffect(() => {
    setRevealStep("sealed");
    if (revealTimer.current) {
      window.clearTimeout(revealTimer.current);
      revealTimer.current = null;
    }
    return () => {
      if (revealTimer.current) {
        window.clearTimeout(revealTimer.current);
      }
    };
  }, [card?.name, card?.gate]);

  const openPack = () => {
    setRevealStep("opening");
    revealTimer.current = window.setTimeout(() => setRevealStep("revealed"), 1450);
  };

  return (
    <main className="board-screen pack-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <section className="pack-stage">
        <h2>Quantum Pack</h2>
        <div className={`pack-opening ${revealStep}`}>
          <div className="pack-shell" aria-hidden={revealStep === "revealed"}>
            <div className="pack-core">
              <span>QUANTUM</span>
              <strong>PACK</strong>
              <small>RX PHASE SERIES</small>
            </div>
            <div className="pack-rip pack-rip-left" />
            <div className="pack-rip pack-rip-right" />
            <div className="pack-glow" />
          </div>
          {card && (
            <article className={`q-card pack-reveal rarity-${card.rarity}`} aria-hidden={revealStep !== "revealed"}>
              <strong>{card.gate}</strong>
              <span>{card.name}</span>
              <small>Uses: {card.durability}</small>
              {card.lesson && <small>{card.lesson}</small>}
            </article>
          )}
        </div>
        {revealStep === "sealed" ? (
          <button className="btn btn-observe" onClick={openPack} disabled={!card}>
            Open Pack
          </button>
        ) : revealStep === "opening" ? (
          <button className="btn btn-clear" disabled>
            Opening...
          </button>
        ) : (
          <button className="btn btn-play-hand" onClick={() => onAction("/cards/collect-pack")}>
            Collect Card
          </button>
        )}
      </section>
    </main>
  );
}

function ProbabilityChart({ probabilities, targets }) {
  return (
    <div className="prob-chart">
      <h3>Target Match</h3>
      <div className="bars">
        {STATES.map((stateName) => {
          const current = probabilities[stateName] || 0;
          const target = targets[stateName] || 0;
          return (
            <div key={stateName} className="bar-group">
              <div className="bar-track">
                {target > 0 && <div className="target-mark" style={{ height: `${target * 100}%` }} />}
                <div className="bar-fill" style={{ height: `${current * 100}%` }} />
              </div>
              <span>{stateName}</span>
              <small>{Math.round(current * 100)}%</small>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CircuitScoreBreakdown({ state }) {
  const chances = state.roulette_chances || {};
  return (
    <div className="score-breakdown">
      <h3>Score Breakdown</h3>
      <div className="score-line">
        <span>Target match</span>
        <strong>{state.preview.match_chips}</strong>
      </div>
      <div className="score-line">
        <span>Gate multiplier</span>
        <strong>x{state.preview.gate_mult}</strong>
      </div>
      <div className="score-line">
        <span>Stored multiplier</span>
        <strong>x{state.preview.stored_mult}</strong>
      </div>
      <div className="score-line">
        <span>Observe risk</span>
        <strong>{state.observe_count} used</strong>
      </div>
      <div className="chance-grid">
        {Object.entries(chances).map(([name, chance]) => (
          <span key={name}>{name}: {chance}%</span>
        ))}
      </div>
    </div>
  );
}

function CircuitFormulaSummary({ state }) {
  const chips = state.last_chips || state.preview?.match_chips || 0;
  const mult = state.last_chips > 0 ? state.last_mult : state.preview?.gate_mult || 1;
  const total = Math.round(chips * mult);
  const hasPlayed = state.last_chips > 0 || state.phase !== "PLAYING";

  if (!hasPlayed) return null;

  return (
    <div className="formula-card">
      <span className="formula-label">Last Formula</span>
      <h3>Quantum Probability Score</h3>
      <div className="formula-line">
        <code>P(s) = |amplitude(s)|^2</code>
        <small>measurement probability from the circuit statevector</small>
      </div>
      <div className="formula-line">
        <code>chips = 200 x sum(min(P(s), target(s)))</code>
        <strong>{chips} chips</strong>
      </div>
      <div className="formula-line">
        <code>score = floor(chips x multiplier)</code>
        <strong>{chips} x {mult} = {total}</strong>
      </div>
    </div>
  );
}

function CardScoreBreakdown({ breakdown }) {
  if (!breakdown || breakdown.hand === "None") {
    return (
      <div className="score-breakdown">
        <h3>Last Score</h3>
        <p className="empty-hand-note">Play a staged circuit to measure fidelity.</p>
      </div>
    );
  }

  return (
    <div className="score-breakdown">
      <h3>Last Score</h3>
      <div className="score-line">
        <span>Base</span>
        <strong>{breakdown.base_chips} x {breakdown.base_mult}</strong>
      </div>
      <div className="score-line">
        <span>Jokers</span>
        <strong>+{breakdown.joker_chips_delta} chips / +{breakdown.joker_mult_delta} mult</strong>
      </div>
      <div className="score-line">
        <span>Fidelity</span>
        <strong>{Math.round((breakdown.fidelity || 0) * 100)}%</strong>
      </div>
      <div className="score-line total">
        <span>Total</span>
        <strong>{breakdown.score}</strong>
      </div>
    </div>
  );
}

function CardFormulaSummary({ breakdown }) {
  if (!breakdown || breakdown.hand === "None") return null;

  const chips = (breakdown.base_chips || 0) + (breakdown.joker_chips_delta || 0);
  const mult = (breakdown.base_mult || 0) + (breakdown.joker_mult_delta || 0);
  const fidelity = breakdown.fidelity || 0;

  return (
    <div className="formula-card">
      <span className="formula-label">Last Formula</span>
      <h3>{breakdown.hand}</h3>
      <div className="formula-line">
        <code>F = |&lt;target | current&gt;|^2</code>
        <strong>{Math.round(fidelity * 100)}% fidelity</strong>
      </div>
      <div className="formula-line">
        <code>chips = base + joker bonus</code>
        <strong>{breakdown.base_chips} + {breakdown.joker_chips_delta} = {chips}</strong>
      </div>
      <div className="formula-line">
        <code>score = floor(chips x mult x F)</code>
        <strong>{chips} x {mult} x {fidelity} = {breakdown.score}</strong>
      </div>
    </div>
  );
}

function JokerBuildPanel({ jokers = [], gates = [], compact = false }) {
  const builds = buildSynergySummary(jokers, gates);
  const primary = builds[0];
  const ownedCount = jokers.length;
  const nextWants = primary.wants.slice(0, 3).join(" / ");

  return (
    <div className={`build-panel ${compact ? "compact" : ""}`}>
      <span className="formula-label">Joker Build</span>
      <div className="build-head">
        <h3>{primary.label} Line</h3>
        <strong>{ownedCount ? `${ownedCount} relic${ownedCount > 1 ? "s" : ""}` : "No relics"}</strong>
      </div>
      <p>{primary.hint}</p>
      <div className="build-track">
        {builds.slice(0, 4).map((build) => (
          <div key={build.key} className={`build-row ${build.key === primary.key ? "active" : ""}`}>
            <span>{build.label}</span>
            <div className="build-meter" aria-label={`${build.label} build score ${build.score}`}>
              {Array.from({ length: 5 }, (_, index) => (
                <i key={index} className={index < Math.min(5, build.score) ? "filled" : ""} />
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="build-next">
        <span>Next pick</span>
        <strong>{nextWants}</strong>
      </div>
    </div>
  );
}

function QuantumRecapPanel({ recap, compact = false }) {
  if (!recap) return null;
  const hasCircuitRecap = recap.type === "probability" && recap.probabilities;
  const hasCardRecap = recap.type === "fidelity" && Array.isArray(recap.gates) && recap.gates.length > 0;
  if (!hasCircuitRecap && !hasCardRecap) return null;

  const gateText = recap.gates
    .map((item) => (typeof item === "string" ? item : `${item.gate}(q${item.qubit})`))
    .join(" -> ") || "No gates played";

  return (
    <div className={`quantum-recap ${compact ? "compact" : ""}`}>
      <span className="formula-label">Quantum Recap</span>
      <h3>{recap.title || "Last hand"}</h3>
      <div className="recap-line">
        <span>Gate path</span>
        <code>{gateText}</code>
      </div>
      {recap.type === "probability" ? (
        <>
          <div className="recap-line">
            <span>Measured probabilities</span>
            <code>{formatProbabilityMap(recap.probabilities)}</code>
          </div>
          <div className="recap-line">
            <span>Target</span>
            <code>{formatProbabilityMap(recap.targets)}</code>
          </div>
          <div className="recap-line">
            <span>Result</span>
            <strong>{recap.chips} chips x {recap.mult} = {recap.score}</strong>
          </div>
        </>
      ) : (
        <>
          <div className="recap-line">
            <span>State comparison</span>
            <code>F = |&lt;target|current&gt;|^2</code>
          </div>
          <div className="recap-line">
            <span>Fidelity</span>
            <strong>{Math.round((recap.fidelity || 0) * 100)}%</strong>
          </div>
        </>
      )}
      <p>{recap.note}</p>
    </div>
  );
}

function formatProbabilityMap(map = {}) {
  const entries = Object.entries(map);
  if (!entries.length) return "none";
  return entries
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([state, value]) => `${state}: ${Math.round(Number(value || 0) * 100)}%`)
    .join(", ");
}

function StateEvolutionTimeline({ gates = [], qubits = 2 }) {
  const steps = buildEvolutionSteps(gates, qubits);
  return (
    <div className="state-evolution">
      <div className="state-evolution-head">
        <h3>State Evolution</h3>
        <span>{gates.length ? `${gates.length} gate${gates.length > 1 ? "s" : ""}` : "idle"}</span>
      </div>
      <div className="evolution-track" aria-label="Quantum state evolution timeline">
        {steps.map((step, index) => (
          <div key={`${step.label}-${index}`} className={`evolution-step ${step.kind}`}>
            <code>{step.label}</code>
            <small>{step.note}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function buildEvolutionSteps(gates = [], qubits = 2) {
  const steps = [{ label: `|${"0".repeat(Math.max(1, qubits))}>`, note: "initial basis state", kind: "state" }];
  const seen = [];
  gates.forEach((item) => {
    const gate = item.gate || "?";
    const qubitText = Number.isInteger(item.qubit) ? `(q${item.qubit})` : "";
    seen.push(gate);
    steps.push({ label: `${gate}${qubitText}`, note: gateEvolutionNote(gate, item), kind: "gate" });
    steps.push({ label: inferStateLabel(seen), note: inferStateNote(seen), kind: "state" });
  });
  if (!gates.length) {
    steps.push({ label: "add a gate", note: "timeline updates as you stage cards", kind: "hint" });
  }
  return steps;
}

function gateEvolutionNote(gate, item = {}) {
  if (gate === "H") return "creates superposition";
  if (gate === "X") return "flips basis value";
  if (gate === "Z") return "changes phase sign";
  if (gate === "CNOT" || gate === "CX") return targetNote(item, "conditional flip");
  if (gate === "CZ") return targetNote(item, "conditional phase");
  if (gate === "SWAP") return targetNote(item, "exchange states");
  if (["RX", "RY", "RZ"].includes(gate)) return "continuous rotation";
  if (gate === "CCX") return "two-control flip";
  return "updates the quantum state";
}

function targetNote(item, fallback) {
  if (!Array.isArray(item.targets) || item.targets.length < 2) return fallback;
  return `${fallback}: q${item.targets[0]} -> q${item.targets[1]}`;
}

function inferStateLabel(gates) {
  if (gates.includes("CCX")) return "Toffoli control";
  if (gates.includes("SWAP")) return "routed state";
  if (gates.some((gate) => ["RX", "RY", "RZ"].includes(gate))) return "rotated state";
  if (gates.includes("CNOT") || gates.includes("CX") || gates.includes("CZ")) {
    return gates.includes("H") ? "entangled state" : "correlated state";
  }
  if (gates.includes("H")) return "superposition";
  if (gates.includes("Z")) return "phase-shifted state";
  if (gates.includes("X")) return "flipped basis state";
  return "current state";
}

function inferStateNote(gates) {
  if (gates.includes("H") && (gates.includes("CNOT") || gates.includes("CX") || gates.includes("CZ"))) {
    return "superposition plus control can create entanglement";
  }
  if (gates.includes("H")) return "measurement can branch across outcomes";
  if (gates.includes("Z")) return "probability may stay unchanged while phase changes";
  if (gates.some((gate) => ["RX", "RY", "RZ"].includes(gate))) return "angle controls amplitude and phase";
  return "state updated by the latest gate";
}

function ConceptCodexModal({ unlockedIds, onClose }) {
  const unlocked = new Set(unlockedIds);
  const groups = ["Gates", "States", "Formulas", "Systems"];

  return (
    <div className="codex-overlay" role="dialog" aria-modal="true" aria-labelledby="concept-codex-title">
      <section className="codex-modal">
        <div className="codex-header">
          <div>
            <span className="formula-label">Auto Collection</span>
            <h2 id="concept-codex-title">Quantum Concept Codex</h2>
            <p>Concepts unlock when you see gates, create states, use formulas, clear blinds, or fail a run.</p>
          </div>
          <button className="btn-back" onClick={onClose}>Close</button>
        </div>
        <div className="codex-progress">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${Math.round((unlocked.size / CONCEPT_LIBRARY.length) * 100)}%` }} />
          </div>
          <span>{unlocked.size}/{CONCEPT_LIBRARY.length}</span>
        </div>
        <div className="codex-groups">
          {groups.map((group) => (
            <div key={group} className="codex-group">
              <h3>{group}</h3>
              <div className="codex-grid">
                {CONCEPT_LIBRARY.filter((concept) => concept.group === group).map((concept) => {
                  const isUnlocked = unlocked.has(concept.id);
                  return (
                    <article key={concept.id} className={`codex-card ${isUnlocked ? "unlocked" : "locked"}`}>
                      <span>{isUnlocked ? "Unlocked" : "Locked"}</span>
                      <h4>{isUnlocked ? concept.title : "???"}</h4>
                      <p>{isUnlocked ? concept.desc : "Discover this concept by playing more hands."}</p>
                    </article>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function TeachingPanel({ lesson }) {
  if (!lesson?.title && !lesson?.body) return null;
  return (
    <div className="teaching-panel">
      <h3>{lesson.title || "Quantum lesson"}</h3>
      <p>{lesson.body}</p>
      {lesson.gates?.length ? <small>Played gates: {lesson.gates.join(", ")}</small> : null}
    </div>
  );
}

function LearningCatalog({ state }) {
  const hands = state.hand_catalog || [];
  const packs = state.pack_catalog || [];
  if (!hands.length && !packs.length) return null;
  return (
    <section className="learning-catalog">
      <div>
        <h3>Hand Types</h3>
        <div className="catalog-grid">
          {hands.map((hand) => (
            <span key={hand.name}>{hand.name}: {hand.chips} x {hand.mult}</span>
          ))}
        </div>
      </div>
      <div>
        <h3>Pack Types</h3>
        <div className="catalog-grid">
          {packs.map((pack) => (
            <span key={pack.type}>{pack.name}: {pack.desc}</span>
          ))}
        </div>
      </div>
    </section>
  );
}

function RouletteChances({ chances = {} }) {
  return (
    <div className="roulette-chances">
      {Object.entries(chances).map(([name, chance]) => (
        <span key={name}>{name}: {chance}%</span>
      ))}
    </div>
  );
}

function ProgressMeter({ current, target }) {
  const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0;
  return (
    <div className="progress-meter" aria-label={`Progress ${pct}%`}>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span>{pct}%</span>
    </div>
  );
}

function MeasurementBurst({ label }) {
  return (
    <div className="measurement-burst" aria-hidden="true">
      <div className="measurement-ring" />
      <span className="measurement-chip">{label}</span>
      <i className="spark spark-1" />
      <i className="spark spark-2" />
      <i className="spark spark-3" />
      <i className="spark spark-4" />
      <i className="spark spark-5" />
      <i className="spark spark-6" />
    </div>
  );
}

function CircuitRulesPage({ onBack, onExit }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} />
      <section className="rules-page">
        <div className="rules-header">
          <div>
            <span className="game-badge static">circuit</span>
            <h2>Quantum Hacker Rules</h2>
            <p>Build a two-qubit circuit, match the target distribution, and decide when to lock in riskier multipliers.</p>
          </div>
          <button className="btn btn-play-hand" onClick={onBack}>Back to Game</button>
        </div>

        <div className="rules-grid">
          <article className="rule-card">
            <h3>Goal</h3>
            <p>Each blind gives a target probability distribution. Your circuit produces probabilities for 00, 01, 10, and 11. Better overlap creates more base chips.</p>
          </article>
          <article className="rule-card">
            <h3>Gates</h3>
            <p>H creates superposition and multiplies score. X flips a qubit. Z can become a multiplier with the Phase joker. CNOT entangles one qubit with the other.</p>
          </article>
          <article className="rule-card">
            <h3>Play Hand</h3>
            <p>Play Hand scores the current circuit, consumes one hand, clears the board, and resets stored multiplier back to x1.</p>
          </article>
          <article className="rule-card">
            <h3>Observe</h3>
            <p>Observe stores the current gate multiplier without spending a hand, then clears the circuit and spins roulette. More Observe uses and higher stored multiplier increase risk.</p>
          </article>
          <article className="rule-card">
            <h3>Roulette</h3>
            <p>SAFE has no penalty. Other outcomes can remove one hand, reset stored multiplier, or remove score. The visible odds are the odds used for that spin.</p>
          </article>
          <article className="rule-card">
            <h3>Shop</h3>
            <p>After clearing a blind, buy up to two jokers. Active jokers change scoring or boss constraints, and can be toggled in the shop.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

function CardRulesPage({ onBack, onExit }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} />
      <section className="rules-page">
        <div className="rules-header">
          <div>
            <span className="game-badge static">cards</span>
            <h2>Quantum Balatro Original Rules</h2>
            <p>Stage gate cards into qubit slots, make a quantum poker hand, and score through both hand type and state fidelity.</p>
          </div>
          <button className="btn btn-play-hand" onClick={onBack}>Back to Game</button>
        </div>

        <div className="rules-grid">
          <article className="rule-card">
            <h3>Goal</h3>
            <p>Reach the blind target before plays run out. Clearing a blind pays chips based on blind size and unused plays.</p>
          </article>
          <article className="rule-card">
            <h3>Staging</h3>
            <p>Drag cards into the circuit. Slots determine the order cards are played, and the row determines the target qubit. CNOT uses the next qubit when needed.</p>
          </article>
          <article className="rule-card">
            <h3>Hand Types</h3>
            <p>Gate combinations create hands such as Bell Pair, Flush, Full House, W State, and GHZ State. Stronger hands have higher base chips and multiplier.</p>
          </article>
          <article className="rule-card">
            <h3>Fidelity</h3>
            <p>Your circuit is compared against the target quantum state for the detected hand. Higher fidelity preserves more of the base score.</p>
          </article>
          <article className="rule-card">
            <h3>Discards</h3>
            <p>Select hand cards and discard them to draw replacements. Discards are limited per blind, so use them to search for missing gate combinations.</p>
          </article>
          <article className="rule-card">
            <h3>Shop</h3>
            <p>Spend chips on jokers or packs. Jokers alter scoring, while packs add new quantum cards such as RX phase cards to your deck.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

function TopBar({ onExit, onRules }) {
  return (
    <div className="top-controls">
      <button className="btn-back" onClick={onExit}>Back to Game Lobby</button>
      {onRules && <button className="btn-back" onClick={onRules}>Rules</button>}
    </div>
  );
}
