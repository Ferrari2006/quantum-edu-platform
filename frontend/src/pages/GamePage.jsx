import { useRef, useState } from "react";
import { useLanguage } from "../i18n.jsx";
import "./GamePage.css";

const GAMES = [
  {
    id: "xiaohei", url: "/games/xiaohei/", tag: "01 / CIRCUIT REPAIR",
    zh: { title: "小黑天天上夜班", description: "跟小黑上一班夜班，在量子线路维修中认识量子门。", note: "查看游戏介绍与已有的轻量试玩；完整游戏通过页面中的微信小游戏码进入。" },
    en: { title: "XiaoHei Night Shift", description: "Join XiaoHei on the night shift and explore quantum circuit repair.", note: "Explore the introduction and existing browser demo. The full game uses WeChat. The promotional page is in Chinese." },
  },
  {
    id: "quantum-orb", url: "/games/quantum-orb/", tag: "02 / QUANTUM SHOP",
    zh: { title: "女巫的量子魔法球铺", description: "接下订单，用量子门调制魔法球，观察状态与概率的变化。", note: "查看商店故事、门图鉴与状态演示。微信小程序码待接入，目前尚不能扫码进入完整游戏。" },
    en: { title: "The Witch’s Quantum Orb Shop", description: "Prepare magical orbs with quantum gates and explore states and probabilities.", note: "Explore the story, gate handbook and state visualization. The WeChat code is pending. The promotional page is in Chinese." },
  },
];

export default function GamePage() {
  const frame = useRef(null);
  const [selected, setSelected] = useState("xiaohei");
  const [fullscreenError, setFullscreenError] = useState(false);
  const { language } = useLanguage();
  const english = language === "en";
  const game = GAMES.find((item) => item.id === selected);
  const copy = english ? game.en : game.zh;

  async function enterFullscreen() {
    try {
      await frame.current.requestFullscreen();
      setFullscreenError(false);
    } catch {
      setFullscreenError(true);
    }
  }

  return (
    <section className="game-showcase" aria-label={english ? "Game laboratory" : "游戏实验室"}>
      <header className="game-showcase-heading">
        <p className="game-showcase-kicker">QUANTUM GAME LAB</p>
        <h1>{english ? "Two worlds. A little quantum discovery." : "两个小世界，一点量子发现。"}</h1>
        <p>{english ? "Choose a game to explore its promotional page and WeChat entry." : "选择一个游戏，看看它的故事、玩法和微信试玩入口。"}</p>
      </header>
      <div className="game-picker" role="group" aria-label={english ? "Choose a game" : "选择游戏"}>
        {GAMES.map((item) => {
          const text = english ? item.en : item.zh;
          return (
            <button key={item.id} type="button" className={`game-choice ${selected === item.id ? "is-selected" : ""}`}
              aria-pressed={selected === item.id} aria-controls="game-preview"
              onClick={() => { setSelected(item.id); setFullscreenError(false); }}>
              <span className="game-choice-tag">{item.tag}</span>
              <strong>{text.title}</strong>
              <span className="game-choice-description">{text.description}</span>
              <span className="game-choice-action">{selected === item.id ? (english ? "Viewing ↓" : "正在查看 ↓") : (english ? "Explore →" : "查看介绍 →")}</span>
            </button>
          );
        })}
      </div>
      <div className="game-preview-toolbar">
        <div><h2>{copy.title}</h2><p>{copy.note}</p></div>
        <div className="game-preview-actions">
          <a href={game.url} target="_blank" rel="noopener noreferrer">{english ? "Open separately ↗" : "独立打开 ↗"}</a>
          <button type="button" onClick={enterFullscreen}>{english ? "Fullscreen" : "全屏查看"}</button>
        </div>
      </div>
      {fullscreenError && <p className="game-preview-message" role="status">{english ? "Fullscreen is unavailable. Use Open separately instead." : "当前浏览器无法进入全屏，请使用“独立打开”。"}</p>}
      <iframe key={game.id} ref={frame} id="game-preview" className="game-preview-frame" src={game.url}
        title={english ? `${copy.title} — promotional page` : `${copy.title}：推广网页`} allow="fullscreen" allowFullScreen />
    </section>
  );
}
