import { useState } from "react";
import { HashLink as Link } from "../router.jsx";
import { assessmentDemo as bank } from "../data/assessmentDemo.js";
import { scoreForm, comparison, downloadJson } from "../utils/assessment.js";

export default function AssessmentPage() {
  const [run, setRun] = useState(null);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState("");
  const [activity, setActivity] = useState("external_game");
  const [gameVersion, setGameVersion] = useState("");
  const [minutes, setMinutes] = useState("20");
  const stage = run?.stage || "intro";
  const form = bank.forms[stage];
  function submit(event) {
    event.preventDefault(); setError("");
    try {
      const scored = { ...scoreForm(form, answers), started_at: run.phase_started_at, submitted_at: new Date().toISOString() };
      setRun({ ...run, [stage]: scored, stage: stage === "pre" ? "activity" : "report" });
      setAnswers({});
    } catch (e) { setError(e.message); }
  }
  const report = stage === "report" ? comparison(run.pre, run.post) : null;
  return <main className="learning-workspace">
    <header className="workspace-heading"><span className="workspace-kicker">LEARNING STUDY / 学习效果评估</span><h1>看见学习前后的变化</h1><p>前测 → 游戏或阅读 → 后测 → 对比报告与学习建议</p></header>
    <div className="workspace-notice">当前为流程演示：正式题目待团队提供。结果不作为能力认证，不用于证明游戏有效，也不收费。记录仅保留在当前页面，离开前请导出。</div>
    <ol className="study-steps">{["intro", "pre", "activity", "post", "report"].map((s, i) => <li key={s} aria-current={stage === s ? "step" : undefined}>{i + 1}. {["准备", "前测", "体验", "后测", "报告"][i]}</li>)}</ol>
    {stage === "intro" && <section className="workspace-panel"><h2>先试走一遍完整流程</h2><p>演示卷各有2题。正式研究需要经审校的前后测题、统一活动时间，以及游戏版本和分组记录。前测后暂不显示答案，避免提示影响后测。</p><button className="workspace-primary" onClick={() => setRun({ id: crypto.randomUUID(), bank_id: bank.id, bank_version: bank.version, demo: true, stage: "pre", phase_started_at: new Date().toISOString() })}>开始演示前测</button><button className="workspace-secondary" onClick={() => downloadJson({ ...bank, status: "draft", note: "交给出题成员的结构示例；正式答案应由后端保管，不能公开发送至考生浏览器。" }, "assessment-bank-template.json")}>下载题库结构示例</button></section>}
    {form && <form onSubmit={submit} className="workspace-panel"><h2>{stage === "pre" ? "体验前" : "体验后"} · 概念检查</h2>{form.map((q, i) => <fieldset key={q.id} className="study-question"><legend>{i + 1}. {q.prompt}</legend>{q.options.map((o, index) => <label key={o}><input type="radio" name={q.id} checked={answers[q.id] === index} onChange={() => setAnswers({ ...answers, [q.id]: index })} />{o}</label>)}</fieldset>)}{error && <p role="alert">{error}</p>}<button className="workspace-primary" type="submit">提交{stage === "pre" ? "前测" : "后测"}</button></form>}
    {stage === "activity" && <section className="workspace-panel"><h2>记录体验活动</h2><p>新 C 语言游戏由同学独立开发，目前尚未接入。本演示允许手动记录；正式试验应由活动组织者统一分组并核验时长。</p><label>活动类型<select value={activity} onChange={e => setActivity(e.target.value)}><option value="external_game">外部新游戏（手动记录）</option><option value="reading">阅读活动（手动记录）</option></select></label><label>游戏或阅读材料版本<input value={gameVersion} onChange={e => setGameVersion(e.target.value)} placeholder="例如 demo-2026-09；未运行请填写流程演示" maxLength={100} /></label><label>实际活动时长（分钟，自报）<input type="number" min="0" max="240" value={minutes} onChange={e => setMinutes(e.target.value)} /></label><p><Link to="/resources" target="_blank">另开资料库</Link> · <Link to="/game" target="_blank">另开已有游戏（不是新 C 游戏）</Link></p><button className="workspace-primary" disabled={!gameVersion.trim() || minutes === "" || !Number.isFinite(Number(minutes)) || Number(minutes) < 0 || Number(minutes) > 240} onClick={() => setRun({ ...run, activity: { type: activity, version: gameVersion.trim(), duration_minutes: Number(minutes), source: "self_report", verified: false }, stage: "post", phase_started_at: new Date().toISOString() })}>已完成活动，进入后测</button></section>}
    {report && <section className="workspace-panel"><h2>本次演示报告</h2><div className="study-scores"><div><span>前测正确率</span><strong>{report.pre_percent}%</strong></div><div><span>后测正确率</span><strong>{report.post_percent}%</strong></div><div><span>分数变化</span><strong>{report.change_percentage_points > 0 ? "+" : ""}{report.change_percentage_points} <small>百分点</small></strong></div></div><p>{report.interpretation}</p><p>两题样例不足以估算稳定的能力分数。请结合正式题库和后续复测评估。</p><h3>可继续巩固的概念</h3>{run.post.responses.filter(r => !r.correct).map(r => <p key={r.question_id}><Link to={`/knowledge/${r.concept_id}`}>{r.concept_id === "measurement" ? "测量与概率" : "量子比特基础"} → 阅读讲解</Link></p>)}{run.post.correct === run.post.total && <p>这两道演示题已答对，可继续进行线路练习；不等同于已掌握全部知识。</p>}<button className="workspace-primary" onClick={() => downloadJson({ ...run, report, exported_at: new Date().toISOString() }, `study-demo-${run.id}.json`)}>导出演示记录</button><Link className="workspace-secondary" to="/path">查看学习路径</Link><button className="workspace-secondary" onClick={() => { setRun(null); setAnswers({}); }}>重新演示</button></section>}
  </main>;
}
