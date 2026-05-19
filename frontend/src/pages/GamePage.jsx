import { useEffect, useMemo, useRef, useState } from "react";
import "./GamePage.css";

const API_BASE = "http://127.0.0.1:8000/api/quantum-game";
const GATES = ["H", "X", "Z", "CNOT"];
const STATES = ["00", "01", "10", "11"];
const DRAG_TYPE = "application/quantum-game";

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

export default function GamePage() {
  const [gamesList, setGamesList] = useState([]);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState("");

  const refreshState = () =>
    api("/state")
      .then(setGameState)
      .catch((err) => setError(err.message));

  useEffect(() => {
    api("/list").then(setGamesList).catch((err) => setError(err.message));
    refreshState();
  }, []);

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
  const [selectedGate, setSelectedGate] = useState("H");
  const [showRules, setShowRules] = useState(false);
  const gatesBySlot = useMemo(() => {
    const map = new Map();
    state.gates.forEach((gate) => map.set(`${gate.qubit}_${gate.slot}`, gate));
    return map;
  }, [state.gates]);

  const setGate = async (qubit, slot) => {
    const key = `${qubit}_${slot}`;
    const withoutSlot = state.gates.filter((gate) => `${gate.qubit}_${gate.slot}` !== key);
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({ gates: [...withoutSlot, { gate: selectedGate, qubit, slot }] }),
    });
    await onRefresh();
  };

  const setGateByName = async (gateName, qubit, slot) => {
    const key = `${qubit}_${slot}`;
    const withoutSlot = state.gates.filter((gate) => `${gate.qubit}_${gate.slot}` !== key);
    await api("/circuit/stage", {
      method: "POST",
      body: JSON.stringify({ gates: [...withoutSlot, { gate: gateName, qubit, slot }] }),
    });
    await onRefresh();
  };

  const startGateDrag = (event, gateName) => {
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData(DRAG_TYPE, JSON.stringify({ type: "gate", gate: gateName }));
  };

  const dropGate = async (event, qubit, slot) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData(DRAG_TYPE);
    if (!raw) return;
    const payload = JSON.parse(raw);
    if (payload.type === "gate") {
      await setGateByName(payload.gate, qubit, slot);
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
    <main className="board-screen">
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
        </div>
      </header>

      <section className="main-layout">
        <div className="circuit-board">
          <div className="section-head">
            <h3>Quantum Circuit</h3>
            <div className="gate-palette" aria-label="Gate palette">
              {GATES.map((gate) => (
                <button
                  key={gate}
                  className={selectedGate === gate ? "active" : ""}
                  onClick={() => setSelectedGate(gate)}
                  draggable
                  onDragStart={(event) => startGateDrag(event, gate)}
                >
                  {gate}
                </button>
              ))}
            </div>
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
                      title={gate ? "Click to remove" : `Place ${selectedGate}`}
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
          <div className="preview-box">
            <span>Preview</span>
            <strong>{state.preview.chips} x {state.preview.mult} = {state.preview.total}</strong>
          </div>
          <CircuitScoreBreakdown state={state} />
          {state.stored_mult > 1 && <div className="notice">Stored multiplier x{state.stored_mult}</div>}
          {state.warning && <div className="warning">{state.warning}</div>}
          <button className="btn btn-observe" onClick={() => action("/circuit/observe")}>Observe</button>
          <button className="btn btn-play-hand" onClick={() => action("/circuit/play")}>Play Hand</button>
          <button className="btn btn-clear" onClick={() => action("/circuit/clear")}>Clear Circuit</button>
        </aside>
      </section>

      {state.phase !== "PLAYING" && (
        <div className="game-overlay">
          <h2>{state.phase === "GAME_OVER" ? "Wave Collapsed" : state.phase === "WIN" ? "Run Won" : "Blind Defeated"}</h2>
          <button className="btn btn-play-hand" onClick={() => action("/start/game1")}>Restart</button>
        </div>
      )}
    </main>
  );
}

