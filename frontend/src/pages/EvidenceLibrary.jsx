import { useEffect, useMemo, useState } from 'react';
import catalog from '../data/resourceCatalog.json';
import { HashLink as Link } from '../router.jsx';

export default function EvidenceLibrary() {
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [index, setIndex] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/rag/index-status', { signal: controller.signal }).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(setIndex).catch(() => {});
    return () => controller.abort();
  }, []);
  const sources = [...new Set(catalog.resources.map(r => r.source))];
  const items = useMemo(() => catalog.resources.filter(r => (!source || r.source === source) && `${r.title} ${r.topic} ${r.id}`.toLowerCase().includes(query.trim().toLowerCase())), [query, source]);
  return <main className="learning-workspace"><header className="workspace-heading"><span className="workspace-kicker">EVIDENCE LIBRARY / 知识来源</span><h1>让每一次提问，<br />都有资料可循。</h1><p>查看项目实际收录的检索语料，了解出处、内容类型与版本。学习资料面向阅读，这里展示 AI 问答背后的知识来源。</p></header><div className="source-summary"><div><strong>{catalog.resources.length}</strong><span>本地语料文件</span></div><div><strong>{sources.length}</strong><span>来源类别</span></div><div><strong>{index ? index.indexed_chunks : "未连接"}</strong><span>{index ? (index.ready ? "已入库向量片段" : "向量索引尚未构建") : "运行时向量索引状态"}</span></div></div><section className="workspace-toolbar"><label>搜索来源<input value={query} onChange={e => setQuery(e.target.value)} placeholder="论文标题、教材章节或主题" /></label><label>来源类别<select value={source} onChange={e => setSource(e.target.value)}><option value="">全部来源</option>{sources.map(s => <option key={s}>{s}</option>)}</select></label><Link to="/oa">带着资料提问 ↗</Link></section><p className="workspace-count" aria-live="polite">找到 {items.length} 个语料文件</p><section className="resource-grid">{items.map(r => <article className="resource-card" key={r.id}><span className="resource-status">{r.source} · {r.type === 'paper' ? '论文元数据 / 摘要' : '参考文档'}</span><h2>{r.title}</h2><p className="source-file">{r.id}</p><dl className="source-details"><div><dt>记录日期</dt><dd>{r.updated || '未登记'}</dd></div><div><dt>资料版本</dt><dd>{r.version || '未登记'}</dd></div><div><dt>许可记录</dt><dd>{r.license || '待核对'}</dd></div></dl>{r.sourceUrl && <a href={r.sourceUrl} target="_blank" rel="noopener noreferrer">查看原始来源 ↗</a>}</article>)}</section>{!items.length && <div className="workspace-panel">没有匹配来源，请调整搜索条件。</div>}<aside className="workspace-notice">此目录由项目语料生成，文件数不代表已成功入库的向量片段数。当前默认使用哈希向量与关键词混合检索；语义嵌入升级、Qiskit 文档导入及检索效果评测仍需继续完成。</aside></main>;
}
