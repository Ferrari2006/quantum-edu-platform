export const knowledgeModules = [
  {
    id: "orientation",
    order: "01",
    title: "先看见全景",
    shortTitle: "认识量子",
    description: "从问题和应用出发，先建立不依赖公式的整体认识。",
    color: "#ff6b3d",
    articles: [
      {
        id: "what-is-quantum-computing",
        title: "量子计算究竟是什么？",
        summary: "用三个问题分清量子计算、量子力学与经典计算。",
        minutes: 8,
        difficulty: "零基础",
        status: "sample",
        keywords: ["量子计算", "经典计算", "入门", "应用"],
      },
      {
        id: "classical-bit-and-qubit",
        title: "经典比特与量子比特",
        summary: "从开关、硬币和方向三个类比理解信息的不同载体。",
        minutes: 10,
        difficulty: "零基础",
        status: "sample",
        keywords: ["比特", "量子比特", "qubit", "状态"],
      },
      {
        id: "learning-map",
        title: "你的量子学习地图",
        summary: "了解概念、线路、算法和实践之间的先后关系。",
        minutes: 5,
        difficulty: "零基础",
        status: "outline",
        keywords: ["学习路径", "课程", "导学"],
      },
    ],
  },
  {
    id: "intuition",
    order: "02",
    title: "建立核心直觉",
    shortTitle: "核心直觉",
    description: "抓住叠加、相位、干涉与测量这四个关键动作。",
    color: "#7c8cff",
    articles: [
      {
        id: "superposition",
        title: "叠加不是“同时发生”",
        summary: "理解振幅如何共同描述一个量子状态。",
        minutes: 12,
        difficulty: "入门",
        status: "sample",
        keywords: ["叠加", "振幅", "概率"],
      },
      {
        id: "phase-and-interference",
        title: "看不见的相位，如何制造干涉",
        summary: "用波峰与波谷的直觉理解量子算法的核心资源。",
        minutes: 14,
        difficulty: "入门",
        status: "outline",
        keywords: ["相位", "干涉", "振幅"],
      },
      {
        id: "measurement",
        title: "测量：从可能到结果",
        summary: "区分状态、测量概率和一次实验结果。",
        minutes: 12,
        difficulty: "入门",
        status: "sample",
        keywords: ["测量", "坍缩", "概率", "Born rule"],
      },
      {
        id: "bloch-sphere",
        title: "在布洛赫球上看见量子态",
        summary: "把单量子比特的状态变化变成空间中的旋转。",
        minutes: 15,
        difficulty: "进阶",
        status: "outline",
        keywords: ["布洛赫球", "态矢量", "旋转"],
      },
    ],
  },
  {
    id: "circuits",
    order: "03",
    title: "读懂量子线路",
    shortTitle: "量子线路",
    description: "把量子门看作操作，把线路看作一段可执行的思路。",
    color: "#24b57a",
    articles: [
      {
        id: "single-qubit-gates",
        title: "X、Z、H：三扇基础量子门",
        summary: "从翻转、相位与均匀叠加理解最常见的单比特门。",
        minutes: 16,
        difficulty: "入门",
        status: "sample",
        keywords: ["量子门", "X门", "Z门", "H门"],
      },
      {
        id: "multi-qubit-and-cnot",
        title: "多比特系统与 CNOT",
        summary: "理解控制、目标以及联合状态为何不只是两份信息。",
        minutes: 18,
        difficulty: "进阶",
        status: "outline",
        keywords: ["CNOT", "多比特", "张量积"],
      },
      {
        id: "bell-state",
        title: "亲手制备一个 Bell 态",
        summary: "用 H 与 CNOT 走完从初态到纠缠态的每一步。",
        minutes: 15,
        difficulty: "进阶",
        status: "outline",
        keywords: ["Bell态", "纠缠", "H门", "CNOT"],
      },
      {
        id: "read-a-circuit",
        title: "像读乐谱一样读量子线路",
        summary: "认识时间方向、线路、门、测量和输出结果。",
        minutes: 12,
        difficulty: "入门",
        status: "outline",
        keywords: ["量子线路", "电路图", "测量"],
      },
    ],
  },
  {
    id: "algorithms",
    order: "04",
    title: "走近量子算法",
    shortTitle: "经典算法",
    description: "不追求背代码，先理解每个算法如何利用量子特性。",
    color: "#e6a23c",
    articles: [
      {
        id: "deutsch-jozsa",
        title: "Deutsch–Jozsa：一次提问的优势",
        summary: "从黑盒问题看量子并行性与干涉怎样协作。",
        minutes: 18,
        difficulty: "进阶",
        status: "outline",
        keywords: ["Deutsch-Jozsa", "量子并行"],
      },
      {
        id: "grover-search",
        title: "Grover 搜索：放大正确答案",
        summary: "理解 Oracle、振幅放大与平方级加速。",
        minutes: 22,
        difficulty: "进阶",
        status: "outline",
        keywords: ["Grover", "搜索", "Oracle", "振幅放大"],
      },
      {
        id: "variational-algorithms",
        title: "VQE 与 QAOA：让经典和量子协作",
        summary: "认识当前量子设备上常见的混合优化思路。",
        minutes: 24,
        difficulty: "拓展",
        status: "outline",
        keywords: ["VQE", "QAOA", "变分算法", "优化"],
      },
      {
        id: "shor-overview",
        title: "Shor 算法为什么改变密码学",
        summary: "从周期查找到大数分解，理解它的意义与边界。",
        minutes: 25,
        difficulty: "拓展",
        status: "outline",
        keywords: ["Shor", "密码学", "大数分解"],
      },
    ],
  },
  {
    id: "practice",
    order: "05",
    title: "开始动手实践",
    shortTitle: "编程实践",
    description: "用模拟器和真实框架，把概念转换成可运行的线路。",
    color: "#ef5da8",
    articles: [
      {
        id: "qiskit-first-step",
        title: "Qiskit 第一步",
        summary: "认识开发环境、量子线路和一次完整运行流程。",
        minutes: 20,
        difficulty: "入门",
        status: "outline",
        keywords: ["Qiskit", "Python", "开发环境"],
      },
      {
        id: "first-bell-circuit",
        title: "运行你的第一个 Bell 线路",
        summary: "从代码、状态向量到测量计数逐层验证。",
        minutes: 25,
        difficulty: "进阶",
        status: "outline",
        keywords: ["Qiskit", "Bell态", "代码"],
      },
      {
        id: "noise-and-fidelity",
        title: "噪声、保真度与真实量子计算机",
        summary: "理解模拟结果为何和真实设备不完全相同。",
        minutes: 20,
        difficulty: "进阶",
        status: "outline",
        keywords: ["噪声", "保真度", "NISQ", "真实设备"],
      },
    ],
  },
  {
    id: "game-lab",
    order: "06",
    title: "回到游戏验证",
    shortTitle: "游戏实验室",
    description: "把游戏里的选择翻译回量子概念，完成体验到理解的闭环。",
    color: "#26a7dd",
    articles: [
      {
        id: "quantum-hacker-guide",
        title: "《量子小丑牌》概念图鉴",
        summary: "牌、量子门、目标态和保真度分别代表什么。",
        minutes: 10,
        difficulty: "入门",
        status: "outline",
        keywords: ["量子小丑牌", "游戏", "保真度"],
      },
      {
        id: "roulette-and-measurement",
        title: "坍塌轮盘背后的测量",
        summary: "从游戏风险机制回看概率、采样与测量。",
        minutes: 12,
        difficulty: "入门",
        status: "outline",
        keywords: ["坍塌轮盘", "测量", "游戏"],
      },
      {
        id: "quantum-mage-map",
        title: "《量子魔法师》术式映射",
        summary: "把状态旋转、双比特门与战术选择一一对应。",
        minutes: 14,
        difficulty: "进阶",
        status: "outline",
        keywords: ["量子魔法师", "量子门", "游戏"],
      },
    ],
  },
];