function CircuitRoulette({ state, onAction, onExit, onRules }) {
  const hitIndex = Math.max(
    0,
    state.roulette_items.findIndex((item) => item.name === state.last_roulette?.name),
  );
  const segmentCenter = hitIndex * 90 + 45;
  const rotation = 360 * 4 - segmentCenter;

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
        >
          {state.roulette_items.map((item, index) => (
            <span key={item.name} className={`roulette-label roulette-label-${index}`}>
              {item.name}
            </span>
          ))}
        </div>
        <div className={`roulette-result result-${state.last_roulette?.color || "green"}`}>
          <strong>{state.last_roulette?.name}</strong>
          <span>{state.last_roulette?.message}</span>
        </div>
        <RouletteChances chances={state.roulette_chances} />
        <button className="btn btn-play-hand" onClick={() => onAction("/circuit/roulette/continue")}>
          Continue
        </button>
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
                  <h4>{joker.name}</h4>
                  <p>{joker.desc}</p>
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

  useEffect(() => {
    setSelectedCardIds([]);
    setStagedCards({});
  }, [state.phase, state.hand_cards.length, state.current_score, state.plays_left, state.discards_left]);

  const visibleStagedCards = useMemo(() => {
    return Object.fromEntries(
      Object.entries(stagedCards).filter((entry) => state.hand_cards[entry[1]]),
    );
  }, [stagedCards, state.hand_cards]);

  const stageCard = (cardIndex, qubit, slot) => {
    setStagedCards((current) => {
      const next = Object.fromEntries(Object.entries(current).filter((entry) => entry[1] !== cardIndex));
      next[`${qubit}_${slot}`] = cardIndex;
      return next;
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
    await api("/play", {
      method: "POST",
      body: JSON.stringify({
        selected_indices: pairs.map((pair) => pair[1]),
        targets: pairs.map((pair) => [Number(pair[0].split("_")[0])]),
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
    <main className="board-screen">
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
        <div className="circuit-board">
          <h3>Card Staging Circuit</h3>
          {Array.from({ length: state.num_qubits }, (_, qubit) => (
            <div key={qubit} className="circuit-row">
              <span className="qubit-label">q[{qubit}]</span>
              <div className="slots-container">
                {[0, 1, 2, 3].map((slot) => {
                  const stagedCardIdx = visibleStagedCards[`${qubit}_${slot}`];
                  const card = state.hand_cards[stagedCardIdx];
                  return (
                    <div
                      key={slot}
                      className={`circuit-slot ${card ? "occupied draggable-card-slot" : ""}`}
                      draggable={Boolean(card)}
                      onDragStart={(event) => card && startCardDrag(event, stagedCardIdx, "stage")}
                      onDragEnd={() => setDraggingCardId(null)}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={(event) => dropCard(event, qubit, slot)}
                      onClick={() => card && unstageSlot(qubit, slot)}
                      title={card ? "Drag to another slot or click to remove" : "Drop a card here"}
                    >
                      {card?.gate || "+"}
                      {!card && (
                        <div className="slot-selector">
                          {state.hand_cards.map((handCard, index) =>
                            Object.values(visibleStagedCards).includes(index) ? null : (
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

        <aside className="control-panel">
          <div className="preview-box">
            <span>Last hand</span>
            <strong>{state.last_hand_played}</strong>
          </div>
          <CardScoreBreakdown breakdown={state.last_score_breakdown} />
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
            if (Object.values(visibleStagedCards).includes(index)) return null;
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
              </button>
            );
          })}
        </div>
      </section>

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
                  <h4>{joker.name}</h4>
                  <p>{joker.desc}</p>
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
          <h3>Pack</h3>
          {state.shop_pack ? (
            <article className="shop-card pack-shop-card">
              <span className="shop-type">PACK</span>
              <h4>{state.shop_pack.name}</h4>
              <p>Open to reveal a purple RX phase card, then collect it into your deck.</p>
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
