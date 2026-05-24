import { useEffect, useMemo, useRef, useState } from "react";
import Balatro from "../components/Balatro.jsx";
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
const GATE_USAGE = {
  H: "推荐用途：想把一个确定结果拆成多个可能结果时使用。常用于制造叠加，也常作为 CNOT 之前的起手。",
  X: "推荐用途：想把 |0> 翻成 |1>，或把目标概率推向另一个基态时使用。",
  Z: "推荐用途：它主要改变相位，概率图不一定立刻变化；适合相位奖励、相位目标或 Z 相关支线。",
  CNOT: "推荐用途：先用 H 制造叠加，再接 CNOT，最容易做出 Bell Pair 或纠缠相关效果。",
  CX: "推荐用途：CNOT 的另一种写法。用一个量子比特控制另一个量子比特翻转。",
  CZ: "推荐用途：受控相位门。适合相位流、Phase Lock、以及需要两个量子比特产生相位关联时。",
  SWAP: "推荐用途：交换两个量子比特的状态。适合修正线路路由，或触发拓扑/换线相关牌型。",
  RX: "推荐用途：绕 X 轴旋转。适合旋转流，也能把确定态转成带角度的量子态。",
  RY: "推荐用途：绕 Y 轴旋转。适合制造平滑的概率变化，常用于提高保真度。",
  RZ: "推荐用途：绕 Z 轴改变相位。适合相位流和 Phase Experiment 事件。",
  CCX: "推荐用途：两个控制位共同决定一次翻转。适合高阶控制牌型和后期强牌。",
  NOISE: "推荐用途：噪声通常不是好牌，尽量通过弃牌或卡包管理减少它的影响。",
};

function gateUsage(gate) {
  return GATE_USAGE[String(gate || "").toUpperCase()] || "推荐用途：观察目标概率和当前牌型，尝试把它放在线路中测试效果。";
}

function buildRecommendationMap(gates = []) {
  const map = new Map();
  if (!Array.isArray(gates)) return map;
  gates.forEach((gate) => {
    if (!gate || !Number.isInteger(gate.qubit) || !Number.isInteger(gate.slot)) return;
    map.set(`${gate.qubit}_${gate.slot}`, gate);
  });
  return map;
}

function normalizeRecommendation(recommendation) {
  return {
    used: true,
    text: recommendation?.text || "",
    gates: Array.isArray(recommendation?.gates) ? recommendation.gates : [],
  };
}

function availableGate(state, preferred, fallback = null) {
  const hand = Array.isArray(state.hand_cards) ? state.hand_cards : [];
  if (hand.some((card) => card.gate === preferred)) return preferred;
  return fallback || hand[0]?.gate || preferred;
}

function localCircuitRecommendation(state) {
  const targets = state.level?.target_probs || {};
  const positive = Object.entries(targets)
    .filter(([, probability]) => probability > 0.01)
    .map(([name]) => name);
  const positiveSet = new Set(positive);

  if (positiveSet.size === 1 && positiveSet.has("00")) {
    return normalizeRecommendation({
      text: "目标只有 00：少放门，保持干净态。",
      gates: [{ gate: "KEEP", qubit: 0, slot: 0 }],
    });
  }

  if (positiveSet.has("00") && positiveSet.has("11")) {
    const gates = [{ gate: availableGate(state, "H"), qubit: 0, slot: 0 }];
    if (availableGate(state, "CNOT", "") === "CNOT") {
      gates.push({ gate: "CNOT", qubit: 0, slot: 1, targets: [0, 1] });
    }
    return normalizeRecommendation({
      text: "想触发 Bell Pair：先 H，再 CNOT。",
      gates,
    });
  }

  if (positiveSet.has("00") && positiveSet.has("10") && positiveSet.size <= 2) {
    return normalizeRecommendation({
      text: "想让 00 和 10 都出现：试试 H 放在 q0。",
      gates: [{ gate: availableGate(state, "H"), qubit: 0, slot: 0 }],
    });
  }

  return normalizeRecommendation({
    text: "目标分布较散：先用 H 制造叠加，再根据目标微调。",
    gates: [{ gate: availableGate(state, "H"), qubit: 0, slot: 0 }],
  });
}

function localCardRecommendation(state) {
  const hand = Array.isArray(state.hand_cards) ? state.hand_cards : [];
  const hasGate = (gate) => hand.some((card) => card.gate === gate);
  if (hasGate("H") && hasGate("CNOT")) {
    return normalizeRecommendation({
      text: "想触发 Bell Pair：先 H，再 CNOT。",
      gates: [
        { gate: "H", qubit: 0, slot: 0 },
        { gate: "CNOT", qubit: 0, slot: 1, targets: [0, 1] },
      ],
    });
  }
  if (hasGate("H")) {
    return normalizeRecommendation({
      text: "想让多个结果出现：先把 H 放在 q0。",
      gates: [{ gate: "H", qubit: 0, slot: 0 }],
    });
  }
  const phaseGate = ["Z", "CZ", "RZ"].find((gate) => hasGate(gate));
  if (phaseGate) {
    return normalizeRecommendation({
      text: "手里有相位牌：优先试一次相位门，配合相位奖励。",
      gates: [{ gate: phaseGate, qubit: 0, slot: 0 }],
    });
  }
  return normalizeRecommendation({
    text: "目标只有 00 时可以少放门；否则先放一张最稳定的基础门试探。",
    gates: [{ gate: hand[0]?.gate || "KEEP", qubit: 0, slot: 0 }],
  });
}
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
    title: "准备好就结算本手",
    body: "结算本手会结算当前线路、消耗一次出手机会，并在达标后进入商店。Boss 关还会限制线路规则。",
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
    body: "右侧会显示最近一次牌型、分数拆解和教学提示。准备好后按结算本手；不想要的牌可以选中后弃掉。",
    cue: "开始游戏",
  },
];