export const knowledgeArticles = knowledgeModules.flatMap((module) =>
  module.articles.map((article, index) => ({
    ...article,
    moduleId: module.id,
    moduleTitle: module.title,
    moduleOrder: module.order,
    moduleColor: module.color,
    indexInModule: index,
  })),
);

const sampleContent = {
  "what-is-quantum-computing": {
    eyebrow: "第一站 · 建立全景",
    lead: "量子计算不是一台“什么都更快”的电脑，而是一套使用量子态来表达和处理信息的新方法。",
    objectives: ["说清量子计算与经典计算的差别", "知道量子优势只发生在特定问题上", "建立后续学习所需的四个关键词"],
    sections: [
      {
        title: "先不从公式开始",
        paragraphs: [
          "经典计算机把信息写成 0 和 1，再用逻辑门一步步加工。量子计算机同样处理信息，但它的基本载体是量子比特，操作对象是振幅、相位以及多个量子比特之间的关联。",
          "这意味着它不是把同一道题“算得更用力”，而是允许我们为某些问题设计完全不同的求解过程。",
        ],
        callout: "一个稳妥的心智模型：经典程序安排确定的状态变化；量子程序设计多条可能路径如何相互增强或抵消。",
      },
      {
        title: "它擅长什么，也不擅长什么",
        paragraphs: [
          "量子算法已经在大数分解、无结构搜索、量子系统模拟和部分优化问题中展示出独特思路。但浏览网页、编辑文档或运行普通应用，并不会因为换成量子计算机就自然变快。",
        ],
        bullets: ["模拟分子与材料等量子系统", "在特定结构的问题中减少所需步骤", "与经典计算机协作完成混合计算", "不替代日常通用计算"],
      },
      {
        title: "后面会反复遇到的四个词",
        paragraphs: ["先记住它们的角色，不必急着记住数学定义。后续章节会让这些词逐渐变成可以操作的直觉。"],
        concepts: [
          ["叠加", "用多个基态的振幅共同描述一个量子态"],
          ["相位", "不直接等于概率，却决定不同路径如何干涉"],
          ["纠缠", "多个量子比特形成无法各自独立描述的整体"],
          ["测量", "把量子状态转化为一次可记录的经典结果"],
        ],
      },
    ],
    takeaway: "量子计算的关键不是“同时试完所有答案”，而是设计振幅和相位的演化，让正确结果更容易在测量时出现。",
    gameLink: "在《量子小丑牌》中，手牌对应量子门，得分不是随机魔法，而是线路输出与目标态之间的匹配程度。",
  },
  "classical-bit-and-qubit": {
    eyebrow: "第一站 · 信息的载体",
    lead: "比特像一个只能指向两个离散方向的开关；量子比特则需要振幅与相位共同描述。",
    objectives: ["区分经典比特与量子比特", "理解基态 |0⟩ 与 |1⟩", "避免把量子比特误解为模糊的经典概率"],
    sections: [
      {
        title: "经典比特：读出前后都很明确",
        paragraphs: ["经典比特在任一时刻取 0 或 1。即使我们不知道它的值，这种“不知道”通常只是信息缺失，并不改变它已经处于某个确定状态。"],
      },
      {
        title: "量子比特：状态由两个振幅描述",
        paragraphs: [
          "一个纯量子态可以写成 α|0⟩ + β|1⟩。α 与 β 是复数振幅，它们的模平方给出测量得到 0 或 1 的概率，并满足总概率为 1。",
          "只知道测量概率仍不足以完整描述量子态，因为相位差也会影响之后的干涉结果。",
        ],
        callout: "“50% 得到 0、50% 得到 1”可能对应多个不同量子态；它们在另一组测量方式下会表现不同。",
      },
      {
        title: "为什么不能把它当成旋转中的硬币",
        paragraphs: ["硬币类比适合解释测量的不确定性，却无法表达相位与干涉。使用类比时要知道边界：量子态不是一个被我们暂时看不清的经典对象。"],
        bullets: ["硬币概率描述我们的未知", "量子振幅可以相加并发生干涉", "测量通常会改变后续可观察的状态"],
      },
    ],
    takeaway: "量子比特不只是 0 和 1 的随机混合；振幅和相位一起决定它未来如何演化。",
  },
  superposition: {
    eyebrow: "第二站 · 核心直觉",
    lead: "叠加描述的是量子态的表达方式。真正让它产生计算价值的，是后续操作能让不同振幅发生干涉。",
    objectives: ["理解叠加态的基本表达", "区分振幅与概率", "知道归一化条件的意义"],
    sections: [
      {
        title: "从基向量到叠加",
        paragraphs: ["|0⟩ 与 |1⟩ 可以看作描述单量子比特的两个基向量。其他纯态都能写成它们的线性组合，这种线性组合就是叠加。"],
        callout: "|ψ⟩ = α|0⟩ + β|1⟩，其中 |α|² + |β|² = 1。",
      },
      {
        title: "振幅不是普通概率",
        paragraphs: ["概率只能取非负实数，而振幅可以带符号与复相位。正因为如此，两条路径的振幅能够增强，也能够抵消。"],
        concepts: [
          ["振幅", "状态表达中的系数，可以携带相位"],
          ["概率", "振幅模平方得到的可观测统计"],
          ["归一化", "保证所有可能测量结果的总概率为 1"],
        ],
      },
      {
        title: "H 门制造的均匀叠加",
        paragraphs: ["从 |0⟩ 出发施加 H 门，会得到测量概率各为一半的叠加态。再次施加 H 门却会回到 |0⟩，这正说明相位与干涉比“随机一半”更接近事实。"],
      },
    ],
    takeaway: "叠加提供多条振幅路径，干涉决定这些路径最后是被放大还是被抵消。",
  },
  measurement: {
    eyebrow: "第二站 · 从可能到结果",
    lead: "测量不是偷看一个早已写好的答案，而是按量子态给出的分布产生一次经典结果。",
    objectives: ["区分状态、概率分布与采样结果", "理解为什么要重复运行线路", "认识测量基的作用"],
    sections: [
      {
        title: "一次运行只给出一个结果",
        paragraphs: ["对单个量子比特做计算基测量，一次实验记录为 0 或 1。要估计概率分布，需要准备同样的状态并重复运行很多次。"],
      },
      {
        title: "从 shots 看到统计规律",
        paragraphs: ["模拟器和真实设备常用 shots 表示重复次数。次数越多，频率通常越接近理论概率，但有限采样始终会有波动。"],
        bullets: ["状态向量描述测量前的量子态", "概率分布由振幅的模平方计算", "计数结果来自有限次重复采样"],
      },
      {
        title: "换一个测量基，会看见另一面",
        paragraphs: ["计算基适合区分 |0⟩ 和 |1⟩，却不能直接看见某些相位差。通过先旋转状态再测量，我们可以在不同测量基下读取互补信息。"],
        callout: "游戏里的“坍塌轮盘”适合表达一次测量的风险；完整概念还需要加上重复采样和测量基。",
      },
    ],
    takeaway: "量子线路的输出不是单个神秘答案，而是状态、测量规则与有限采样共同形成的结果。",
    gameLink: "观察游戏里的概率柱状图，再触发一次 Observe：前者是分布，后者是从分布中抽到的一次结果。",
  },
  "single-qubit-gates": {
    eyebrow: "第三站 · 读懂量子线路",
    lead: "量子门是可逆的状态变换。X、Z 与 H 分别帮助我们理解翻转、相位和基之间的转换。",
    objectives: ["理解三种基础门的直觉", "预测简单门序列的结果", "把游戏手牌与真实线路操作对应起来"],
    sections: [
      {
        title: "X 门：交换两个基态",
        paragraphs: ["X 门把 |0⟩ 变为 |1⟩，也把 |1⟩ 变为 |0⟩。它最像经典逻辑中的 NOT，但对一般叠加态的作用仍是完整的线性变换。"],
      },
      {
        title: "Z 门：概率不变，相位改变",
        paragraphs: ["Z 门保持 |0⟩ 不变，并给 |1⟩ 分量加上负号。紧接着测量时概率可能没有变化，但后续经过 H 等操作后，相位差会转化为可见的概率差。"],
      },
      {
        title: "H 门：在两种观察方式间架桥",
        paragraphs: ["H 门可以从基态制造均匀叠加，也能把特定叠加态还原为基态。H·H 等于恒等操作，是理解干涉的最短实验之一。"],
        concepts: [
          ["X", "交换 |0⟩ 与 |1⟩"],
          ["Z", "改变 |1⟩ 分量的相位"],
          ["H", "连接计算基与叠加基"],
        ],
      },
    ],
    takeaway: "不要只背门矩阵；先问每扇门改变的是测量概率、相位，还是我们观察状态的方式。",
    gameLink: "在游戏里连续打出两张相同的 X、Z 或 H 卡，观察线路是否回到原来的状态。",
  },
};

