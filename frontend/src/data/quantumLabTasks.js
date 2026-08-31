const EPSILON = 1e-6;

export const quantumLabTasks = [
  {
    id: "hadamard-superposition",
    conceptId: "superposition",
    difficulty: "01",
    minutes: 4,
    numQubits: 1,
    target: "plus",
    starterOps: [],
    requiredGates: ["H"],
    minFidelity: 0.98,
    copy: {
      zh: {
        title: "用 H 门制备叠加态",
        goal: "从 |0⟩ 出发，制备测量概率各为 50% 的 |+⟩ 状态。",
        steps: ["选择 H 门", "点击 q0 放置量子门", "运行线路并观察 |0⟩、|1⟩ 的概率"],
        hint: "H 门会把计算基 |0⟩ 变成 (|0⟩+|1⟩)/√2。",
        reflect: "为什么 50%/50% 的测量概率还不能完整描述相位？",
      },
      en: {
        title: "Prepare superposition with H",
        goal: "Starting from |0⟩, prepare |+⟩ with 50% probability for each outcome.",
        steps: ["Choose the H gate", "Place it on q0", "Run and inspect the |0⟩ and |1⟩ probabilities"],
        hint: "H maps the computational basis state |0⟩ to (|0⟩+|1⟩)/√2.",
        reflect: "Why can a 50/50 probability distribution not fully describe phase?",
      },
    },
  },
  {
    id: "bit-flip",
    conceptId: "single-qubit-gates",
    difficulty: "01",
    minutes: 4,
    numQubits: 1,
    target: "one",
    starterOps: [],
    requiredGates: ["X"],
    minFidelity: 0.98,
    copy: {
      zh: {
        title: "完成一次量子比特翻转",
        goal: "只使用一个门，把初始态 |0⟩ 确定地变成 |1⟩。",
        steps: ["选择 X 门", "把 X 放到 q0", "运行并确认 |1⟩ 概率接近 100%"],
        hint: "X 门在线路中的作用类似经典 NOT，但它也能作用在叠加态上。",
        reflect: "如果先放 H 再放 X，最终测量概率为什么看起来没有改变？",
      },
      en: {
        title: "Flip one qubit",
        goal: "Use one gate to map the initial |0⟩ state deterministically to |1⟩.",
        steps: ["Choose X", "Place X on q0", "Run and confirm that |1⟩ is near 100%"],
        hint: "X acts like classical NOT on basis states, but it also acts on superpositions.",
        reflect: "Why do H followed by X appear to leave the measurement probabilities unchanged?",
      },
    },
  },
  {
    id: "phase-interference",
    conceptId: "phase-and-interference",
    difficulty: "02",
    minutes: 7,
    numQubits: 1,
    target: "one",
    starterOps: [
      { gate: "H", targets: [0] },
      { gate: "Z", targets: [0] },
    ],
    requiredGates: ["H", "Z"],
    minGateCount: 3,
    minFidelity: 0.98,
    copy: {
      zh: {
        title: "让不可见相位变成可见结果",
        goal: "在线路 H—Z 之后补上一个门，让相位差通过干涉变成确定的 |1⟩。",
        steps: ["先运行脚手架并记录概率", "思考哪个门能让两条振幅路径重新干涉", "补上该门并再次运行"],
        hint: "用同一个 H 门把相位基信息转换回计算基信息。",
        reflect: "Z 门之后立即测量为何仍是 50%/50%，而第二个 H 会改变结果？",
      },
      en: {
        title: "Turn hidden phase into a visible result",
        goal: "Complete H—Z so interference converts phase into the deterministic |1⟩ outcome.",
        steps: ["Run the scaffold and note its probabilities", "Find the gate that recombines the amplitude paths", "Add it and run again"],
        hint: "Use H again to convert phase-basis information back into the computational basis.",
        reflect: "Why is Z followed by measurement still 50/50, while a second H changes the outcome?",
      },
    },
  },
  {
    id: "bell-pair",
    conceptId: "bell-state",
    difficulty: "02",
    minutes: 8,
    numQubits: 2,
    target: "bell",
    starterOps: [{ gate: "H", targets: [0] }],
    requiredGates: ["H", "CX"],
    minFidelity: 0.98,
    copy: {
      zh: {
        title: "从叠加到 Bell 纠缠",
        goal: "在已有 H 门之后加入受控操作，制备 (|00⟩+|11⟩)/√2。",
        steps: ["观察 q0 上的 H 门", "选择 CX，先点 q0 作为控制位，再点 q1", "运行并检查 00、11 各约 50%"],
        hint: "控制位必须是已经处于叠加的 q0，目标位是 q1。",
        reflect: "为什么结果不是四种基态各 25%，而只保留 00 和 11？",
      },
      en: {
        title: "From superposition to a Bell pair",
        goal: "Add a controlled operation after H to prepare (|00⟩+|11⟩)/√2.",
        steps: ["Inspect H on q0", "Choose CX, click q0 as control, then q1", "Run and look for about 50% each on 00 and 11"],
        hint: "The control is the superposed q0 and the target is q1.",
        reflect: "Why are only 00 and 11 present instead of four outcomes at 25% each?",
      },
    },
  },
  {
    id: "ghz-chain",
    conceptId: "multi-qubit-and-cnot",
    difficulty: "03",
    minutes: 10,
    numQubits: 3,
    target: "ghz",
    starterOps: [
      { gate: "H", targets: [0] },
      { gate: "CX", targets: [0, 1] },
    ],
    requiredGates: ["H", "CX"],
    minGateCount: 3,
    minFidelity: 0.98,
    copy: {
      zh: {
        title: "把纠缠扩展为三比特 GHZ",
        goal: "在线路脚手架上再加入一次 CX，得到 (|000⟩+|111⟩)/√2。",
        steps: ["理解已有 H 与 CX 如何关联 q0、q1", "选择 CX，依次点击 q1、q2", "运行并确认只有 000、111 具有概率"],
        hint: "沿纠缠链把 q1 作为下一次 CX 的控制位。",
        reflect: "若第二个 CX 改为 q0→q2，理想无噪声结果是否相同？为什么？",
      },
      en: {
        title: "Extend entanglement into a three-qubit GHZ state",
        goal: "Add one CX to the scaffold and prepare (|000⟩+|111⟩)/√2.",
        steps: ["Understand how H and CX connect q0 and q1", "Choose CX, then click q1 and q2", "Run and confirm only 000 and 111 have probability"],
        hint: "Continue the entanglement chain by using q1 as the next control.",
        reflect: "Would q0→q2 produce the same ideal result? Why?",
      },
    },
  },
];

