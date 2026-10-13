import { useRef, useState } from "react";
import { useLanguage } from "../i18n.jsx";
import "./GamePage.css";

const GAME_URL = "/games/xiaohei/";

export default function GamePage() {
  const frame = useRef(null);
  const [fullscreenError, setFullscreenError] = useState(false);
  const { language } = useLanguage();
  const english = language === "en";

  async function enterFullscreen() {
    try {
      await frame.current.requestFullscreen();
      setFullscreenError(false);
    } catch {
      setFullscreenError(true);
    }
  }

  return (
    <section className="xiaohei-game" aria-label={english ? "Game laboratory" : "游戏实验室"}>
      <div className="xiaohei-toolbar">
        <div>
          <h1>{english ? "XiaoHei Night Shift" : "小黑天天上夜班"}</h1>
          <p>{english ? "Try repairing a quantum circuit. The full game is available in WeChat." : "先试一班量子线路维修，完整游戏请通过页面中的微信小游戏码进入。"}</p>
        </div>
        <div className="xiaohei-actions">
          <a href={GAME_URL} target="_blank" rel="noopener noreferrer">
            {english ? "Open separately ↗" : "独立打开 ↗"}
          </a>
          <button type="button" onClick={enterFullscreen}>
            {english ? "Fullscreen" : "全屏体验"}
          </button>
        </div>
      </div>
      {fullscreenError && (
        <p className="xiaohei-message" role="status">
          {english ? "Fullscreen is unavailable. Use Open separately instead." : "当前浏览器无法进入全屏，请使用“独立打开”。"}
        </p>
      )}
      <iframe
        ref={frame}
        className="xiaohei-frame"
        src={GAME_URL}
        title={english ? "XiaoHei Night Shift — introduction and playable demo" : "小黑天天上夜班：游戏介绍与量子线路试玩"}
        allow="fullscreen"
        allowFullScreen
      />
    </section>
  );
}
