export function calculateQuizResult(questions, answers) {
  const correctCount = questions.filter(
    (question) => answers[question.id] === question.answer,
  ).length;
  return {
    correctCount,
    questionCount: questions.length,
    score: questions.length ? correctCount / questions.length : 0,
  };
}

export function buildGameLearningEvent(gameState) {
  if (!gameState?.active || !gameState.run_id) return null;
  const isCircuitResult = gameState.kind === "circuit"
    && ["SHOP", "WIN", "GAME_OVER"].includes(gameState.phase);
  const isCardResult = gameState.kind === "cards"
    && ["REWARD", "GAME_OVER"].includes(gameState.phase);
  if (!isCircuitResult && !isCardResult) return null;

  const levelKey = gameState.kind === "circuit"
    ? `level-${gameState.level_index}`
    : `ante-${gameState.ante}-blind-${gameState.blind_index}`;
  const milestoneKey = `${gameState.run_id}:${levelKey}:${gameState.phase}`;
  const success = gameState.kind === "circuit"
    ? ["SHOP", "WIN"].includes(gameState.phase)
    : gameState.phase === "REWARD";
  const performance = gameState.kind === "circuit"
    ? Number(gameState.last_recap?.match_quality || 0)
    : Number(gameState.last_fidelity ?? gameState.last_score_breakdown?.fidelity ?? 0);
  const gates = gameState.kind === "circuit"
    ? (gameState.last_recap?.gates || []).map((gate) => gate.gate)
    : (gameState.last_recap?.gates || []);

  return {
    milestoneKey,
    payload: {
      concept_id: gameState.kind === "circuit" ? "quantum-hacker-guide" : "quantum-mage-map",
      event_type: "game_result",
      source: gameState.game_id,
      score: Math.max(0, Math.min(1, success ? performance : performance * 0.5)),
      idempotency_key: `game:${milestoneKey}`,
      metadata: {
        run_id: gameState.run_id,
        game_id: gameState.game_id,
        phase: gameState.phase,
        success,
        level: levelKey,
        performance,
        gates,
        score: gameState.score ?? gameState.current_score ?? 0,
        target_score: gameState.level?.target ?? gameState.target_score ?? 0,
      },
    },
  };
}