function makeOutlineContent(article) {
  return {
    eyebrow: `${article.moduleOrder} · ${article.moduleTitle}`,
    lead: article.summary,
    objectives: ["明确本节核心概念与前置知识", "补充一个直觉类比与类比边界", "加入一个可操作的线路、练习或游戏关联"],
    sections: [
      {
        title: "为什么要学这个",
        paragraphs: ["【待整理】用一个学习者会遇到的真实问题开场，说明本节概念解决什么困惑。"],
      },
      {
        title: "核心直觉",
        paragraphs: ["【待整理】先给无公式解释，再补充标准定义；明确哪些常见类比可用、哪些地方会失效。"],
        callout: "编辑提示：这里适合放一句可被记住的核心结论。",
      },
      {
        title: "动手验证",
        paragraphs: ["【待整理】加入一个最小示例、交互操作、游戏关卡或纸笔练习，并给出预期结果。"],
        bullets: ["观察什么发生了变化", "解释为什么会变化", "尝试修改一个条件并预测结果"],
      },
    ],
    takeaway: "本页已完成阅读框架，等待团队补充、审校并发布正式内容。",
  };
}

export function getKnowledgeArticle(articleId) {
  const article = knowledgeArticles.find((item) => item.id === articleId);
  if (!article) return null;
  return {
    ...article,
    ...(sampleContent[articleId] || makeOutlineContent(article)),
  };
}

export function getNextArticle(articleId) {
  const index = knowledgeArticles.findIndex((item) => item.id === articleId);
  return index >= 0 && index < knowledgeArticles.length - 1 ? knowledgeArticles[index + 1] : null;
}
