import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth.jsx";
import {
  evaluateLabTask,
  getLabTaskCopy,
  quantumLabTaskById,
  quantumLabTasks,
} from "../data/quantumLabTasks.js";
import { useLanguage } from "../i18n.jsx";
import { HashLink, navigateTo } from "../router.jsx";

const GATES = [
  { gate: "H", arity: 1, tone: "cyan" },
  { gate: "X", arity: 1, tone: "rose" },
  { gate: "Y", arity: 1, tone: "rose" },
  { gate: "Z", arity: 1, tone: "rose" },
  { gate: "S", arity: 1, tone: "violet" },
  { gate: "T", arity: 1, tone: "violet" },
  { gate: "RX", arity: 1, rotation: true, tone: "amber" },
  { gate: "RY", arity: 1, rotation: true, tone: "amber" },
  { gate: "RZ", arity: 1, rotation: true, tone: "amber" },
  { gate: "CX", arity: 2, tone: "green" },
  { gate: "CZ", arity: 2, tone: "green" },
  { gate: "SWAP", arity: 2, tone: "green" },
];

const PRESETS = {
  plus: {
    numQubits: 1,
    target: "plus",
    ops: [{ gate: "H", targets: [0] }],
  },
  bell: {
    numQubits: 2,
    target: "bell",
    ops: [
      { gate: "H", targets: [0] },
      { gate: "CX", targets: [0, 1] },
    ],
  },
  ghz: {
    numQubits: 3,
    target: "ghz",
    ops: [
      { gate: "H", targets: [0] },
      { gate: "CX", targets: [0, 1] },
      { gate: "CX", targets: [1, 2] },
    ],
  },
};

function localQiskitCode(numQubits, operations) {
  const lines = [
    "from qiskit import QuantumCircuit",
    "from qiskit.quantum_info import Statevector",
    "",
    `qc = QuantumCircuit(${numQubits})`,
  ];
  operations.forEach((operation) => {
    const method = operation.gate === "CX" ? "cx" : operation.gate.toLowerCase();
    const args = operation.theta === undefined
      ? operation.targets
      : [operation.theta, ...operation.targets];
    lines.push(`qc.${method}(${args.join(", ")})`);
  });
  lines.push("", "state = Statevector.from_instruction(qc)", "print(state.probabilities_dict())");
  return lines.join("\n");
}

function targetPayload(target, numQubits) {
  const amplitude = 1 / Math.sqrt(2);
  if (target === "zero") return { target_basis_state: "0".repeat(numQubits) };
  if (target === "one") return { target_basis_state: "1".repeat(numQubits) };
  if (target === "plus" && numQubits === 1) {
    return { target_statevector: [amplitude, amplitude] };
  }
  if (target === "bell" && numQubits === 2) {
    return { target_statevector: [amplitude, 0, 0, amplitude] };
  }
  if (target === "ghz" && numQubits === 3) {
    return { target_statevector: [amplitude, 0, 0, 0, 0, 0, 0, amplitude] };
  }
  return null;
}

