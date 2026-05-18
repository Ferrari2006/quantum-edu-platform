import { useEffect, useMemo, useState } from "react";
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

  return (
    <main className="board-screen">
      <TopBar onExit={onExit} />
      <header className="hud">
        <div>
          <h2>Quantum Hacker</h2>
          <p>{state.level.desc}</p>
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
          {state.phase === "NEXT_BLIND" ? (
            <button className="btn btn-play-hand" onClick={() => action("/circuit/next")}>Next Blind</button>
          ) : (
            <button className="btn btn-play-hand" onClick={() => action("/start/game1")}>Restart</button>
          )}
        </div>
      )}
    </main>
  );
}

function CardGame({ state, onRefresh, onExit }) {
  const [selectedCardIds, setSelectedCardIds] = useState([]);
  const [stagedCards, setStagedCards] = useState({});
  const [draggingCardId, setDraggingCardId] = useState(null);

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

  if (state.phase === "SHOP") {
    return <CardShop state={state} onAction={action} onExit={onExit} />;
  }

  if (state.phase === "OPENING_PACK") {
    return <PackOpening state={state} onAction={action} onExit={onExit} />;
  }

  return (
    <main className="board-screen">
      <TopBar onExit={onExit} />
      <header className="hud">
        <div>
          <h2>Quantum Balatro Original</h2>
          <p>Build a hand by placing gate cards into qubit slots.</p>
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

function CardShop({ state, onAction, onExit }) {
  return (
    <main className="board-screen">
      <TopBar onExit={onExit} />
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

function PackOpening({ state, onAction, onExit }) {
  const card = state.opened_card;
  return (
    <main className="board-screen pack-screen">
      <TopBar onExit={onExit} />
      <section className="pack-stage">
        <h2>Quantum Pack</h2>
        {card ? (
          <article className={`q-card pack-reveal rarity-${card.rarity}`}>
            <strong>{card.gate}</strong>
            <span>{card.name}</span>
            <small>Uses: {card.durability}</small>
          </article>
        ) : (
          <div className="shop-card pack-reveal">Opening...</div>
        )}
        <button className="btn btn-play-hand" onClick={() => onAction("/cards/collect-pack")}>
          Collect Card
        </button>
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

function TopBar({ onExit }) {
  return (
    <div className="top-controls">
      <button className="btn-back" onClick={onExit}>Back to Game Lobby</button>
    </div>
  );
}
