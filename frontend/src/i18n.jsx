import { createContext, useContext, useMemo, useState } from "react";

const LanguageContext = createContext(null);

export const copy = {
  zh: {
    nav: {
      brand: "量智启学",
      home: "首页",
      qa: "问答",
      game: "游戏",
      toggle: "EN"
    },
    notFound: {
      back: "返回首页"
    },
    home: {
      eyebrow: "量智启学 · Quantum Edu Platform",
      title: "AI 驱动的沉浸式量子计算启蒙平台",
      intro:
        "把智能问答、知识检索和游戏化练习放在同一个学习工作台里，让量子概念从“看不懂”变成“能提问、能操作、能验证”。",
      ask: "开始问答",
      game: "打开游戏",
      statusLabel: "平台状态",
      modulesLabel: "平台模块",
      quickTitle: "快捷入口",
      quickHint: "选择一个学习动作",
      progressTitle: "学习进度",
      progressHint: "概念掌握概览",
      extendTitle: "下一步可扩展功能",
      extendText: "首页可以继续接入文档上传、知识库索引状态、每日挑战、错题记录和个人学习报告。",
      plan: "规划学习任务",
      metrics: [
        ["FastAPI", "后端服务"],
        ["React", "前端界面"],
        ["RAG", "知识问答"],
        ["Game", "沉浸练习"]
      ],
      quickActions: [
        {
          title: "智能问答",
          text: "围绕量子计算概念、课程资料和平台文档进行检索式问答。",
          label: "开始提问"
        },
        {
          title: "量子游戏",
          text: "通过概率匹配、量子态反馈和得分机制理解抽象概念。",
          label: "进入游戏"
        },
        {
          title: "学习路线",
          text: "从量子比特、叠加态、测量到量子门，按阶段推进。",
          label: "询问路线"
        }
      ],
      learningSteps: [
        { name: "量子比特", status: "入门" },
        { name: "叠加与测量", status: "练习中" },
        { name: "量子门", status: "待强化" },
        { name: "纠缠", status: "待开启" }
      ]
    }
  },
  en: {
    nav: {
      brand: "Quantum Edu",
      home: "Home",
      qa: "Q&A",
      game: "Game",
      toggle: "中"
    },
    notFound: {
      back: "Back Home"
    },
    home: {
      eyebrow: "Quantum Edu Platform",
      title: "An AI-Powered Immersive Platform for Quantum Learning",
      intro:
        "Bring intelligent Q&A, knowledge retrieval, and game-based practice into one learning workspace, turning abstract quantum ideas into questions, actions, and feedback.",
      ask: "Start Q&A",
      game: "Open Game",
      statusLabel: "Platform status",
      modulesLabel: "Platform modules",
      quickTitle: "Quick Actions",
      quickHint: "Choose a learning path",
      progressTitle: "Learning Progress",
      progressHint: "Concept mastery overview",
      extendTitle: "What Can Come Next",
      extendText: "The home page can later connect document upload, knowledge indexing, daily challenges, mistake review, and personal learning reports.",
      plan: "Plan Study Tasks",
      metrics: [
        ["FastAPI", "Backend"],
        ["React", "Frontend"],
        ["RAG", "Knowledge Q&A"],
        ["Game", "Immersive Practice"]
      ],
      quickActions: [
        {
          title: "Smart Q&A",
          text: "Ask retrieval-based questions about quantum concepts, course materials, and platform documents.",
          label: "Ask a Question"
        },
        {
          title: "Quantum Game",
          text: "Learn abstract ideas through probability matching, quantum-state feedback, and scoring loops.",
          label: "Enter Game"
        },
        {
          title: "Learning Path",
          text: "Move step by step from qubits and superposition to measurement and quantum gates.",
          label: "Ask for a Path"
        }
      ],
      learningSteps: [
        { name: "Qubits", status: "Started" },
        { name: "Superposition & Measurement", status: "Practicing" },
        { name: "Quantum Gates", status: "Needs Focus" },
        { name: "Entanglement", status: "Locked" }
      ]
    }
  }
};

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState("zh");
  const value = useMemo(() => {
    const toggleLanguage = () => setLanguage((current) => (current === "zh" ? "en" : "zh"));
    return { language, t: copy[language], toggleLanguage };
  }, [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return context;
}
