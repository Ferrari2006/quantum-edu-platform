import { knowledgeArticles, knowledgeModules } from "../data/knowledgeContent.js";
import { HashLink as Link } from "../router.jsx";
import { useLanguage } from "../i18n.jsx";

export default function Home() {
  const { language } = useLanguage();
  const en = language === "en";
  const readable = knowledgeArticles.filter(a => a.status === "sample");
  const entries = [
    ["/resources", "01 / READ", en ? "Build your intuition" : "读懂量子的第一步", en ? "Find approachable articles, organized by concept and stage." : "从量子比特到干涉，用短篇讲解建立直觉。按主题和阶段，找到适合自己的资料。", en ? "Explore resources" : "浏览学习资料"],
    ["/lab", "02 / EXPERIMENT", en ? "Make ideas visible" : "把抽象概念变成实验", en ? "Build circuits and observe how gates change probabilities." : "搭一条量子线路，观察概率如何变化。跟着任务动手验证，比背下公式更有用。", en ? "Open the circuit lab" : "进入线路实验室"],
    ["/game", "03 / PLAY", en ? "Learn through play" : "在小黑的夜班里练习", en ? "Try the latest XiaoHei Night Shift quantum circuit challenge." : "跟着小黑修复量子线路，让刚学会的知识在游戏中派上用场。", en ? "Try XiaoHei Night Shift" : "体验小黑夜班"],
  ];
  return <main className="learner-home">
    <section className="learner-hero">
      <div className="hero-copy"><span className="workspace-kicker">QUANTUM LEARNING, ONE STEP AT A TIME</span><h1>{en ? <>A small step.<br />A quantum leap.</> : <>从一点好奇，<br />走进<span>量子世界。</span></>}</h1><p>{en ? "Read, experiment, and play. Find your own path into quantum computing." : "读一份资料，做一个实验，玩一局游戏。\n把难懂的量子概念，变成你亲手验证的发现。"}</p><div className="hero-actions"><Link className="workspace-primary" to="/path">{en ? "Find my learning path" : "找到我的学习路径"} <span>↗</span></Link><Link className="hero-text-link" to="/resources">{en ? "Browse resources" : "先看看学习资料"} →</Link></div><div className="hero-facts"><span>{knowledgeModules.length} {en ? "learning stages" : "个学习阶段"}</span><span>{readable.length} {en ? "sample readings" : "篇入门示例"}</span><span>{en ? "Start without formulas" : "零基础也能开始"}</span></div></div>
      <div className="quantum-visual" aria-hidden="true"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="orbit orbit-c"/><div className="quantum-core">ψ</div><div className="state-label state-zero">|0⟩</div><div className="state-label state-one">|1⟩</div><div className="visual-caption">EXPLORE THE POSSIBILITIES<br /><span>从观察，到理解</span></div></div>
    </section>
    <section className="home-learning-section"><div className="section-heading"><div><span className="workspace-kicker">YOUR NEXT DISCOVERY</span><h2>{en ? "Choose how you learn." : "今天，想从哪里开始？"}</h2></div><Link to="/path">{en ? "View learning map" : "查看完整学习地图"} ↗</Link></div><div className="learning-entry-grid">{entries.map(([url, number, title, description, action]) => <Link to={url} key={url} className="learning-entry"><span className="entry-number">{number}</span><h3>{title}</h3><p>{description}</p><strong>{action} <span>↗</span></strong></Link>)}</div></section>
    <section className="home-roadmap"><div><span className="workspace-kicker">A PATH THAT MAKES SENSE</span><h2>{en ? "Follow the ideas,\nnot just the pages." : "每一步学习，\n都知道为什么。"}</h2><p>{en ? "Start with the basics, then build toward gates and algorithms." : "认识量子、建立直觉、理解量子门，再走向算法与实践。先补前置概念，逐步连接新知识。"}</p><Link to="/path">探索六阶段路径 →</Link></div><ol>{knowledgeModules.map(m => <li key={m.id}><span>{m.order}</span><Link to="/path">{m.shortTitle}</Link><span>↗</span></li>)}</ol></section>
    <section className="home-evidence"><div><span className="workspace-kicker">ASK WITH EVIDENCE</span><h2>{en ? "Bring your questions." : "遇到疑问，让资料陪你一起找答案。"}</h2><p>{en ? "Explore source documents and discuss them with the AI tutor." : "查看问答知识库的真实来源，带着教材、论文和参考资料向 AI 伴学提问。"}</p></div><div><Link className="workspace-primary" to="/oa">向 AI 伴学提问 ↗</Link><Link className="hero-text-link" to="/sources">查看知识来源 →</Link></div></section>
    <footer className="learner-footer"><span>量智启学 / QUANTUM EDU</span><span>从好奇出发，以理解抵达。</span></footer>
  </main>;
}