async function readJson(response) {
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function guidedTaskIdFromHash() {
  const query = window.location.hash.split("?")[1] || "";
  return new URLSearchParams(query).get("task");
}

function cloneOperations(operations) {
  return operations.map((operation) => ({
    ...operation,
    targets: [...operation.targets],
  }));
}

function OperationCell({ operation, qubit }) {
  const position = operation.targets.indexOf(qubit);
  if (position < 0) return <span className="ql-wire-line" />;
  if (operation.targets.length === 1) {
    return <span className={`ql-op ql-op-${operation.gate.toLowerCase()}`}>{operation.gate}</span>;
  }
  if (operation.gate === "SWAP") return <span className="ql-op ql-op-swap">×</span>;
  if (position === 0) return <span className="ql-control-dot" title="control" />;
  return <span className="ql-op ql-op-controlled">{operation.gate}</span>;
}

function inferLearningConcepts(operations, target) {
  const concepts = new Set();
  const gates = operations.map((operation) => operation.gate);
  if (gates.includes("H")) concepts.add("superposition");
  if (gates.some((gate) => ["RX", "RY", "RZ"].includes(gate))) concepts.add("bloch-sphere");
  if (gates.some((gate) => ["CX", "CZ", "SWAP"].includes(gate))) {
    concepts.add(target === "bell" ? "bell-state" : "multi-qubit-and-cnot");
  }
  if (!concepts.size && gates.length) concepts.add("single-qubit-gates");
  if (!concepts.size) concepts.add("read-a-circuit");
  return [...concepts].slice(0, 3);
}

export default function QuantumLab() {
  const { authHeaders, isAuthenticated } = useAuth();
  const { language, t } = useLanguage();
  const [numQubits, setNumQubits] = useState(2);
  const [operations, setOperations] = useState([]);
  const [selectedGate, setSelectedGate] = useState(GATES[0]);
  const [pendingTargets, setPendingTargets] = useState([]);
  const [theta, setTheta] = useState(Math.PI / 2);
  const [target, setTarget] = useState("bell");
  const [result, setResult] = useState(null);
  const [fidelity, setFidelity] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [learningSync, setLearningSync] = useState("idle");
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [taskEvaluation, setTaskEvaluation] = useState(null);
  const [showTaskHint, setShowTaskHint] = useState(false);

  const qiskitCode = result?.qiskit_code || localQiskitCode(numQubits, operations);
  const activeTask = activeTaskId ? quantumLabTaskById[activeTaskId] : null;
  const activeTaskCopy = getLabTaskCopy(activeTask, language);
  const targetOptions = useMemo(
    () => [
      { value: "none", label: t.lab.targets.none },
      { value: "zero", label: `|${"0".repeat(numQubits)}⟩` },
      { value: "one", label: `|${"1".repeat(numQubits)}⟩` },
      ...(numQubits === 1 ? [{ value: "plus", label: "|+⟩" }] : []),
      ...(numQubits === 2 ? [{ value: "bell", label: t.lab.targets.bell }] : []),
      ...(numQubits === 3 ? [{ value: "ghz", label: t.lab.targets.ghz }] : []),
    ],
    [numQubits, t.lab.targets],
  );

  function resetOutput() {
    setResult(null);
    setFidelity(null);
    setError("");
    setLearningSync("idle");
    setTaskEvaluation(null);
  }

  function loadGuidedTask(taskId, updateLocation = true) {
    const task = quantumLabTaskById[taskId];
    if (!task) return;
    setActiveTaskId(task.id);
    setNumQubits(task.numQubits);
    setOperations(cloneOperations(task.starterOps));
    setTarget(task.target);
    setPendingTargets([]);
    setShowTaskHint(false);
    resetOutput();
    if (updateLocation) navigateTo(`/lab?task=${task.id}`, { replace: true });
  }

  useEffect(() => {
    const requestedTask = guidedTaskIdFromHash();
    if (requestedTask && quantumLabTaskById[requestedTask]) {
      loadGuidedTask(requestedTask, false);
    }
  }, []);

  function chooseGate(item) {
    setSelectedGate(item);
    setPendingTargets([]);
  }

  function addAtQubit(qubit) {
    const targets = [...pendingTargets, qubit];
    if (pendingTargets.includes(qubit)) {
      setError(t.lab.distinctTargets);
      return;
    }
    if (targets.length < selectedGate.arity) {
      setPendingTargets(targets);
      setError("");
      return;
    }
    setOperations((current) => [
      ...current,
      {
        gate: selectedGate.gate,
        targets,
        ...(selectedGate.rotation ? { theta: Number(theta) } : {}),
      },
    ]);
    setPendingTargets([]);
    resetOutput();
  }

  function changeQubitCount(value) {
    setNumQubits(value);
    setOperations([]);
    setPendingTargets([]);
    setTarget(value === 2 ? "bell" : value === 3 ? "ghz" : "zero");
    resetOutput();
  }

  function loadPreset(name) {
    const preset = PRESETS[name];
    setActiveTaskId(null);
    setShowTaskHint(false);
    setNumQubits(preset.numQubits);
    setOperations(preset.ops);
    setTarget(preset.target);
    setPendingTargets([]);
    resetOutput();
    navigateTo("/lab", { replace: true });
  }

  async function runCircuit() {
    setBusy(true);
    setError("");
    try {
      const payload = { num_qubits: numQubits, ops: operations };
      const runPromise = fetch("/api/quantum/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(readJson);
      const targetData = targetPayload(target, numQubits);
      const fidelityPromise = targetData
        ? fetch("/api/quantum/fidelity", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...payload, ...targetData }),
          }).then(readJson)
        : Promise.resolve(null);
      const [runResult, fidelityResult] = await Promise.all([runPromise, fidelityPromise]);
      setResult(runResult);
      setFidelity(fidelityResult);
      const guidedEvaluation = activeTask
        ? evaluateLabTask(activeTask, {
            numQubits,
            operations,
            fidelity: fidelityResult,
          })
        : null;
      setTaskEvaluation(guidedEvaluation);
      if (isAuthenticated) {
        setLearningSync("syncing");
        const evidenceScore = guidedEvaluation?.score
          ?? fidelityResult?.fidelity
          ?? Math.min(0.55 + operations.length * 0.03, 0.85);
        const concepts = activeTask
          ? [activeTask.conceptId]
          : inferLearningConcepts(operations, target);
        const attemptId = activeTask
          ? globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
          : null;
        Promise.all(
          concepts.map((conceptId) => fetch("/api/learning/events", {
            method: "POST",
            headers: authHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({
              concept_id: conceptId,
              event_type: guidedEvaluation && !guidedEvaluation.passed
                ? "lab_attempt"
                : "lab_completed",
              source: activeTask ? "guided_quantum_lab" : "quantum_lab",
              score: evidenceScore,
              metadata: {
                num_qubits: numQubits,
                gate_count: operations.length,
                gates: operations.map((operation) => operation.gate),
                target,
                fidelity: fidelityResult?.fidelity ?? null,
                task_id: activeTask?.id ?? null,
                task_passed: guidedEvaluation?.passed ?? null,
                task_checks: guidedEvaluation?.checks ?? [],
              },
              idempotency_key: attemptId ? `lab:${activeTask.id}:${attemptId}` : undefined,
            }),
          }).then((response) => {
            if (!response.ok) throw new Error("Learning sync failed");
            return response.json();
          })),
        )
          .then(() => setLearningSync("synced"))
          .catch(() => setLearningSync("failed"));
      }
    } catch (runError) {
      setError(runError.message || t.lab.runFailed);
    } finally {
      setBusy(false);
    }
  }

  function askAI() {
    window.localStorage.setItem(
      "quantum-lab-ai-draft",
      JSON.stringify({
        query: activeTaskCopy
          ? `${t.lab.aiQuestion}\n\n${t.lab.guided.aiContext}: ${activeTaskCopy.goal}\n${t.lab.guided.reflect}: ${activeTaskCopy.reflect}`
          : t.lab.aiQuestion,
        code: qiskitCode,
      }),
    );
    navigateTo("/oa");
  }

  return (
    <div className="ql-page">
      <section className="ql-hero">
        <div>
          <div className="ql-eyebrow">QUANTUM CIRCUIT LAB</div>
          <h1>{t.lab.title}</h1>
          <p>{t.lab.subtitle}</p>
        </div>
        <div className="ql-hero-actions">
          <button onClick={() => loadPreset("plus")} type="button">|+⟩</button>
          <button onClick={() => loadPreset("bell")} type="button">Bell</button>
          <button onClick={() => loadPreset("ghz")} type="button">GHZ</button>
        </div>
      </section>

      <section className="ql-guided">
        <div className="ql-guided-heading">
          <div>
            <span>{t.lab.guided.eyebrow}</span>
            <h2>{t.lab.guided.title}</h2>
            <p>{t.lab.guided.subtitle}</p>
          </div>
          {activeTask ? (
            <HashLink to={`/knowledge/${activeTask.conceptId}`}>{t.lab.guided.readConcept}</HashLink>
          ) : null}
        </div>
        <div className="ql-task-tabs">
          {quantumLabTasks.map((task) => {
            const taskCopy = getLabTaskCopy(task, language);
            return (
              <button
                className={activeTaskId === task.id ? "active" : ""}
                key={task.id}
                onClick={() => loadGuidedTask(task.id)}
                type="button"
              >
                <small>{task.difficulty}</small>
                <strong>{taskCopy.title}</strong>
                <span>{task.minutes} {t.lab.guided.minutes}</span>
              </button>
            );
          })}
        </div>
        {activeTask && activeTaskCopy ? (
          <div className="ql-task-brief">
            <div className="ql-task-goal">
              <span>{t.lab.guided.goal}</span>
              <h3>{activeTaskCopy.title}</h3>
              <p>{activeTaskCopy.goal}</p>
              <div>
                <button onClick={() => loadGuidedTask(activeTask.id, false)} type="button">
                  {t.lab.guided.reset}
                </button>
                <button onClick={() => setShowTaskHint((current) => !current)} type="button">
                  {showTaskHint ? t.lab.guided.hideHint : t.lab.guided.showHint}
                </button>
              </div>
              {showTaskHint ? <aside>{activeTaskCopy.hint}</aside> : null}
            </div>
            <div className="ql-task-steps">
              <span>{t.lab.guided.steps}</span>
              <ol>
                {activeTaskCopy.steps.map((step) => <li key={step}>{step}</li>)}
              </ol>
            </div>
            <div className={`ql-task-evaluation${taskEvaluation ? (taskEvaluation.passed ? " passed" : " pending") : ""}`}>
              <span>{t.lab.guided.acceptance}</span>
              <strong>
                {taskEvaluation
                  ? (taskEvaluation.passed ? t.lab.guided.passed : t.lab.guided.tryAgain)
                  : t.lab.guided.notRun}
              </strong>
              <div>
                {(taskEvaluation?.checks || [
                  { id: "qubits", passed: false },
                  { id: "gates", passed: false },
                  { id: "gateCount", passed: false },
                  { id: "fidelity", passed: false },
                ]).map((check) => (
                  <small className={check.passed ? "passed" : ""} key={check.id}>
                    {check.passed ? "✓" : "○"} {t.lab.guided.checks[check.id]}
                  </small>
                ))}
              </div>
              {taskEvaluation?.passed ? (
                <p><b>{t.lab.guided.reflect}：</b>{activeTaskCopy.reflect}</p>
              ) : null}
            </div>
          </div>
        ) : (
          <p className="ql-task-empty">{t.lab.guided.choose}</p>
        )}
      </section>

      <section className="ql-toolbar">
        <label>
          <span>{t.lab.qubits}</span>
          <select value={numQubits} onChange={(event) => changeQubitCount(Number(event.target.value))}>
            {[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          <span>{t.lab.target}</span>
          <select value={target} onChange={(event) => {
            setTarget(event.target.value);
            setFidelity(null);
            setTaskEvaluation(null);
          }}>
            {targetOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
        {selectedGate.rotation ? (
          <label>
            <span>θ ({t.lab.radians})</span>
            <input
              max={Math.PI * 2}
              min={-Math.PI * 2}
              onChange={(event) => setTheta(Number(event.target.value))}
              step="0.1"
              type="number"
              value={theta}
            />
          </label>
        ) : null}
        <div className="ql-toolbar-actions">
          <button disabled={!operations.length} onClick={() => {
            setOperations((current) => current.slice(0, -1));
            resetOutput();
          }} type="button">{t.lab.undo}</button>
          <button disabled={!operations.length} onClick={() => {
            setOperations([]);
            setPendingTargets([]);
            resetOutput();
          }} type="button">{t.lab.clear}</button>
        </div>
      </section>

      <div className="ql-layout">
        <aside className="ql-palette">
          <h2>{t.lab.palette}</h2>
          <p>{t.lab.paletteHint}</p>
          <div className="ql-gates">
            {GATES.map((item) => (
              <button
                className={`ql-gate ql-gate-${item.tone}${selectedGate.gate === item.gate ? " selected" : ""}`}
                key={item.gate}
                onClick={() => chooseGate(item)}
                type="button"
              >
                <strong>{item.gate}</strong>
                <small>{item.arity === 1 ? t.lab.singleGate : t.lab.multiGate}</small>
              </button>
            ))}
          </div>
        </aside>

        <main className="ql-workspace">
          <div className="ql-workspace-head">
            <div>
              <h2>{t.lab.circuit}</h2>
              <p>
                {pendingTargets.length
                  ? t.lab.chooseNext.replace("{gate}", selectedGate.gate)
                  : t.lab.placeGate.replace("{gate}", selectedGate.gate)}
              </p>
            </div>
            <button className="ql-run" disabled={busy} onClick={runCircuit} type="button">
              {busy ? t.lab.running : t.lab.run}
            </button>
          </div>

          <div className="ql-circuit-scroll">
            <div className="ql-circuit-grid" style={{ "--ql-columns": Math.max(operations.length, 1) }}>
              {Array.from({ length: numQubits }, (_, qubit) => (
                <div className="ql-wire-row" key={qubit}>
                  <button className="ql-wire-label" onClick={() => addAtQubit(qubit)} type="button">
                    q{qubit}
                  </button>
                  <div className="ql-wire-cells">
                    {operations.length ? operations.map((operation, index) => (
                      <button
                        aria-label={`${t.lab.removeOperation} ${index + 1}`}
                        className="ql-wire-cell"
                        key={`${index}-${operation.gate}`}
                        onClick={() => {
                          setOperations((current) => current.filter((_, itemIndex) => itemIndex !== index));
                          resetOutput();
                        }}
                        title={t.lab.removeOperation}
                        type="button"
                      >
                        <OperationCell operation={operation} qubit={qubit} />
                      </button>
                    )) : <span className="ql-empty-wire">{t.lab.emptyCircuit}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
          {error ? <div className="ql-error">{error}</div> : null}
        </main>
      </div>

      <section className="ql-results">
        <div className="ql-result-card">
          <div className="ql-card-head">
            <div>
              <span>{t.lab.result}</span>
              <h2>{t.lab.probabilities}</h2>
            </div>
            {fidelity ? (
              <div className="ql-fidelity">
                <small>{t.lab.fidelity}</small>
                <strong>{Math.round(fidelity.fidelity * 100)}%</strong>
              </div>
            ) : null}
          </div>
          {result ? (
            <div className="ql-probabilities">
              {Object.entries(result.probabilities).map(([basis, probability]) => (
                <div className="ql-probability" key={basis}>
                  <span>|{basis}⟩</span>
                  <div><i style={{ width: `${Math.max(probability * 100, probability ? 1 : 0)}%` }} /></div>
                  <strong>{(probability * 100).toFixed(1)}%</strong>
                </div>
              ))}
            </div>
          ) : <p className="ql-empty-result">{t.lab.runHint}</p>}
          {result ? (
            <div className="ql-metrics">
              <span>{t.lab.depth}: {result.metrics.depth}</span>
              <span>{t.lab.operations}: {result.metrics.operation_count}</span>
              <span>{t.lab.engine}: Statevector</span>
              {learningSync === "syncing" ? <span>{t.lab.learningSyncing}</span> : null}
              {learningSync === "synced" ? <span className="ql-learning-synced">{t.lab.learningSynced}</span> : null}
              {learningSync === "failed" ? <span className="ql-learning-failed">{t.lab.learningSyncFailed}</span> : null}
            </div>
          ) : null}
        </div>

        <div className="ql-result-card ql-code-card">
          <div className="ql-card-head">
            <div>
              <span>QISKIT</span>
              <h2>{t.lab.code}</h2>
            </div>
            <button onClick={askAI} type="button">{t.lab.askAI}</button>
          </div>
          <pre>{qiskitCode}</pre>
        </div>
      </section>
    </div>
  );
}
