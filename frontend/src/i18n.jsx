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
      lab: "量子线路",
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
      taskMode: "任务模式",
      modes: {
        auto: "自动识别",
        concept: "概念解释",
        derivation: "算法与公式解析",
        code: "Qiskit 代码纠错",
        game_strategy: "游戏关卡攻略",
        learning_path: "学习路径推荐",
      },
      modeHints: {
        auto: "系统会根据问题自动选择处理方式。",
        concept: "先解释直觉，再给出定义、例子和引用。",
        derivation: "按步骤说明算法或公式，并明确使用前提。",
        code: "粘贴代码后会先进行安全静态检查，再结合资料给出修复建议。",
        game_strategy: "提问时会自动读取当前正在进行的游戏状态。",
        learning_path: "登录后会结合学习目标、水平和薄弱点进行推荐。",
      },
      codePlaceholder: "在这里粘贴需要检查的 Qiskit / Python 代码（不会直接运行）",
      gameStateHint: "请先在游戏实验室开始一局游戏，提问时系统会自动读取当前状态。",
      gameStateConnected: "已读取当前游戏状态，并作为攻略生成依据。",
      gameStateFailed: "读取游戏状态失败",
      noActiveGame: "当前没有正在进行的游戏，请先进入游戏实验室开始一局。",
    },
    lab: {
      title: "图形化量子线路实验室",
      subtitle: "选择量子门并点击线路，把抽象的态演化变成可以观察、运行和追问的实验。",
      qubits: "量子比特数",
      target: "对照目标态",
      targets: { none: "不计算保真度", bell: "Bell态 (|00⟩+|11⟩)/√2", ghz: "GHZ态" },
      radians: "弧度",
      undo: "撤销",
      clear: "清空",
      palette: "量子门工具箱",
      paletteHint: "先选择量子门，再点击左侧q编号放置。双比特门需要依次选择两个不同量子比特。",
      singleGate: "单比特门",
      multiGate: "双比特门",
      circuit: "线路画布",
      placeGate: "已选择 {gate}，点击一个量子比特放置。",
      chooseNext: "{gate} 已选择第一个量子比特，请点击另一个量子比特。",
      distinctTargets: "多比特门需要选择不同的量子比特。",
      run: "运行线路",
      running: "计算中…",
      runFailed: "线路运行失败",
      removeOperation: "删除这一步",
      emptyCircuit: "从左侧选择量子门，然后点击q编号开始搭建",
      result: "SIMULATION RESULT",
      probabilities: "测量概率",
      fidelity: "目标保真度",
      runHint: "运行线路后将在这里显示各基态的测量概率。",
      depth: "线路深度",
      operations: "门数量",
      engine: "模拟方式",
      learningSyncing: "正在同步学习记录…",
      learningSynced: "学习记录已同步",
      learningSyncFailed: "学习记录暂未同步",
      code: "对应代码",
      askAI: "让AI解释线路",
      aiQuestion: "请分析这段Qiskit线路：解释每个量子门如何改变状态、最终概率分布代表什么，并指出可以继续尝试的实验。",
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
      lab: "Circuit Lab",
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
      taskMode: "Task mode",
      modes: {
        auto: "Auto detect",
        concept: "Concept explanation",
        derivation: "Algorithm & derivation",
        code: "Qiskit code diagnosis",
        game_strategy: "Game strategy",
        learning_path: "Learning path",
      },
      modeHints: {
        auto: "The system selects a workflow based on your question.",
        concept: "Explains intuition first, followed by definitions, examples, and citations.",
        derivation: "Explains algorithms or formulas step by step and states assumptions.",
        code: "Runs safe static checks before producing grounded repair guidance.",
        game_strategy: "Reads the currently active game state when the question is submitted.",
        learning_path: "Uses saved goals, level, and weak areas when signed in.",
      },
      codePlaceholder: "Paste Qiskit / Python code here (it will not be executed)",
      gameStateHint: "Start a game in Game Lab first. Its current state will be attached automatically.",
      gameStateConnected: "Current game state attached as strategy context.",
      gameStateFailed: "Failed to load game state",
      noActiveGame: "No game is active. Start one in Game Lab first.",
    },
    lab: {
      title: "Visual Quantum Circuit Lab",
      subtitle: "Choose gates and place them on wires to observe, run, and question quantum state evolution.",
      qubits: "Qubits",
      target: "Target state",
      targets: { none: "No fidelity target", bell: "Bell state (|00⟩+|11⟩)/√2", ghz: "GHZ state" },
      radians: "radians",
      undo: "Undo",
      clear: "Clear",
      palette: "Gate palette",
      paletteHint: "Choose a gate, then click a q label. Two-qubit gates require two distinct qubits in order.",
      singleGate: "single-qubit",
      multiGate: "two-qubit",
      circuit: "Circuit canvas",
      placeGate: "{gate} selected. Click a qubit to place it.",
      chooseNext: "First qubit selected for {gate}. Choose another qubit.",
      distinctTargets: "A multi-qubit gate requires distinct qubits.",
      run: "Run circuit",
      running: "Running…",
      runFailed: "Circuit execution failed",
      removeOperation: "Remove this operation",
      emptyCircuit: "Choose a gate and click a q label to start",
      result: "SIMULATION RESULT",
      probabilities: "Measurement probabilities",
      fidelity: "Target fidelity",
      runHint: "Run the circuit to see the probability of each basis state.",
      depth: "Depth",
      operations: "Gates",
      engine: "Engine",
      learningSyncing: "Syncing learning record…",
      learningSynced: "Learning record synced",
      learningSyncFailed: "Learning record not synced",
      code: "Generated code",
      askAI: "Ask AI to explain",
      aiQuestion: "Analyze this Qiskit circuit. Explain how each gate changes the state, what the final probabilities mean, and what experiment I should try next.",
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
