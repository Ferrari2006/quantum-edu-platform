import assert from "node:assert/strict";
import test from "node:test";

import { knowledgeQuizzes } from "../src/data/knowledgeQuizzes.js";
import {
  evaluateLabTask,
  quantumLabTaskById,
  quantumLabTasks,
} from "../src/data/quantumLabTasks.js";
import {
  buildGameLearningEvent,
  calculateQuizResult,
} from "../src/utils/learningEvidence.js";


test("quiz bank contains valid three-question assessments", () => {
  assert.equal(Object.keys(knowledgeQuizzes).length, 5);
  Object.values(knowledgeQuizzes).forEach((questions) => {
    assert.equal(questions.length, 3);
    questions.forEach((question) => {
      assert.ok(question.answer >= 0 && question.answer < question.options.length);
      assert.ok(question.explanation.length > 0);
    });
  });
});

test("quiz result uses actual correct answers", () => {
  const questions = knowledgeQuizzes.superposition;
  const answers = {
    [questions[0].id]: questions[0].answer,
    [questions[1].id]: questions[1].answer,
    [questions[2].id]: (questions[2].answer + 1) % questions[2].options.length,
  };

  const result = calculateQuizResult(questions, answers);

  assert.equal(result.correctCount, 2);
  assert.equal(result.questionCount, 3);
  assert.equal(result.score, 2 / 3);
});

test("Quantum Hacker milestone maps match quality to learning evidence", () => {
  const event = buildGameLearningEvent({
    active: true,
    run_id: "run-circuit",
    game_id: "game1",
    kind: "circuit",
    phase: "SHOP",
    level_index: 2,
    score: 900,
    level: { target: 800 },
    last_recap: { match_quality: 0.93, gates: [{ gate: "H" }, { gate: "CNOT" }] },
  });

  assert.equal(event.payload.concept_id, "quantum-hacker-guide");
  assert.equal(event.payload.score, 0.93);
  assert.equal(event.payload.metadata.success, true);
  assert.deepEqual(event.payload.metadata.gates, ["H", "CNOT"]);
  assert.match(event.payload.idempotency_key, /run-circuit:level-2:SHOP/);
});

test("card game reward maps fidelity and ignores non-result phases", () => {
  const playing = buildGameLearningEvent({
    active: true,
    run_id: "run-card",
    kind: "cards",
    phase: "PLAYING",
  });
  const reward = buildGameLearningEvent({
    active: true,
    run_id: "run-card",
    game_id: "game2",
    kind: "cards",
    phase: "REWARD",
    ante: 1,
    blind_index: 0,
    current_score: 500,
    target_score: 450,
    last_fidelity: 0.81,
    last_recap: { gates: ["H", "CX"] },
  });

  assert.equal(playing, null);
  assert.equal(reward.payload.concept_id, "quantum-mage-map");
  assert.equal(reward.payload.score, 0.81);
  assert.equal(reward.payload.metadata.success, true);
});

test("failed game keeps diagnostic performance but reduces mastery evidence", () => {
  const event = buildGameLearningEvent({
    active: true,
    run_id: "run-failed",
    game_id: "game1",
    kind: "circuit",
    phase: "GAME_OVER",
    level_index: 1,
    last_recap: { match_quality: 0.8, gates: [{ gate: "H" }] },
  });

  assert.equal(event.payload.metadata.performance, 0.8);
  assert.equal(event.payload.metadata.success, false);
  assert.equal(event.payload.score, 0.4);
});

test("guided lab catalog exposes reviewed bilingual missions", () => {
  assert.equal(quantumLabTasks.length, 5);
  assert.equal(new Set(quantumLabTasks.map((task) => task.id)).size, 5);
  quantumLabTasks.forEach((task) => {
    assert.ok(task.copy.zh.title.length > 0);
    assert.ok(task.copy.en.title.length > 0);
    assert.ok(task.copy.zh.steps.length >= 3);
    assert.ok(task.minFidelity >= 0.98);
  });
});

test("Bell mission passes only after its controlled gate and fidelity target", () => {
  const task = quantumLabTaskById["bell-pair"];
  const incomplete = evaluateLabTask(task, {
    numQubits: 2,
    operations: task.starterOps,
    fidelity: 0.5,
  });
  const completed = evaluateLabTask(task, {
    numQubits: 2,
    operations: [...task.starterOps, { gate: "CX", targets: [0, 1] }],
    fidelity: { fidelity: 1 },
  });

  assert.equal(incomplete.passed, false);
  assert.ok(incomplete.score < 0.7);
  assert.equal(completed.passed, true);
  assert.equal(completed.score, 1);
  assert.ok(completed.checks.every((check) => check.passed));
});