const CONCEPT_LIBRARY = [
  { id: "gate-h", group: "Gates", title: "H 门", desc: "制造叠加态：一个基态可以分裂成多个测量结果。" },
  { id: "gate-x", group: "Gates", title: "X 门", desc: "比特翻转门，把 |0> 变成 |1>，也把 |1> 变成 |0>。" },
  { id: "gate-z", group: "Gates", title: "Z 门", desc: "相位翻转门。它不一定立刻改变测量概率，但会改变干涉。" },
  { id: "gate-cnot", group: "Gates", title: "CNOT 门", desc: "受控操作。在叠加态上使用时，可能产生纠缠。" },
  { id: "gate-cz", group: "Gates", title: "CZ 门", desc: "受控相位门，用相位把两个量子比特联系起来。" },
  { id: "gate-swap", group: "Gates", title: "SWAP 门", desc: "交换两个量子比特的状态，让线路路由也成为解题的一部分。" },
  { id: "gate-rx", group: "Gates", title: "RX 门", desc: "绕 Bloch 球 X 轴的连续旋转。" },
  { id: "gate-ry", group: "Gates", title: "RY 门", desc: "绕 Bloch 球 Y 轴的连续旋转。" },
  { id: "gate-rz", group: "Gates", title: "RZ 门", desc: "绕 Bloch 球 Z 轴旋转，改变相对相位。" },
  { id: "gate-ccx", group: "Gates", title: "CCX 门", desc: "Toffoli 门：两个控制位共同决定目标位是否翻转。" },
  { id: "formula-probability", group: "Formulas", title: "测量概率", desc: "P(s) = |amplitude(s)|^2。Game1 通过匹配测量概率得分。" },
  { id: "formula-fidelity", group: "Formulas", title: "态保真度", desc: "F = |<target|current>|^2。Game2 用它衡量当前量子态和目标态的接近程度。" },
  { id: "formula-score", group: "Formulas", title: "得分公式", desc: "得分由基础筹码、倍率，以及概率重合或保真度共同决定。" },
  { id: "state-bell", group: "States", title: "Bell 对", desc: "一种双量子比特纠缠态，测量结果之间有很强相关性。" },
  { id: "state-ghz", group: "States", title: "GHZ 态", desc: "多量子比特纠缠态，所有量子比特共享一个整体相关性。" },
  { id: "state-w", group: "States", title: "W 态", desc: "一种多量子比特态，单个激发分布在多个量子比特上。" },
  { id: "state-phase", group: "States", title: "相位锁", desc: "概率看起来可能接近，但相对相位会影响保真度。" },
  { id: "state-rotation", group: "States", title: "旋转组", desc: "使用连续旋转门，而不是只做离散翻转的牌型。" },
  { id: "system-measurement", group: "Systems", title: "测量坍缩", desc: "观察会提取信息，也会让准备好的线路不再保持原样。" },
  { id: "system-overlap", group: "Systems", title: "目标重合", desc: "可以用输出分布和目标分布的重合程度来评价线路。" },
  { id: "system-boss", group: "Systems", title: "硬件约束", desc: "Boss 规则代表深度、路由、相位要求、门数量等限制。" },
  { id: "system-clear", group: "Systems", title: "关卡完成", desc: "完成关卡表示你的量子策略达到了目标分。" },
  { id: "system-failure", group: "Systems", title: "运行失败", desc: "失败也是诊断信息：比较门序列、目标和回顾面板，再规划下一条线路。" },
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
    label: "纠缠流",
    hint: "用 CNOT 和 Bell 类牌型把相关性转化成额外筹码。",
    gates: ["CNOT", "CX"],
    wants: ["CNOT", "Bell 牌型", "稳定器"],
  },
  Phase: {
    label: "相位流",
    hint: "Z/CZ/RZ 把看不见的相位变化转成倍率收益。",
    gates: ["Z", "CZ", "RZ"],
    wants: ["Z", "CZ", "相位钥匙"],
  },
  Compiler: {
    label: "压缩流",
    hint: "更短、更干净的线路会获得更高收益。",
    gates: [],
    wants: ["护盾", "低门数", "高目标重合"],
  },
  Topology: {
    label: "拓扑流",
    hint: "用换线和约束工具处理更刁钻的 Boss 规则。",
    gates: ["SWAP", "CCX"],
    wants: ["SWAP", "CCX", "护盾"],
  },
  Measurement: {
    label: "测量流",
    hint: "纯态或均匀分布目标会变成稳定的筹码来源。",
    gates: ["H"],
    wants: ["H", "纯态目标", "均匀目标"],
  },
  Rotation: {
    label: "旋转流",
    hint: "围绕 RX/RY/RZ 组成连续旋转牌型。",
    gates: ["RX", "RY", "RZ"],
    wants: ["RX", "RY", "RZ"],
  },
  Tempo: {
    label: "节奏流",
    hint: "用容错和补救效果提高失误后的续航。",
    gates: [],
    wants: ["保命效果", "额外机会", "兜底得分"],
  },
  Wildcard: {
    label: "混搭流",
    hint: "适合还没定型的混合量子手牌。",
    gates: [],
    wants: ["任意高价值牌型"],
  },
};

const EVENT_TEXT = {
  CALIBRATION_DRIFT: {
    name: "校准漂移",
    desc: "本关第一次打出 H 时，获得额外倍率。",
  },
  NOISY_HARDWARE: {
    name: "噪声硬件",
    desc: "本关出牌/放门超过 3 张后，结算会受到噪声惩罚。",
  },
  CHEAP_MEASUREMENT: {
    name: "廉价测量",
    desc: "本关测量代价降低，观察或测量更安全。",
  },
  PHASE_EXPERIMENT: {
    name: "相位实验",
    desc: "Z/CZ/RZ 这类相位门会提供额外奖励。",
  },
  ENTANGLEMENT_TAX: {
    name: "纠缠税",
    desc: "CNOT 更强，但会消耗一部分资源。",
  },
};

const BONUS_OBJECTIVE_TEXT = {
  LOW_GATE_CLEAR: {
    name: "极简线路",
    desc: "本关通关时，最后一手不超过 3 个门。",
  },
  HIGH_FIDELITY: {
    name: "干净态",
    desc: "任意一手达到至少 90% 保真度。",
  },
  NO_CNOT_CLEAR: {
    name: "无纠缠路线",
    desc: "本关通关时，最后一手不使用 CNOT。",
  },
  Z_SCORE: {
    name: "相位标记",
    desc: "使用 Z/CZ/RZ 并成功得分。",
  },
  BELL_PAIR: {
    name: "Bell Pair 触发",
    desc: "打出一次 Bell Pair 牌型。",
  },
  TWO_HAND_CLIMB: {
    name: "连续提分",
    desc: "连续两手都比上一手得分更高。",
  },
};

const EVENT_NOTE_TEXT = [
  ["+1.5 mult from first H", "第一次 H：+1.5 倍率"],
  ["+2 mult from first H", "第一次 H：+2 倍率"],
  ["-15% chips after 3 gates", "超过 3 个门：筹码 -15%"],
  ["-18% fidelity after 3 cards", "超过 3 张牌：保真度 -18%"],
  ["+0.10 fidelity from cheap measurement", "廉价测量：保真度 +0.10"],
  ["chips from phase cards", "相位门额外筹码"],
  ["chips from CNOT", "CNOT 额外筹码，同时缴纳纠缠税"],
  ["score from Entanglement Tax", "纠缠税消耗分数"],
  ["chips per Z", "每个 Z 额外筹码"],
  ["CNOT, -80 score", "CNOT 增强，结算时 -80 分"],
];

