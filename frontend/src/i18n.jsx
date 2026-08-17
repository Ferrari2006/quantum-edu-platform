import { createContext, useContext, useMemo, useState } from "react";

const LanguageContext = createContext(null);

export const copy = {
  zh: {
    nav: {
      brand: "量智启学",
      subtitle: "QUANTUM EDU",
      home: "首页",
      knowledge: "知识库",
      qa: "AI 伴学",
      game: "游戏实验室",
      account: "账号",
      quickStart: "开始学习",
      toggle: "EN",
    },
    notFound: {
      back: "返回首页",
    },
    home: {
      eyebrow: "AI 伴学 × 沉浸交互 × 量子启蒙",
      title: (
        <>
          在好奇心消失以前，
          <br />
          先让量子世界变得可理解。
        </>
      ),
      intro:
        "量智启学连接游戏体验、系统知识、智能问答与线路实践，帮助每一位学习者从“觉得神奇”走向“真正明白”。",
      knowledgeAction: "探索知识库",
      gameAction: "进入游戏实验室",
      entries: [
        {
          kicker: "01 · KNOWLEDGE",
          title: "量子知识库",
          text: "六阶段学习路径、主题目录、文章阅读与个人进度。",
          action: "从第一节开始 →",
        },
        {
          kicker: "02 · AI TUTOR",
          title: "AI 智能伴学",
          text: "基于可信资料检索，解释概念、追溯来源并结合个人记忆辅助答疑。",
          action: "提出一个问题 →",
        },
        {
          kicker: "03 · GAME LAB",
          title: "游戏实验室",
          text: "用量子门、目标态与保真度，把抽象知识变成策略。",
          action: "开始沉浸体验 →",
        },
      ],
    },
    qa: {
      title: "智能问答",
      placeholder: "输入你的问题",
      ask: "提问",
      asking: "思考中…",
      answer: "回答",
      citations: "引用来源",
      contexts: "检索上下文",
      source: "来源",
      chunk: "片段",
      empty: "提问后会在这里显示回答。",
      authHint: "已登录，回答会在相关时结合你的学习记忆。",
      guestHint: "当前为访客模式，登录后可使用个人学习记忆。",
      requestFailed: "请求失败",
      pipeline: "多智能体处理流程",
      confidence: "置信度",
      review: "审查",
      status: {
        completed: "完成",
        passed: "通过",
        needs_revision: "需要修正",
        insufficient_context: "资料不足",
        skipped: "已跳过",
      },
    },
    account: {
      title: "账号与学习记忆",
      subtitle:
        "登录后，平台可以保存你的学习偏好、目标和薄弱点，并在 AI 伴学时提供个性化解释。",
      loginTab: "登录",
      registerTab: "注册",
      username: "用户名",
      email: "邮箱（可选）",
      password: "密码",
      login: "登录",
      register: "创建账号",
      logout: "退出登录",
      signedInAs: "当前用户",
      memoryTitle: "用户记忆",
      memoryHint: "这些内容会在问答时作为个性化上下文使用。",
      memoryKey: "记忆名称",
      memoryValue: "记忆内容",
      memoryKeyPlaceholder: "例如：学习水平",
      memoryValuePlaceholder: "例如：刚开始学习量子门，希望解释更直观",
      saveMemory: "保存记忆",
      delete: "删除",
      noMemories: "还没有记忆，先添加一条学习偏好吧。",
      error: "操作失败",
    },
  },
  en: {
    nav: {
      brand: "Quantum Edu",
      subtitle: "LEARNING PLATFORM",
      home: "Home",
      knowledge: "Knowledge",
      qa: "AI Tutor",
      game: "Game Lab",
      account: "Account",
      quickStart: "Start Learning",
      toggle: "中文",
    },
    notFound: {
      back: "Back Home",
    },
    home: {
      eyebrow: "AI TUTOR × IMMERSIVE INTERACTION × QUANTUM LEARNING",
      title: (
        <>
          Make the quantum world understandable
          <br />
          while curiosity is still alive.
        </>
      ),
      intro:
        "Quantum Edu connects games, structured knowledge, AI tutoring, and circuit practice—helping every learner move from wonder to understanding.",
      knowledgeAction: "Explore Knowledge",
      gameAction: "Enter Game Lab",
      entries: [
        {
          kicker: "01 · KNOWLEDGE",
          title: "Quantum Knowledge",
          text: "A six-stage path with topics, articles, bookmarks, and progress.",
          action: "Start the first lesson →",
        },
        {
          kicker: "02 · AI TUTOR",
          title: "AI Learning Tutor",
          text: "Ask grounded questions with sources and relevant personal learning memory.",
          action: "Ask a question →",
        },
        {
          kicker: "03 · GAME LAB",
          title: "Game Laboratory",
          text: "Turn gates, target states, and fidelity into playable strategy.",
          action: "Start the experience →",
        },
      ],
    },
    qa: {
      title: "AI Tutor",
      placeholder: "Enter your question",
      ask: "Ask",
      asking: "Thinking…",
      answer: "Answer",
      citations: "Citations",
      contexts: "Retrieved Context",
      source: "Source",
      chunk: "Chunk",
      empty: "Your answer will appear here after asking.",
      authHint: "Signed in. Relevant learning memory can personalize answers.",
      guestHint: "Guest mode. Sign in to use personal learning memory.",
      requestFailed: "Request failed",
      pipeline: "Multi-agent pipeline",
      confidence: "Confidence",
      review: "Review",
      status: {
        completed: "Completed",
        passed: "Passed",
        needs_revision: "Needs revision",
        insufficient_context: "Insufficient context",
        skipped: "Skipped",
      },
    },
    account: {
      title: "Account & Learning Memory",
      subtitle:
        "Sign in to save preferences, goals, and weak spots that can personalize AI tutoring.",
      loginTab: "Sign In",
      registerTab: "Register",
      username: "Username",
      email: "Email (optional)",
      password: "Password",
      login: "Sign In",
      register: "Create Account",
      logout: "Sign Out",
      signedInAs: "Signed in as",
      memoryTitle: "Learning Memory",
      memoryHint: "These notes can be used as personalized context in Q&A.",
      memoryKey: "Memory Name",
      memoryValue: "Memory Content",
      memoryKeyPlaceholder: "Example: learning level",
      memoryValuePlaceholder:
        "Example: new to quantum gates and prefers intuitive explanations",
      saveMemory: "Save Memory",
      delete: "Delete",
      noMemories: "No memories yet. Add a learning preference first.",
      error: "Operation failed",
    },
  },
};

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState("zh");
  const value = useMemo(
    () => ({
      language,
      t: copy[language],
      toggleLanguage: () =>
        setLanguage((current) => (current === "zh" ? "en" : "zh")),
    }),
    [language],
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return context;
}