export const quantumLabTaskById = Object.fromEntries(
  quantumLabTasks.map((task) => [task.id, task]),
);

export function getLabTaskCopy(task, language = "zh") {
  return task?.copy?.[language] || task?.copy?.zh || null;
}

function includesRequiredGates(operations, requiredGates = []) {
  const gates = operations.map((operation) => String(operation.gate).toUpperCase());
  return requiredGates.every((gate) => gates.includes(gate));
}

export function evaluateLabTask(task, { numQubits, operations = [], fidelity = null } = {}) {
  if (!task) return null;
  const fidelityValue = Number(fidelity?.fidelity ?? fidelity ?? 0);
  const checks = [
    { id: "qubits", passed: numQubits === task.numQubits },
    { id: "gates", passed: includesRequiredGates(operations, task.requiredGates) },
    { id: "gateCount", passed: operations.length >= (task.minGateCount || 1) },
    { id: "fidelity", passed: fidelityValue + EPSILON >= task.minFidelity },
  ];
  const completedChecks = checks.filter((check) => check.passed).length;
  const passed = checks.every((check) => check.passed);
  return {
    taskId: task.id,
    conceptId: task.conceptId,
    passed,
    fidelity: fidelityValue,
    score: passed
      ? Math.max(0.85, fidelityValue)
      : Math.min(0.69, (completedChecks / checks.length) * 0.45 + fidelityValue * 0.35),
    checks,
  };
}