function localizeEvent(event = {}) {
  const text = EVENT_TEXT[event.id] || {};
  return {
    ...event,
    name: text.name || event.name,
    desc: text.desc || event.desc,
  };
}

function localizeEventNote(note = "") {
  if (!note) return "";
  const match = EVENT_NOTE_TEXT.find(([source]) => note.includes(source));
  return match ? match[1] : note;
}

function localizeBonusObjective(objective = {}) {
  const text = BONUS_OBJECTIVE_TEXT[objective.id] || {};
  return {
    ...objective,
    name: text.name || objective.name,
    desc: text.desc || objective.desc,
  };
}

function localizeRoulette(item = {}) {
  const text = {
    SAFE: ["安全", "波形稳定"],
    "-1 HAND": ["-1 次出手", "时间膨胀"],
    "RESET MULT": ["重置倍率", "倍率坍缩"],
    "-200 CHIPS": ["-200 筹码", "能量泄漏"],
  }[item.name];
  return text ? { ...item, name: text[0], message: text[1] } : item;
}

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

function QuantumBalatroBackdrop() {
  return (
    <div className="quantum-balatro-backdrop" aria-hidden="true">
      <Balatro
        color1="#12B981"
        color2="#0EA5E9"
        color3="#0B1020"
        contrast={3.2}
        isRotate
        lighting={0.34}
        mouseInteraction
        pixelFilter={700}
        spinAmount={0.22}
        spinRotation={-1.8}
        spinSpeed={5.2}
      />
    </div>
  );
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
    return (
      <div className="quantum-game">
        <QuantumBalatroBackdrop />
        <div className="game-loading">Loading quantum game...</div>
      </div>
    );
  }

  return (
    <div className="quantum-game">
      <QuantumBalatroBackdrop />
      <button className="codex-toggle" onClick={() => setCodexOpen(true)}>
        概念图鉴 <span>{conceptIds.length}/{CONCEPT_LIBRARY.length}</span>
      </button>
      {newConceptCount > 0 && <div className="codex-toast">解锁 {newConceptCount} 条新概念</div>}
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
      <h1 className="main-title">量子游戏</h1>
      <p className="subtitle">选择一个游戏开始。两个游戏都会在平台内直接运行。</p>
      <div className="games-grid">
        {gamesList.map((game) => (
          <article key={game.id} className="game-entry-card">
            <span className="game-badge">{game.kind}</span>
            <h2>{game.name}</h2>
            <p>{game.desc}</p>
            <code>{game.dir}</code>
            <button className="btn-enter" onClick={() => onStart(game.id)}>
              开始游戏
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
  const [localRecommendation, setLocalRecommendation] = useState(null);
  const [showRecommendationShadow, setShowRecommendationShadow] = useState(false);
  const recommendation = localRecommendation || state.recommendation;
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
  const recommendationBySlot = useMemo(
    () => buildRecommendationMap(showRecommendationShadow ? recommendation?.gates : []),
    [showRecommendationShadow, recommendation],
  );
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
    setLocalRecommendation(null);
    setShowRecommendationShadow(false);
  }, [state.level_index]);

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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({
        gates: state.gates.filter((gate) => gate.qubit !== qubit || gate.slot !== slot),
      }),
    });
    await onRefresh();
  };

  const action = async (path) => {
    setShowRecommendationShadow(false);
    await api(path, { method: "POST" });
    await onRefresh();
  };

  const recommendCircuit = async () => {
    const fallback = localCircuitRecommendation(state);
    setLocalRecommendation(fallback);
    setShowRecommendationShadow(true);
    try {
      const nextState = await api("/circuit/recommend", { method: "POST" });
      if (nextState?.recommendation) setLocalRecommendation(normalizeRecommendation(nextState.recommendation));
      setShowRecommendationShadow(true);
      await onRefresh();
    } catch (err) {
      console.warn("Circuit recommendation fallback used", err);
    }
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
      <TopBar
        onExit={onExit}
        onRules={() => setShowRules(true)}
        onTutorial={() => {
          window.localStorage.removeItem(CIRCUIT_TUTORIAL_STORAGE_KEY);
          setTutorialStep(0);
          setShowTutorialLocal(true);
        }}
      />
      <header className="hud">
        <div>
          <h2>Quantum Hacker</h2>
          <p>{state.level.desc}</p>
          <ProgressMeter current={state.score} target={state.level.target} />
        </div>
        <div className="stats">
          <span>关卡 {state.level_index + 1}/{state.level_count}</span>
          <span>分数 {state.score} / {state.level.target}</span>
          <span>出手机会 {state.hands_left}</span>
          <span>资金 ${state.money}</span>
          <span>牌库 {state.deck_count} / 弃牌 {state.discard_count}</span>
          <span className={recommendation?.used ? "stat-used" : ""}>推荐 {recommendation?.used ? 1 : 0}/1</span>
        </div>
      </header>

      <section className="main-layout">
        {playAnimating && <MeasurementBurst label="测量线路" />}
        <aside className="side-panel">
          <LevelEventPanel event={state.blind_event} note={state.preview?.event_note} />
          <BonusObjectivePanel objective={state.bonus_objective} rewardUnit="资金" />
          <JokerBuildPanel jokers={state.owned_jokers} gates={stagedEvolutionGates} compact />
          <QuantumRecapPanel recap={state.last_recap} />
        </aside>

        <div className="circuit-board">
          <div className="section-head">
            <h3>量子线路</h3>
            <span className="selected-gate-readout">已选 {selectedCard ? `${selectedCard.gate} #${selectedCard.id}` : "无"}</span>
          </div>

          <div className="gate-palette circuit-card-hand" aria-label="Gate card hand">
            {handCards.map((card) => {
              const detail = GATE_DETAILS[card.gate] || card;
              return (
                <button
                  key={card.id}
                  className={`gate-card gate-card-${card.gate.toLowerCase()} ${selectedCard?.id === card.id ? "active" : ""}`}
                  data-usage={gateUsage(card.gate)}
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
            {!handCards.length && <p className="empty-hand-note">当前没有可用门卡。</p>}
          </div>

          {[0, 1].map((qubit) => (
            <div key={qubit} className="circuit-row">
              <span className="qubit-label">q[{qubit}]</span>
              <div className="slots-container">
                {[0, 1, 2, 3].map((slot) => {
                  const gate = gatesBySlot.get(`${qubit}_${slot}`);
                  const recommendedGate = !gate ? recommendationBySlot.get(`${qubit}_${slot}`) : null;
                  return (
                    <button
                      key={slot}
                      className={`circuit-slot ${gate ? "occupied" : ""} ${recommendedGate ? "recommended-slot" : ""}`}
                      onClick={() => (gate ? removeGate(qubit, slot) : setGate(qubit, slot))}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={(event) => dropGate(event, qubit, slot)}
                      title={gate ? "点击收回手牌" : selectedCard ? `放置 ${selectedCard.gate}` : "还没有选牌"}
                    >
                      {gate?.gate || (recommendedGate ? <span className="shadow-gate">{recommendedGate.gate === "KEEP" ? "空" : recommendedGate.gate}</span> : "+")}
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
          <div className="preview-box">
            <span>预览</span>
            <strong>{state.preview.chips} x {state.preview.mult} = {state.preview.total}</strong>
          </div>
          <CircuitScoreBreakdown state={state} />
          {state.stored_mult > 1 && <div className="notice">已保存倍率 x{state.stored_mult}</div>}
          {state.warning && <div className="warning">{state.warning}</div>}
          <button
            className="btn btn-recommend"
            onClick={recommendCircuit}
            disabled={recommendation?.used}
          >
            {recommendation?.used ? "影子线路已显示" : "推荐出牌"}
          </button>
          <button className="btn btn-observe" onClick={() => action("/circuit/observe")}>观察</button>
          <button className="btn btn-play-hand" onClick={playCircuitHand}>结算本手</button>
          <button className="btn btn-clear" onClick={() => action("/circuit/clear")}>清空线路</button>
        </aside>
      </section>

      {state.phase !== "PLAYING" && (
        <div className="game-overlay">
          <h2>{state.phase === "GAME_OVER" ? "波函数坍缩" : state.phase === "WIN" ? "通关成功" : "关卡完成"}</h2>
          <CircuitFormulaSummary state={state} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          <button className="btn btn-play-hand" onClick={() => action("/start/game1")}>重新开始</button>
        </div>
      )}
    </main>
  );
}

function CircuitRoulette({ state, onAction, onExit, onRules }) {
  const [revealed, setRevealed] = useState(false);
  const rouletteResult = localizeRoulette(state.last_roulette);
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
          <h2>测量轮盘</h2>
          <p>观察会保存当前倍率，同时让线路坍缩为一个随机事件。</p>
        </div>
        <div className="stats">
          <span>分数 {state.score} / {state.level.target}</span>
          <span>出手机会 {state.hands_left}</span>
          <span>已保存 x{state.stored_mult}</span>
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
            <strong>{rouletteResult?.name}</strong>
            <span>{rouletteResult?.message}</span>
          </div>
        ) : (
          <div className="roulette-result roulette-pending">
            <strong>旋转中...</strong>
            <span>正在坍缩波形</span>
          </div>
        )}
        <RouletteChances chances={state.roulette_chances} />
        {revealed ? (
          <button className="btn btn-play-hand" onClick={() => onAction("/circuit/roulette/continue")}>
            继续
          </button>
        ) : (
          <button className="btn btn-clear" disabled>
            旋转中
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
          <h2>Quantum Hacker 商店</h2>
          <p>最多购买两个 Joker。启用的 Joker 会改变线路得分和 Boss 约束。</p>
        </div>
        <div className="stats">
          <span>资金 ${state.money}</span>
          <span>关卡 {state.level_index + 1}/{state.level_count}</span>
          <span>Joker {state.owned_jokers.length}/2</span>
        </div>
      </header>

      <section className="shop-layout">
        <div className="shop-shelf">
          <h3>Joker</h3>
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
                    购买 Joker
                  </button>
                </article>
              ))
            ) : (
              <p className="empty-hand-note">本次商店没有剩余 Joker。</p>
            )}
          </div>
        </div>

        <aside className="shop-side">
          <JokerBuildPanel jokers={state.owned_jokers} gates={state.last_recap?.gates || []} />
          <CircuitFormulaSummary state={state} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          <h3>已拥有 Joker</h3>
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
                  <span>{active ? "已启用" : "未启用"} - {joker.desc}</span>
                </button>
              );
            })
          ) : (
            <p className="empty-hand-note">还没有拥有 Joker。</p>
          )}
          <button className="btn btn-play-hand" onClick={() => onAction("/circuit/next")}>
            下一关
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
  const [localRecommendation, setLocalRecommendation] = useState(null);
  const [showRecommendationShadow, setShowRecommendationShadow] = useState(false);
  const recommendation = localRecommendation || state.recommendation;

  useEffect(() => {
    setSelectedCardIds([]);
    setStagedCards({});
    setShowTutorialLocal(Boolean(state.show_tutorial));
    if (state.show_tutorial) {
      setTutorialStep(0);
    }
  }, [state.phase, state.hand_cards.length, state.current_score, state.plays_left, state.discards_left, state.show_tutorial]);

  useEffect(() => {
    setLocalRecommendation(null);
    setShowRecommendationShadow(false);
  }, [state.ante, state.blind_index]);

  const tutorial = CARD_TUTORIAL_STEPS[tutorialStep] || CARD_TUTORIAL_STEPS[0];

  const visibleStagedCards = useMemo(() => {
    return Object.fromEntries(
      Object.entries(stagedCards).filter((entry) => state.hand_cards[entry[1].cardIndex]),
    );
  }, [stagedCards, state.hand_cards]);
  const recommendationBySlot = useMemo(
    () => buildRecommendationMap(showRecommendationShadow ? recommendation?.gates : []),
    [showRecommendationShadow, recommendation],
  );
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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
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
    setShowRecommendationShadow(false);
    await api("/discard", { method: "POST", body: JSON.stringify(selectedCardIds) });
    await onRefresh();
  };

  const action = async (path) => {
    setShowRecommendationShadow(false);
    await api(path, { method: "POST" });
    await onRefresh();
  };

  const recommendCards = async () => {
    const fallback = localCardRecommendation(state);
    setLocalRecommendation(fallback);
    setShowRecommendationShadow(true);
    try {
      const result = await api("/cards/recommend", { method: "POST" });
      if (result?.recommendation) setLocalRecommendation(normalizeRecommendation(result.recommendation));
      setShowRecommendationShadow(true);
      await onRefresh();
    } catch (err) {
      console.warn("Card recommendation fallback used", err);
    }
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

  if (state.phase === "OPENING_JOKER_PACK") {
    return <JokerPackOpening state={state} onAction={action} onExit={onExit} onRules={() => setShowRules(true)} />;
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
          <p>把门卡放进量子比特插槽，组成一手量子牌型。</p>
          <ProgressMeter current={state.current_score} target={state.target_score} />
        </div>
        <div className="stats">
          <span>筹码 ${state.chips}</span>
          <span>分数 {state.current_score} / {state.target_score}</span>
          <span>出手 {state.plays_left}</span>
          <span>弃牌 {state.discards_left}</span>
          <span className={recommendation?.used ? "stat-used" : ""}>推荐 {recommendation?.used ? 1 : 0}/1</span>
        </div>
      </header>

      <section className="main-layout">
        {playAnimating && <MeasurementBurst label="测量手牌" />}
        <aside className="side-panel">
          <TeachingPanel lesson={state.lesson} />
          <LevelEventPanel event={state.blind_event} note={state.last_score_breakdown?.event_note} />
          <BonusObjectivePanel objective={state.bonus_objective} rewardUnit="筹码" />
          <JokerBuildPanel jokers={state.jokers} gates={stagedEvolutionGates} compact />
          <QuantumRecapPanel recap={state.last_recap} />
        </aside>

        <div className="circuit-board">
          <h3>出牌线路</h3>
          <div className="circuit-grid">
          {Array.from({ length: state.num_qubits }, (_, qubit) => (
            <div key={qubit} className="circuit-row">
              <span className="qubit-label">q[{qubit}]</span>
              <div className="slots-container">
                {[0, 1, 2, 3].map((slot) => {
                  const staged = visibleStagedCards[`${qubit}_${slot}`];
                  const stagedCardIdx = staged?.cardIndex;
                  const card = state.hand_cards[stagedCardIdx];
                  const recommendedGate = !card ? recommendationBySlot.get(`${qubit}_${slot}`) : null;
                  const isControlled = CONTROLLED_GATES.has(card?.gate);
                  const targetQubit = staged?.targets?.[1] ?? (qubit + 1) % state.num_qubits;
                  const targetOffset = targetQubit - qubit;
                  return (
                    <div
                      key={slot}
                      className={`circuit-slot ${card ? "occupied draggable-card-slot" : ""} ${isControlled ? "controlled-gate" : ""} ${recommendedGate ? "recommended-slot" : ""}`}
                      draggable={Boolean(card)}
                      onDragStart={(event) => card && startCardDrag(event, stagedCardIdx, "stage")}
                      onDragEnd={() => setDraggingCardId(null)}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={(event) => dropCard(event, qubit, slot)}
                      onClick={() => card && unstageSlot(qubit, slot)}
                      title={card ? "拖到其他插槽，或点击移除" : "把卡牌拖到这里"}
                    >
                      {isControlled && (
                        <span
                          className={`gate-connector ${targetOffset < 0 ? "target-up" : "target-down"}`}
                          style={{ "--connector-span": Math.max(1, Math.abs(targetOffset)) }}
                          aria-hidden="true"
                        />
                      )}
                      {card?.gate || (recommendedGate ? <span className="shadow-gate">{recommendedGate.gate === "KEEP" ? "空" : recommendedGate.gate}</span> : "+")}
                      {isControlled && (
                        <label className="target-picker" onClick={(event) => event.stopPropagation()}>
                          <span>到</span>
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
          <CardHandArea
            state={state}
            visibleStagedCards={visibleStagedCards}
            selectedCardIds={selectedCardIds}
            draggingCardId={draggingCardId}
            startCardDrag={startCardDrag}
            setDraggingCardId={setDraggingCardId}
            setSelectedCardIds={setSelectedCardIds}
          />
        </div>

        <aside className="control-panel">
          <div className="preview-box">
            <span>上一手</span>
            <strong>{state.last_hand_played}</strong>
          </div>
          <CardScoreBreakdown breakdown={state.last_score_breakdown} />
          <StateEvolutionTimeline gates={stagedEvolutionGates} qubits={state.num_qubits} />
          <button
            className="btn btn-recommend"
            onClick={recommendCards}
            disabled={recommendation?.used}
          >
            {recommendation?.used ? "影子线路已显示" : "推荐出牌"}
          </button>
          <button className="btn btn-play-hand" onClick={playHand} disabled={!Object.keys(visibleStagedCards).length}>
            结算本手
          </button>
          <button className="btn btn-discard" onClick={discard} disabled={!selectedCardIds.length}>
            弃掉已选
          </button>
          <button className="btn btn-clear" onClick={() => setStagedCards({})}>
            清空出牌区
          </button>
        </aside>
      </section>

      <section className="hand-area">
        <h3>手牌</h3>
        {state.phase !== "PLAYING" && (
          <p className="empty-hand-note">
            {state.phase === "REWARD"
              ? "关卡已完成。刚才的手牌已经结算并进入弃牌堆。"
              : "当前已经不在出牌阶段。"}
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
              ? "关卡完成"
              : state.phase === "VICTORY"
                ? "通关成功"
                : "游戏结束"}
          </h2>
          {state.phase === "REWARD" && <p>奖励已加入。当前筹码：${state.chips}</p>}
          <CardFormulaSummary breakdown={state.last_score_breakdown} />
          <QuantumRecapPanel recap={state.last_recap} compact />
          {state.phase === "REWARD" ? (
            <button className="btn btn-play-hand" onClick={() => action("/cards/shop")}>进入商店</button>
          ) : (
            <button className="btn btn-play-hand" onClick={() => action("/start/game2")}>重新开始</button>
          )}
        </div>
      )}
    </main>
  );
}

function CardHandArea({
  state,
  visibleStagedCards,
  selectedCardIds,
  draggingCardId,
  startCardDrag,
  setDraggingCardId,
  setSelectedCardIds,
}) {
  return (
    <section className="hand-area board-hand-area">
      <h3>手牌</h3>
      {state.phase !== "PLAYING" && (
        <p className="empty-hand-note">
          {state.phase === "REWARD"
            ? "关卡已完成。刚才的手牌已经结算并进入弃牌堆。"
            : "当前已经不在出牌阶段。"}
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
              data-usage={gateUsage(card.gate)}
              draggable
              onDragStart={(event) => startCardDrag(event, index)}
              onDragEnd={() => setDraggingCardId(null)}
              onClick={() =>
                draggingCardId === index
                  ? undefined
                  : setSelectedCardIds((current) =>
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
  );
}

function CardShop({ state, onAction, onExit, onRules }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <header className="hud">
        <div>
          <h2>量子商店</h2>
          <p>花费筹码购买 Joker，或把量子卡包加入牌库。</p>
        </div>
        <div className="stats">
          <span>筹码 ${state.chips}</span>
          <span>轮次 {state.ante}</span>
          <span>{state.blind_index + 1} / 3</span>
          <span>Joker {state.jokers.length} / 5</span>
        </div>
      </header>

      <section className="shop-layout">
        <div className="shop-shelf">
          <h3>Joker</h3>
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
                    购买 Joker
                  </button>
                </article>
              ))
            ) : (
              <p className="empty-hand-note">本次商店没有剩余 Joker。</p>
            )}
          </div>
        </div>

        <aside className="shop-side">
          <JokerBuildPanel jokers={state.jokers} gates={state.last_recap?.gates || []} />
          <h3>卡包</h3>
          {state.shop_pack ? (
            <article className="shop-card pack-shop-card">
              <span className="shop-type">PACK</span>
              <h4>{state.shop_pack.name}</h4>
              <p>{state.shop_pack.desc || "打开后获得一张量子门卡，并加入你的牌库。"}</p>
              <strong>${state.shop_pack.cost}</strong>
              <button
                className="btn btn-observe"
                onClick={() => onAction("/cards/buy-pack")}
                disabled={state.chips < state.shop_pack.cost}
              >
                购买卡包
              </button>
            </article>
          ) : (
            <p className="empty-hand-note">卡包已售罄。</p>
          )}

          {state.shop_joker_pack ? (
            <article className="shop-card pack-shop-card joker-pack-shop-card">
              <span className="shop-type">JOKER PACK</span>
              <h4>{state.shop_joker_pack.name}</h4>
              <p>{state.shop_joker_pack.desc || "打开后随机出现两张 Joker，选择一张加入你的流派。"}</p>
              <strong>${state.shop_joker_pack.cost}</strong>
              <button
                className="btn btn-observe"
                onClick={() => onAction("/cards/buy-joker-pack")}
                disabled={state.chips < state.shop_joker_pack.cost || state.jokers.length >= 5}
              >
                购买小丑包
              </button>
            </article>
          ) : (
            <p className="empty-hand-note">小丑包已售罄。</p>
          )}

          <div className="owned-jokers">
            <h3>已拥有 Joker</h3>
            {state.jokers.map((joker, index) => (
              <div key={`${joker.name}-${index}`} className="owned-joker">
                <strong>{joker.name}</strong>
                <em>{joker.archetype || jokerArchetype(joker)}</em>
                <span>{joker.desc}</span>
              </div>
            ))}
          </div>

          <button className="btn btn-play-hand" onClick={() => onAction("/cards/next")}>
            下一关
          </button>
        </aside>
      </section>
    </main>
  );
}

function JokerPackOpening({ state, onAction, onExit, onRules }) {
  const choices = state.opened_joker_choices || [];
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
  }, [choices.map((joker) => joker.name).join("|")]);

  const openPack = () => {
    setRevealStep("opening");
    revealTimer.current = window.setTimeout(() => setRevealStep("revealed"), 1450);
  };

  return (
    <main className="board-screen pack-screen">
      <TopBar onExit={onExit} onRules={onRules} />
      <section className="pack-stage joker-pack-stage">
        <h2>Joker 卡包</h2>
        <div className={`pack-opening joker-pack-opening ${revealStep}`}>
          <div className="pack-shell joker-pack-shell" aria-hidden={revealStep === "revealed"}>
            <div className="pack-core">
              <span>QUANTUM</span>
              <strong>JOKER</strong>
              <small>BUILD SERIES</small>
            </div>
            <div className="pack-rip pack-rip-left" />
            <div className="pack-rip pack-rip-right" />
            <div className="pack-glow" />
          </div>
          <div className="joker-pack-reveal" aria-hidden={revealStep !== "revealed"}>
            {choices.map((joker) => (
              <button
                key={`${joker.name}-${joker.index}`}
                className="shop-card joker-choice-card pack-reveal"
                onClick={() => onAction(`/cards/collect-joker-pack/${joker.index}`)}
                disabled={revealStep !== "revealed"}
              >
                <span className="shop-type">JOKER</span>
                <span className="archetype-badge">{joker.archetype || jokerArchetype(joker)}</span>
                <h4>{joker.name}</h4>
                <p>{joker.desc}</p>
                <small>{joker.synergy || BUILD_ARCHETYPES[jokerArchetype(joker)]?.hint}</small>
                <strong>选择这张</strong>
              </button>
            ))}
          </div>
        </div>
        {revealStep === "sealed" ? (
          <button className="btn btn-observe" onClick={openPack} disabled={!choices.length}>
            打开小丑包
          </button>
        ) : revealStep === "opening" ? (
          <button className="btn btn-clear" disabled>
            打开中...
          </button>
        ) : (
          <p className="empty-hand-note">选择一张 Joker 加入当前流派。</p>
        )}
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
        <h2>量子卡包</h2>
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
              <small>耐久：{card.durability}</small>
              {card.lesson && <small>{card.lesson}</small>}
            </article>
          )}
        </div>
        {revealStep === "sealed" ? (
          <button className="btn btn-observe" onClick={openPack} disabled={!card}>
            打开卡包
          </button>
        ) : revealStep === "opening" ? (
          <button className="btn btn-clear" disabled>
            打开中...
          </button>
        ) : (
          <button className="btn btn-play-hand" onClick={() => onAction("/cards/collect-pack")}>
            收下卡牌
          </button>
        )}
      </section>
    </main>
  );
}

function ProbabilityChart({ probabilities, targets }) {
  return (
    <div className="prob-chart">
      <h3>目标匹配</h3>
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
  const chanceNames = {
    SAFE: "安全",
    "-1 HAND": "-1 次出手",
    "RESET MULT": "重置倍率",
    "-200 CHIPS": "-200 筹码",
  };
  return (
    <div className="score-breakdown">
      <h3>分数拆解</h3>
      <div className="score-line">
        <span>目标匹配</span>
        <strong>{state.preview.match_chips}</strong>
      </div>
      <div className="score-line">
        <span>门倍率</span>
        <strong>x{state.preview.gate_mult}</strong>
      </div>
      <div className="score-line">
        <span>已保存倍率</span>
        <strong>x{state.preview.stored_mult}</strong>
      </div>
      {state.preview.event_note && (
        <div className="score-line">
          <span>事件</span>
          <strong>{localizeEventNote(state.preview.event_note)}</strong>
        </div>
      )}
      <div className="score-line">
        <span>观察风险</span>
        <strong>已用 {state.observe_count} 次</strong>
      </div>
      <div className="chance-grid">
        {Object.entries(chances).map(([name, chance]) => (
          <span key={name}>{chanceNames[name] || name}: {chance}%</span>
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
      <span className="formula-label">上一局公式</span>
      <h3>量子概率得分</h3>
      <div className="formula-line">
        <code>P(s) = |amplitude(s)|^2</code>
        <small>由线路态向量得到测量概率</small>
      </div>
      <div className="formula-line">
        <code>chips = 200 x sum(min(P(s), target(s)))</code>
        <strong>{chips} 筹码</strong>
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
        <h3>上一手得分</h3>
        <p className="empty-hand-note">先放置线路，再测量保真度。</p>
      </div>
    );
  }

  return (
    <div className="score-breakdown">
      <h3>上一手得分</h3>
      <div className="score-line">
        <span>基础</span>
        <strong>{breakdown.base_chips} x {breakdown.base_mult}</strong>
      </div>
      <div className="score-line">
        <span>Jokers</span>
        <strong>+{breakdown.joker_chips_delta} 筹码 / +{breakdown.joker_mult_delta} 倍率</strong>
      </div>
      <div className="score-line">
        <span>保真度</span>
        <strong>{Math.round((breakdown.fidelity || 0) * 100)}%</strong>
      </div>
      {breakdown.event_note && (
        <div className="score-line">
          <span>事件</span>
          <strong>{localizeEventNote(breakdown.event_note)}</strong>
        </div>
      )}
      <div className="score-line total">
        <span>合计</span>
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
      <span className="formula-label">上一局公式</span>
      <h3>{breakdown.hand}</h3>
      <div className="formula-line">
        <code>F = |&lt;target | current&gt;|^2</code>
        <strong>{Math.round(fidelity * 100)}% 保真度</strong>
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

function LevelEventPanel({ event, note }) {
  if (!event?.name) return null;
  const displayEvent = localizeEvent(event);
  const result = localizeEventNote(note || event.last_result);

  return (
    <div className={`level-event event-${String(event.id || "unknown").toLowerCase()}`}>
      <span className="formula-label">关卡事件</span>
      <div className="event-head">
        <h3>{displayEvent.name}</h3>
        {event.used && <strong>已触发</strong>}
      </div>
      <p>{displayEvent.desc}</p>
      {result && <small>{result}</small>}
    </div>
  );
}

function BonusObjectivePanel({ objective, rewardUnit = "奖励" }) {
  if (!objective?.name) return null;
  const displayObjective = localizeBonusObjective(objective);
  const stateText = objective.claimed ? "已领取" : objective.complete ? "已完成" : "进行中";

  return (
    <div className={`bonus-objective ${objective.complete ? "complete" : ""}`}>
      <span className="formula-label">支线目标</span>
      <div className="event-head">
        <h3>{displayObjective.name}</h3>
        <strong>{stateText}</strong>
      </div>
      <p>{displayObjective.desc}</p>
      <small>奖励：+{objective.reward || 0} {rewardUnit}</small>
    </div>
  );
}

function RecommendationPanel({ recommendation }) {
  if (!recommendation?.text) return null;

  return (
    <div className="recommendation-card">
      <span className="formula-label">推荐出牌</span>
      <p>{recommendation.text}</p>
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
      <span className="formula-label">Joker 流派</span>
      <div className="build-head">
        <h3>{primary.label}</h3>
        <strong>{ownedCount ? `${ownedCount} 个遗物` : "暂无遗物"}</strong>
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
        <span>下一步优先</span>
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
    .join(" -> ") || "还没有打出量子门";

  return (
    <div className={`quantum-recap ${compact ? "compact" : ""}`}>
      <span className="formula-label">量子回顾</span>
      <h3>{recap.title || "上一手"}</h3>
      <div className="recap-line">
        <span>门序列</span>
        <code>{gateText}</code>
      </div>
      {recap.type === "probability" ? (
        <>
          <div className="recap-line">
            <span>测量概率</span>
            <code>{formatProbabilityMap(recap.probabilities)}</code>
          </div>
          <div className="recap-line">
            <span>目标</span>
            <code>{formatProbabilityMap(recap.targets)}</code>
          </div>
          <div className="recap-line">
            <span>结果</span>
            <strong>{recap.chips} 筹码 x {recap.mult} = {recap.score}</strong>
          </div>
        </>
      ) : (
        <>
          <div className="recap-line">
            <span>态比较</span>
            <code>F = |&lt;target|current&gt;|^2</code>
          </div>
          <div className="recap-line">
            <span>保真度</span>
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
  if (!entries.length) return "无";
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
        <h3>态演化</h3>
        <span>{gates.length ? `${gates.length} 个门` : "待放置"}</span>
      </div>
      <div className="evolution-track" aria-label="量子态演化时间线">
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
  const steps = [{ label: `|${"0".repeat(Math.max(1, qubits))}>`, note: "初始基态", kind: "state" }];
  const seen = [];
  gates.forEach((item) => {
    const gate = item.gate || "?";
    const qubitText = Number.isInteger(item.qubit) ? `(q${item.qubit})` : "";
    seen.push(gate);
    steps.push({ label: `${gate}${qubitText}`, note: gateEvolutionNote(gate, item), kind: "gate" });
    steps.push({ label: inferStateLabel(seen), note: inferStateNote(seen), kind: "state" });
  });
  if (!gates.length) {
    steps.push({ label: "放置一个门", note: "出牌后这里会显示态演化", kind: "hint" });
  }
  return steps;
}

function gateEvolutionNote(gate, item = {}) {
  if (gate === "H") return "制造叠加态";
  if (gate === "X") return "翻转基态取值";
  if (gate === "Z") return "改变相位符号";
  if (gate === "CNOT" || gate === "CX") return targetNote(item, "条件翻转");
  if (gate === "CZ") return targetNote(item, "条件相位");
  if (gate === "SWAP") return targetNote(item, "交换状态");
  if (["RX", "RY", "RZ"].includes(gate)) return "连续旋转";
  if (gate === "CCX") return "双控制翻转";
  return "更新量子态";
}

function targetNote(item, fallback) {
  if (!Array.isArray(item.targets) || item.targets.length < 2) return fallback;
  return `${fallback}: q${item.targets[0]} -> q${item.targets[1]}`;
}

function inferStateLabel(gates) {
  if (gates.includes("CCX")) return "Toffoli 控制态";
  if (gates.includes("SWAP")) return "重排后的态";
  if (gates.some((gate) => ["RX", "RY", "RZ"].includes(gate))) return "旋转后的态";
  if (gates.includes("CNOT") || gates.includes("CX") || gates.includes("CZ")) {
    return gates.includes("H") ? "纠缠态" : "相关态";
  }
  if (gates.includes("H")) return "叠加态";
  if (gates.includes("Z")) return "相位改变后的态";
  if (gates.includes("X")) return "翻转后的基态";
  return "当前态";
}

function inferStateNote(gates) {
  if (gates.includes("H") && (gates.includes("CNOT") || gates.includes("CX") || gates.includes("CZ"))) {
    return "叠加态加受控门可能产生纠缠";
  }
  if (gates.includes("H")) return "测量结果会分支到多个可能状态";
  if (gates.includes("Z")) return "概率可能不变，但相位已经改变";
  if (gates.some((gate) => ["RX", "RY", "RZ"].includes(gate))) return "角度会影响振幅和相位";
  return "最新量子门已经更新状态";
}

function ConceptCodexModal({ unlockedIds, onClose }) {
  const unlocked = new Set(unlockedIds);
  const groups = ["Gates", "States", "Formulas", "Systems"];
  const groupNames = { Gates: "量子门", States: "量子态", Formulas: "公式", Systems: "系统机制" };

  return (
    <div className="codex-overlay" role="dialog" aria-modal="true" aria-labelledby="concept-codex-title">
      <section className="codex-modal">
        <div className="codex-header">
          <div>
            <span className="formula-label">自动收集</span>
            <h2 id="concept-codex-title">量子概念图鉴</h2>
            <p>遇到量子门、生成量子态、使用公式、通关或失败时，都会自动解锁相关概念。</p>
          </div>
          <button className="btn-back" onClick={onClose}>关闭</button>
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
              <h3>{groupNames[group] || group}</h3>
              <div className="codex-grid">
                {CONCEPT_LIBRARY.filter((concept) => concept.group === group).map((concept) => {
                  const isUnlocked = unlocked.has(concept.id);
                  return (
                    <article key={concept.id} className={`codex-card ${isUnlocked ? "unlocked" : "locked"}`}>
                      <span>{isUnlocked ? "已解锁" : "未解锁"}</span>
                      <h4>{isUnlocked ? concept.title : "???"}</h4>
                      <p>{isUnlocked ? concept.desc : "继续游玩即可发现这个概念。"}</p>
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
      <h3>{lesson.title || "量子提示"}</h3>
      <p>{lesson.body}</p>
      {lesson.gates?.length ? <small>已打出的门：{lesson.gates.join(", ")}</small> : null}
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
        <h3>牌型</h3>
        <div className="catalog-grid">
          {hands.map((hand) => (
            <span key={hand.name}>{hand.name}: {hand.chips} x {hand.mult}</span>
          ))}
        </div>
      </div>
      <div>
        <h3>卡包类型</h3>
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
  const chanceNames = {
    SAFE: "安全",
    "-1 HAND": "-1 次出手",
    "RESET MULT": "重置倍率",
    "-200 CHIPS": "-200 筹码",
  };
  return (
    <div className="roulette-chances">
      {Object.entries(chances).map(([name, chance]) => (
        <span key={name}>{chanceNames[name] || name}: {chance}%</span>
      ))}
    </div>
  );
}

function ProgressMeter({ current, target }) {
  const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0;
  return (
    <div className="progress-meter" aria-label={`进度 ${pct}%`}>
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
            <h2>Quantum Hacker 规则</h2>
            <p>搭建双量子比特线路，匹配目标概率分布，并判断何时冒险保存倍率。</p>
          </div>
          <button className="btn btn-play-hand" onClick={onBack}>返回游戏</button>
        </div>

        <div className="rules-grid">
          <article className="rule-card">
            <h3>目标</h3>
            <p>每一关都会给出目标概率分布。你的线路会生成 00、01、10、11 的概率，重合越高，基础筹码越多。</p>
          </article>
          <article className="rule-card">
            <h3>量子门</h3>
            <p>H 制造叠加并提高倍率；X 翻转量子比特；Z 可配合相位 Joker；CNOT 会把两个量子比特关联起来。</p>
          </article>
          <article className="rule-card">
            <h3>结算本手</h3>
            <p>结算当前线路，消耗一次出手机会，清空棋盘，并把已保存倍率重置为 x1。</p>
          </article>
          <article className="rule-card">
            <h3>Observe</h3>
            <p>观察会保存当前门倍率，不消耗出手机会，但会清空线路并旋转轮盘。观察次数越多、倍率越高，风险越大。</p>
          </article>
          <article className="rule-card">
            <h3>轮盘</h3>
            <p>SAFE 没有惩罚。其他结果可能减少出手机会、重置倍率或扣分。界面显示的概率就是本次轮盘使用的概率。</p>
          </article>
          <article className="rule-card">
            <h3>商店</h3>
            <p>通关后可以购买最多两个 Joker。启用的 Joker 会改变得分或 Boss 约束，也可以在商店里开关。</p>
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
            <h2>Quantum Balatro Original 规则</h2>
            <p>把门卡放进量子比特插槽，组成量子牌型，并通过牌型和态保真度共同得分。</p>
          </div>
          <button className="btn btn-play-hand" onClick={onBack}>返回游戏</button>
        </div>

        <div className="rules-grid">
          <article className="rule-card">
            <h3>目标</h3>
            <p>在出手次数用完前达到目标分。通关后会根据关卡大小和剩余出手次数发放筹码。</p>
          </article>
          <article className="rule-card">
            <h3>出牌</h3>
            <p>把卡牌拖进线路。横向插槽决定出牌顺序，所在行决定作用的量子比特。CNOT 等受控门可以选择目标。</p>
          </article>
          <article className="rule-card">
            <h3>牌型</h3>
            <p>不同门组合会形成 Bell Pair、Flush、Full House、W State、GHZ State 等牌型。更强牌型有更高基础筹码和倍率。</p>
          </article>
          <article className="rule-card">
            <h3>保真度</h3>
            <p>系统会把你的线路态和目标量子态比较。保真度越高，基础分保留得越多。</p>
          </article>
          <article className="rule-card">
            <h3>弃牌</h3>
            <p>选择手牌并弃掉，可以抽取替换牌。每关弃牌次数有限，适合用来寻找缺少的门组合。</p>
          </article>
          <article className="rule-card">
            <h3>商店</h3>
            <p>花费筹码购买 Joker 或卡包。Joker 改变结算，卡包会把 RX 等新量子门加入牌库。</p>
          </article>
        </div>
      </section>
    </main>
  );
}

function TopBar({ onExit, onRules, onTutorial }) {
  return (
    <div className="top-controls">
      <button className="btn-back" onClick={onExit}>返回大厅</button>
      {onRules && <button className="btn-back" onClick={onRules}>规则</button>}
      {onTutorial && <button className="btn-back" onClick={onTutorial}>新手教程</button>}
    </div>
  );
}
