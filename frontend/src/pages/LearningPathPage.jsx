import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { knowledgeModules, knowledgeArticles } from "../data/knowledgeContent.js";
import { HashLink as Link } from "../router.jsx";

export default function LearningPathPage() {
  const { authHeaders, isAuthenticated } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setItems([]); setError("");
    if (!isAuthenticated) { setLoading(false); return; }
    const controller = new AbortController(); setLoading(true);
    fetch("/api/learning/recommendations?limit=6", { headers: authHeaders(), signal: controller.signal }).then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || "推荐加载失败"); return d; }).then(d => setItems(d.items || [])).catch(e => { if (e.name !== "AbortError") setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [authHeaders, isAuthenticated]);
  return <main className="learning-workspace"><header className="workspace-heading"><span className="workspace-kicker">LEARNING PATH / 学习路径</span><h1>知道下一步学什么，也知道为什么</h1><p>先补前置概念，再阅读、动手验证和回顾。推荐基于当前学习证据，不是能力认证。</p></header><section className="workspace-panel"><h2>你的下一步</h2>{!isAuthenticated ? <p>当前展示通用课程顺序。<Link to="/account">登录</Link>后可根据已有学习记录获得建议。</p> : loading ? <p role="status">正在读取学习记录…</p> : error ? <p role="alert">{error}</p> : items.map(item => { const article = knowledgeArticles.find(a => a.id === item.article_id); return <div className="path-recommendation" key={item.concept_id}><h3>{item.title}</h3><p>{item.reason}</p><p>{article?.status === "sample" ? <Link to={`/knowledge/${item.article_id}`}>阅读示例文章 →</Link> : <span>文章待补充；可先查看前置概念或进入AI伴学。</span>}</p>{item.missing_prerequisites?.map(id => <Link className="path-prerequisite" key={id} to={`/knowledge/${id}`}>前置：{knowledgeArticles.find(a => a.id === id)?.title || id}</Link>)}</div>; })}</section><ol className="path-module-list">{knowledgeModules.map(m => <li key={m.id}><span className="path-number">{m.order}</span><div><h2>{m.shortTitle}</h2><p>{m.description}</p><div className="path-articles">{m.articles.map(a => a.status === "sample" ? <Link key={a.id} to={`/knowledge/${a.id}`}>{a.title} →</Link> : <span key={a.id}>{a.title} · 待补充</span>)}</div></div></li>)}</ol><section className="workspace-panel"><h2>用练习校准，而不只靠阅读记录</h2><p>正式前后测题库由团队准备。你现在可以体验评估流程，或完成一个引导式线路实验。</p><Link className="workspace-primary" to="/assessment">体验前后测框架</Link><Link className="workspace-secondary" to="/lab?task=bell-pair">进入Bell态实验</Link></section></main>;
}
