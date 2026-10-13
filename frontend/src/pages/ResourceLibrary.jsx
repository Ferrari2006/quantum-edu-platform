import { useState } from "react";
import { knowledgeArticles, knowledgeModules } from "../data/knowledgeContent.js";
import { HashLink as Link } from "../router.jsx";

export default function ResourceLibrary() {
  const [query, setQuery] = useState("");
  const [module, setModule] = useState("");
  const [includeOutline, setIncludeOutline] = useState(false);
  const articles = knowledgeArticles.filter(a => (includeOutline || a.status === "sample") && (!module || a.moduleId === module) && `${a.title} ${a.summary} ${a.keywords.join(" ")}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <main className="learning-workspace"><header className="workspace-heading"><span className="workspace-kicker">RESOURCE LIBRARY / 用户资料库</span><h1>找到下一份值得读的资料</h1><p>按主题查找入门讲解，再带着问题进入实验与AI伴学。</p></header><section className="workspace-toolbar"><label>搜索资料<input value={query} onChange={e => setQuery(e.target.value)} placeholder="例如：量子比特、测量、量子门" /></label><label>学习阶段<select value={module} onChange={e => setModule(e.target.value)}><option value="">全部阶段</option>{knowledgeModules.map(m => <option key={m.id} value={m.id}>{m.shortTitle}</option>)}</select></label><label className="inline-check"><input type="checkbox" checked={includeOutline} onChange={e => setIncludeOutline(e.target.checked)} />显示待补充主题</label></section><p className="workspace-count" aria-live="polite">{articles.length} 份资料 · 示例内容仍需专业审校</p><section className="resource-grid">{articles.map(a => <article key={a.id} className="resource-card"><span className="resource-status">{a.status === "sample" ? "可阅读 · 示例文章" : "待补充 · 主题框架"}</span><h2>{a.title}</h2><p>{a.summary}</p><div className="resource-meta">{a.moduleTitle} · {a.difficulty} · 约{a.minutes}分钟</div><Link to={`/knowledge/${a.id}`}>{a.status === "sample" ? "阅读资料" : "查看主题规划"} →</Link></article>)}</section>{!articles.length && <div className="workspace-panel">没有匹配的资料，请调整关键词或学习阶段。</div>}<section className="workspace-panel"><h2>带着资料继续学习</h2><p>不确定从哪里开始，可以先看学习路径；阅读时遇到疑问，可以使用带来源的AI伴学。</p><Link className="workspace-primary" to="/path">规划学习路径</Link><Link className="workspace-secondary" to="/oa">向AI提问</Link></section></main>;
}
