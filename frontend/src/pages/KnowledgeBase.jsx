import { useEffect, useMemo, useRef, useState } from "react";

import { useAuth } from "../auth.jsx";
import {
  getKnowledgeArticle,
  getNextArticle,
  knowledgeArticles,
  knowledgeModules,
} from "../data/knowledgeContent.js";
import { getKnowledgeQuiz } from "../data/knowledgeQuizzes.js";
import { calculateQuizResult } from "../utils/learningEvidence.js";
import {
  HashLink as Link,
  HashNavLink as NavLink,
  navigateTo,
  useHashLocation,
} from "../router.jsx";
import "./KnowledgeBase.css";

const STORAGE_KEYS = {
  completed: "quantum-edu:knowledge-completed",
  bookmarks: "quantum-edu:knowledge-bookmarks",
};

function readStoredList(key) {
  try {
    return JSON.parse(window.localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function Icon({ name, size = 18 }) {
  const paths = {
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
    bookmark: <path d="M6 4.8A1.8 1.8 0 0 1 7.8 3h8.4A1.8 1.8 0 0 1 18 4.8V21l-6-3.8L6 21Z" />,
    check: <path d="m5 12 4.2 4.2L19 6.5" />,
    arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    home: <><path d="m4 11 8-7 8 7" /><path d="M6.5 10v10h11V10" /></>,
    spark: <><path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4Z" /><path d="m18.5 14 .8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8Z" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v17H6.5A2.5 2.5 0 0 0 4 22.5Z" /><path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v17h4.5a2.5 2.5 0 0 1 2.5 2.5Z" /></>,
    play: <path d="m9 7 8 5-8 5Z" />,
  };
  return (
    <svg
      aria-hidden="true"
      className="kb-icon"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      {paths[name]}
    </svg>
  );
}

function KnowledgeSidebar({ completed, mobileOpen, onClose }) {
  const progress = Math.round((completed.length / knowledgeArticles.length) * 100);
  return (
    <>
      <button
        aria-label="关闭知识库目录"
        className={`kb-sidebar-scrim ${mobileOpen ? "is-open" : ""}`}
        onClick={onClose}
        type="button"
      />
      <aside className={`kb-sidebar ${mobileOpen ? "is-open" : ""}`}>
        <div className="kb-sidebar-head">
          <Link className="kb-library-mark" onClick={onClose} to="/knowledge">
            <span className="kb-library-symbol"><Icon name="book" size={19} /></span>
            <span>
              <strong>量子知识库</strong>
              <small>LEARNING ATLAS</small>
            </span>
          </Link>
          <button aria-label="关闭目录" className="kb-mobile-close" onClick={onClose} type="button">
            <Icon name="close" />
          </button>
        </div>

        <div className="kb-progress-card">
          <div className="kb-progress-copy">
            <span>你的探索进度</span>
            <strong>{completed.length}<small> / {knowledgeArticles.length} 节</small></strong>
          </div>
          <div className="kb-progress-ring" style={{ "--progress": `${progress * 3.6}deg` }}>
            <span>{progress}%</span>
          </div>
        </div>

        <nav aria-label="知识库目录" className="kb-catalogue">
          {knowledgeModules.map((module) => (
            <section className="kb-module-nav" key={module.id}>
              <div className="kb-module-label">
                <span style={{ color: module.color }}>{module.order}</span>
                {module.shortTitle}
              </div>
              <div className="kb-module-links">
                {module.articles.map((article) => (
                  <NavLink
                    className={({ isActive }) => `kb-article-link ${isActive ? "active" : ""}`}
                    key={article.id}
                    onClick={onClose}
                    to={`/knowledge/${article.id}`}
                  >
                    <span className={`kb-status-dot ${completed.includes(article.id) ? "is-complete" : ""}`}>
                      {completed.includes(article.id) ? <Icon name="check" size={10} /> : null}
                    </span>
                    <span>{article.title}</span>
                  </NavLink>
                ))}
              </div>
            </section>
          ))}
        </nav>

        <div className="kb-sidebar-foot">
          <span>内容框架 v0.1</span>
          <span>持续生长中</span>
        </div>
      </aside>
    </>
  );
}

function KnowledgeTopbar({ query, setQuery, onMenu }) {
  const inputRef = useRef(null);
  const [focused, setFocused] = useState(false);
  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    return knowledgeArticles
      .filter((article) =>
        [article.title, article.summary, article.moduleTitle, ...article.keywords]
          .join(" ")
          .toLowerCase()
          .includes(normalized),
      )
      .slice(0, 6);
  }, [query]);

  useEffect(() => {
    const handleShortcut = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  return (
    <header className="kb-topbar">
      <button aria-label="打开知识库目录" className="kb-menu-button" onClick={onMenu} type="button">
        <Icon name="menu" />
      </button>
      <Link className="kb-topbar-home" to="/knowledge">
        <Icon name="home" size={16} />
        <span>知识库首页</span>
      </Link>
      <div className={`kb-search ${focused ? "is-focused" : ""}`}>
        <Icon name="search" size={17} />
        <input
          aria-label="搜索知识库"
          onBlur={() => window.setTimeout(() => setFocused(false), 120)}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setFocused(true)}
          placeholder="搜索概念、算法或工具…"
          ref={inputRef}
          value={query}
        />
        {query ? (
          <button aria-label="清空搜索" onClick={() => setQuery("")} type="button">
            <Icon name="close" size={15} />
          </button>
        ) : (
          <kbd>Ctrl K</kbd>
        )}
        {focused && query ? (
          <div className="kb-search-popover">
            <div className="kb-search-caption">找到 {results.length} 个相关主题</div>
            {results.length ? results.map((article) => (
              <Link key={article.id} onClick={() => setQuery("")} to={`/knowledge/${article.id}`}>
                <span className="kb-search-order">{article.moduleOrder}</span>
                <span>
                  <strong>{article.title}</strong>
                  <small>{article.moduleTitle} · {article.minutes} 分钟</small>
                </span>
                <Icon name="arrow" size={15} />
              </Link>
            )) : <div className="kb-no-result">换一个关键词试试，例如“测量”或“Grover”。</div>}
          </div>
        ) : null}
      </div>
      <Link className="kb-ai-link" to="/oa">
        <Icon name="spark" size={16} />
        问 AI 伴学
      </Link>
    </header>
  );
}

function ModuleCard({ module, completed }) {
  const completeCount = module.articles.filter((article) => completed.includes(article.id)).length;
  return (
    <article className="kb-path-card" style={{ "--module-color": module.color }}>
      <div className="kb-path-card-top">
        <span className="kb-path-order">{module.order}</span>
        <span className="kb-path-count">{completeCount}/{module.articles.length} 完成</span>
      </div>
      <h3>{module.title}</h3>
      <p>{module.description}</p>
      <div className="kb-path-line">
        <span style={{ width: `${(completeCount / module.articles.length) * 100}%` }} />
      </div>
      <Link to={`/knowledge/${module.articles[0].id}`}>
        开始本阶段
        <Icon name="arrow" size={16} />
      </Link>
    </article>
  );
}

function LearningInsights({ authHeaders, isAuthenticated, refreshKey }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setData(null);
      setLoadError(false);
      return undefined;
    }
    const controller = new AbortController();
    setLoading(true);
    setLoadError(false);
    fetch("/api/learning/recommendations?limit=4", {
      headers: authHeaders(),
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "加载学习画像失败");
        setData(payload);
      })
      .catch((error) => {
        if (error.name !== "AbortError") setLoadError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [authHeaders, isAuthenticated, refreshKey]);

  if (!isAuthenticated) {
    return (
      <section className="kb-insight-card kb-insight-login">
        <div>
          <span>PERSONAL LEARNING LOOP</span>
          <h2>登录后生成你的概念掌握图谱</h2>
          <p>完成资料或运行量子实验后，平台会记录学习证据，并推荐下一步最值得巩固的主题。</p>
        </div>
        <Link to="/account">登录 / 注册 <Icon name="arrow" size={16} /></Link>
      </section>
    );
  }

  const summary = data?.summary;
  return (
    <section className="kb-insight-card">
      <div className="kb-insight-heading">
        <div>
          <span>PERSONAL LEARNING LOOP</span>
          <h2>你的学习画像与下一步</h2>
        </div>
        <div className="kb-mastery-score">
          <strong>{summary ? Math.round(summary.average_mastery * 100) : 0}%</strong>
          <small>平均掌握度</small>
        </div>
      </div>
      {loadError && !data ? (
        <p className="kb-insight-loading">暂时无法读取云端学习画像，本地阅读进度仍会正常保留。</p>
      ) : loading && !data ? <p className="kb-insight-loading">正在整理学习证据…</p> : (
        <>
          <div className="kb-insight-stats">
            <span><strong>{summary?.covered_concepts || 0}</strong> / {summary?.total_concepts || knowledgeArticles.length} 已覆盖概念</span>
            <span><strong>{summary?.mastered_concepts || 0}</strong> 个概念达到熟练</span>
          </div>
          <div className="kb-recommendation-list">
            {data?.items?.map((item, index) => (
              <Link key={item.concept_id} to={`/knowledge/${item.article_id}`}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div><strong>{item.title}</strong><small>{item.reason}</small></div>
                <Icon name="arrow" size={16} />
              </Link>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function KnowledgeHome({ authHeaders, bookmarks, completed, isAuthenticated, masteryRefresh }) {
  const continueArticle =
    knowledgeArticles.find((article) => !completed.includes(article.id)) || knowledgeArticles[0];
  const sampleCount = knowledgeArticles.filter((article) => article.status === "sample").length;
  const bookmarkedArticles = knowledgeArticles.filter((article) => bookmarks.includes(article.id));

  return (
    <div className="kb-home">
      <section className="kb-hero">
        <div className="kb-hero-grid" aria-hidden="true" />
        <div className="kb-orbit kb-orbit-one" aria-hidden="true"><span /></div>
        <div className="kb-orbit kb-orbit-two" aria-hidden="true"><span /></div>
        <div className="kb-hero-copy">
          <div className="kb-kicker"><span /> QUANTUM LEARNING ATLAS</div>
          <h1>把抽象的量子世界，<br /><em>拆成一条走得完的路。</em></h1>
          <p>从直觉启蒙到线路实践，再回到游戏验证。这里不是资料堆放处，而是你理解量子计算的导航系统。</p>
          <div className="kb-hero-actions">
            <Link className="kb-primary-action" to={`/knowledge/${continueArticle.id}`}>
              <span className="kb-play"><Icon name="play" size={17} /></span>
              {completed.length ? "继续上次学习" : "从第一节开始"}
            </Link>
            <a className="kb-secondary-action" href="#learning-path">查看完整路径 <Icon name="arrow" size={16} /></a>
          </div>
        </div>
        <div className="kb-hero-stats">
          <div><strong>{knowledgeModules.length}</strong><span>学习阶段</span></div>
          <div><strong>{knowledgeArticles.length}</strong><span>主题框架</span></div>
          <div><strong>{sampleCount}</strong><span>示例文章</span></div>
        </div>
      </section>

      <LearningInsights
        authHeaders={authHeaders}
        isAuthenticated={isAuthenticated}
        refreshKey={masteryRefresh}
      />

      <section className="kb-home-section" id="learning-path">
        <div className="kb-section-heading">
          <div>
            <span className="kb-section-index">01</span>
            <div>
              <p>RECOMMENDED ROUTE</p>
              <h2>推荐学习路径</h2>
            </div>
          </div>
          <p>按认知负荷分成六个阶段；你也可以跳到任何感兴趣的主题。</p>
        </div>
        <div className="kb-path-grid">
          {knowledgeModules.map((module) => (
            <ModuleCard completed={completed} key={module.id} module={module} />
          ))}
        </div>
      </section>

      <section className="kb-home-section kb-library-overview">
        <div className="kb-section-heading">
          <div>
            <span className="kb-section-index">02</span>
            <div>
              <p>CONTENT BLUEPRINT</p>
              <h2>内容目录总览</h2>
            </div>
          </div>
          <p>“示例”可直接阅读；“框架”已预设学习目标和写作槽位，等待团队补充。</p>
        </div>
        <div className="kb-outline-list">
          {knowledgeModules.map((module) => (
            <div className="kb-outline-row" key={module.id}>
              <div className="kb-outline-module">
                <span style={{ background: module.color }}>{module.order}</span>
                <div><strong>{module.title}</strong><small>{module.description}</small></div>
              </div>
              <div className="kb-outline-articles">
                {module.articles.map((article) => (
                  <Link key={article.id} to={`/knowledge/${article.id}`}>
                    {article.title}
                    <small className={article.status === "sample" ? "is-sample" : ""}>
                      {article.status === "sample" ? "示例" : "框架"}
                    </small>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {bookmarkedArticles.length ? (
        <section className="kb-home-section">
          <div className="kb-section-heading">
            <div>
              <span className="kb-section-index">03</span>
              <div><p>YOUR SAVED TOPICS</p><h2>我的收藏</h2></div>
            </div>
          </div>
          <div className="kb-bookmark-grid">
            {bookmarkedArticles.map((article) => (
              <Link key={article.id} to={`/knowledge/${article.id}`}>
                <span>{article.moduleOrder}</span>
                <strong>{article.title}</strong>
                <small>{article.summary}</small>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function ArticleQuiz({ article, authHeaders, isAuthenticated, onMasteryRecorded }) {
  const questions = getKnowledgeQuiz(article.id);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [syncState, setSyncState] = useState("idle");

  useEffect(() => {
    setAnswers({});
    setSubmitted(false);
    setScore(0);
    setSyncState("idle");
  }, [article.id]);

  if (!questions.length) return null;
  const answeredCount = Object.keys(answers).length;

  const submitQuiz = () => {
    if (answeredCount !== questions.length) return;
    const result = calculateQuizResult(questions, answers);
    const correct = result.correctCount;
    const nextScore = result.score;
    setScore(nextScore);
    setSubmitted(true);
    if (!isAuthenticated) return;

    setSyncState("syncing");
    fetch("/api/learning/events", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        concept_id: article.id,
        event_type: "quiz_attempt",
        source: "knowledge_quiz",
        score: nextScore,
        metadata: {
          title: article.title,
          question_count: questions.length,
          correct_count: correct,
          answers,
        },
      }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("小测结果同步失败");
        setSyncState("synced");
        onMasteryRecorded();
      })
      .catch(() => setSyncState("failed"));
  };

  const retryQuiz = () => {
    setAnswers({});
    setSubmitted(false);
    setScore(0);
    setSyncState("idle");
  };

  return (
    <section className="kb-quiz">
      <div className="kb-quiz-heading">
        <div><span>CONCEPT CHECK</span><h2>三道题，检查是否真的理解</h2></div>
        <small>{answeredCount} / {questions.length} 已作答</small>
      </div>
      <div className="kb-quiz-questions">
        {questions.map((question, questionIndex) => {
          const selected = answers[question.id];
          const isCorrect = submitted && selected === question.answer;
          return (
            <div className="kb-quiz-question" key={question.id}>
              <strong><span>{String(questionIndex + 1).padStart(2, "0")}</span>{question.prompt}</strong>
              <div className="kb-quiz-options">
                {question.options.map((option, optionIndex) => {
                  const chosen = selected === optionIndex;
                  const correctOption = submitted && question.answer === optionIndex;
                  const wrongOption = submitted && chosen && !correctOption;
                  return (
                    <button
                      aria-pressed={chosen}
                      className={`${chosen ? "is-selected" : ""} ${correctOption ? "is-correct" : ""} ${wrongOption ? "is-wrong" : ""}`}
                      disabled={submitted}
                      key={option}
                      onClick={() => setAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
                      type="button"
                    >
                      <span>{String.fromCharCode(65 + optionIndex)}</span>{option}
                    </button>
                  );
                })}
              </div>
              {submitted ? (
                <p className={isCorrect ? "is-correct" : "is-wrong"}>
                  <strong>{isCorrect ? "回答正确" : "需要再想一步"}</strong>{question.explanation}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
      <div className="kb-quiz-actions">
        {submitted ? (
          <>
            <div className="kb-quiz-result">
              <strong>{Math.round(score * 100)}%</strong>
              <span>{score >= 2 / 3 ? "已建立基本理解，可以继续前进。" : "建议回看本节重点后再试一次。"}</span>
            </div>
            <button onClick={retryQuiz} type="button">再测一次</button>
          </>
        ) : (
          <>
            <span>{isAuthenticated ? "结果将计入你的概念掌握度" : "登录后可把结果计入学习画像"}</span>
            <button disabled={answeredCount !== questions.length} onClick={submitQuiz} type="button">提交答案</button>
          </>
        )}
      </div>
      {syncState === "syncing" ? <p className="kb-quiz-sync">正在同步学习结果…</p> : null}
      {syncState === "synced" ? <p className="kb-quiz-sync is-synced">小测结果已计入学习画像。</p> : null}
      {syncState === "failed" ? <p className="kb-quiz-sync is-failed">本次结果暂未同步，你仍可以继续学习。</p> : null}
    </section>
  );
}

function ArticleReader({ article, authHeaders, bookmarked, completed, isAuthenticated, onBookmark, onComplete, onMasteryRecorded }) {
  const nextArticle = getNextArticle(article.id);
  const sectionIds = article.sections.map((section, index) => `section-${index + 1}`);

  return (
    <article className="kb-reader">
      <div className="kb-breadcrumb">
        <Link to="/knowledge">知识库</Link><span>/</span>
        <span>{article.moduleTitle}</span><span>/</span>
        <strong>{article.title}</strong>
      </div>

      <header className="kb-article-header" style={{ "--article-color": article.moduleColor }}>
        <div className="kb-article-label">
          <span>{article.eyebrow}</span>
          <span className={article.status === "sample" ? "is-ready" : ""}>
            {article.status === "sample" ? "示例内容" : "内容框架"}
          </span>
        </div>
        <h1>{article.title}</h1>
        <p>{article.lead}</p>
        <div className="kb-article-meta">
          <span><Icon name="clock" size={15} /> 约 {article.minutes} 分钟</span>
          <span>{article.difficulty}</span>
          <span>{article.moduleOrder} / {knowledgeModules.length}</span>
        </div>
        <div className="kb-article-actions">
          <button className={completed ? "is-complete" : ""} onClick={onComplete} type="button">
            <Icon name="check" size={16} />
            {completed ? "已完成" : "标记为已完成"}
          </button>
          <button className={bookmarked ? "is-bookmarked" : ""} onClick={onBookmark} type="button">
            <Icon name="bookmark" size={15} />
            {bookmarked ? "已收藏" : "收藏"}
          </button>
        </div>
      </header>

      <div className="kb-reader-layout">
        <div className="kb-article-body">
          <section className="kb-objectives">
            <span>完成本节后，你将能够</span>
            <ul>{article.objectives.map((objective) => <li key={objective}><Icon name="check" size={14} />{objective}</li>)}</ul>
          </section>

          {article.sections.map((section, index) => (
            <section className="kb-content-section" id={sectionIds[index]} key={section.title}>
              <div className="kb-content-index">{String(index + 1).padStart(2, "0")}</div>
              <h2>{section.title}</h2>
              {section.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
              {section.callout ? (
                <div className="kb-callout">
                  <span><Icon name="spark" size={17} /></span>
                  <p>{section.callout}</p>
                </div>
              ) : null}
              {section.bullets ? (
                <ul className="kb-bullet-list">
                  {section.bullets.map((bullet) => <li key={bullet}><span />{bullet}</li>)}
                </ul>
              ) : null}
              {section.concepts ? (
                <div className="kb-concept-grid">
                  {section.concepts.map(([term, meaning]) => (
                    <div key={term}><strong>{term}</strong><p>{meaning}</p></div>
                  ))}
                </div>
              ) : null}
            </section>
          ))}

          <section className="kb-takeaway">
            <div><Icon name="spark" size={19} /> 本节带走一句话</div>
            <p>{article.takeaway}</p>
          </section>

          <ArticleQuiz
            article={article}
            authHeaders={authHeaders}
            isAuthenticated={isAuthenticated}
            key={article.id}
            onMasteryRecorded={onMasteryRecorded}
          />

          {article.gameLink ? (
            <section className="kb-game-bridge">
              <div>
                <span>GAME ↔ KNOWLEDGE</span>
                <h3>回到游戏里验证</h3>
                <p>{article.gameLink}</p>
              </div>
              <Link to="/game">进入游戏大厅 <Icon name="arrow" size={16} /></Link>
            </section>
          ) : null}

          {nextArticle ? (
            <Link className="kb-next-article" to={`/knowledge/${nextArticle.id}`}>
              <span>下一节</span>
              <strong>{nextArticle.title}</strong>
              <Icon name="arrow" size={22} />
            </Link>
          ) : (
            <Link className="kb-next-article" to="/knowledge">
              <span>你已走完当前路径</span>
              <strong>返回知识库首页</strong>
              <Icon name="arrow" size={22} />
            </Link>
          )}
        </div>

        <aside className="kb-on-this-page">
          <div className="kb-toc-card">
            <strong>本页目录</strong>
            {article.sections.map((section, index) => (
              <a href={`#${sectionIds[index]}`} key={section.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>{section.title}
              </a>
            ))}
          </div>
          <div className="kb-source-note">
            <span>内容状态</span>
            <strong>{article.status === "sample" ? "结构示例 · 待专业审校" : "框架已就绪 · 待整理"}</strong>
            <p>正式发布前建议补充来源、审核人和最后更新时间。</p>
          </div>
        </aside>
      </div>
    </article>
  );
}

export default function KnowledgeBase({ articleId = "" }) {
  const { authHeaders, isAuthenticated } = useAuth();
  const locationPath = useHashLocation();
  const [query, setQuery] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [completed, setCompleted] = useState(() => readStoredList(STORAGE_KEYS.completed));
  const [bookmarks, setBookmarks] = useState(() => readStoredList(STORAGE_KEYS.bookmarks));
  const [masteryRefresh, setMasteryRefresh] = useState(0);
  const article = articleId ? getKnowledgeArticle(articleId) : null;

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    setMobileOpen(false);
  }, [locationPath]);

  useEffect(() => {
    if (articleId && !article) navigateTo("/knowledge", { replace: true });
  }, [article, articleId]);

  const toggleStoredItem = (setter, key, id) => {
    setter((current) => {
      const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
      window.localStorage.setItem(key, JSON.stringify(next));
      return next;
    });
  };

  const toggleArticleCompletion = () => {
    if (!article) return;
    const alreadyCompleted = completed.includes(article.id);
    toggleStoredItem(setCompleted, STORAGE_KEYS.completed, article.id);
    if (alreadyCompleted || !isAuthenticated) return;

    fetch("/api/learning/events", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        concept_id: article.id,
        event_type: "article_completed",
        source: "knowledge_base",
        score: article.status === "sample" ? 0.72 : 0.6,
        idempotency_key: `knowledge_base:${article.id}:completed`,
        metadata: {
          title: article.title,
          module: article.moduleTitle,
          difficulty: article.difficulty,
          content_status: article.status,
        },
      }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("学习进度同步失败");
        setMasteryRefresh((value) => value + 1);
      })
      .catch(() => {
        // Local completion remains available offline; the learning profile is optional.
      });
  };

  return (
    <div className="knowledge-shell">
      <KnowledgeSidebar
        completed={completed}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />
      <main className="kb-main">
        <KnowledgeTopbar onMenu={() => setMobileOpen(true)} query={query} setQuery={setQuery} />
        {article ? (
          <ArticleReader
            article={article}
            authHeaders={authHeaders}
            bookmarked={bookmarks.includes(article.id)}
            completed={completed.includes(article.id)}
            isAuthenticated={isAuthenticated}
            onBookmark={() => toggleStoredItem(setBookmarks, STORAGE_KEYS.bookmarks, article.id)}
            onComplete={toggleArticleCompletion}
            onMasteryRecorded={() => setMasteryRefresh((value) => value + 1)}
          />
        ) : (
          <KnowledgeHome
            authHeaders={authHeaders}
            bookmarks={bookmarks}
            completed={completed}
            isAuthenticated={isAuthenticated}
            masteryRefresh={masteryRefresh}
          />
        )}
      </main>
    </div>
  );
}
